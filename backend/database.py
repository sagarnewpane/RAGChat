import os
from datetime import datetime, timezone
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pgvector.sqlalchemy import Vector

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/rag_db")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class DocumentChunk(Base):
    """Stores document text chunks with their vector embeddings for similarity search."""
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True)
    filename = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    embedding = Column(Vector(768))  # Gemini embedding dimension


class ChatHistory(Base):
    """Stores conversation messages for multi-turn chat support."""
    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(String, index=True, nullable=False)
    role = Column(String, nullable=False)  # "user" or "model"
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


def init_db():
    """Initialize database with pgvector extension and create tables."""
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()
    Base.metadata.create_all(bind=engine)