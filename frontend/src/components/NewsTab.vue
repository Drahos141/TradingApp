<template>
  <div class="flex-1 p-4 max-w-6xl mx-auto w-full">

    <!-- ===== Header & Filters ===== -->
    <div class="flex flex-wrap items-center justify-between gap-4 mb-6">
      <h2 class="text-lg font-bold text-white flex items-center gap-2">
        📰 Crypto News
      </h2>

      <div class="flex items-center gap-2 flex-wrap">
        <!-- Token filter buttons -->
        <button
          v-for="f in filters"
          :key="f.value ?? 'all'"
          class="px-3 py-1.5 rounded-lg text-xs font-semibold transition-all duration-200"
          :class="store.newsTokenFilter === f.value
            ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/30'
            : 'bg-surface border border-border text-gray-400 hover:border-blue-500 hover:text-white'"
          @click="setFilter(f.value)"
        >
          {{ f.icon }} {{ f.label }}
        </button>

        <!-- Refresh button -->
        <button
          class="px-3 py-1.5 rounded-lg text-xs font-semibold bg-surface border border-border text-gray-400 hover:border-blue-500 hover:text-white transition-all duration-200"
          :disabled="store.newsLoading"
          @click="store.fetchNews()"
        >
          <span v-if="store.newsLoading" class="inline-block animate-spin mr-1">↻</span>
          <span v-else>↻</span>
          Refresh
        </button>
      </div>
    </div>

    <!-- ===== Loading ===== -->
    <div v-if="store.newsLoading && !store.news.length" class="flex items-center justify-center py-24 gap-3 text-gray-500">
      <svg class="w-6 h-6 animate-spin text-blue-500" viewBox="0 0 24 24" fill="none">
        <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-dasharray="31.4 31.4" />
      </svg>
      <span>Fetching news…</span>
    </div>

    <!-- ===== Error ===== -->
    <div
      v-else-if="store.newsError"
      class="px-4 py-3 rounded-xl bg-red-900/40 border border-red-700/50 text-red-300 text-sm mb-4"
    >
      ⚠️ {{ store.newsError }}
    </div>

    <!-- ===== No results ===== -->
    <div
      v-else-if="!store.newsLoading && store.filteredNews.length === 0"
      class="text-center py-16 text-gray-600"
    >
      <span class="text-5xl block mb-3">🔍</span>
      <p>No news found{{ store.newsTokenFilter ? ` for ${store.newsTokenFilter}` : '' }}.</p>
    </div>

    <!-- ===== News Grid ===== -->
    <div v-else class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
      <a
        v-for="article in store.filteredNews"
        :key="article.id"
        :href="article.url !== '#' ? article.url : undefined"
        target="_blank"
        rel="noopener noreferrer"
        class="block bg-card border border-border rounded-2xl p-5 hover:border-blue-500/60 hover:shadow-lg hover:shadow-blue-500/10 transition-all duration-200 group"
      >
        <!-- Token badges -->
        <div v-if="article.tokens.length" class="flex gap-1.5 mb-3">
          <span
            v-for="token in article.tokens"
            :key="token"
            class="px-2 py-0.5 rounded-full text-xs font-bold"
            :class="tokenBadgeClass(token)"
          >
            {{ tokenIcon(token) }} {{ token }}
          </span>
        </div>
        <div v-else class="flex gap-1.5 mb-3">
          <span class="px-2 py-0.5 rounded-full text-xs font-bold bg-gray-700/50 text-gray-400">
            🌐 General
          </span>
        </div>

        <!-- Title -->
        <h3 class="text-white font-semibold text-sm leading-snug mb-2 group-hover:text-blue-300 transition-colors line-clamp-3">
          {{ article.title }}
        </h3>

        <!-- Summary -->
        <p v-if="article.summary" class="text-gray-500 text-xs leading-relaxed mb-3 line-clamp-3">
          {{ article.summary }}
        </p>

        <!-- Footer: source + date -->
        <div class="flex items-center justify-between mt-auto pt-2 border-t border-border/50">
          <span class="text-xs font-medium text-gray-500">{{ article.source }}</span>
          <span class="text-xs text-gray-600">{{ formatDate(article.published_at) }}</span>
        </div>
      </a>
    </div>

  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useMarketStore } from '@/store/market'

const store = useMarketStore()

const filters = [
  { value: null,   label: 'All',  icon: '🌐' },
  { value: 'BTC',  label: 'BTC',  icon: '₿'  },
  { value: 'ETH',  label: 'ETH',  icon: '⟠'  },
  { value: 'HYPE', label: 'HYPE', icon: '🔥' },
]

function setFilter(value) {
  store.setNewsFilter(value)
}

function tokenBadgeClass(token) {
  switch (token) {
    case 'BTC':  return 'bg-orange-500/20 text-orange-400'
    case 'ETH':  return 'bg-blue-500/20 text-blue-400'
    case 'HYPE': return 'bg-purple-500/20 text-purple-400'
    default:     return 'bg-gray-700/50 text-gray-400'
  }
}

function tokenIcon(token) {
  switch (token) {
    case 'BTC':  return '₿'
    case 'ETH':  return '⟠'
    case 'HYPE': return '🔥'
    default:     return '🪙'
  }
}

function formatDate(isoStr) {
  if (!isoStr) return ''
  try {
    const d = new Date(isoStr)
    const now = new Date()
    const diffMs = now - d
    const diffH = Math.floor(diffMs / 3600000)
    if (diffH < 1) {
      const diffM = Math.floor(diffMs / 60000)
      return diffM <= 0 ? 'just now' : `${diffM}m ago`
    }
    if (diffH < 24) return `${diffH}h ago`
    const diffD = Math.floor(diffH / 24)
    if (diffD < 7) return `${diffD}d ago`
    return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
  } catch {
    return isoStr
  }
}

onMounted(() => {
  if (!store.news.length) {
    store.fetchNews()
  }
})
</script>
