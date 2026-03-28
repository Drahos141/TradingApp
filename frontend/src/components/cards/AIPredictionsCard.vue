<template>
  <BaseCard title="MORE AI Predictions" icon="🧬" @remove="$emit('remove')">
    <!-- Timeframe radio selector -->
    <p class="text-xs text-gray-500 mb-3">
      Select a timeframe to fetch predictions from 8 AI trading tools
    </p>

    <div class="flex gap-2 flex-wrap mb-4">
      <button
        v-for="tf in TIMEFRAMES"
        :key="tf.key"
        class="px-3 py-1.5 rounded-lg text-xs font-semibold border transition-all duration-200 flex items-center gap-1.5"
        :class="selectedTf === tf.key
          ? 'bg-violet-600 border-violet-500 text-white shadow-lg shadow-violet-500/30'
          : 'bg-surface border-border text-gray-400 hover:border-violet-500 hover:text-violet-300'"
        @click="selectTimeframe(tf.key)"
      >
        <span
          class="w-2 h-2 rounded-full border-2 transition-colors"
          :class="selectedTf === tf.key ? 'bg-white border-white' : 'bg-transparent border-gray-500'"
        />
        {{ tf.label }}
      </button>
    </div>

    <!-- Loading state -->
    <div v-if="loading" class="flex items-center justify-center gap-3 py-10 text-gray-500 text-sm">
      <svg class="w-5 h-5 animate-spin text-violet-400" viewBox="0 0 24 24" fill="none">
        <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="3"
          stroke-linecap="round" stroke-dasharray="31.4 31.4" />
      </svg>
      Querying AI tools…
    </div>

    <!-- Idle state -->
    <div
      v-else-if="!selectedTf"
      class="flex flex-col items-center justify-center py-10 text-gray-600"
    >
      <span class="text-4xl mb-2">🧬</span>
      <p class="text-sm">Click a timeframe above to activate predictions</p>
    </div>

    <!-- Error state -->
    <div v-else-if="error" class="py-6 text-center text-red-400 text-sm">
      ⚠️ {{ error }}
    </div>

    <!-- Results grid -->
    <div v-else-if="tools.length" class="space-y-2">
      <!-- Consensus bar -->
      <div class="flex items-center gap-2 mb-3 px-1">
        <span class="text-xs text-gray-500 shrink-0">Consensus:</span>
        <div class="flex-1 h-2 rounded-full bg-border overflow-hidden">
          <div
            class="h-full rounded-full transition-all duration-700"
            :class="consensusClass"
            :style="{ width: consensusPct + '%' }"
          />
        </div>
        <span class="text-xs font-bold shrink-0" :class="consensusTextClass">
          {{ consensusSignal }}
        </span>
      </div>

      <div
        v-for="tool in tools"
        :key="tool.id"
        class="flex items-center gap-3 rounded-xl px-3 py-2.5 bg-surface border border-border/60 hover:border-border transition-colors"
      >
        <!-- Icon + name -->
        <div class="shrink-0 text-xl leading-none">{{ tool.icon }}</div>
        <div class="flex-1 min-w-0">
          <p class="text-xs font-semibold text-white truncate">{{ tool.name }}</p>
          <p class="text-[10px] text-gray-600 truncate">{{ tool.methodology }}</p>
        </div>

        <!-- Score bar -->
        <div class="shrink-0 w-16">
          <div class="h-1.5 rounded-full bg-border overflow-hidden">
            <div
              class="h-full rounded-full transition-all duration-700"
              :class="signalBarClass(tool.signal)"
              :style="{ width: tool.score + '%' }"
            />
          </div>
          <p class="text-[10px] text-gray-500 text-center mt-0.5">{{ tool.score }}/100</p>
        </div>

        <!-- Signal badge -->
        <div
          class="shrink-0 px-2 py-0.5 rounded-full text-[10px] font-bold min-w-[52px] text-center"
          :class="signalBadgeClass(tool.signal)"
        >
          {{ tool.signal }}
        </div>
      </div>
    </div>
  </BaseCard>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useMarketStore } from '@/store/market'
import BaseCard from './BaseCard.vue'

defineEmits(['remove'])

const TIMEFRAMES = [
  { key: '5m',  label: '5 min'  },
  { key: '1h',  label: '1 hour' },
  { key: '4h',  label: '4 hours' },
  { key: '24h', label: '24 hours' },
]

const store = useMarketStore()
const selectedTf = ref(null)
const tools = ref([])
const loading = ref(false)
const error = ref(null)

const API_BASE = import.meta.env.VITE_API_URL ?? ''

async function fetchPredictions(timeframe) {
  loading.value = true
  error.value = null
  tools.value = []
  try {
    const res = await fetch(`${API_BASE}/api/ai_predictions/${store.selectedSymbol}?timeframe=${timeframe}`)
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    const data = await res.json()
    tools.value = data.tools ?? []
  } catch (e) {
    error.value = e.message || 'Failed to fetch predictions'
  } finally {
    loading.value = false
  }
}

function selectTimeframe(tf) {
  selectedTf.value = tf
  fetchPredictions(tf)
}

// Re-fetch when symbol changes (if a timeframe is already selected)
watch(() => store.selectedSymbol, () => {
  if (selectedTf.value) fetchPredictions(selectedTf.value)
})

// Consensus
const consensusSignal = computed(() => {
  if (!tools.value.length) return 'N/A'
  const buys = tools.value.filter(t => t.signal === 'BUY').length
  const sells = tools.value.filter(t => t.signal === 'SELL').length
  const neutrals = tools.value.length - buys - sells
  if (buys > sells && buys > neutrals) return `BUY (${buys}/${tools.value.length})`
  if (sells > buys && sells > neutrals) return `SELL (${sells}/${tools.value.length})`
  return `NEUTRAL (${neutrals}/${tools.value.length})`
})

const consensusPct = computed(() => {
  if (!tools.value.length) return 50
  const avg = tools.value.reduce((s, t) => s + t.score, 0) / tools.value.length
  return Math.round(avg)
})

const consensusClass = computed(() => {
  const pct = consensusPct.value
  if (pct >= 60) return 'bg-buy'
  if (pct <= 40) return 'bg-sell'
  return 'bg-neutral'
})

const consensusTextClass = computed(() => {
  const pct = consensusPct.value
  if (pct >= 60) return 'text-buy'
  if (pct <= 40) return 'text-sell'
  return 'text-neutral'
})

function signalBarClass(signal) {
  if (signal === 'BUY') return 'bg-buy'
  if (signal === 'SELL') return 'bg-sell'
  return 'bg-neutral'
}

function signalBadgeClass(signal) {
  if (signal === 'BUY') return 'bg-buy/20 text-buy'
  if (signal === 'SELL') return 'bg-sell/20 text-sell'
  return 'bg-neutral/20 text-neutral'
}
</script>
