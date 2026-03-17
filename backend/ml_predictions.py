"""
ML-based multi-timeframe buy/sell predictions.

For each requested timeframe we train (or reuse) a RandomForestClassifier
on the available OHLCV + indicator features and return a buy-probability
score mapped to [1, 100].

Because model training is expensive, we cache the model per (symbol, tf) key
for the lifetime of the process.  The cache is refreshed every 5 minutes.
"""
import time
import hashlib
import logging
from typing import Optional

import numpy as np
import pandas as pd
from sklearn.ensemble import (
    GradientBoostingClassifier,
    RandomForestClassifier,
    VotingClassifier,
)
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split

import pandas_ta as ta

logger = logging.getLogger(__name__)

# Seconds between full model retrains per (symbol, timeframe) key
MODEL_TTL = 300

_model_cache: dict[str, dict] = {}


# ---------------------------------------------------------------------------
# Feature engineering
# ---------------------------------------------------------------------------

def _build_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add technical-indicator columns to *df* and return a clean feature matrix."""
    c = df["close"].copy()
    h = df["high"].copy()
    lo = df["low"].copy()
    v = df["volume"].copy()

    feats = pd.DataFrame(index=df.index)

    # Price derived
    feats["ret1"]  = c.pct_change(1)
    feats["ret3"]  = c.pct_change(3)
    feats["ret5"]  = c.pct_change(5)
    feats["ret10"] = c.pct_change(10)

    # RSI variants
    try:
        feats["rsi14"] = ta.rsi(c, 14)
        feats["rsi7"]  = ta.rsi(c, 7)
    except Exception:  # noqa: BLE001
        pass

    # MACD
    try:
        macd_df = ta.macd(c, fast=12, slow=26, signal=9)
        feats["macd"]  = macd_df["MACD_12_26_9"]
        feats["macds"] = macd_df["MACDs_12_26_9"]
        feats["macdh"] = macd_df["MACDh_12_26_9"]
    except Exception:  # noqa: BLE001
        pass

    # Bollinger bandwidth
    try:
        bb = ta.bbands(c, 20, 2)
        feats["bb_bw"]  = bb["BBB_20_2.0"]
        feats["bb_pct"] = bb["BBP_20_2.0"]
    except Exception:  # noqa: BLE001
        pass

    # Stochastic
    try:
        stoch = ta.stoch(h, lo, c, k=14, d=3, smooth_k=3)
        feats["stoch_k"] = stoch["STOCHk_14_3_3"]
        feats["stoch_d"] = stoch["STOCHd_14_3_3"]
    except Exception:  # noqa: BLE001
        pass

    # ATR (normalised by close)
    try:
        atr = ta.atr(h, lo, c, 14)
        feats["atr_norm"] = atr / c
    except Exception:  # noqa: BLE001
        pass

    # ADX
    try:
        adx_df = ta.adx(h, lo, c, 14)
        feats["adx"]  = adx_df["ADX_14"]
        feats["adx_dmp"] = adx_df["DMP_14"]
        feats["adx_dmn"] = adx_df["DMN_14"]
    except Exception:  # noqa: BLE001
        pass

    # CCI
    try:
        feats["cci"] = ta.cci(h, lo, c, 20)
    except Exception:  # noqa: BLE001
        pass

    # Williams %R
    try:
        feats["willr"] = ta.willr(h, lo, c, 14)
    except Exception:  # noqa: BLE001
        pass

    # EMA cross
    try:
        ema20 = ta.ema(c, 20)
        ema50 = ta.ema(c, 50)
        feats["ema_cross"] = (ema20 - ema50) / c
    except Exception:  # noqa: BLE001
        pass

    # Volume momentum
    feats["vol_mom"] = v.pct_change(5)

    feats = feats.replace([np.inf, -np.inf], np.nan).dropna()
    return feats


def _build_labels(df: pd.DataFrame, forward_bars: int) -> pd.Series:
    """Binary label: 1 if close price rises in *forward_bars* candles, else 0."""
    future_ret = df["close"].shift(-forward_bars) / df["close"] - 1
    return (future_ret > 0).astype(int)


def _timeframe_to_forward_bars(timeframe: str) -> int:
    """Approximate number of OHLCV bars that map to the prediction horizon."""
    # Most of our fetched data is on 1h candles for the default endpoint.
    mapping = {
        "1m":  1,
        "3m":  1,
        "5m":  1,
        "10m": 2,
        "15m": 2,
        "30m": 3,
        "1h":  5,
        "24h": 10,
    }
    return mapping.get(timeframe, 3)


def _cache_key(symbol: str, timeframe: str, n_rows: int) -> str:
    raw = f"{symbol}:{timeframe}:{n_rows // 50}"  # bucket by dataset size
    return hashlib.md5(raw.encode()).hexdigest()  # noqa: S324  (non-crypto use)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def predict_all_timeframes(
    df: pd.DataFrame,
    symbol: str,
    timeframes: Optional[list[str]] = None,
) -> dict[str, dict]:
    """
    Return buy/sell predictions for every requested timeframe.

    Each entry contains:
      - score       : int 1-100 (>50 = bullish)
      - signal      : "BUY" | "SELL" | "NEUTRAL"
      - confidence  : float 0-1
      - probability : float (raw model probability for class 1)
    """
    if timeframes is None:
        timeframes = ["1m", "3m", "5m", "10m", "15m", "30m", "1h", "24h"]

    results: dict[str, dict] = {}
    for tf in timeframes:
        results[tf] = _predict_single(df, symbol, tf)
    return results


def _predict_single(df: pd.DataFrame, symbol: str, timeframe: str) -> dict:
    """Train (or load from cache) a model and return the prediction for *timeframe*."""
    key = _cache_key(symbol, timeframe, len(df))
    now = time.time()

    entry = _model_cache.get(key)
    if entry and (now - entry["ts"]) < MODEL_TTL:
        model = entry["model"]
    else:
        model = _train_model(df, timeframe)
        if model is None:
            return _fallback_prediction(df)
        _model_cache[key] = {"model": model, "ts": now}

    try:
        feats = _build_features(df)
        if feats.empty:
            return _fallback_prediction(df)

        last_row = feats.iloc[[-1]]
        proba = model.predict_proba(last_row)[0]
        # proba[0] = P(SELL), proba[1] = P(BUY)
        buy_prob = float(proba[1])
        score = int(round(buy_prob * 100))
        score = max(1, min(100, score))

        if score >= 60:
            signal = "BUY"
        elif score <= 40:
            signal = "SELL"
        else:
            signal = "NEUTRAL"

        return {
            "score": score,
            "signal": signal,
            "confidence": round(abs(buy_prob - 0.5) * 2, 3),
            "probability": round(buy_prob, 4),
        }
    except Exception as exc:  # noqa: BLE001
        logger.warning("Prediction error for %s/%s: %s", symbol, timeframe, exc)
        return _fallback_prediction(df)


def _train_model(df: pd.DataFrame, timeframe: str) -> Optional[Pipeline]:
    """Build and fit an ensemble Pipeline on *df*."""
    try:
        feats = _build_features(df)
        forward = _timeframe_to_forward_bars(timeframe)
        labels = _build_labels(df, forward)

        # Align indices
        common = feats.index.intersection(labels.index)
        X = feats.loc[common]
        y = labels.loc[common].dropna()
        common2 = X.index.intersection(y.index)
        X = X.loc[common2]
        y = y.loc[common2]

        # Remove last *forward* rows (no label available yet)
        X = X.iloc[:-forward]
        y = y.iloc[:-forward]

        if len(X) < 40 or y.nunique() < 2:
            logger.warning("Not enough training data (rows=%d)", len(X))
            return None

        rf = RandomForestClassifier(
            n_estimators=100,
            max_depth=6,
            min_samples_leaf=5,
            random_state=42,
        )
        gb = GradientBoostingClassifier(
            n_estimators=80,
            max_depth=4,
            learning_rate=0.05,
            random_state=42,
        )
        ensemble = VotingClassifier(
            estimators=[("rf", rf), ("gb", gb)],
            voting="soft",
        )
        pipeline = Pipeline([
            ("scaler", StandardScaler()),
            ("clf", ensemble),
        ])
        pipeline.fit(X, y)
        return pipeline
    except Exception as exc:  # noqa: BLE001
        logger.warning("Training failed for timeframe=%s: %s", timeframe, exc)
        return None


def _fallback_prediction(df: pd.DataFrame) -> dict:
    """Simple rule-based fallback when the ML model cannot be used."""
    try:
        close = df["close"]
        ret5 = float(close.iloc[-1] / close.iloc[-6] - 1) if len(close) >= 6 else 0.0
        # Gentle bias toward direction of last 5-bar return
        raw = 0.5 + ret5 * 2
        buy_prob = max(0.05, min(0.95, raw))
        score = int(round(buy_prob * 100))
        score = max(1, min(100, score))
        signal = "BUY" if score >= 60 else ("SELL" if score <= 40 else "NEUTRAL")
        return {
            "score": score,
            "signal": signal,
            "confidence": round(abs(buy_prob - 0.5) * 2, 3),
            "probability": round(buy_prob, 4),
        }
    except Exception:  # noqa: BLE001
        return {"score": 50, "signal": "NEUTRAL", "confidence": 0.0, "probability": 0.5}
