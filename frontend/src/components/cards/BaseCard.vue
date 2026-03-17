<template>
  <div class="card flex flex-col h-full">
    <!-- Header (drag handle) -->
    <div class="drag-handle flex items-center justify-between px-4 py-3 border-b border-border bg-card/60 select-none">
      <div class="flex items-center gap-2">
        <span class="text-lg">{{ icon }}</span>
        <span class="font-semibold text-sm tracking-wide text-gray-300">{{ title }}</span>
      </div>
      <div class="flex items-center gap-2">
        <slot name="header-actions" />
        <button
          class="text-gray-500 hover:text-gray-300 transition-colors text-xs"
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
  icon:  { type: String, default: '📊' },
})
defineEmits(['remove'])
</script>
