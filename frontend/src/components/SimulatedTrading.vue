<template>
  <div class="flex-1 p-4 max-w-6xl mx-auto w-full">

    <!-- ===== Portfolio Summary ===== -->
    <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
      <div class="bg-card border border-border rounded-2xl px-4 py-3">
        <p class="text-xs text-gray-500 mb-1">Open Positions</p>
        <p class="text-2xl font-bold text-white">{{ store.openPositions.length }}</p>
      </div>
      <div class="bg-card border border-border rounded-2xl px-4 py-3">
        <p class="text-xs text-gray-500 mb-1">Total Exposure</p>
        <p class="text-2xl font-bold text-white">${{ totalExposure.toLocaleString() }}</p>
      </div>
      <div class="bg-card border border-border rounded-2xl px-4 py-3">
        <p class="text-xs text-gray-500 mb-1">Unrealised PnL</p>
        <p class="text-2xl font-bold" :class="totalPnL >= 0 ? 'text-green-400' : 'text-red-400'">
          {{ totalPnL >= 0 ? '+' : '' }}${{ totalPnL.toFixed(2) }}
        </p>
      </div>
      <div class="bg-card border border-border rounded-2xl px-4 py-3">
        <p class="text-xs text-gray-500 mb-1">Closed Trades</p>
        <p class="text-2xl font-bold text-white">{{ store.closedPositions.length }}</p>
      </div>
    </div>

    <!-- ===== Open New Position ===== -->
    <div class="bg-card border border-border rounded-2xl p-6 mb-6">
      <h2 class="text-lg font-bold text-white mb-5 flex items-center gap-2">
        💼 Open New Position
      </h2>

      <form @submit.prevent="submitPosition" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 items-end">
        <!-- Token -->
        <div>
          <label class="block text-xs text-gray-400 mb-1.5 font-medium">Token</label>
          <select
            v-model="form.symbol"
            class="w-full bg-surface border border-border rounded-xl px-3 py-2.5 text-sm text-white focus:outline-none focus:border-blue-500 transition-colors"
            @change="onSymbolChange"
          >
            <option v-for="asset in store.assets" :key="asset.symbol" :value="asset.symbol">
              {{ asset.symbol }} — {{ asset.name }}
            </option>
          </select>
        </div>

        <!-- Amount (USDC) -->
        <div>
          <label class="block text-xs text-gray-400 mb-1.5 font-medium">Amount (USDC)</label>
          <div class="flex gap-1.5 flex-wrap mb-1.5">
            <button
              v-for="preset in [50, 100, 500, 1000]"
              :key="preset"
              type="button"
              class="px-2 py-0.5 rounded text-[10px] font-semibold bg-surface border border-border hover:border-blue-500 hover:text-blue-400 text-gray-500 transition-colors"
              @click="form.amount = preset"
            >${{ preset }}</button>
          </div>
          <input
            v-model.number="form.amount"
            type="number"
            min="1"
            step="1"
            required
            placeholder="e.g. 100"
            class="w-full bg-surface border border-border rounded-xl px-3 py-2.5 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-blue-500 transition-colors"
          />
        </div>

        <!-- Entry Price -->
        <div>
          <label class="block text-xs text-gray-400 mb-1.5 font-medium">
            Entry Price (USD)
            <button
              type="button"
              class="ml-2 text-blue-400 hover:text-blue-300 text-xs underline"
              @click="useCurrentPrice"
            >use current</button>
          </label>
          <div class="relative">
            <input
              v-model.number="form.entryPrice"
              type="number"
              min="0.000001"
              step="any"
              required
              placeholder="Auto-filled"
              class="w-full bg-surface border border-border rounded-xl px-3 py-2.5 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-blue-500 transition-colors"
            />
            <div
              v-if="fetchingPrice"
              class="absolute right-3 top-1/2 -translate-y-1/2"
            >
              <svg class="w-3 h-3 animate-spin text-blue-400" viewBox="0 0 24 24" fill="none">
                <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="3"
                  stroke-linecap="round" stroke-dasharray="31.4 31.4" />
              </svg>
            </div>
          </div>
        </div>

        <!-- Direction + Submit -->
        <div>
          <label class="block text-xs text-gray-400 mb-1.5 font-medium">Direction</label>
          <div class="flex gap-2">
            <button
              type="button"
              class="flex-1 py-2.5 rounded-xl text-sm font-bold transition-all duration-200"
              :class="form.direction === 'LONG'
                ? 'bg-green-600 text-white shadow-lg shadow-green-500/30'
                : 'bg-surface text-gray-400 border border-border hover:border-green-600 hover:text-green-400'"
              @click="form.direction = 'LONG'"
            >↑ LONG</button>
            <button
              type="button"
              class="flex-1 py-2.5 rounded-xl text-sm font-bold transition-all duration-200"
              :class="form.direction === 'SHORT'
                ? 'bg-red-600 text-white shadow-lg shadow-red-500/30'
                : 'bg-surface text-gray-400 border border-border hover:border-red-600 hover:text-red-400'"
              @click="form.direction = 'SHORT'"
            >↓ SHORT</button>
          </div>
          <button
            type="submit"
            class="mt-2 w-full py-2.5 rounded-xl text-sm font-bold bg-blue-600 hover:bg-blue-500 text-white transition-colors shadow-lg shadow-blue-500/20"
          >
            Open Position
          </button>
        </div>
      </form>

      <p v-if="formError" class="mt-3 text-red-400 text-xs">⚠️ {{ formError }}</p>
    </div>

    <!-- ===== Open Positions ===== -->
    <div class="bg-card border border-border rounded-2xl p-6 mb-6">
      <div class="flex items-center justify-between mb-5">
        <h2 class="text-lg font-bold text-white flex items-center gap-2">
          📊 Open Positions
          <span v-if="store.openPositions.length" class="px-2 py-0.5 rounded-full bg-blue-600/30 text-blue-400 text-xs font-semibold">
            {{ store.openPositions.length }}
          </span>
        </h2>
        <span class="text-xs text-gray-500 flex items-center gap-1">
          <svg class="w-3 h-3 animate-spin" viewBox="0 0 24 24" fill="none">
            <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2.5"
              stroke-linecap="round" stroke-dasharray="31.4 31.4" />
          </svg>
          Prices update every 10s
        </span>
      </div>

      <div v-if="!store.openPositions.length" class="text-center py-10 text-gray-600">
        <span class="text-4xl block mb-2">📭</span>
        No open positions. Open one above!
      </div>

      <div v-else class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead>
            <tr class="text-gray-500 text-xs uppercase tracking-wide border-b border-border">
              <th class="text-left pb-3 pr-4">Token</th>
              <th class="text-left pb-3 pr-4">Direction</th>
              <th class="text-right pb-3 pr-4">Size</th>
              <th class="text-right pb-3 pr-4">Entry Price</th>
              <th class="text-right pb-3 pr-4">Current Price</th>
              <th class="text-right pb-3 pr-4">PnL $</th>
              <th class="text-right pb-3 pr-4">PnL %</th>
              <th class="text-right pb-3">Action</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="pos in store.openPositions"
              :key="pos.id"
              class="border-b border-border/50 hover:bg-surface/40 transition-colors"
            >
              <td class="py-3 pr-4 font-semibold text-white">
                {{ categoryIcon(pos.symbol) }} {{ pos.symbol }}
              </td>
              <td class="py-3 pr-4">
                <span
                  class="px-2 py-0.5 rounded-full text-xs font-bold"
                  :class="pos.direction === 'LONG'
                    ? 'bg-green-500/20 text-green-400'
                    : 'bg-red-500/20 text-red-400'"
                >
                  {{ pos.direction === 'LONG' ? '↑' : '↓' }} {{ pos.direction }}
                </span>
              </td>
              <td class="py-3 pr-4 text-right text-gray-300">${{ pos.amount.toLocaleString() }}</td>
              <td class="py-3 pr-4 text-right text-gray-300">{{ formatPrice(pos.entryPrice) }}</td>
              <td class="py-3 pr-4 text-right text-white font-medium">
                <span v-if="getLivePrice(pos.symbol) != null">{{ formatPrice(getLivePrice(pos.symbol)) }}</span>
                <span v-else class="text-gray-600">—</span>
              </td>
              <td class="py-3 pr-4 text-right font-semibold" :class="getPnL(pos).pnlUSD >= 0 ? 'text-green-400' : 'text-red-400'">
                {{ getPnL(pos).pnlUSD >= 0 ? '+' : '' }}${{ getPnL(pos).pnlUSD.toFixed(2) }}
              </td>
              <td class="py-3 pr-4 text-right font-semibold" :class="getPnL(pos).pnlPct >= 0 ? 'text-green-400' : 'text-red-400'">
                {{ getPnL(pos).pnlPct >= 0 ? '+' : '' }}{{ getPnL(pos).pnlPct.toFixed(2) }}%
              </td>
              <td class="py-3 text-right">
                <button
                  class="px-3 py-1 rounded-lg text-xs font-semibold bg-surface border border-border hover:border-red-500 hover:text-red-400 text-gray-400 transition-colors"
                  @click="closePosition(pos)"
                >
                  Close
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- ===== Closed Positions ===== -->
    <div v-if="store.closedPositions.length" class="bg-card border border-border rounded-2xl p-6">
      <div class="flex items-center justify-between mb-5">
        <h2 class="text-lg font-bold text-white flex items-center gap-2">
          🗂️ Closed Positions
          <span class="px-2 py-0.5 rounded-full bg-gray-700/50 text-gray-400 text-xs font-semibold">
            {{ store.closedPositions.length }}
          </span>
        </h2>
        <button
          class="text-xs text-gray-500 hover:text-red-400 transition-colors"
          @click="store.clearClosedPositions()"
        >
          Clear history
        </button>
      </div>

      <div class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead>
            <tr class="text-gray-500 text-xs uppercase tracking-wide border-b border-border">
              <th class="text-left pb-3 pr-4">Token</th>
              <th class="text-left pb-3 pr-4">Direction</th>
              <th class="text-right pb-3 pr-4">Size</th>
              <th class="text-right pb-3 pr-4">Entry</th>
              <th class="text-right pb-3 pr-4">Close</th>
              <th class="text-right pb-3 pr-4">PnL $</th>
              <th class="text-right pb-3">PnL %</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="pos in recentClosed"
              :key="pos.id"
              class="border-b border-border/50 text-gray-500"
            >
              <td class="py-3 pr-4 font-semibold">{{ pos.symbol }}</td>
              <td class="py-3 pr-4">
                <span
                  class="px-2 py-0.5 rounded-full text-xs font-bold opacity-60"
                  :class="pos.direction === 'LONG'
                    ? 'bg-green-500/20 text-green-400'
                    : 'bg-red-500/20 text-red-400'"
                >
                  {{ pos.direction }}
                </span>
              </td>
              <td class="py-3 pr-4 text-right">${{ pos.amount.toLocaleString() }}</td>
              <td class="py-3 pr-4 text-right">{{ formatPrice(pos.entryPrice) }}</td>
              <td class="py-3 pr-4 text-right">{{ formatPrice(pos.closePrice) }}</td>
              <td class="py-3 pr-4 text-right font-semibold" :class="getClosedPnL(pos).pnlUSD >= 0 ? 'text-green-400/70' : 'text-red-400/70'">
                {{ getClosedPnL(pos).pnlUSD >= 0 ? '+' : '' }}${{ getClosedPnL(pos).pnlUSD.toFixed(2) }}
              </td>
              <td class="py-3 text-right font-semibold" :class="getClosedPnL(pos).pnlPct >= 0 ? 'text-green-400/70' : 'text-red-400/70'">
                {{ getClosedPnL(pos).pnlPct >= 0 ? '+' : '' }}{{ getClosedPnL(pos).pnlPct.toFixed(2) }}%
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useMarketStore } from '@/store/market'

