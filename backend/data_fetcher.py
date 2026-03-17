"""
Market data fetcher using yfinance.
Supports crypto (BTC, ETH, BNB), Gold (XAU) and Oil (CL).
"""
import yfinance as yf
import pandas as pd
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# Map our asset symbols to Yahoo Finance tickers
ASSET_MAP = {
    "BTC": "BTC-USD",
    "ETH": "ETH-USD",
    "BNB": "BNB-USD",
    "SOL": "SOL-USD",
    "XAU": "GC=F",   # Gold futures
    "CL":  "CL=F",   # WTI Crude Oil futures
}

# Map our timeframe labels to yfinance interval / period combos
TIMEFRAME_CONFIG = {
    "1m":  {"interval": "1m",  "period": "1d"},
    "3m":  {"interval": "5m",  "period": "5d"},   # 3 m not supported, use 5m proxy
    "5m":  {"interval": "5m",  "period": "5d"},
    "10m": {"interval": "15m", "period": "5d"},   # 10 m not supported, use 15m proxy
    "15m": {"interval": "15m", "period": "30d"},
    "30m": {"interval": "30m", "period": "30d"},
    "1h":  {"interval": "1h",  "period": "60d"},
    "24h": {"interval": "1d",  "period": "180d"},
}

# Minimum rows needed to calculate indicators reliably
MIN_ROWS = 60


def get_ticker(symbol: str) -> str:
    """Return Yahoo Finance ticker for the given asset symbol."""
    return ASSET_MAP.get(symbol.upper(), symbol)


def fetch_ohlcv(symbol: str, timeframe: str = "1h") -> Optional[pd.DataFrame]:
    """
    Fetch OHLCV data for *symbol* at the given *timeframe*.

    Returns a DataFrame with columns [open, high, low, close, volume]
    indexed by datetime, or None on failure.
    """
    ticker = get_ticker(symbol)
    cfg = TIMEFRAME_CONFIG.get(timeframe, TIMEFRAME_CONFIG["1h"])
    try:
        df = yf.download(
            ticker,
            interval=cfg["interval"],
            period=cfg["period"],
            progress=False,
            auto_adjust=True,
        )
        if df is None or df.empty:
            logger.warning("No data returned for %s (%s)", symbol, timeframe)
            return None

        # Flatten multi-level columns that yfinance sometimes returns
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        df.columns = [c.lower() for c in df.columns]
        df = df[["open", "high", "low", "close", "volume"]].dropna()

        if len(df) < MIN_ROWS:
            logger.warning(
                "Insufficient rows (%d) for %s / %s", len(df), symbol, timeframe
            )
            return None

        return df
    except Exception as exc:  # noqa: BLE001
        logger.exception("Error fetching %s / %s: %s", symbol, timeframe, exc)
        return None


def get_current_price(symbol: str) -> Optional[dict]:
    """Return latest price info (price, change_pct, volume) for *symbol*."""
    ticker = get_ticker(symbol)
    try:
        t = yf.Ticker(ticker)
        info = t.fast_info
        price = float(info.last_price) if info.last_price else None
        prev  = float(info.previous_close) if info.previous_close else None
        change_pct = ((price - prev) / prev * 100) if price and prev else 0.0
        return {
            "symbol": symbol,
            "ticker": ticker,
            "price": round(price, 4) if price else None,
            "prev_close": round(prev, 4) if prev else None,
            "change_pct": round(change_pct, 2),
        }
    except Exception as exc:  # noqa: BLE001
        logger.exception("Error getting price for %s: %s", symbol, exc)
        return None
