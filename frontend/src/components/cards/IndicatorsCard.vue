<template>
  <BaseCard title="Technical Indicators" icon="📐" @remove="$emit('remove')">
    <div v-if="hasIndicators" class="space-y-2">
      <!-- RSI -->
      <IndicatorRow label="RSI (14)" :value="ind.rsi?.value" type="oscillator">
        <GaugeBar :value="ind.rsi?.value" :min="0" :max="100" :low="30" :high="70" />
      </IndicatorRow>

      <!-- MACD -->
      <IndicatorRow label="MACD" :value="ind.macd?.value" type="trend">
        <span :class="macdColor" class="text-xs font-mono">
          H: {{ fmtS(ind.macd?.histogram) }}
        </span>
      </IndicatorRow>

      <!-- Bollinger Bands -->
      <IndicatorRow label="BB Bandwidth" :value="ind.bbands?.bandwidth" type="volatility">
        <span class="text-xs text-gray-400 font-mono">
          {{ fmtS(ind.bbands?.lower) }} / {{ fmtS(ind.bbands?.upper) }}
        </span>
      </IndicatorRow>

      <!-- EMA -->
      <IndicatorRow label="EMA 20/50" :value="ind.ema?.ema20" type="trend">
        <span class="text-xs font-mono" :class="ind.ema?.ema20 > ind.ema?.ema50 ? 'text-buy' : 'text-sell'">
          {{ fmtS(ind.ema?.ema20) }} / {{ fmtS(ind.ema?.ema50) }}
        </span>
      </IndicatorRow>

      <!-- SMA -->
      <IndicatorRow label="SMA 20/50" :value="ind.sma?.sma20" type="trend">
        <span class="text-xs font-mono" :class="ind.sma?.sma20 > ind.sma?.sma50 ? 'text-buy' : 'text-sell'">
          {{ fmtS(ind.sma?.sma20) }} / {{ fmtS(ind.sma?.sma50) }}
        </span>
      </IndicatorRow>

      <!-- Stochastic -->
      <IndicatorRow label="Stoch %K/%D" :value="ind.stoch?.k" type="oscillator">
        <GaugeBar :value="ind.stoch?.k" :min="0" :max="100" :low="20" :high="80" />
      </IndicatorRow>

      <!-- ATR -->
      <IndicatorRow label="ATR (14)" :value="ind.atr?.value" type="volatility" />

      <!-- ADX -->
      <IndicatorRow label="ADX (14)" :value="ind.adx?.adx" type="trend">
        <span class="text-xs font-mono" :class="ind.adx?.dmp > ind.adx?.dmn ? 'text-buy' : 'text-sell'">
          +DI {{ fmtS(ind.adx?.dmp) }} / -DI {{ fmtS(ind.adx?.dmn) }}
        </span>
      </IndicatorRow>

      <!-- CCI -->
      <IndicatorRow label="CCI (20)" :value="ind.cci?.value" type="oscillator">
        <span :class="cciColor" class="text-xs font-mono">{{ fmtS(ind.cci?.value) }}</span>
      </IndicatorRow>

      <!-- Williams %R -->
      <IndicatorRow label="Williams %R" :value="ind.willr?.value" type="oscillator">
        <GaugeBar :value="ind.willr?.value ? ind.willr.value + 100 : null" :min="0" :max="100" :low="20" :high="80" />
      </IndicatorRow>

      <!-- VWAP -->
      <IndicatorRow label="VWAP" :value="ind.vwap?.value" type="volume" />

      <!-- OBV -->
      <IndicatorRow label="OBV" :value="ind.obv?.value" type="volume" />
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
import IndicatorRow from '@/components/ui/IndicatorRow.vue'
import GaugeBar from '@/components/ui/GaugeBar.vue'

defineEmits(['remove'])

const store = useMarketStore()
const ind = computed(() => store.indicators)
const hasIndicators = computed(() => Object.keys(ind.value).length > 0)

const macdColor = computed(() =>
  (ind.value.macd?.histogram ?? 0) > 0 ? 'text-buy' : 'text-sell'
)
const cciColor = computed(() => {
  const v = ind.value.cci?.value
  if (v == null) return 'text-gray-400'
  if (v > 100) return 'text-sell'
  if (v < -100) return 'text-buy'
  return 'text-neutral'
})

function fmtS(val) {
  if (val == null) return '—'
  const n = Number(val)
  if (Math.abs(n) >= 1000) return n.toLocaleString('en-US', { maximumFractionDigits: 0 })
  if (Math.abs(n) >= 1)    return n.toFixed(2)
  return n.toFixed(5)
}
</script>
