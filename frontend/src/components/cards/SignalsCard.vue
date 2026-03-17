<template>
  <BaseCard title="Buy / Sell Signal" icon="🚦" @remove="$emit('remove')">
    <div v-if="summary" class="space-y-5">

      <!-- Big signal light -->
      <div class="flex flex-col items-center justify-center gap-3 pt-2">
        <div
          class="relative w-24 h-24 rounded-full flex items-center justify-center shadow-2xl transition-all duration-700"
          :class="lightClass"
        >
          <span class="text-3xl font-black text-white z-10">{{ summary.score }}</span>
          <!-- glow ring -->
          <div class="absolute inset-0 rounded-full opacity-30 animate-ping" :class="lightClass" />
        </div>
        <p class="text-xl font-bold tracking-wide" :class="textClass">{{ summary.signal }}</p>
        <p class="text-xs text-gray-500">Overall indicator consensus</p>
      </div>

      <!-- Score bar -->
      <div>
        <div class="flex justify-between text-xs text-gray-500 mb-1">
          <span>SELL</span>
          <span>NEUTRAL</span>
          <span>BUY</span>
        </div>
        <div class="relative h-3 rounded-full bg-gradient-to-r from-sell via-neutral to-buy overflow-hidden">
          <div
            class="absolute top-0 bottom-0 w-3 rounded-full bg-white shadow-lg transition-all duration-700"
            :style="{ left: `calc(${summary.score}% - 6px)` }"
          />
        </div>
        <div class="flex justify-between text-xs text-gray-600 mt-1">
          <span>1</span>
          <span>50</span>
          <span>100</span>
        </div>
      </div>

      <!-- Vote breakdown -->
      <div class="grid grid-cols-3 gap-2 text-center">
        <div class="bg-surface rounded-lg py-2">
          <p class="text-buy text-lg font-bold">{{ summary.buy_count }}</p>
          <p class="text-xs text-gray-500">BUY</p>
        </div>
        <div class="bg-surface rounded-lg py-2">
          <p class="text-neutral text-lg font-bold">{{ summary.neutral_count }}</p>
          <p class="text-xs text-gray-500">NEUTRAL</p>
        </div>
        <div class="bg-surface rounded-lg py-2">
          <p class="text-sell text-lg font-bold">{{ summary.sell_count }}</p>
          <p class="text-xs text-gray-500">SELL</p>
        </div>
      </div>

      <!-- Individual indicator signals -->
      <div class="space-y-1">
        <p class="text-xs text-gray-500 uppercase tracking-widest mb-2">Per-indicator signals</p>
        <div
          v-for="(sig, key) in signals"
          :key="key"
          class="flex items-center justify-between px-3 py-1.5 rounded-lg bg-surface"
        >
          <span class="text-xs text-gray-400 capitalize">{{ indicatorLabel(key) }}</span>
          <div class="flex items-center gap-2">
            <div class="h-1.5 w-16 bg-border rounded-full overflow-hidden">
              <div
                class="h-full rounded-full transition-all duration-500"
                :class="sig.signal === 'BUY' ? 'bg-buy' : sig.signal === 'SELL' ? 'bg-sell' : 'bg-neutral'"
                :style="{ width: (sig.strength * 100) + '%' }"
              />
            </div>
            <span
              class="text-xs font-semibold w-14 text-right"
              :class="sig.signal === 'BUY' ? 'text-buy' : sig.signal === 'SELL' ? 'text-sell' : 'text-neutral'"
            >{{ sig.signal }}</span>
          </div>
        </div>
      </div>

    </div>

    <div v-else class="flex items-center justify-center h-24 text-gray-500 text-sm">
      Waiting for data…
    </div>
  </BaseCard>
</template>

<script setup>
import { computed } from 'vue'
import { useMarketStore } from '@/store/market'
import BaseCard from './BaseCard.vue'

defineEmits(['remove'])

const store   = useMarketStore()
const summary = computed(() => store.signalSummary)
const signals = computed(() => store.indicatorSignals)

const lightClass = computed(() => {
  if (!summary.value) return 'bg-gray-600'
  const s = summary.value.signal
  if (s === 'BUY')     return 'bg-buy'
  if (s === 'SELL')    return 'bg-sell'
  return 'bg-neutral'
})

const textClass = computed(() => {
  if (!summary.value) return 'text-gray-400'
  const s = summary.value.signal
  if (s === 'BUY')  return 'text-buy'
  if (s === 'SELL') return 'text-sell'
  return 'text-neutral'
})

const LABELS = {
  rsi: 'RSI', macd: 'MACD', stoch: 'Stochastic', ema: 'EMA cross',
  bbands: 'Bollinger Bands', adx: 'ADX', cci: 'CCI', willr: 'Williams %R',
}

function indicatorLabel(key) {
  return LABELS[key] ?? key
}
</script>
