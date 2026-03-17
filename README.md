# TradingApp

A full-stack trading dashboard for crypto (BTC, ETH, BNB, SOL), gold (XAU) and crude oil (CL).  
It shows live prices, 12 technical indicators, buy/sell signals, ML-powered multi-timeframe predictions and an interactive candlestick chart.

When market data cannot be fetched (e.g. in a restricted network), the app automatically falls back to realistic **demo data** so the dashboard always loads.

---

## Features

| Feature | Details |
|---|---|
| 📈 Live prices | Fetched from Yahoo Finance via yfinance |
| 📐 12 indicators | RSI, MACD, Bollinger Bands, EMA/SMA, Stochastic, ATR, ADX, CCI, Williams %R, VWAP, OBV |
| 🚦 Buy/Sell signals | Consensus signal from all indicators |
| 🤖 ML predictions | Ensemble RandomForest + GradientBoosting for 8 timeframes (1m → 24h) |
| 📊 Candlestick chart | Lightweight-Charts interactive chart |
| 🃏 Draggable dashboard | Customisable card layout |
| 🎭 Demo mode | Automatic fallback to synthetic data |

---

## Quick start with Docker Compose (recommended)

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) ≥ 24  
- [Docker Compose](https://docs.docker.com/compose/install/) ≥ 2

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/Drahos141/TradingApp.git
cd TradingApp

# 2. Start all services
docker compose up --build

# 3. Open the app
#    Frontend: http://localhost:5173
#    Backend API: http://localhost:8000
```

To stop:

```bash
docker compose down
```

---

## Local development setup

### Backend (Python / FastAPI)

**Requirements:** Python 3.11 or 3.12

```bash
cd backend

# (Optional) create a virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the development server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API is now available at <http://localhost:8000>.

### Frontend (Vue 3 / Vite)

**Requirements:** Node.js ≥ 18

```bash
cd frontend

# Install dependencies
npm install

# Start the dev server (proxies /api to localhost:8000)
npm run dev
```

The UI is now available at <http://localhost:5173>.

---

## API reference

All responses are JSON.  When live market data is unavailable the backend automatically serves demo data (responses include `"demo": true`).

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check → `{"status": "ok"}` |
| `GET` | `/api/assets` | List of supported assets |
| `GET` | `/api/price/{symbol}` | Latest price for a symbol |
| `GET` | `/api/dashboard/{symbol}?timeframe=1h` | Full dashboard payload |

**Supported symbols:** `BTC`, `ETH`, `BNB`, `SOL`, `XAU`, `CL`

**Supported timeframes:** `1m`, `3m`, `5m`, `10m`, `15m`, `30m`, `1h`, `24h`

### Example requests

```bash
# Health check
curl http://localhost:8000/health

# Current BTC price
curl http://localhost:8000/api/price/BTC

# Full BTC dashboard (1-hour timeframe)
curl "http://localhost:8000/api/dashboard/BTC?timeframe=1h"
```

---

## Using the dashboard

1. **Select an asset** by clicking one of the symbol buttons in the top bar (`BTC`, `ETH`, etc.).
2. **Change the chart timeframe** using the dropdown inside the Price Chart card.
3. **Add or remove cards** via the `+ Card` button in the top bar.
4. **Drag cards** by their header to rearrange the layout.
5. The dashboard **auto-refreshes every 10 seconds**.  A live/offline indicator in the top-right shows connectivity status.
6. A 🎭 **DEMO** badge appears when the app cannot reach Yahoo Finance and is using synthetic data.

---

## Running the tests

```bash
cd backend
pip install -r requirements.txt   # also installs pytest
python -m pytest tests/ -v
```

The test suite covers:
- All 12 technical indicators (values, ranges, structure)
- Buy/Sell signal logic and consensus summary
- ML feature engineering, label building and predictions
- Demo data generators
- Ticker/symbol mapping
- All HTTP API endpoints via `TestClient` (health, assets, price, dashboard)

---

## Project structure

```
TradingApp/
├── backend/
│   ├── main.py              # FastAPI app & routes
│   ├── data_fetcher.py      # yfinance market data client
│   ├── indicators.py        # 12 technical indicators (pandas-ta)
│   ├── ml_predictions.py    # ML ensemble (RandomForest + GradientBoosting)
│   ├── demo_data.py         # Synthetic OHLCV fallback data
│   ├── requirements.txt
│   ├── Dockerfile
│   └── tests/
│       └── test_backend.py  # Unit + API tests (32 tests)
├── frontend/
│   ├── src/
│   │   ├── components/      # Vue 3 dashboard components
│   │   └── store/market.js  # Pinia state store
│   ├── nginx.conf           # Production reverse proxy config
│   ├── Dockerfile
│   └── package.json
└── docker-compose.yml
```

---

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| 🎭 DEMO badge is shown | No internet / Yahoo Finance blocked | Expected in restricted networks; data is synthetic but fully functional |
| Frontend shows "OFFLINE" | Backend not reachable | Make sure the backend is running on port 8000 |
| `docker compose up` fails | Port 8000 or 5173 already in use | Stop the conflicting service or change the port mapping in `docker-compose.yml` |
| Slow first load | ML models are trained on first request | Wait ~5 seconds; subsequent requests use the model cache |