const store = useMarketStore()

// ---- Form state ----
const form = ref({
  symbol:     store.selectedSymbol || 'BTC',
  direction:  'LONG',
  amount:     100,
  entryPrice: null,
})
const formError = ref('')
const fetchingPrice = ref(false)

function categoryIcon(symbol) {
  const asset = store.assets.find(a => a.symbol === symbol)
  return asset?.category === 'crypto' ? '🪙' : '🏭'
}

function getLivePrice(symbol) {
  return store.livePrices[symbol] ?? null
}

async function onSymbolChange() {
  fetchingPrice.value = true
  await store.fetchLivePrice(form.value.symbol)
  fetchingPrice.value = false
  const p = getLivePrice(form.value.symbol)
  if (p) form.value.entryPrice = p
}

async function useCurrentPrice() {
  fetchingPrice.value = true
  await store.fetchLivePrice(form.value.symbol)
  fetchingPrice.value = false
  const p = getLivePrice(form.value.symbol)
  if (p) form.value.entryPrice = p
}

function submitPosition() {
  formError.value = ''
  if (!form.value.amount || form.value.amount <= 0) {
    formError.value = 'Amount must be greater than 0.'
    return
  }
  if (!form.value.entryPrice || form.value.entryPrice <= 0) {
    formError.value = 'Please set a valid entry price.'
    return
  }
  store.openPosition({
    symbol:     form.value.symbol,
    direction:  form.value.direction,
    amount:     form.value.amount,
    entryPrice: form.value.entryPrice,
  })
  store.updateLivePrice(form.value.symbol, form.value.entryPrice)
  form.value.amount = 100
}

