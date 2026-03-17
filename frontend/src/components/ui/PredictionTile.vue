<template>
  <div
    class="flex flex-col items-center justify-between rounded-xl p-3 transition-all duration-500"
    :class="bgClass"
  >
    <!-- Timeframe label -->
    <p class="text-xs font-semibold text-white/70 mb-2">{{ label }}</p>

    <!-- Traffic-light dot -->
    <div
      class="relative w-10 h-10 rounded-full flex items-center justify-center shadow-lg mb-2"
      :class="dotClass"
    >
      <span class="text-white font-bold text-sm z-10">{{ score }}</span>
      <div
        v-if="signal !== 'NEUTRAL'"
        class="absolute inset-0 rounded-full opacity-40 animate-ping"
        :class="dotClass"
      />
    </div>

    <!-- Signal text -->
    <p
      class="text-xs font-bold tracking-wide"
      :class="textClass"
    >{{ signal }}</p>

    <!-- Confidence bar -->
    <div class="w-full mt-2 h-1 rounded-full bg-white/10 overflow-hidden">
      <div
        class="h-full rounded-full transition-all duration-700"
        :class="dotClass"
        :style="{ width: (data?.confidence ?? 0) * 100 + '%' }"
      />
    </div>
    <p class="text-[10px] text-white/40 mt-1">
      {{ ((data?.confidence ?? 0) * 100).toFixed(0) }}% conf
    </p>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  label: { type: String, required: true },
  data:  { type: Object, default: null },
})

const score  = computed(() => props.data?.score ?? '—')
const signal = computed(() => props.data?.signal ?? 'N/A')

const dotClass = computed(() => {
  const s = signal.value
  if (s === 'BUY')  return 'bg-buy'
  if (s === 'SELL') return 'bg-sell'
  return 'bg-neutral'
})

const bgClass = computed(() => {
  const s = signal.value
  if (s === 'BUY')  return 'bg-buy/10 border border-buy/30'
  if (s === 'SELL') return 'bg-sell/10 border border-sell/30'
  return 'bg-surface border border-border'
})

const textClass = computed(() => {
  const s = signal.value
  if (s === 'BUY')  return 'text-buy'
  if (s === 'SELL') return 'text-sell'
  return 'text-neutral'
})
</script>
