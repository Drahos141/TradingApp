import { defineStore } from 'pinia'
import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL || ''

const POSITIONS_KEY  = 'tradingApp_positions'
const WALLET_KEY     = 'tradingApp_wallet'
const INITIAL_WALLET = 10_000

function loadPositions() {
  try {
    const raw = localStorage.getItem(POSITIONS_KEY)
    return raw ? JSON.parse(raw) : []
  } catch {
    return []
  }
}

function loadWallet() {
  try {
    const raw = localStorage.getItem(WALLET_KEY)
    return raw ? JSON.parse(raw) : { balance: INITIAL_WALLET, totalDeposited: INITIAL_WALLET }
  } catch {
    return { balance: INITIAL_WALLET, totalDeposited: INITIAL_WALLET }
  }
}

function savePositions(positions) {
  try {
    localStorage.setItem(POSITIONS_KEY, JSON.stringify(positions))
  } catch { /* ignore */ }
}

function saveWallet(wallet) {
  try {
    localStorage.setItem(WALLET_KEY, JSON.stringify(wallet))
  } catch { /* ignore */ }
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
    wallet: loadWallet(),

    // --- backtesting ---
    backtestLoading: false,
    backtestResult: null,
    backtestError: null,
    backtestStrategies: [],

    // --- news ---
    news: [],
    newsLoading: false,
    newsError: null,
    newsTokenFilter: null,
  }),

  getters: {
    price:            (s) => s.dashboardData?.price ?? null,
    indicators:       (s) => s.dashboardData?.indicators ?? {},
    indicatorSignals: (s) => s.dashboardData?.indicator_signals ?? {},
    signalSummary:    (s) => s.dashboardData?.signal_summary ?? null,
    predictions:      (s) => s.dashboardData?.predictions ?? {},
    candles:          (s) => s.dashboardData?.candles ?? [],
    currentAsset:     (s) => s.assets.find((a) => a.symbol === s.selectedSymbol) ?? null,

    openPositions:   (s) => s.positions.filter((p) => p.status === 'OPEN'),
    closedPositions: (s) => s.positions.filter((p) => p.status === 'CLOSED'),

    walletBalance: (s) => s.wallet.balance,
    walletPnL:     (s) => s.wallet.balance - s.wallet.totalDeposited,

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

    // ---- Live price fetching ----
    async fetchLivePrice(symbol) {
      try {
        const res = await axios.get(`${BASE_URL}/api/price/${symbol}`)
        if (res.data?.price) {
          this.livePrices[symbol] = res.data.price
          // Auto-trigger stop loss / take profit checks after every price update
          this._checkStopLossTakeProfit(symbol)
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

    // ---- Stop loss / Take profit auto-close ----
    _checkStopLossTakeProfit(symbol) {
      const price = this.livePrices[symbol]
      if (!price) return
      this.openPositions
        .filter((p) => p.symbol === symbol)
        .forEach((pos) => {
          const isLong = pos.direction === 'LONG'
          const slHit = pos.stopLoss  && (isLong ? price <= pos.stopLoss  : price >= pos.stopLoss)
          const tpHit = pos.takeProfit && (isLong ? price >= pos.takeProfit : price <= pos.takeProfit)
          if (slHit || tpHit) {
            this._closePosition(pos.id, price, slHit ? 'SL' : 'TP')
          }
        })
    },

    // ---- Paper trading positions ----
    openPosition({ symbol, direction, amount, entryPrice, stopLoss, takeProfit }) {
      const cost = Number(amount)
      if (cost > this.wallet.balance) return false
      const position = {
        id:         Date.now(),
        symbol,
        direction,
        amount:     cost,
        entryPrice: Number(entryPrice),
        stopLoss:   stopLoss   ? Number(stopLoss)   : null,
        takeProfit: takeProfit ? Number(takeProfit) : null,
        openedAt:   new Date().toISOString(),
        status:     'OPEN',
        closePrice: null,
        closedAt:   null,
        closeReason: null,
      }
      this.positions.push(position)
      this.wallet.balance -= cost
      savePositions(this.positions)
      saveWallet(this.wallet)
      return true
    },

    closePosition(id) {
      const pos = this.positions.find((p) => p.id === id)
      if (!pos || pos.status !== 'OPEN') return
      const currentPrice = this.livePrices[pos.symbol] ?? pos.entryPrice
      this._closePosition(id, currentPrice, 'MANUAL')
    },

    _closePosition(id, closePrice, reason = 'MANUAL') {
      const pos = this.positions.find((p) => p.id === id)
      if (!pos || pos.status !== 'OPEN') return
      const priceDiff = closePrice - pos.entryPrice
      const mult = pos.direction === 'LONG' ? 1 : -1
      const pnlUSD = (priceDiff / pos.entryPrice) * pos.amount * mult
      pos.status      = 'CLOSED'
      pos.closePrice  = closePrice
      pos.closedAt    = new Date().toISOString()
      pos.closeReason = reason
      pos.pnlUSD      = pnlUSD
      // Return original cost + profit/loss to wallet
      this.wallet.balance += pos.amount + pnlUSD
      savePositions(this.positions)
      saveWallet(this.wallet)
    },

    clearClosedPositions() {
      this.positions = this.positions.filter((p) => p.status === 'OPEN')
      savePositions(this.positions)
    },

    resetWallet() {
      this.wallet = { balance: INITIAL_WALLET, totalDeposited: INITIAL_WALLET }
      saveWallet(this.wallet)
    },

    depositWallet(amount) {
      this.wallet.balance       += Number(amount)
      this.wallet.totalDeposited += Number(amount)
      saveWallet(this.wallet)
    },

    // ---- Backtesting ----
    async fetchBacktestStrategies() {
      try {
        const res = await axios.get(`${BASE_URL}/api/backtest/strategies`)
        this.backtestStrategies = res.data.strategies ?? []
      } catch (e) {
        console.error('Failed to fetch backtest strategies', e)
      }
    },

    async runBacktest({ symbol, strategy, timeframe, params }) {
      this.backtestLoading = true
      this.backtestResult  = null
      this.backtestError   = null
      try {
        const paramsStr = JSON.stringify(params || {})
        const res = await axios.post(
          `${BASE_URL}/api/backtest/${symbol}`,
          null,
          { params: { strategy, timeframe, params: paramsStr } }
        )
        this.backtestResult = res.data
      } catch (e) {
        this.backtestError = e?.response?.data?.detail ?? e.message ?? 'Backtest failed'
      } finally {
        this.backtestLoading = false
      }
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
