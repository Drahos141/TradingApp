<template>
  <div class="min-h-screen bg-surface flex flex-col relative">
    <ParticleBackground />

    <!-- ===== Top Bar ===== -->
    <header class="sticky top-0 z-30 cyber-header px-4 py-3 flex flex-wrap items-center gap-3" style="position: relative; z-index: 30;">
      <!-- Logo -->
      <div class="flex items-center gap-2 mr-3">
        <span class="text-2xl">📈</span>
        <span class="font-bold text-lg tracking-tight text-neon-cyan font-mono neon-text-cyan">TRADING<span class="text-white">APP</span></span>
      </div>

      <!-- Main navigation tabs -->
      <nav class="flex gap-1">
        <button
          v-for="tab in mainTabs"
          :key="tab.id"
          :class="activeTab === tab.id ? 'nav-tab-active' : 'nav-tab'"
          @click="activeTab = tab.id"
        >
          {{ tab.icon }} {{ tab.label }}
        </button>
      </nav>

      <!-- Asset tabs (markets only) -->
      <div v-if="activeTab === 'markets'" class="flex gap-1 flex-wrap">
        <button
          v-for="asset in store.assets"
          :key="asset.symbol"
          class="px-3 py-1.5 rounded text-xs font-semibold font-mono uppercase tracking-widest transition-all duration-200"
          :class="store.selectedSymbol === asset.symbol
            ? 'bg-cyan-900/40 text-neon-cyan border border-cyan-500/50 shadow-neon-cyan'
            : 'text-cyan-700 border border-transparent hover:border-cyan-800 hover:text-cyan-400'"
          @click="store.setSymbol(asset.symbol)"
        >
          <span class="mr-1">{{ categoryIcon(asset.category) }}</span>{{ asset.symbol }}
        </button>
      </div>

      <div class="flex-1" />

      <!-- Demo mode badge -->
      <div v-if="store.demoMode && activeTab === 'markets'"
        class="flex items-center gap-1.5 px-2 py-1 rounded border border-yellow-700/50 text-yellow-400 text-xs font-mono uppercase">
        🎭 DEMO
      </div>

      <!-- Live indicator -->
      <div class="flex items-center gap-2 text-xs">
        <div class="relative w-2.5 h-2.5">
          <div class="w-2.5 h-2.5 rounded-full" :class="store.connected ? 'bg-neon-green' : 'bg-sell'" />
          <div v-if="store.connected" class="absolute inset-0 rounded-full bg-neon-green animate-ping opacity-60" />
        </div>
        <span class="font-mono text-xs" :class="store.connected ? 'text-neon-green' : 'text-sell'">
          {{ store.connected ? 'LIVE' : 'OFFLINE' }}
        </span>
      </div>

      <!-- Last updated -->
      <span class="text-xs text-cyan-800 font-mono">{{ lastUpdatedStr }}</span>

      <!-- Refresh countdown (markets only) -->
      <div v-if="activeTab === 'markets'" class="flex items-center gap-1 text-xs text-cyan-700 font-mono">
        <svg class="w-3 h-3 animate-spin text-cyan-600" viewBox="0 0 24 24" fill="none">
          <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-dasharray="31.4 31.4" />
        </svg>
        <span>{{ countdown }}s</span>
      </div>

      <!-- Add card button (markets only) -->
      <div v-if="activeTab === 'markets'" class="relative" ref="addMenuRef">
        <button class="cyber-btn py-1.5 text-xs" @click="showAddMenu = !showAddMenu">+ CARD</button>

        <div v-if="showAddMenu"
          class="absolute right-0 top-full mt-1 cyber-card shadow-2xl p-2 z-50 min-w-56 space-y-1">
          <p class="text-[10px] text-cyan-700 uppercase tracking-widest px-2 pb-1 font-mono">Choose card type</p>
          <button v-for="card in ALL_CARDS" :key="card.type"
            class="w-full text-left px-3 py-2 rounded text-xs hover:bg-cyan-900/20 transition-colors text-gray-300 flex items-center gap-2 font-mono"
            @click="addCard(card.type); showAddMenu = false">
            <span class="text-base leading-none">{{ card.icon }}</span>
            <span class="flex-1">{{ card.label }}</span>
            <span v-if="cardCount(card.type) > 0"
              class="text-[10px] px-1.5 py-0.5 rounded border border-cyan-700 text-cyan-400">×{{ cardCount(card.type) }}</span>
          </button>
        </div>
      </div>
    </header>

    <!-- ===== Markets Tab ===== -->
    <template v-if="activeTab === 'markets'">
      <div v-if="store.error && !store.demoMode"
        class="mx-4 mt-3 px-4 py-3 rounded border border-sell/40 bg-sell/10 text-sell text-sm relative z-10 font-mono">
        ⚠ {{ store.error }}
      </div>

      <div v-if="store.loading && !store.dashboardData"
        class="flex-1 flex items-center justify-center gap-3 text-cyan-700 relative z-10">
        <svg class="w-6 h-6 animate-spin text-cyan-500" viewBox="0 0 24 24" fill="none">
          <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-dasharray="31.4 31.4" />
        </svg>
        <span class="font-mono text-sm">Loading market data…</span>
      </div>

      <main class="flex-1 p-4 relative z-10">
        <draggable v-model="cards" handle=".drag-handle" item-key="id"
          class="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4 gap-4 auto-rows-auto"
          :animation="200" ghost-class="opacity-30" chosen-class="scale-105 shadow-2xl">
          <template #item="{ element }">
            <div class="min-h-56">
              <component :is="CARD_MAP[element.type]" @remove="removeCard(element.id)" />
            </div>
          </template>
        </draggable>

        <div v-if="!cards.length" class="flex flex-col items-center justify-center py-24 text-cyan-900 font-mono">
          <span class="text-5xl mb-4">⬜</span>
          <p class="text-lg">No cards on the dashboard</p>
          <p class="text-sm mt-1 text-cyan-800">Click <strong class="text-cyan-600">+ CARD</strong> to add one</p>
        </div>
      </main>
    </template>

    <!-- ===== Trading Tab ===== -->
    <div v-else-if="activeTab === 'trading'" class="relative z-10 flex-1">
      <SimulatedTrading />
    </div>

    <!-- ===== Backtesting Tab ===== -->
    <div v-else-if="activeTab === 'backtest'" class="relative z-10 flex-1">
      <Backtesting />
    </div>

    <!-- ===== News Tab ===== -->
    <div v-else-if="activeTab === 'news'" class="relative z-10 flex-1">
      <NewsTab />
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import draggable from 'vuedraggable'
import { useMarketStore } from '@/store/market'
import PriceCard          from './cards/PriceCard.vue'
import ChartCard          from './cards/ChartCard.vue'
import IndicatorsCard     from './cards/IndicatorsCard.vue'
import SignalsCard        from './cards/SignalsCard.vue'
import PredictionsCard    from './cards/PredictionsCard.vue'
import AIPredictionsCard  from './cards/AIPredictionsCard.vue'
import SimulatedTrading   from './SimulatedTrading.vue'
import Backtesting        from './Backtesting.vue'
import NewsTab            from './NewsTab.vue'
import ParticleBackground from './ParticleBackground.vue'

