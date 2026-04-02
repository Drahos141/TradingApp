<template>
  <div class="flex-1 p-4 max-w-7xl mx-auto w-full space-y-5">

    <!-- ===== Wallet Bar ===== -->
    <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
      <div class="cyber-card px-4 py-3">
        <p class="text-xs text-cyan-500/70 mb-1 uppercase tracking-widest font-mono">Wallet Balance</p>
        <p class="text-2xl font-bold text-cyan-300 font-mono">${{ store.walletBalance.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }}</p>
      </div>
      <div class="cyber-card px-4 py-3">
        <p class="text-xs text-cyan-500/70 mb-1 uppercase tracking-widest font-mono">Unrealised PnL</p>
        <p class="text-2xl font-bold font-mono" :class="totalPnL >= 0 ? 'text-neon-green' : 'text-sell'">
          {{ totalPnL >= 0 ? '+' : '' }}${{ totalPnL.toFixed(2) }}
        </p>
      </div>
      <div class="cyber-card px-4 py-3">
        <p class="text-xs text-cyan-500/70 mb-1 uppercase tracking-widest font-mono">Open Positions</p>
        <p class="text-2xl font-bold text-white font-mono">{{ store.openPositions.length }}</p>
      </div>
      <div class="cyber-card px-4 py-3 flex flex-col justify-between">
        <p class="text-xs text-cyan-500/70 mb-1 uppercase tracking-widest font-mono">Closed Trades</p>
        <div class="flex items-center justify-between">
          <p class="text-2xl font-bold text-white font-mono">{{ store.closedPositions.length }}</p>
          <button @click="showDeposit = !showDeposit" class="cyber-btn-sm text-cyan-400">+ Deposit</button>
        </div>
        <div v-if="showDeposit" class="mt-2 flex gap-1">
          <input v-model.number="depositAmount" type="number" min="100" step="100" placeholder="Amount"
            class="cyber-input flex-1 text-xs py-1 px-2" />
          <button @click="doDeposit" class="cyber-btn-sm text-neon-green">Add</button>
        </div>
      </div>
    </div>

    <!-- ===== Open New Position ===== -->
    <div class="cyber-card p-6">
      <h2 class="text-lg font-bold text-cyan-300 mb-5 flex items-center gap-2 font-mono">
        <span class="text-neon-green">▶</span> OPEN NEW POSITION
      </h2>

      <form @submit.prevent="submitPosition" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4 items-end">
        <!-- Token -->
        <div>
          <label class="block text-xs text-cyan-500/70 mb-1.5 font-mono uppercase tracking-widest">Token</label>
          <select v-model="form.symbol" class="cyber-input w-full" @change="onSymbolChange">
            <option v-for="asset in store.assets" :key="asset.symbol" :value="asset.symbol">
              {{ asset.symbol }} — {{ asset.name }}
            </option>
          </select>
        </div>

        <!-- Amount -->
        <div>
          <label class="block text-xs text-cyan-500/70 mb-1.5 font-mono uppercase tracking-widest">Amount (USDC)</label>
          <div class="flex gap-1 flex-wrap mb-1.5">
            <button v-for="preset in [50, 100, 500, 1000]" :key="preset" type="button"
              class="cyber-btn-xs" @click="form.amount = preset">${{ preset }}</button>
          </div>
          <input v-model.number="form.amount" type="number" min="1" step="1" required placeholder="100"
            class="cyber-input w-full" />
        </div>

        <!-- Entry Price -->
        <div>
          <label class="block text-xs text-cyan-500/70 mb-1.5 font-mono uppercase tracking-widest">
            Entry Price (USD)
            <button type="button" class="ml-2 text-cyan-400 hover:text-cyan-300 underline" @click="useCurrentPrice">↻ live</button>
          </label>
          <div class="relative">
            <input v-model.number="form.entryPrice" type="number" min="0.000001" step="any" required placeholder="Auto-filled"
              class="cyber-input w-full" />
            <div v-if="fetchingPrice" class="absolute right-3 top-1/2 -translate-y-1/2">
              <svg class="w-3 h-3 animate-spin text-cyan-400" viewBox="0 0 24 24" fill="none">
                <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-dasharray="31.4 31.4" />
              </svg>
            </div>
          </div>
        </div>

        <!-- Stop Loss -->
        <div>
          <label class="block text-xs text-cyan-500/70 mb-1.5 font-mono uppercase tracking-widest">Stop Loss (USD)</label>
          <input v-model.number="form.stopLoss" type="number" min="0" step="any" placeholder="Optional"
            class="cyber-input w-full" />
        </div>

        <!-- Take Profit -->
        <div>
          <label class="block text-xs text-cyan-500/70 mb-1.5 font-mono uppercase tracking-widest">Take Profit (USD)</label>
          <input v-model.number="form.takeProfit" type="number" min="0" step="any" placeholder="Optional"
            class="cyber-input w-full" />
        </div>

        <!-- Direction + Submit -->
        <div>
          <label class="block text-xs text-cyan-500/70 mb-1.5 font-mono uppercase tracking-widest">Direction</label>
          <div class="flex gap-2 mb-2">
            <button type="button" class="flex-1 py-2 rounded-lg text-sm font-bold font-mono transition-all duration-200"
              :class="form.direction === 'LONG' ? 'bg-neon-green/20 text-neon-green border border-neon-green shadow-lg shadow-neon-green/20' : 'cyber-btn-ghost text-gray-400'"
              @click="form.direction = 'LONG'">↑ LONG</button>
            <button type="button" class="flex-1 py-2 rounded-lg text-sm font-bold font-mono transition-all duration-200"
              :class="form.direction === 'SHORT' ? 'bg-sell/20 text-sell border border-sell shadow-lg shadow-sell/20' : 'cyber-btn-ghost text-gray-400'"
              @click="form.direction = 'SHORT'">↓ SHORT</button>
          </div>
          <button type="submit" class="cyber-btn w-full">
            EXECUTE TRADE
          </button>
        </div>
      </form>

      <div v-if="formError" class="mt-3 text-sell text-xs font-mono">⚠ {{ formError }}</div>
      <div v-if="formSuccess" class="mt-3 text-neon-green text-xs font-mono">✓ {{ formSuccess }}</div>
    </div>

    <!-- ===== Open Positions ===== -->
    <div class="cyber-card p-6">
      <div class="flex items-center justify-between mb-5">
        <h2 class="text-lg font-bold text-cyan-300 flex items-center gap-2 font-mono">
          <span class="text-neon-green">◈</span> OPEN POSITIONS
          <span v-if="store.openPositions.length" class="px-2 py-0.5 rounded border border-cyan-600 text-cyan-400 text-xs">
            {{ store.openPositions.length }}
          </span>
        </h2>
        <span class="text-xs text-cyan-600 flex items-center gap-1 font-mono">
          <svg class="w-3 h-3 animate-spin" viewBox="0 0 24 24" fill="none">
            <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-dasharray="31.4 31.4" />
          </svg>
          Prices refresh every 5s
        </span>
      </div>

      <div v-if="!store.openPositions.length" class="text-center py-10 text-cyan-900 font-mono">
        <span class="text-4xl block mb-2">⬜</span>
        No open positions. Execute a trade above.
      </div>

      <div v-else class="overflow-x-auto">
        <table class="w-full text-sm font-mono">
          <thead>
            <tr class="text-cyan-600 text-xs uppercase tracking-widest border-b border-cyan-900">
              <th class="text-left pb-3 pr-4">Token</th>
              <th class="text-left pb-3 pr-4">Dir</th>
              <th class="text-right pb-3 pr-4">Size</th>
              <th class="text-right pb-3 pr-4">Entry</th>
              <th class="text-right pb-3 pr-4">Current</th>
              <th class="text-right pb-3 pr-4">SL / TP</th>
              <th class="text-right pb-3 pr-4">PnL $</th>
              <th class="text-right pb-3 pr-4">PnL %</th>
              <th class="text-right pb-3">Action</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="pos in store.openPositions" :key="pos.id"
              class="border-b border-cyan-900/30 hover:bg-cyan-900/10 transition-colors">
              <td class="py-3 pr-4 font-bold text-white">{{ categoryIcon(pos.symbol) }} {{ pos.symbol }}</td>
              <td class="py-3 pr-4">
                <span class="px-2 py-0.5 rounded text-xs font-bold border"
                  :class="pos.direction === 'LONG' ? 'border-neon-green/50 text-neon-green bg-neon-green/10' : 'border-sell/50 text-sell bg-sell/10'">
                  {{ pos.direction === 'LONG' ? '↑' : '↓' }} {{ pos.direction }}
                </span>
              </td>
              <td class="py-3 pr-4 text-right text-gray-300">${{ pos.amount.toLocaleString() }}</td>
              <td class="py-3 pr-4 text-right text-gray-300">{{ formatPrice(pos.entryPrice) }}</td>
              <td class="py-3 pr-4 text-right text-white">
                <span v-if="getLivePrice(pos.symbol) != null" class="text-cyan-200">{{ formatPrice(getLivePrice(pos.symbol)) }}</span>
                <span v-else class="text-gray-600">—</span>
              </td>
              <td class="py-3 pr-4 text-right text-gray-500 text-xs">
                <span v-if="pos.stopLoss" class="text-sell/70">SL {{ formatPrice(pos.stopLoss) }}</span>
                <span v-if="pos.stopLoss && pos.takeProfit"> / </span>
                <span v-if="pos.takeProfit" class="text-neon-green/70">TP {{ formatPrice(pos.takeProfit) }}</span>
                <span v-if="!pos.stopLoss && !pos.takeProfit" class="text-gray-700">—</span>
              </td>
              <td class="py-3 pr-4 text-right font-bold" :class="getPnL(pos).pnlUSD >= 0 ? 'text-neon-green' : 'text-sell'">
                {{ getPnL(pos).pnlUSD >= 0 ? '+' : '' }}${{ getPnL(pos).pnlUSD.toFixed(2) }}
              </td>
              <td class="py-3 pr-4 text-right font-bold" :class="getPnL(pos).pnlPct >= 0 ? 'text-neon-green' : 'text-sell'">
                {{ getPnL(pos).pnlPct >= 0 ? '+' : '' }}{{ getPnL(pos).pnlPct.toFixed(2) }}%
              </td>
              <td class="py-3 text-right">
                <button class="cyber-btn-sm text-sell hover:border-sell" @click="store.closePosition(pos.id)">Close</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- ===== Closed Positions ===== -->
    <div v-if="store.closedPositions.length" class="cyber-card p-6">
      <div class="flex items-center justify-between mb-5">
        <h2 class="text-lg font-bold text-cyan-300 flex items-center gap-2 font-mono">
          <span class="text-gray-500">◇</span> TRADE HISTORY
          <span class="px-2 py-0.5 rounded border border-gray-700 text-gray-400 text-xs">{{ store.closedPositions.length }}</span>
        </h2>
        <button class="text-xs text-gray-500 hover:text-sell transition-colors font-mono" @click="store.clearClosedPositions()">
          [ clear history ]
        </button>
      </div>

      <div class="overflow-x-auto">
        <table class="w-full text-sm font-mono">
          <thead>
            <tr class="text-gray-600 text-xs uppercase tracking-widest border-b border-gray-800">
              <th class="text-left pb-3 pr-4">Token</th>
              <th class="text-left pb-3 pr-4">Dir</th>
              <th class="text-right pb-3 pr-4">Size</th>
              <th class="text-right pb-3 pr-4">Entry</th>
              <th class="text-right pb-3 pr-4">Close</th>
              <th class="text-right pb-3 pr-4">Reason</th>
              <th class="text-right pb-3 pr-4">PnL $</th>
              <th class="text-right pb-3">PnL %</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="pos in recentClosed" :key="pos.id" class="border-b border-gray-800/50 text-gray-500">
              <td class="py-3 pr-4 font-semibold">{{ pos.symbol }}</td>
              <td class="py-3 pr-4">
                <span class="px-2 py-0.5 rounded text-xs font-bold opacity-60"
                  :class="pos.direction === 'LONG' ? 'text-neon-green' : 'text-sell'">
                  {{ pos.direction }}
                </span>
              </td>
              <td class="py-3 pr-4 text-right">${{ pos.amount.toLocaleString() }}</td>
              <td class="py-3 pr-4 text-right">{{ formatPrice(pos.entryPrice) }}</td>
              <td class="py-3 pr-4 text-right">{{ formatPrice(pos.closePrice) }}</td>
              <td class="py-3 pr-4 text-right text-xs">
                <span :class="pos.closeReason === 'SL' ? 'text-sell/70' : pos.closeReason === 'TP' ? 'text-neon-green/70' : 'text-gray-600'">
                  {{ pos.closeReason || '—' }}
                </span>
              </td>
              <td class="py-3 pr-4 text-right font-semibold" :class="getClosedPnL(pos).pnlUSD >= 0 ? 'text-neon-green/70' : 'text-sell/70'">
                {{ getClosedPnL(pos).pnlUSD >= 0 ? '+' : '' }}${{ getClosedPnL(pos).pnlUSD.toFixed(2) }}
              </td>
              <td class="py-3 text-right font-semibold" :class="getClosedPnL(pos).pnlPct >= 0 ? 'text-neon-green/70' : 'text-sell/70'">
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

