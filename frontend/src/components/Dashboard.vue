<template>
  <div class="min-h-screen bg-surface flex flex-col">

    <!-- ===== Top Bar ===== -->
    <header class="sticky top-0 z-30 bg-card/90 backdrop-blur border-b border-border px-4 py-3 flex flex-wrap items-center gap-3">
      <!-- Logo -->
      <div class="flex items-center gap-2 mr-2">
        <span class="text-2xl">📈</span>
        <span class="font-bold text-lg tracking-tight text-white">TradingApp</span>
      </div>

      <!-- Main navigation tabs -->
      <nav class="flex gap-1">
        <button
          v-for="tab in mainTabs"
          :key="tab.id"
          class="px-3 py-1.5 rounded-lg text-xs font-semibold transition-all duration-200"
          :class="activeTab === tab.id
            ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/30'
            : 'bg-surface text-gray-400 hover:bg-border hover:text-white'"
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
          class="px-3 py-1.5 rounded-lg text-xs font-semibold transition-all duration-200"
          :class="store.selectedSymbol === asset.symbol
            ? 'bg-blue-600/80 text-white shadow-lg shadow-blue-500/20'
            : 'bg-surface text-gray-400 hover:bg-border hover:text-white'"
          @click="store.setSymbol(asset.symbol)"
        >
          <span class="mr-1">{{ categoryIcon(asset.category) }}</span>
          {{ asset.symbol }}
        </button>
      </div>

      <!-- Spacer -->
      <div class="flex-1" />

      <!-- Demo mode badge -->
      <div
        v-if="store.demoMode && activeTab === 'markets'"
        class="flex items-center gap-1.5 px-2 py-1 rounded-lg bg-yellow-900/50 border border-yellow-700/50 text-yellow-400 text-xs font-semibold"
      >
        🎭 DEMO
      </div>

      <!-- Live indicator -->
      <div class="flex items-center gap-2 text-xs">
        <div class="relative w-2.5 h-2.5">
          <div
            class="w-2.5 h-2.5 rounded-full"
            :class="store.connected ? 'bg-green-400' : 'bg-red-500'"
          />
          <div
            v-if="store.connected"
            class="absolute inset-0 rounded-full bg-green-400 animate-ping opacity-75"
          />
        </div>
        <span class="text-gray-400">
          {{ store.connected ? 'LIVE' : 'OFFLINE' }}
        </span>
      </div>

      <!-- Last updated -->
      <span class="text-xs text-gray-600">
        {{ lastUpdatedStr }}
      </span>

      <!-- Refresh countdown (markets only) -->
      <div v-if="activeTab === 'markets'" class="flex items-center gap-1 text-xs text-gray-500">
        <svg class="w-3 h-3 animate-spin" viewBox="0 0 24 24" fill="none">
          <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-dasharray="31.4 31.4" />
        </svg>
        <span>{{ countdown }}s</span>
      </div>

      <!-- Add card button (markets only) -->
      <div v-if="activeTab === 'markets'" class="relative" ref="addMenuRef">
        <button
          class="px-3 py-1.5 rounded-lg text-xs font-semibold bg-blue-600 hover:bg-blue-500 text-white transition-colors"
          @click="showAddMenu = !showAddMenu"
        >+ Card</button>

        <!-- Dropdown -->
        <div
          v-if="showAddMenu"
          class="absolute right-0 top-full mt-1 bg-card border border-border rounded-xl shadow-2xl p-2 z-50 min-w-40 space-y-1"
        >
          <button
            v-for="card in availableCards"
            :key="card.type"
            class="w-full text-left px-3 py-2 rounded-lg text-xs hover:bg-border transition-colors text-gray-300"
            @click="addCard(card.type); showAddMenu = false"
          >{{ card.icon }} {{ card.label }}</button>
        </div>
      </div>
    </header>

    <!-- ===== Markets Tab ===== -->
    <template v-if="activeTab === 'markets'">
      <!-- Error Banner -->
      <div
        v-if="store.error && !store.demoMode"
        class="mx-4 mt-3 px-4 py-3 rounded-xl bg-red-900/40 border border-red-700/50 text-red-300 text-sm"
      >
        ⚠️ {{ store.error }}
      </div>

      <!-- Loading overlay -->
      <div
        v-if="store.loading && !store.dashboardData"
        class="flex-1 flex items-center justify-center gap-3 text-gray-500"
      >
        <svg class="w-6 h-6 animate-spin text-blue-500" viewBox="0 0 24 24" fill="none">
          <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-dasharray="31.4 31.4" />
        </svg>
        <span>Loading market data…</span>
      </div>

      <!-- Draggable Grid -->
      <main class="flex-1 p-4">
        <draggable
          v-model="cards"
          handle=".drag-handle"
          item-key="id"
          class="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4 gap-4 auto-rows-auto"
          :animation="200"
          ghost-class="opacity-30"
          chosen-class="scale-105 shadow-2xl"
        >
          <template #item="{ element }">
            <div class="min-h-56">
              <component
                :is="CARD_MAP[element.type]"
                @remove="removeCard(element.id)"
              />
            </div>
          </template>
        </draggable>

        <!-- Empty state -->
        <div
          v-if="!cards.length"
          class="flex flex-col items-center justify-center py-24 text-gray-600"
        >
          <span class="text-5xl mb-4">🃏</span>
          <p class="text-lg">No cards on the dashboard</p>
          <p class="text-sm mt-1">Click <strong class="text-gray-400">+ Card</strong> to add one</p>
        </div>
      </main>
    </template>

    <!-- ===== Trading Tab ===== -->
    <SimulatedTrading v-else-if="activeTab === 'trading'" />

    <!-- ===== News Tab ===== -->
    <NewsTab v-else-if="activeTab === 'news'" />

  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import draggable from 'vuedraggable'
