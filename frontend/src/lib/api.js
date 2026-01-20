const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export async function checkDocumentStatus() {
	const res = await fetch(`${API_URL}/documents/status`);
	return res.json();
}

export async function loadConversations() {
	const res = await fetch(`${API_URL}/conversations`);
	return res.json();
}

export async function uploadDocument(file) {
	const formData = new FormData();
	formData.append('file', file);

	const res = await fetch(`${API_URL}/upload`, {
		method: 'POST',
		body: formData
	});

	if (!res.ok) {
		const err = await res.json();
		throw new Error(err.detail || 'Upload failed');
	}

	return res.json();
}

export async function clearDocuments() {
	const res = await fetch(`${API_URL}/clear-documents`, { method: 'DELETE' });
	return res.json();
}

export async function getChatHistory(conversationId) {
	const res = await fetch(`${API_URL}/chat/history/${conversationId}`);
	if (!res.ok) {
		const err = await res.json();
		throw new Error(err.detail || 'Failed to load conversation');
	}
	return res.json();
}

export async function sendChatMessage(query, conversationId) {
	const res = await fetch(`${API_URL}/chat`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ query, conversation_id: conversationId })
	});

	if (!res.ok) {
		const err = await res.json();
		throw new Error(err.detail);
	}

	return res.json();
}
