<template>
  <div class="flex-1 p-4 max-w-7xl mx-auto w-full space-y-5">

    <!-- ===== Header ===== -->
    <div class="cyber-card p-6">
      <h2 class="text-xl font-bold text-cyan-300 font-mono flex items-center gap-3 mb-1">
        <span class="text-neon-green">⟨/⟩</span> BACKTESTING ENGINE
      </h2>
      <p class="text-sm text-cyan-700 font-mono">Simulate trading strategies on historical data — analyse performance before going live.</p>
    </div>

    <!-- ===== Configuration ===== -->
    <div class="cyber-card p-6">
      <h3 class="text-sm font-bold text-cyan-400 font-mono uppercase tracking-widest mb-5 flex items-center gap-2">
        <span class="text-neon-green">▷</span> Strategy Configuration
      </h3>

      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-5">
        <!-- Symbol -->
        <div>
          <label class="block text-xs text-cyan-600 mb-1.5 font-mono uppercase tracking-widest">Asset</label>
          <select v-model="config.symbol" class="cyber-input w-full">
            <option v-for="asset in store.assets" :key="asset.symbol" :value="asset.symbol">
              {{ asset.symbol }} — {{ asset.name }}
            </option>
          </select>
        </div>

        <!-- Timeframe -->
        <div>
          <label class="block text-xs text-cyan-600 mb-1.5 font-mono uppercase tracking-widest">Timeframe</label>
          <select v-model="config.timeframe" class="cyber-input w-full">
            <option v-for="tf in TIMEFRAMES" :key="tf" :value="tf">{{ tf }}</option>
          </select>
        </div>

        <!-- Strategy -->
        <div>
          <label class="block text-xs text-cyan-600 mb-1.5 font-mono uppercase tracking-widest">Strategy</label>
          <select v-model="config.strategy" class="cyber-input w-full" @change="onStrategyChange">
            <option v-for="s in store.backtestStrategies" :key="s.id" :value="s.id">{{ s.name }}</option>
          </select>
        </div>

        <!-- Run button -->
        <div class="flex flex-col justify-end">
          <button
            class="cyber-btn w-full flex items-center justify-center gap-2"
            :disabled="store.backtestLoading"
            @click="runBacktest"
          >
            <svg v-if="store.backtestLoading" class="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="none">
              <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-dasharray="31.4 31.4" />
            </svg>
            <span>{{ store.backtestLoading ? 'RUNNING…' : '▶ RUN BACKTEST' }}</span>
          </button>
        </div>
      </div>

      <!-- Strategy description -->
      <div v-if="selectedStrategy" class="mb-5 px-4 py-3 rounded border border-cyan-900 bg-cyan-950/30 font-mono text-sm text-cyan-400">
        {{ selectedStrategy.description }}
      </div>

      <!-- Dynamic params -->
      <div v-if="selectedStrategy && selectedStrategy.params.length" class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        <div v-for="param in selectedStrategy.params" :key="param.name">
          <label class="block text-xs text-cyan-600 mb-1 font-mono uppercase tracking-widest">{{ param.label }}</label>
          <select v-if="param.type === 'select'" v-model="paramValues[param.name]" class="cyber-input w-full text-xs">
            <option v-for="opt in param.options" :key="opt" :value="opt">{{ opt }}</option>
          </select>
          <input v-else v-model.number="paramValues[param.name]"
            :type="'number'"
            :min="param.min"
            :max="param.max"
            :step="param.type === 'float' ? 0.1 : 1"
            class="cyber-input w-full text-xs"
          />
        </div>
      </div>

      <div v-if="store.backtestError" class="mt-4 text-sell text-xs font-mono">⚠ {{ store.backtestError }}</div>
    </div>

    <!-- ===== Results ===== -->
    <template v-if="result">
      <!-- KPI Cards -->
      <div class="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-3">
        <div class="cyber-card px-4 py-3 text-center">
          <p class="text-xs text-cyan-600 font-mono uppercase tracking-widest mb-1">Total Return</p>
          <p class="text-xl font-bold font-mono" :class="result.total_return_pct >= 0 ? 'text-neon-green' : 'text-sell'">
            {{ result.total_return_pct >= 0 ? '+' : '' }}{{ result.total_return_pct.toFixed(2) }}%
          </p>
        </div>
        <div class="cyber-card px-4 py-3 text-center">
          <p class="text-xs text-cyan-600 font-mono uppercase tracking-widest mb-1">Max Drawdown</p>
          <p class="text-xl font-bold font-mono text-sell">-{{ result.max_drawdown_pct.toFixed(2) }}%</p>
        </div>
        <div class="cyber-card px-4 py-3 text-center">
          <p class="text-xs text-cyan-600 font-mono uppercase tracking-widest mb-1">Trades</p>
          <p class="text-xl font-bold font-mono text-white">{{ result.num_trades }}</p>
        </div>
        <div class="cyber-card px-4 py-3 text-center">
          <p class="text-xs text-cyan-600 font-mono uppercase tracking-widest mb-1">Win Rate</p>
          <p class="text-xl font-bold font-mono" :class="result.win_rate_pct >= 50 ? 'text-neon-green' : 'text-sell'">
            {{ result.win_rate_pct.toFixed(1) }}%
          </p>
        </div>
        <div class="cyber-card px-4 py-3 text-center">
          <p class="text-xs text-cyan-600 font-mono uppercase tracking-widest mb-1">Sharpe</p>
          <p class="text-xl font-bold font-mono" :class="result.sharpe_ratio >= 1 ? 'text-neon-green' : result.sharpe_ratio >= 0 ? 'text-yellow-400' : 'text-sell'">
            {{ result.sharpe_ratio.toFixed(3) }}
          </p>
        </div>
        <div class="cyber-card px-4 py-3 text-center">
          <p class="text-xs text-cyan-600 font-mono uppercase tracking-widest mb-1">Profit Factor</p>
          <p class="text-xl font-bold font-mono" :class="result.profit_factor >= 1 ? 'text-neon-green' : 'text-sell'">
            {{ result.profit_factor === Infinity ? '∞' : result.profit_factor.toFixed(2) }}
          </p>
        </div>
        <div class="cyber-card px-4 py-3 text-center">
          <p class="text-xs text-cyan-600 font-mono uppercase tracking-widest mb-1">Avg Trade</p>
          <p class="text-xl font-bold font-mono" :class="result.avg_trade_pct >= 0 ? 'text-neon-green' : 'text-sell'">
            {{ result.avg_trade_pct >= 0 ? '+' : '' }}{{ result.avg_trade_pct.toFixed(3) }}%
          </p>
        </div>
      </div>

      <!-- Equity Curve (simple bar chart) -->
      <div v-if="result.equity_curve && result.equity_curve.length > 1" class="cyber-card p-6">
        <h3 class="text-sm font-bold text-cyan-400 font-mono uppercase tracking-widest mb-4">
          Equity Curve · {{ store.backtestResult?.symbol }} {{ store.backtestResult?.strategy }}
        </h3>
        <div class="relative h-40 flex items-end gap-px overflow-hidden">
          <div
            v-for="(val, i) in equityBars"
            :key="i"
            class="flex-1 min-w-0 transition-all duration-300 rounded-sm"
            :class="val.color"
            :style="{ height: val.heightPct + '%' }"
            :title="`$${val.value.toFixed(2)}`"
          />
        </div>
        <div class="flex justify-between text-xs text-cyan-700 font-mono mt-1">
          <span>${{ result.equity_curve[0].toLocaleString('en-US', { maximumFractionDigits: 0 }) }}</span>
          <span :class="result.equity_curve.at(-1) >= result.equity_curve[0] ? 'text-neon-green' : 'text-sell'">
            ${{ result.equity_curve.at(-1).toLocaleString('en-US', { maximumFractionDigits: 0 }) }}
          </span>
        </div>
      </div>

      <!-- Trade List -->
      <div v-if="result.trades && result.trades.length" class="cyber-card p-6">
        <h3 class="text-sm font-bold text-cyan-400 font-mono uppercase tracking-widest mb-4">
          Recent Trades (last {{ result.trades.length }})
        </h3>
        <div class="overflow-x-auto">
          <table class="w-full text-xs font-mono">
            <thead>
              <tr class="text-cyan-700 uppercase tracking-widest border-b border-cyan-900">
                <th class="text-left pb-2 pr-4">#</th>
                <th class="text-left pb-2 pr-4">Side</th>
                <th class="text-right pb-2 pr-4">Entry</th>
                <th class="text-right pb-2 pr-4">Exit</th>
                <th class="text-right pb-2 pr-4">PnL %</th>
                <th v-if="hasExitReason" class="text-right pb-2">Reason</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(trade, i) in [...result.trades].reverse().slice(0, 20)" :key="i"
                class="border-b border-cyan-900/20 hover:bg-cyan-900/10">
                <td class="py-1.5 pr-4 text-cyan-700">{{ result.trades.length - i }}</td>
                <td class="py-1.5 pr-4">
                  <span :class="trade.side === 'LONG' ? 'text-neon-green' : 'text-sell'">
                    {{ trade.side === 'LONG' ? '↑' : '↓' }} {{ trade.side }}
                  </span>
                </td>
                <td class="py-1.5 pr-4 text-right text-gray-400">{{ trade.entry_price }}</td>
                <td class="py-1.5 pr-4 text-right text-gray-400">{{ trade.close_price }}</td>
                <td class="py-1.5 pr-4 text-right font-bold" :class="trade.pnl_pct >= 0 ? 'text-neon-green' : 'text-sell'">
                  {{ trade.pnl_pct >= 0 ? '+' : '' }}{{ trade.pnl_pct.toFixed(3) }}%
                </td>
                <td v-if="hasExitReason" class="py-1.5 text-right">
                  <span v-if="trade.exit_reason" :class="trade.exit_reason === 'TP' ? 'text-neon-green/70' : 'text-sell/70'">
                    {{ trade.exit_reason }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- No trades message -->
      <div v-else-if="!store.backtestLoading" class="cyber-card p-10 text-center text-cyan-800 font-mono">
        <p class="text-2xl mb-2">◻</p>
        No trades generated with current parameters. Try adjusting the strategy settings.
      </div>
    </template>

    <!-- Strategy Cards (shown before first run) -->
    <div v-if="!result && !store.backtestLoading" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      <div v-for="s in store.backtestStrategies" :key="s.id"
        class="cyber-card p-5 cursor-pointer hover:border-cyan-500 transition-colors duration-200"
        @click="config.strategy = s.id; onStrategyChange()">
        <div class="flex items-start justify-between mb-2">
          <h3 class="font-bold text-white font-mono">{{ s.name }}</h3>
          <span v-if="config.strategy === s.id" class="text-xs text-neon-green font-mono">[ SELECTED ]</span>
        </div>
        <p class="text-xs text-cyan-600 font-mono">{{ s.description }}</p>
        <div class="mt-3 flex flex-wrap gap-1">
          <span v-for="p in s.params" :key="p.name"
            class="px-2 py-0.5 rounded border border-cyan-900 text-cyan-700 text-[10px] font-mono">
            {{ p.label }}: {{ p.default }}
          </span>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useMarketStore } from '@/store/market'

