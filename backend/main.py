import os
import io
import uuid
from pathlib import Path
from contextlib import asynccontextmanager
import markdown2
from bs4 import BeautifulSoup
from pypdf import PdfReader
from sqlalchemy import func
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from google import genai
from google.genai import types
from langchain_text_splitters import RecursiveCharacterTextSplitter
from dotenv import load_dotenv

from database import SessionLocal, DocumentChunk, ChatHistory, init_db
from models import ChatRequest

# Load .env from root directory (works for both local dev and Docker)
load_dotenv(Path(__file__).parent.parent / ".env")

# Configuration
MODEL_ID = "gemini-2.5-flash"
EMBEDDING_MODEL = "gemini-embedding-001"
EMBEDDING_DIMENSION = 768
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 100
TOP_K_CHUNKS = 5

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup."""
    init_db()
    yield


app = FastAPI(title="RAG Chat API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL", "http://localhost:5173")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    """Dependency that provides a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



@app.post("/upload")
async def upload_document(file: UploadFile = File(...), db=Depends(get_db)):
    """Upload a document, chunk it, generate embeddings, and store for RAG retrieval."""
    try:
        file_bytes = await file.read()
        content = extract_text_from_file(file.filename, file_bytes)

        if not content.strip():
            raise HTTPException(status_code=400, detail="The uploaded file is empty or unreadable.")

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP
        )
        chunks = text_splitter.split_text(content)

        for chunk in chunks:
            embedding = client.models.embed_content(
                model=EMBEDDING_MODEL,
                contents=chunk,
                config=types.EmbedContentConfig(output_dimensionality=EMBEDDING_DIMENSION)
            ).embeddings[0].values

            db.add(DocumentChunk(
                filename=file.filename,
                content=chunk,
                embedding=embedding
            ))

        db.commit()
        return {
            "status": "success",
            "filename": file.filename,
            "chunks_created": len(chunks),
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to process document: {str(e)}")

SYSTEM_PROMPT = """You are a helpful assistant that answers questions based on the provided context.
                    Rules:
                    - Only use information from the context to answer
                    - If the context doesn't contain relevant information, say "Document has no information regarding this."
                    - Be concise and direct
                    - Do not use markdown formatting"""


@app.post("/chat")
async def chat(request: ChatRequest, db=Depends(get_db)):
    """Process a chat message: retrieve relevant chunks and generate a response."""
    if db.query(DocumentChunk).count() == 0:
        raise HTTPException(
            status_code=400,
            detail="No documents found. Please upload a document first."
        )

    conversation_id = request.conversation_id.strip() if request.conversation_id else ""
    if not conversation_id:
        conversation_id = str(uuid.uuid4())

    # Retrieve conversation history
    past_messages = db.query(ChatHistory).filter(
        ChatHistory.conversation_id == conversation_id
    ).order_by(ChatHistory.created_at.asc()).all()

    # Embed the query and find similar chunks
    query_embedding = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=request.query,
        config=types.EmbedContentConfig(output_dimensionality=EMBEDDING_DIMENSION)
    ).embeddings[0].values

    relevant_chunks = db.query(DocumentChunk).order_by(
        DocumentChunk.embedding.l2_distance(query_embedding)
    ).limit(TOP_K_CHUNKS).all()

    context = "\n---\n".join(chunk.content for chunk in relevant_chunks)

    # Build conversation for the LLM
    contents = [
        types.Content(role=msg.role, parts=[types.Part.from_text(text=msg.content)])
        for msg in past_messages
    ]
    prompt = f"Context:\n{context}\n\nQuestion: {request.query}"
    contents.append(types.Content(role="user", parts=[types.Part.from_text(text=prompt)]))

    # Generate response
    response_text = ""
    for chunk in client.models.generate_content_stream(
        model=MODEL_ID,
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            thinking_config=types.ThinkingConfig(thinking_budget=0)
        )
    ):
        if chunk.text:
            response_text += chunk.text

    # Persist conversation
    db.add(ChatHistory(conversation_id=conversation_id, role="user", content=request.query))
    db.add(ChatHistory(conversation_id=conversation_id, role="model", content=response_text))
    db.commit()

    return {"answer": response_text, "conversation_id": conversation_id}

@app.delete("/clear-documents")
async def clear_documents(db=Depends(get_db)):
    """Remove all stored documents and chat history."""
    try:
        db.query(DocumentChunk).delete()
        db.query(ChatHistory).delete()
        db.commit()
        return {"status": "success"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/chat/history/{conversation_id}")
async def get_chat_history(conversation_id: str, db=Depends(get_db)):
    """Retrieve chat history for a conversation."""
    messages = db.query(ChatHistory).filter(
        ChatHistory.conversation_id == conversation_id
    ).order_by(ChatHistory.created_at.asc()).all()

    return [{"role": msg.role, "content": msg.content} for msg in messages]


@app.get("/documents/status")
async def get_document_status(db=Depends(get_db)):
    """Check if any documents have been uploaded."""
    chunk = db.query(DocumentChunk).first()
    return {
        "has_documents": chunk is not None,
        "filename": chunk.filename if chunk else None
    }


@app.get("/conversations")
async def list_conversations(db=Depends(get_db)):
    """List all conversation sessions with their first message as title."""
    conversations = db.query(
        ChatHistory.conversation_id,
        func.min(ChatHistory.content).label("first_message"),
        func.min(ChatHistory.created_at).label("created_at")
    ).filter(
        ChatHistory.role == "user"
    ).group_by(
        ChatHistory.conversation_id
    ).order_by(
        func.max(ChatHistory.created_at).desc()
    ).all()

    return [
        {
            "id": c.conversation_id,
            "title": (c.first_message[:50] + "...") if len(c.first_message) > 50 else c.first_message,
            "created_at": c.created_at.isoformat()
        }
        for c in conversations
    ]


# --- Helper Functions ---

SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md"}


def extract_text_from_file(filename: str, file_bytes: bytes) -> str:
    """Extract text content from PDF, TXT, or Markdown files."""
    ext = os.path.splitext(filename)[1].lower()

    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported file type. Supported: {', '.join(SUPPORTED_EXTENSIONS)}"
        )

    if ext == ".pdf":
        reader = PdfReader(io.BytesIO(file_bytes))
        return " ".join(
            page.extract_text() for page in reader.pages if page.extract_text()
        )

    if ext == ".md":
        html = markdown2.markdown(
            file_bytes.decode("utf-8"),
            extras=["fenced-code-blocks", "tables"]
        )
        return BeautifulSoup(html, "html.parser").get_text(separator=" ", strip=True)

    # .txt
    return file_bytes.decode("utf-8")