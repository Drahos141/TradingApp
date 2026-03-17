import { defineStore } from 'pinia'
import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL || ''

export const useMarketStore = defineStore('market', {
  state: () => ({
    assets: [],
    selectedSymbol: 'BTC',
    selectedTimeframe: '1h',
    dashboardData: null,
    loading: false,
    error: null,
    lastUpdated: null,
    connected: false,
    demoMode: false,
  }),

  getters: {
    price: (s) => s.dashboardData?.price ?? null,
    indicators: (s) => s.dashboardData?.indicators ?? {},
    indicatorSignals: (s) => s.dashboardData?.indicator_signals ?? {},
    signalSummary: (s) => s.dashboardData?.signal_summary ?? null,
    predictions: (s) => s.dashboardData?.predictions ?? {},
    candles: (s) => s.dashboardData?.candles ?? [],
    currentAsset: (s) => s.assets.find((a) => a.symbol === s.selectedSymbol) ?? null,
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
  },
})