import { useMarketStore } from '@/store/market'
import PriceCard       from './cards/PriceCard.vue'
import ChartCard       from './cards/ChartCard.vue'
import IndicatorsCard  from './cards/IndicatorsCard.vue'
import SignalsCard     from './cards/SignalsCard.vue'
import PredictionsCard from './cards/PredictionsCard.vue'
import SimulatedTrading from './SimulatedTrading.vue'
import NewsTab          from './NewsTab.vue'

const CARD_MAP = {
  price:       PriceCard,
  chart:       ChartCard,
  indicators:  IndicatorsCard,
  signals:     SignalsCard,
  predictions: PredictionsCard,
}

const ALL_CARDS = [
  { type: 'price',       label: 'Price Overview',    icon: '💰' },
  { type: 'chart',       label: 'Price Chart',       icon: '📈' },
  { type: 'indicators',  label: 'Indicators',         icon: '📐' },
  { type: 'signals',     label: 'Buy/Sell Signals',   icon: '🚦' },
  { type: 'predictions', label: 'ML Predictions',     icon: '🤖' },
]

const mainTabs = [
  { id: 'markets', label: 'Markets',  icon: '📊' },
  { id: 'trading', label: 'Trading',  icon: '💼' },
  { id: 'news',    label: 'News',     icon: '📰' },
]

const store = useMarketStore()

// Active main tab
const activeTab = ref('markets')

// Initial card layout
const cards = ref([
  { id: 1, type: 'price'       },
  { id: 2, type: 'signals'     },
  { id: 3, type: 'predictions' },
  { id: 4, type: 'chart'       },
  { id: 5, type: 'indicators'  },
])

let nextId = 10

const availableCards = computed(() =>
  ALL_CARDS.filter((c) => !cards.value.some((card) => card.type === c.type))
)

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

// ---- Last updated string ----
const lastUpdatedStr = computed(() => {
  if (!store.lastUpdated) return ''
  return store.lastUpdated.toLocaleTimeString()
})

// ---- Add menu close on outside click ----
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
