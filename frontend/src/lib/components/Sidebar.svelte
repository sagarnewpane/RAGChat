<script>
	let {
		conversations,
		conversationId,
		documentName,
		sidebarOpen,
		onNewChat,
		onLoadConversation,
		onClearDocuments,
		onCloseSidebar
	} = $props();
</script>

<!-- Mobile overlay -->
<div
	class="fixed inset-0 bg-black/50 z-40 lg:hidden {sidebarOpen ? 'block' : 'hidden'}"
	onclick={onCloseSidebar}
	onkeydown={(e) => e.key === 'Escape' && onCloseSidebar()}
	role="button"
	tabindex="0"
></div>

<aside
	class="fixed lg:static inset-y-0 left-0 z-50 w-64 bg-gray-900 text-white transform transition-transform lg:translate-x-0 {sidebarOpen
		? 'translate-x-0'
		: '-translate-x-full'}"
>
	<div class="flex flex-col h-full">
		<div class="p-4 border-b border-gray-700">
			<button
				onclick={onNewChat}
				class="w-full py-2 px-4 border border-gray-600 rounded-lg hover:bg-gray-800 transition text-sm"
			>
				New chat
			</button>
		</div>

		<div class="flex-1 overflow-y-auto p-2">
			<p class="px-2 py-1 text-xs text-gray-500 uppercase"><i>History</i></p>
			{#each conversations as conv}
				<button
					onclick={() => onLoadConversation(conv.id)}
					class="w-full text-left px-3 py-2 rounded-lg hover:bg-gray-800 text-sm truncate {conversationId === conv.id ? 'bg-gray-800' : ''}"
				>
					{conv.title}
				</button>
			{/each}
			{#if conversations.length === 0}
				<p class="px-3 py-2 text-sm text-gray-500">No chats...</p>
			{/if}
		</div>

		<div class="p-4 border-t border-gray-700">
			<div class="text-xs text-gray-400 mb-2 truncate" title={documentName}>
				📄 {documentName}
			</div>
			<button
				onclick={onClearDocuments}
				class="w-full py-2 text-sm text-red-400 hover:text-red-300 hover:bg-gray-800 rounded transition"
			>
				Delete document
			</button>
		</div>
	</div>
</aside>
