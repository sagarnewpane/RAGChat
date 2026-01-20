<script>
	let { role, content } = $props();
</script>

<div class="mb-6 {role === 'user' ? 'text-right' : ''}">
	<div
		class="inline-block max-w-[85%] px-4 py-3 rounded-2xl {role === 'user'
			? 'bg-red-600 text-white'
			: 'bg-gray-200 text-gray-900'}"
	>
		<p class="whitespace-pre-wrap text-sm">{content}</p>
	</div>
</div>