function closePosition(pos) {
  store.closePosition(pos.id)
}

// ---- PnL calculation ----
function getPnL(pos) {
  const currentPrice = getLivePrice(pos.symbol) ?? pos.entryPrice
  const priceDiff = currentPrice - pos.entryPrice
  const multiplier = pos.direction === 'LONG' ? 1 : -1
  const pnlUSD = (priceDiff / pos.entryPrice) * pos.amount * multiplier
  const pnlPct = (priceDiff / pos.entryPrice) * 100 * multiplier
  return { pnlUSD, pnlPct }
}

function getClosedPnL(pos) {
  const priceDiff = (pos.closePrice ?? pos.entryPrice) - pos.entryPrice
  const multiplier = pos.direction === 'LONG' ? 1 : -1
  const pnlUSD = (priceDiff / pos.entryPrice) * pos.amount * multiplier
  const pnlPct = (priceDiff / pos.entryPrice) * 100 * multiplier
  return { pnlUSD, pnlPct }
}

// ---- Portfolio summary ----
const totalExposure = computed(() =>
  store.openPositions.reduce((sum, pos) => sum + pos.amount, 0)
)

const totalPnL = computed(() =>
  store.openPositions.reduce((sum, pos) => sum + getPnL(pos).pnlUSD, 0)
)

// ---- Helpers ----
function formatPrice(price) {
  if (price == null) return '—'
  if (price >= 1000) return '$' + price.toLocaleString(undefined, { maximumFractionDigits: 2 })
  if (price >= 1)    return '$' + price.toFixed(4)
  return '$' + price.toFixed(6)
}

const recentClosed = computed(() =>
  [...store.closedPositions].reverse().slice(0, 20)
)

// ---- Auto-refresh prices for open positions ----
let priceTimer = null

onMounted(async () => {
  fetchingPrice.value = true
  await store.fetchLivePrice(form.value.symbol)
  fetchingPrice.value = false
  const p = getLivePrice(form.value.symbol)
  if (p) form.value.entryPrice = p

  await store.fetchLivePricesForOpenPositions()

  priceTimer = setInterval(async () => {
    await store.fetchLivePricesForOpenPositions()
    await store.fetchLivePrice(form.value.symbol)
  }, 10000)
})

onBeforeUnmount(() => {
  clearInterval(priceTimer)
})
</script>
