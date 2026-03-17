<template>
  <BaseCard title="ML Predictions" icon="🤖" @remove="$emit('remove')">
    <p class="text-xs text-gray-500 mb-3">
      Ensemble RF + GB model · refreshed every 10s
    </p>

    <div v-if="hasPredictions" class="grid grid-cols-2 gap-2">
      <PredictionTile
        v-for="tf in TIMEFRAMES"
        :key="tf.key"
        :label="tf.label"
        :data="predictions[tf.key]"
      />
    </div>

    <div v-else class="flex items-center justify-center h-24 text-gray-500 text-sm">
      Waiting for predictions…
    </div>
  </BaseCard>
</template>

<script setup>
import { computed } from 'vue'
import { useMarketStore } from '@/store/market'
import BaseCard from './BaseCard.vue'
import PredictionTile from '@/components/ui/PredictionTile.vue'

defineEmits(['remove'])

const TIMEFRAMES = [
  { key: '1m',  label: '1 min'  },
  { key: '3m',  label: '3 min'  },
  { key: '5m',  label: '5 min'  },
  { key: '10m', label: '10 min' },
  { key: '15m', label: '15 min' },
  { key: '30m', label: '30 min' },
  { key: '1h',  label: '1 hour' },
  { key: '24h', label: '24 hour'},
]

const store = useMarketStore()
const predictions = computed(() => store.predictions)
const hasPredictions = computed(() => Object.keys(predictions.value).length > 0)
</script>
