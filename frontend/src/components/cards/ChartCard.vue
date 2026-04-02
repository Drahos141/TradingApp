<template>
  <BaseCard title="Price Chart" icon="📈" @remove="$emit('remove')">
    <template #header-actions>
      <select
        v-model="localTf"
        class="cyber-input text-xs py-1 px-2"
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
      background: { color: '#0d1b2a' },
      textColor: '#22d3ee',
    },
    grid: {
      vertLines: { color: 'rgba(0,229,255,0.05)' },
      horzLines: { color: 'rgba(0,229,255,0.05)' },
    },
    crosshair: { mode: 1 },
    rightPriceScale: { borderColor: 'rgba(0,229,255,0.1)' },
    timeScale: {
      borderColor: 'rgba(0,229,255,0.1)',
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
