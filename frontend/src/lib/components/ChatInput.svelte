<script>
	import { Send } from 'lucide-svelte';
	let { value = $bindable(), sending, onSend } = $props();

	function handleKeydown(e) {
		if (e.key === 'Enter' && !e.shiftKey) {
			e.preventDefault();
			onSend();
		}
	}
</script>

<div class=" bg-white p-4">
	<div class="max-w-3xl mx-auto flex gap-3">
		<textarea
			bind:value
			onkeydown={handleKeydown}
			placeholder="Type your message..."
			rows="1"
			class="flex-1 resize-none border border-opacity-10  border-red-600 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent"
			disabled={sending}
		></textarea>
		<button
			onclick={onSend}
			disabled={sending || !value.trim()}
			class="px-4 py-3 bg-red-600 text-white rounded-xl hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition"
		>
			<Send class="w-5 h-5" />
		</button>
	</div>
</div>
