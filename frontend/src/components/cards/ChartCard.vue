<template>
  <BaseCard title="Price Chart" icon="📈" @remove="$emit('remove')">
    <template #header-actions>
      <select
        v-model="localTf"
        class="bg-surface border border-border rounded px-2 py-0.5 text-xs text-gray-300 focus:outline-none"
        @change="store.setTimeframe(localTf)"
      >
        <option v-for="tf in TIMEFRAMES" :key="tf" :value="tf">{{ tf }}</option>
      </select>
    </template>

    <div ref="chartContainer" class="w-full" style="height: 260px;" />

    <div v-if="!candles.length" class="flex items-center justify-center h-24 text-gray-500 text-sm">
      Waiting for chart data…
    </div>
  </BaseCard>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { createChart } from 'lightweight-charts'
import { useMarketStore } from '@/store/market'
import BaseCard from './BaseCard.vue'

defineEmits(['remove'])

const TIMEFRAMES = ['1m', '5m', '15m', '30m', '1h', '24h']

const store = useMarketStore()
const candles = computed(() => store.candles)
const chartContainer = ref(null)
const localTf = ref(store.selectedTimeframe)

let chart = null
let series = null

function initChart() {
  if (!chartContainer.value) return
  chart = createChart(chartContainer.value, {
    layout: {
      background: { color: '#1e2a3b' },
      textColor: '#94a3b8',
    },
    grid: {
      vertLines: { color: '#263548' },
      horzLines: { color: '#263548' },
    },
    crosshair: { mode: 1 },
    rightPriceScale: { borderColor: '#263548' },
    timeScale: {
      borderColor: '#263548',
      timeVisible: true,
      secondsVisible: false,
    },
    width: chartContainer.value.clientWidth,
    height: 260,
  })
  series = chart.addCandlestickSeries({
    upColor: '#22c55e',
    downColor: '#ef4444',
    borderUpColor: '#22c55e',
    borderDownColor: '#ef4444',
    wickUpColor: '#22c55e',
    wickDownColor: '#ef4444',
  })
  updateChart()
}

function updateChart() {
  if (!series || !candles.value.length) return
  const data = candles.value
    .map((c) => ({
      time: Math.floor(c.t / 1000),
      open: c.o,
      high: c.h,
      low: c.l,
      close: c.c,
    }))
    .sort((a, b) => a.time - b.time)
    .filter((c, i, arr) => i === 0 || c.time !== arr[i - 1].time) // deduplicate
  if (data.length) series.setData(data)
  chart?.timeScale().fitContent()
}

onMounted(async () => {
  await nextTick()
  initChart()
})

onBeforeUnmount(() => {
  chart?.remove()
  chart = null
})

watch(candles, updateChart)
watch(
  () => store.selectedTimeframe,
  (tf) => { localTf.value = tf }
)
</script>
