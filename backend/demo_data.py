"""
Demo data generator for when external market data is unavailable.

Generates realistic synthetic OHLCV data using random-walk simulation,
and returns plausible price info for all supported assets.
"""
import numpy as np
import pandas as pd

# Approximate realistic price levels per asset
ASSET_PRICES = {
    "BTC":  85000.0,
    "ETH":  3200.0,
    "BNB":  580.0,
    "SOL":  145.0,
    "XAU":  3100.0,
    "CL":    72.0,
}

# Approximate daily volatility (σ per bar as fraction of price)
ASSET_VOLATILITY = {
    "BTC":  0.015,
    "ETH":  0.018,
    "BNB":  0.020,
    "SOL":  0.025,
    "XAU":  0.005,
    "CL":   0.012,
}


def generate_ohlcv(
    symbol: str,
    n: int = 200,
    freq: str = "1h",
) -> pd.DataFrame:
    """
    Return a synthetic OHLCV DataFrame for *symbol* with *n* bars.

    The data exhibits realistic patterns:
      - Random walk for the close price
      - Intraday high/low spread proportional to volatility
      - Volume with some autocorrelation
    """
    rng = np.random.default_rng(sum(ord(c) for c in symbol))  # deterministic per symbol

    base_price = ASSET_PRICES.get(symbol.upper(), 100.0)
    vol        = ASSET_VOLATILITY.get(symbol.upper(), 0.015)

    # Random walk with mild mean reversion
    returns = rng.normal(0.0001, vol, n)
    close   = base_price * np.cumprod(1 + returns)

    spread  = close * vol * rng.uniform(0.5, 1.5, n)
    high    = close + spread * rng.uniform(0.3, 0.9, n)
    low     = close - spread * rng.uniform(0.3, 0.9, n)
    open_   = low + (high - low) * rng.uniform(0, 1, n)
    volume  = rng.lognormal(mean=15, sigma=0.5, size=n)

    idx = pd.date_range(end=pd.Timestamp.now("UTC"), periods=n, freq=freq)
    return pd.DataFrame(
        {"open": open_, "high": high, "low": low, "close": close, "volume": volume},
        index=idx,
    )


def generate_price_info(symbol: str) -> dict:
    """Return a synthetic price-info dict for *symbol*."""
    rng = np.random.default_rng(sum(ord(c) for c in symbol) + 1)
    base   = ASSET_PRICES.get(symbol.upper(), 100.0)
    change = float(rng.normal(0, 1.5))
    price  = round(base * (1 + change / 100), 4)
    prev   = round(price / (1 + change / 100), 4)

    from data_fetcher import ASSET_MAP
    ticker = ASSET_MAP.get(symbol.upper(), symbol)

    return {
        "symbol":     symbol.upper(),
        "ticker":     ticker,
        "price":      price,
        "prev_close": prev,
        "change_pct": round(change, 2),
        "demo":       True,
    }