const CARD_MAP = {
  price:          PriceCard,
  chart:          ChartCard,
  indicators:     IndicatorsCard,
  signals:        SignalsCard,
  predictions:    PredictionsCard,
  ai_predictions: AIPredictionsCard,
}

const ALL_CARDS = [
  { type: 'price',          label: 'Price Overview',      icon: '💰' },
  { type: 'chart',          label: 'Price Chart',         icon: '📈' },
  { type: 'indicators',     label: 'Indicators',          icon: '📐' },
  { type: 'signals',        label: 'Buy/Sell Signals',    icon: '🚦' },
  { type: 'predictions',    label: 'ML Predictions',      icon: '🤖' },
  { type: 'ai_predictions', label: 'MORE AI Predictions', icon: '🧬' },
]

const mainTabs = [
  { id: 'markets',  label: 'Markets',     icon: '◈' },
  { id: 'trading',  label: 'Trading',     icon: '◆' },
  { id: 'backtest', label: 'Backtest',    icon: '⟨/⟩' },
  { id: 'news',     label: 'News',        icon: '◉' },
]

const store = useMarketStore()
const activeTab = ref('markets')

const cards = ref([
  { id: 1, type: 'price'       },
  { id: 2, type: 'signals'     },
  { id: 3, type: 'predictions' },
  { id: 4, type: 'chart'       },
  { id: 5, type: 'indicators'  },
])

let nextId = 10

function cardCount(type) {
  return cards.value.filter((c) => c.type === type).length
}

function addCard(type) {
  cards.value.push({ id: nextId++, type })
}

function removeCard(id) {
  cards.value = cards.value.filter((c) => c.id !== id)
}

function categoryIcon(cat) {
  return cat === 'crypto' ? '🪙' : '🏭'
}

// ---- Auto-refresh every 10 seconds ----
const REFRESH_INTERVAL = 10
const countdown = ref(REFRESH_INTERVAL)
let refreshTimer = null
let countdownTimer = null

function startRefresh() {
  countdown.value = REFRESH_INTERVAL
  refreshTimer = setInterval(async () => {
    await store.refreshDashboard()
    countdown.value = REFRESH_INTERVAL
  }, REFRESH_INTERVAL * 1000)

  countdownTimer = setInterval(() => {
    if (countdown.value > 0) countdown.value--
  }, 1000)
}

const lastUpdatedStr = computed(() => {
  if (!store.lastUpdated) return ''
  return store.lastUpdated.toLocaleTimeString()
})

const showAddMenu = ref(false)
const addMenuRef  = ref(null)
function handleOutsideClick(e) {
  if (addMenuRef.value && !addMenuRef.value.contains(e.target)) {
    showAddMenu.value = false
  }
}

onMounted(async () => {
  await store.fetchAssets()
  await store.refreshDashboard()
  startRefresh()
  document.addEventListener('click', handleOutsideClick)
})

onBeforeUnmount(() => {
  clearInterval(refreshTimer)
  clearInterval(countdownTimer)
  document.removeEventListener('click', handleOutsideClick)
})
</script>
