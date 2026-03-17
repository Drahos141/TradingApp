<template>
  <div class="relative h-2 rounded-full bg-border overflow-visible">
    <div
      class="h-full rounded-full transition-all duration-500"
      :class="barColor"
      :style="{ width: pct + '%' }"
    />
    <!-- low/high zone markers -->
    <div
      class="absolute top-0 bottom-0 border-l border-white/20"
      :style="{ left: lowPct + '%' }"
    />
    <div
      class="absolute top-0 bottom-0 border-l border-white/20"
      :style="{ left: highPct + '%' }"
    />
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  value: { type: Number, default: null },
  min:   { type: Number, default: 0 },
  max:   { type: Number, default: 100 },
  low:   { type: Number, default: 30 },
  high:  { type: Number, default: 70 },
})

const pct = computed(() => {
  if (props.value == null) return 0
  return Math.min(100, Math.max(0, ((props.value - props.min) / (props.max - props.min)) * 100))
})

const lowPct  = computed(() => ((props.low  - props.min) / (props.max - props.min)) * 100)
const highPct = computed(() => ((props.high - props.min) / (props.max - props.min)) * 100)

const barColor = computed(() => {
  const v = props.value
  if (v == null) return 'bg-gray-600'
  if (v <= props.low)  return 'bg-buy'
  if (v >= props.high) return 'bg-sell'
  return 'bg-neutral'
})
</script>
