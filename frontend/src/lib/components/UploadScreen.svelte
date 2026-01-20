<script>
	import { FileText, CloudUpload } from 'lucide-svelte';
	let { uploading, uploadError, onUpload } = $props();
</script>

<div class="flex-1 flex items-center justify-center p-6">
	<div class="max-w-md w-full text-center">
		<div class="mb-8">
			<div class="w-16 h-16 mx-auto mb-4 bg-gray-200 rounded-full flex items-center justify-center">
				<FileText class="w-8 h-8 text-gray-500" />
			</div>
			<h1 class="text-3xl font-bold text-gray-900 mb-2">RAG Chat</h1>
			<p class="text-gray-600">Upload a document to start chatting</p>
		</div>

		<label
			class="block w-full p-8 border-2 border-dashed border-gray-300 rounded-xl cursor-pointer hover:border-gray-400 hover:bg-gray-50 transition {uploading ? 'opacity-50 pointer-events-none' : ''}"
		>
			<input
				type="file"
				accept=".pdf,.txt,.md"
				onchange={onUpload}
				class="hidden"
				disabled={uploading}
			/>
			<CloudUpload class="w-10 h-10 mx-auto mb-3 text-gray-400" />
			{#if uploading}
				<p class="text-gray-600">Processing...</p>
			{:else}
				<p class="text-gray-600 mb-1">Click to upload</p>
				<p class="text-sm text-gray-400">PDF, TXT, or Markdown</p>
			{/if}
		</label>

		{#if uploadError}
			<p class="mt-4 text-sm text-red-600">{uploadError}</p>
		{/if}
	</div>
</div>
