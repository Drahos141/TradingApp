<template>
  <BaseCard title="Price Overview" icon="💰" @remove="$emit('remove')">
    <div v-if="price" class="space-y-3">
      <!-- Symbol + price -->
      <div class="flex items-end justify-between">
        <div>
          <p class="text-xs text-gray-500 uppercase tracking-widest">{{ store.selectedSymbol }}</p>
          <p class="text-3xl font-bold text-white">{{ fmt(price.price) }}</p>
        </div>
        <div
          class="text-right"
          :class="price.change_pct >= 0 ? 'text-buy' : 'text-sell'"
        >
          <p class="text-2xl font-semibold">
            {{ price.change_pct >= 0 ? '+' : '' }}{{ price.change_pct.toFixed(2) }}%
          </p>
          <p class="text-xs text-gray-500">24h change</p>
        </div>
      </div>

      <!-- Change bar -->
      <div class="h-1.5 rounded-full bg-border overflow-hidden">
        <div
          class="h-full rounded-full transition-all duration-500"
          :class="price.change_pct >= 0 ? 'bg-buy' : 'bg-sell'"
          :style="{ width: Math.min(Math.abs(price.change_pct) * 5, 100) + '%' }"
        />
      </div>

      <!-- Extra info -->
      <div class="grid grid-cols-2 gap-2 mt-2">
        <div class="bg-surface rounded-lg p-2">
          <p class="text-xs text-gray-500">Prev Close</p>
          <p class="text-sm font-medium">{{ fmt(price.prev_close) }}</p>
        </div>
        <div class="bg-surface rounded-lg p-2">
          <p class="text-xs text-gray-500">Ticker</p>
          <p class="text-sm font-medium text-gray-400">{{ price.ticker }}</p>
        </div>
      </div>
    </div>

    <div v-else class="flex items-center justify-center h-20 text-gray-500 text-sm">
      No price data
    </div>
  </BaseCard>
</template>

<script setup>
import { computed } from 'vue'
import { useMarketStore } from '@/store/market'
import BaseCard from './BaseCard.vue'

defineEmits(['remove'])

const store = useMarketStore()
const price = computed(() => store.price)

function fmt(val) {
  if (val == null) return '—'
  if (val >= 1000) return val.toLocaleString('en-US', { maximumFractionDigits: 2 })
  if (val >= 1)    return val.toFixed(4)
  return val.toFixed(6)
}
</script>
