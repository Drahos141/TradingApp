"""
FastAPI backend for TradingApp Dashboard.

Endpoints
---------
GET /api/assets               – list of supported assets
GET /api/dashboard/{symbol}   – full dashboard payload (price, indicators, predictions)
GET /api/price/{symbol}       – quick price lookup
GET /health                   – health check
"""
import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from data_fetcher import fetch_ohlcv, get_current_price, ASSET_MAP
from indicators import calculate_indicators, indicator_signals
from ml_predictions import predict_all_timeframes
from demo_data import generate_ohlcv, generate_price_info
from news_fetcher import fetch_news

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Application lifecycle
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ARG001
    logger.info("TradingApp backend starting up …")
    yield
    logger.info("TradingApp backend shutting down …")


app = FastAPI(
    title="TradingApp API",
    version="1.0.0",
    description="Crypto, Gold and Oil trading signals powered by ML",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Supported assets
# ---------------------------------------------------------------------------

ASSETS = [
    {"symbol": "BTC",  "name": "Bitcoin",        "category": "crypto",     "ticker": "BTC-USD"},
    {"symbol": "ETH",  "name": "Ethereum",        "category": "crypto",     "ticker": "ETH-USD"},
    {"symbol": "BNB",  "name": "BNB",             "category": "crypto",     "ticker": "BNB-USD"},
    {"symbol": "SOL",  "name": "Solana",           "category": "crypto",     "ticker": "SOL-USD"},
    {"symbol": "HYPE", "name": "Hyperliquid HYPE", "category": "crypto",     "ticker": "HYPE-USD"},
    {"symbol": "XAU",  "name": "Gold",             "category": "commodity",  "ticker": "GC=F"},
    {"symbol": "CL",   "name": "Crude Oil (WTI)",  "category": "commodity",  "ticker": "CL=F"},
]

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/assets")
def list_assets():
    return ASSETS


@app.get("/api/price/{symbol}")
def price(symbol: str):
    sym = symbol.upper()
    info = get_current_price(sym)
    if info is None:
        # Live price unavailable – fall back to demo data so the endpoint
        # always returns a usable response rather than a 404.
        info = generate_price_info(sym)
    return info


@app.get("/api/news")
def news(token: Optional[str] = Query(default=None, description="Filter by token: BTC, ETH, HYPE")):
    """Fetch crypto news articles with optional token filter."""
    articles = fetch_news(token)
    return {"articles": articles}


@app.get("/api/dashboard/{symbol}")
def dashboard(
    symbol: str,
    timeframe: str = Query(default="1h", description="Primary chart timeframe"),
):
    """
    Full dashboard payload for *symbol*.

    Returns:
      - price info
      - 12 technical indicators
      - per-indicator signals
      - ML predictions for 8 timeframes (score 1-100 + BUY/SELL/NEUTRAL)
      - recent OHLCV candles for the mini chart
    """
    sym = symbol.upper()
    if sym not in ASSET_MAP and sym not in [a["symbol"] for a in ASSETS]:
        raise HTTPException(status_code=400, detail=f"Unknown symbol: {symbol}")

    # Fetch primary OHLCV data – fall back to demo data if unavailable
    df = fetch_ohlcv(sym, timeframe)
    demo_mode = df is None
    if demo_mode:
        logger.info("Using demo data for %s / %s", sym, timeframe)
        df = generate_ohlcv(sym)

    # Price
    price_info = get_current_price(sym)
    if price_info is None:
        price_info = generate_price_info(sym)

    # Indicators
    indicators = calculate_indicators(df)

    # Indicator-based signals
    current_price = (price_info or {}).get("price") or float(df["close"].iloc[-1])
    ind_signals = indicator_signals(indicators, current_price)

    # Overall signal summary (majority vote)
    signal_summary = _summarize_signals(ind_signals)

    # ML multi-timeframe predictions
    predictions = predict_all_timeframes(df, sym)

    # Recent OHLCV (last 100 candles for chart)
    chart_df = df.tail(100)
    candles = []
    for ts_idx, row in chart_df.iterrows():
        try:
            # DatetimeIndex entries may be tz-aware or tz-naive
            import pandas as pd
            if isinstance(ts_idx, pd.Timestamp):
                ts = int(ts_idx.timestamp()) * 1000
            else:
                ts = int(float(ts_idx)) * 1000
        except Exception:  # noqa: BLE001
            ts = 0
        candles.append({
            "t": ts,
            "o": round(float(row["open"]), 4),
            "h": round(float(row["high"]), 4),
            "l": round(float(row["low"]), 4),
            "c": round(float(row["close"]), 4),
            "v": round(float(row["volume"]), 2),
        })

    return {
        "symbol": sym,
        "timeframe": timeframe,
        "demo_mode": demo_mode,
        "price": price_info,
        "indicators": indicators,
        "indicator_signals": {k: {"signal": v[0], "strength": round(v[1], 3)} for k, v in ind_signals.items()},
        "signal_summary": signal_summary,
        "predictions": predictions,
        "candles": candles,
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _summarize_signals(signals: dict) -> dict:
    """Compute majority buy/sell/neutral from individual indicator signals."""
    buy_count = sell_count = neutral_count = 0
    buy_strength = sell_strength = 0.0

    for _, (sig, strength) in signals.items():
        if sig == "BUY":
            buy_count += 1
            buy_strength += strength
        elif sig == "SELL":
            sell_count += 1
            sell_strength += strength
        else:
            neutral_count += 1

    total = buy_count + sell_count + neutral_count or 1
    if buy_count > sell_count and buy_count > neutral_count:
        overall = "BUY"
        score = int(50 + (buy_strength / total) * 50)
    elif sell_count > buy_count and sell_count > neutral_count:
        overall = "SELL"
        score = int(50 - (sell_strength / total) * 50)
    else:
        overall = "NEUTRAL"
        score = 50

    score = max(1, min(100, score))
    return {
        "signal": overall,
        "score": score,
        "buy_count": buy_count,
        "sell_count": sell_count,
        "neutral_count": neutral_count,
    }
