import { defineStore } from 'pinia'
import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL || ''

const POSITIONS_KEY = 'tradingApp_positions'

function loadPositions() {
  try {
    const raw = localStorage.getItem(POSITIONS_KEY)
    return raw ? JSON.parse(raw) : []
  } catch {
    return []
  }
}

function savePositions(positions) {
  try {
    localStorage.setItem(POSITIONS_KEY, JSON.stringify(positions))
  } catch {
    // ignore storage errors
  }
}

export const useMarketStore = defineStore('market', {
  state: () => ({
    // --- market data ---
    assets: [],
    selectedSymbol: 'BTC',
    selectedTimeframe: '1h',
    dashboardData: null,
    loading: false,
    error: null,
    lastUpdated: null,
    connected: false,
    demoMode: false,

    // --- simulated trading ---
    positions: loadPositions(),
    livePrices: {},      // symbol -> current price number

    // --- news ---
    news: [],
    newsLoading: false,
    newsError: null,
    newsTokenFilter: null,  // null | 'BTC' | 'ETH' | 'HYPE'
  }),

  getters: {
    price: (s) => s.dashboardData?.price ?? null,
    indicators: (s) => s.dashboardData?.indicators ?? {},
    indicatorSignals: (s) => s.dashboardData?.indicator_signals ?? {},
    signalSummary: (s) => s.dashboardData?.signal_summary ?? null,
    predictions: (s) => s.dashboardData?.predictions ?? {},
    candles: (s) => s.dashboardData?.candles ?? [],
    currentAsset: (s) => s.assets.find((a) => a.symbol === s.selectedSymbol) ?? null,

    openPositions: (s) => s.positions.filter((p) => p.status === 'OPEN'),
    closedPositions: (s) => s.positions.filter((p) => p.status === 'CLOSED'),

    filteredNews: (s) => {
      if (!s.newsTokenFilter) return s.news
      return s.news.filter((a) => a.tokens.includes(s.newsTokenFilter))
    },
  },

  actions: {
    async fetchAssets() {
      try {
        const res = await axios.get(`${BASE_URL}/api/assets`)
        this.assets = res.data
      } catch (e) {
        console.error('Failed to fetch assets', e)
      }
    },

    async refreshDashboard() {
      if (!this.selectedSymbol) return
      this.loading = true
      this.error = null
      try {
        const res = await axios.get(
          `${BASE_URL}/api/dashboard/${this.selectedSymbol}`,
          { params: { timeframe: this.selectedTimeframe } }
        )
        this.dashboardData = res.data
        this.lastUpdated = new Date()
        this.connected = true
        this.demoMode = res.data.demo_mode ?? false
        // keep live price in sync
        if (res.data.price?.price) {
          this.livePrices[this.selectedSymbol] = res.data.price.price
        }
      } catch (e) {
        this.error = e?.response?.data?.detail ?? e.message ?? 'Unknown error'
        this.connected = false
      } finally {
        this.loading = false
      }
    },

    setSymbol(sym) {
      this.selectedSymbol = sym
      this.dashboardData = null
      this.refreshDashboard()
    },

    setTimeframe(tf) {
      this.selectedTimeframe = tf
      this.refreshDashboard()
    },

    // ---- Live price fetching for trading positions ----
    async fetchLivePrice(symbol) {
      try {
        const res = await axios.get(`${BASE_URL}/api/price/${symbol}`)
        if (res.data?.price) {
          this.livePrices[symbol] = res.data.price
        }
      } catch (e) {
        console.warn('Failed to fetch price for', symbol, e.message)
      }
    },

    async fetchLivePricesForOpenPositions() {
      const symbols = [...new Set(this.openPositions.map((p) => p.symbol))]
      await Promise.all(symbols.map((s) => this.fetchLivePrice(s)))
    },

    updateLivePrice(symbol, price) {
      this.livePrices[symbol] = price
    },

    // ---- Paper trading positions ----
    openPosition({ symbol, direction, amount, entryPrice }) {
      const position = {
        id:         Date.now(),
        symbol,
        direction,  // 'LONG' | 'SHORT'
        amount:     Number(amount),
        entryPrice: Number(entryPrice),
        openedAt:   new Date().toISOString(),
        status:     'OPEN',
        closePrice: null,
        closedAt:   null,
      }
      this.positions.push(position)
      savePositions(this.positions)
    },

    closePosition(id) {
      const pos = this.positions.find((p) => p.id === id)
      if (!pos || pos.status !== 'OPEN') return
      const currentPrice = this.livePrices[pos.symbol] ?? pos.entryPrice
      pos.status     = 'CLOSED'
      pos.closePrice = currentPrice
      pos.closedAt   = new Date().toISOString()
      savePositions(this.positions)
    },

    clearClosedPositions() {
      this.positions = this.positions.filter((p) => p.status === 'OPEN')
      savePositions(this.positions)
    },

    // ---- News ----
    async fetchNews() {
      this.newsLoading = true
      this.newsError   = null
      try {
        const params = this.newsTokenFilter ? { token: this.newsTokenFilter } : {}
        const res = await axios.get(`${BASE_URL}/api/news`, { params })
        this.news = res.data.articles ?? []
      } catch (e) {
        this.newsError = e?.response?.data?.detail ?? e.message ?? 'Unknown error'
      } finally {
        this.newsLoading = false
      }
    },

    setNewsFilter(token) {
      this.newsTokenFilter = token
      this.fetchNews()
    },
  },
})
