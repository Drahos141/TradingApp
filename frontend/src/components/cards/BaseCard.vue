<template>
  <div class="cyber-card flex flex-col h-full">
    <!-- Header (drag handle) -->
    <div class="drag-handle flex items-center justify-between px-4 py-3 border-b border-cyan-900/40 bg-cyan-950/20 select-none">
      <div class="flex items-center gap-2">
        <span class="text-base leading-none">{{ icon }}</span>
        <span class="font-semibold text-sm tracking-widest text-cyan-400 font-mono uppercase">{{ title }}</span>
      </div>
      <div class="flex items-center gap-2">
        <slot name="header-actions" />
        <button
          class="text-cyan-800 hover:text-sell transition-colors text-xs font-mono"
          title="Remove card"
          @click="$emit('remove')"
        >✕</button>
      </div>
    </div>

    <!-- Body -->
    <div class="flex-1 overflow-auto p-4">
      <slot />
    </div>
  </div>
</template>

<script setup>
defineProps({
  title: { type: String, required: true },
  icon:  { type: String, default: '◈' },
})
defineEmits(['remove'])
</script>
