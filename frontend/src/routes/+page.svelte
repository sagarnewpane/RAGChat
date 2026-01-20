<script>
	import { Menu } from 'lucide-svelte';
	import Sidebar from '$lib/components/Sidebar.svelte';
	import UploadScreen from '$lib/components/UploadScreen.svelte';
	import ChatMessage from '$lib/components/ChatMessage.svelte';
	import ChatInput from '$lib/components/ChatInput.svelte';
	import TypingIndicator from '$lib/components/TypingIndicator.svelte';
	import * as api from '$lib/api.js';

	let hasDocument = $state(false);
	let documentName = $state(null);
	let uploading = $state(false);
	let uploadError = $state('');

	let messages = $state([]);
	let inputMessage = $state('');
	let sending = $state(false);
	let conversationId = $state('');

	let conversations = $state([]);
	let sidebarOpen = $state(false);

	let chatContainer = $state();

	$effect(() => {
		loadInitialData();
	});

	$effect(() => {
		if (messages.length && chatContainer) {
			setTimeout(() => {
				chatContainer.scrollTop = chatContainer.scrollHeight;
			}, 50);
		}
	});

	async function loadInitialData() {
		try {
			const status = await api.checkDocumentStatus();
			hasDocument = status.has_documents;
			documentName = status.filename;

			conversations = await api.loadConversations();
		} catch (err) {
			console.error('Failed to load initial data:', err);
		}
	}

	async function handleUpload(event) {
		const file = event.target.files[0];
		if (!file) return;

		uploadError = '';
		uploading = true;

		try {
			await api.uploadDocument(file);
			await loadInitialData();
			startNewChat();
		} catch (err) {
			uploadError = err.message;
		} finally {
			uploading = false;
		}
	}

	async function handleClearDocuments() {
		if (!confirm('This will delete all documents and chat history. Continue?')) return;

		try {
			await api.clearDocuments();
			hasDocument = false;
			documentName = null;
			messages = [];
			conversationId = '';
			conversations = [];
		} catch (err) {
			console.error('Failed to clear:', err);
		}
	}

	function startNewChat() {
		messages = [];
		conversationId = '';
		sidebarOpen = false;
	}

	async function handleLoadConversation(id) {
		try {
			const history = await api.getChatHistory(id);
			messages = history;
			conversationId = id;
			sidebarOpen = false;
		} catch (err) {
			console.error('Failed to load conversation:', err);
			alert('Failed to load conversation');
		}
	}

	async function handleSendMessage() {
		if (!inputMessage.trim() || sending) return;

		const userMsg = inputMessage.trim();
		inputMessage = '';
		messages = [...messages, { role: 'user', content: userMsg }];
		sending = true;

		try {
			const data = await api.sendChatMessage(userMsg, conversationId);
			conversationId = data.conversation_id;
			messages = [...messages, { role: 'model', content: data.answer }];
			conversations = await api.loadConversations();
		} catch (err) {
			messages = [...messages, { role: 'model', content: `Error: ${err.message}` }];
		} finally {
			sending = false;
		}
	}
</script>

<div class="h-screen flex bg-gray-50">
	{#if hasDocument}
		<Sidebar
			{conversations}
			{conversationId}
			{documentName}
			{sidebarOpen}
			onNewChat={startNewChat}
			onLoadConversation={handleLoadConversation}
			onClearDocuments={handleClearDocuments}
			onCloseSidebar={() => (sidebarOpen = false)}
		/>
	{/if}

	<main class="flex-1 flex flex-col min-w-0">
		{#if !hasDocument}
			<UploadScreen {uploading} {uploadError} onUpload={handleUpload} />
		{:else}
			<header class="flex items-center px-4 py-5 bg-white">
				<button onclick={() => (sidebarOpen = true)} class="lg:hidden p-2 -ml-2 hover:bg-gray-100 rounded">
					<Menu class="w-5 h-5" />
				</button>
				<h1 class="text-xl font-bold ml-2 lg:ml-0">RAG Chat</h1>
			</header>

			<div bind:this={chatContainer} class="flex-1 overflow-y-auto">
				{#if messages.length === 0}
					<div class="h-full flex items-center justify-center text-gray-400">
						<p>Ask anything about your document</p>
					</div>
				{:else}
					<div class="max-w-3xl mx-auto py-6 px-4">
						{#each messages as msg}
							<ChatMessage role={msg.role} content={msg.content} />
						{/each}
						{#if sending}
							<TypingIndicator />
						{/if}
					</div>
				{/if}
			</div>

			<ChatInput bind:value={inputMessage} {sending} onSend={handleSendMessage} />
		{/if}
	</main>
</div>