const store = useMarketStore()

const TIMEFRAMES = ['1m', '5m', '15m', '30m', '1h', '24h']

const config = ref({
  symbol:    'BTC',
  timeframe: '1h',
  strategy:  'ma_crossover',
})

const paramValues = ref({})

const selectedStrategy = computed(() =>
  store.backtestStrategies.find(s => s.id === config.value.strategy) ?? null
)

function onStrategyChange() {
  const s = selectedStrategy.value
  if (!s) return
  const defaults = {}
  for (const p of s.params) defaults[p.name] = p.default
  paramValues.value = defaults
}

watch(() => store.backtestStrategies, () => {
  if (store.backtestStrategies.length && !paramValues.value[Object.keys(paramValues.value)[0]]) {
    onStrategyChange()
  }
}, { immediate: true })

async function runBacktest() {
  await store.runBacktest({
    symbol:    config.value.symbol,
    strategy:  config.value.strategy,
    timeframe: config.value.timeframe,
    params:    { ...paramValues.value },
  })
}

const result = computed(() => store.backtestResult?.result ?? null)

const hasExitReason = computed(() =>
  result.value?.trades?.some(t => 'exit_reason' in t) ?? false
)

const equityBars = computed(() => {
  const curve = result.value?.equity_curve ?? []
  if (curve.length < 2) return []
  const min = Math.min(...curve)
  const max = Math.max(...curve)
  const range = max - min || 1
  const initial = curve[0]
  // Downsample to max 100 bars for display
  const step = Math.max(1, Math.floor(curve.length / 100))
  return curve.filter((_, i) => i % step === 0 || i === curve.length - 1).map(val => ({
    value: val,
    heightPct: Math.max(2, ((val - min) / range) * 100),
    color: val >= initial ? 'bg-neon-green/60' : 'bg-sell/60',
  }))
})

onMounted(async () => {
  if (!store.backtestStrategies.length) {
    await store.fetchBacktestStrategies()
    onStrategyChange()
  }
})
</script>