const form = ref({
  symbol:     store.selectedSymbol || 'BTC',
  direction:  'LONG',
  amount:     100,
  entryPrice: null,
  stopLoss:   null,
  takeProfit: null,
})
const formError   = ref('')
const formSuccess = ref('')
const fetchingPrice = ref(false)
const showDeposit   = ref(false)
const depositAmount = ref(1000)

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
  formError.value   = ''
  formSuccess.value = ''
  if (!form.value.amount || form.value.amount <= 0) {
    formError.value = 'Amount must be > 0.'
    return
  }
  if (!form.value.entryPrice || form.value.entryPrice <= 0) {
    formError.value = 'Please set a valid entry price (click ↻ live).'
    return
  }
  if (form.value.amount > store.walletBalance) {
    formError.value = `Insufficient balance. Wallet: $${store.walletBalance.toFixed(2)}`
    return
  }
  const ok = store.openPosition({
    symbol:     form.value.symbol,
    direction:  form.value.direction,
    amount:     form.value.amount,
    entryPrice: form.value.entryPrice,
    stopLoss:   form.value.stopLoss   || null,
    takeProfit: form.value.takeProfit || null,
  })
  if (ok !== false) {
    store.updateLivePrice(form.value.symbol, form.value.entryPrice)
    formSuccess.value = `Position opened: ${form.value.direction} ${form.value.symbol} @ ${formatPrice(form.value.entryPrice)}`
    form.value.amount     = 100
    form.value.stopLoss   = null
    form.value.takeProfit = null
    setTimeout(() => { formSuccess.value = '' }, 3000)
  }
}

function doDeposit() {
  if (depositAmount.value >= 100) {
    store.depositWallet(depositAmount.value)
    showDeposit.value = false
  }
}

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

const totalPnL = computed(() =>
  store.openPositions.reduce((sum, pos) => sum + getPnL(pos).pnlUSD, 0)
)

function formatPrice(price) {
  if (price == null) return '—'
  if (price >= 1000) return '$' + price.toLocaleString(undefined, { maximumFractionDigits: 2 })
  if (price >= 1)    return '$' + price.toFixed(4)
  return '$' + price.toFixed(6)
}

const recentClosed = computed(() =>
  [...store.closedPositions].reverse().slice(0, 30)
)

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
  }, 5000)
})

onBeforeUnmount(() => {
  clearInterval(priceTimer)
})
</script>
