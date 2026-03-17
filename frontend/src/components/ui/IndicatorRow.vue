<template>
  <div class="flex items-center justify-between py-1.5 border-b border-border/50 last:border-0">
    <div class="flex items-center gap-2 min-w-0">
      <span
        class="w-2 h-2 rounded-full flex-shrink-0"
        :class="typeColor"
      />
      <span class="text-xs text-gray-400 truncate">{{ label }}</span>
    </div>
    <div class="flex items-center gap-3 flex-shrink-0 ml-2">
      <slot />
      <span class="text-xs font-mono text-gray-200 w-20 text-right">
        {{ fmtVal(value) }}
      </span>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  label: { type: String, required: true },
  value: { type: Number, default: null },
  type:  { type: String, default: 'trend' }, // trend | oscillator | volatility | volume
})

const TYPE_COLORS = {
  trend:      'bg-blue-400',
  oscillator: 'bg-purple-400',
  volatility: 'bg-yellow-400',
  volume:     'bg-cyan-400',
}
const typeColor = TYPE_COLORS[props.type] ?? 'bg-gray-400'

function fmtVal(val) {
  if (val == null) return '—'
  const n = Number(val)
  if (Math.abs(n) >= 100000) return n.toExponential(2)
  if (Math.abs(n) >= 1000)   return n.toLocaleString('en-US', { maximumFractionDigits: 0 })
  if (Math.abs(n) >= 1)      return n.toFixed(2)
  return n.toFixed(5)
}
</script>
