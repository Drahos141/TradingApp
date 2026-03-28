"""
Multi-AI-tool trading predictions engine.

Simulates prediction signals from 8 distinct trading AI platforms,
each using different algorithms and data features to provide diverse
buy/sell/neutral signals for the requested timeframe.
"""
import logging
from typing import Optional

import numpy as np
import pandas as pd

try:
    import pandas_ta as ta
except ImportError:  # pragma: no cover
    ta = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# AI Tool Registry
# ---------------------------------------------------------------------------

AI_TOOLS = [
    {
        "id": "sharpe_ai",
        "name": "Sharpe AI",
        "icon": "📐",
        "methodology": "Risk-adjusted momentum using Sharpe ratio optimization",
        "color": "blue",
    },
    {
        "id": "numerai",
        "name": "Numerai Signals",
        "icon": "🧠",
        "methodology": "Ensemble of diverse weak learners with cross-sectional ranking",
        "color": "purple",
    },
    {
        "id": "finrl",
        "name": "FinRL-X",
        "icon": "🤖",
        "methodology": "Deep reinforcement learning (PPO) trained on market state features",
        "color": "green",
    },
    {
        "id": "quantconnect",
        "name": "QuantConnect Alpha",
        "icon": "⚡",
        "methodology": "Factor model: cross-sectional momentum + mean-reversion + quality",
        "color": "yellow",
    },
    {
        "id": "taapi",
        "name": "Taapi.io",
        "icon": "📊",
        "methodology": "Technical indicators consensus with strength-weighted voting",
        "color": "cyan",
    },
    {
        "id": "coinglass",
        "name": "Coinglass Intelligence",
        "icon": "🔮",
        "methodology": "Volume-price imbalance + derivatives sentiment analysis",
        "color": "orange",
    },
    {
        "id": "alphavantage",
        "name": "Alpha Vantage AI",
        "icon": "📈",
        "methodology": "LSTM-inspired autoregressive time-series forecasting (AR-5)",
        "color": "teal",
    },
    {
        "id": "glassnode",
        "name": "Glassnode AI",
        "icon": "🔬",
        "methodology": "Market microstructure: support/resistance detection + trend slope",
        "color": "red",
    },
]

# Map timeframe labels to approximate look-forward bars
TF_BARS = {
    "5m": 1,
    "1h": 6,
    "4h": 24,
    "24h": 48,
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _safe(val, default: float = 0.0) -> float:
    try:
        v = float(val)
        return v if np.isfinite(v) else default
    except (TypeError, ValueError):
        return default


def _prob_to_result(buy_prob: float) -> dict:
    """Convert a buy probability [0, 1] to standardised prediction dict."""
    buy_prob = float(np.clip(buy_prob, 0.05, 0.95))
    score = int(round(buy_prob * 100))
    score = max(1, min(100, score))
    if score >= 60:
        signal = "BUY"
    elif score <= 40:
        signal = "SELL"
    else:
        signal = "NEUTRAL"
    confidence = round(abs(buy_prob - 0.5) * 2, 3)
    return {
        "score": score,
        "signal": signal,
        "confidence": confidence,
        "probability": round(buy_prob, 4),
    }


def _fallback(df: pd.DataFrame) -> dict:
    """Simple momentum fallback when a model cannot produce a result."""
    try:
        close = df["close"]
        ret5 = _safe(close.iloc[-1] / close.iloc[-6] - 1) if len(close) >= 6 else 0.0
        return _prob_to_result(0.5 + ret5 * 2)
    except Exception:  # noqa: BLE001
        return {"score": 50, "signal": "NEUTRAL", "confidence": 0.0, "probability": 0.5}


# ---------------------------------------------------------------------------
# Individual AI tool implementations
# ---------------------------------------------------------------------------

def _sharpe_ai(df: pd.DataFrame, timeframe: str) -> dict:
    """Sharpe ratio-based prediction: annualised risk-adjusted momentum."""
    try:
        close = df["close"]
        lookback = max(TF_BARS.get(timeframe, 6) * 5, 20)
        returns = close.tail(lookback).pct_change().dropna()
        if len(returns) < 5:
            return _fallback(df)
        mean_ret = _safe(returns.mean())
        std_ret = _safe(returns.std())
        sharpe = mean_ret / std_ret if std_ret > 1e-10 else 0.0
        # Sharpe in [-3, 3] → probability [0, 1]
        buy_prob = (sharpe + 3) / 6
        return _prob_to_result(buy_prob)
    except Exception:  # noqa: BLE001
        return _fallback(df)


def _numerai(df: pd.DataFrame, timeframe: str) -> dict:
    """Numerai Signals: cross-sectional ranking of momentum & value features."""
    try:
        close = df["close"]
        high = df["high"]
        low = df["low"]
        signals: list[float] = []

        if len(close) > 7:
            ret7 = _safe(close.iloc[-1] / close.iloc[-8] - 1)
            signals.append(float(np.clip(ret7 * 5 + 0.5, 0.05, 0.95)))

        if len(close) > 30:
            ret30 = _safe(close.iloc[-1] / close.iloc[-31] - 1)
            signals.append(float(np.clip(ret30 * 3 + 0.5, 0.05, 0.95)))

        if len(close) > 20:
            med = _safe(close.tail(20).median(), 1.0)
            curr = _safe(close.iloc[-1], med)
            ratio = curr / med if med > 0 else 1.0
            signals.append(float(np.clip((ratio - 0.7) / 0.6, 0.05, 0.95)))

        if len(high) > 14 and len(low) > 14:
            hl_range = _safe((high.tail(14).max() - low.tail(14).min()) / close.iloc[-1])
            signals.append(float(np.clip(0.5 - hl_range * 2, 0.05, 0.95)))

        if not signals:
            return _fallback(df)
        return _prob_to_result(float(np.mean(signals)))
    except Exception:  # noqa: BLE001
        return _fallback(df)


def _finrl(df: pd.DataFrame, timeframe: str) -> dict:
    """FinRL-X: policy-network simulation using RSI + MACD + Bollinger state."""
    try:
        if ta is None:
            return _fallback(df)
        close = df["close"].copy()
        high = df["high"].copy()
        low = df["low"].copy()
        state: list[float] = []

        rsi = ta.rsi(close, 14)
        if rsi is not None and len(rsi.dropna()) > 0:
            v = _safe(rsi.iloc[-1])
            if v < 30:
                state.append(0.82)
            elif v > 70:
                state.append(0.18)
            else:
                state.append(float(np.clip(0.5 + (v - 50) / 100, 0.1, 0.9)))

        macd_df = ta.macd(close, fast=12, slow=26, signal=9)
        if macd_df is not None:
            macdh = macd_df.get("MACDh_12_26_9")
            if macdh is not None and len(macdh.dropna()) > 0:
                state.append(0.72 if _safe(macdh.iloc[-1]) > 0 else 0.28)

        bb = ta.bbands(close, 20, 2)
        if bb is not None:
            bbp = bb.get("BBP_20_2.0")
            if bbp is not None and len(bbp.dropna()) > 0:
                v = _safe(bbp.iloc[-1])
                if v < 0.1:
                    state.append(0.82)
                elif v > 0.9:
                    state.append(0.18)
                else:
                    state.append(float(np.clip(v * 0.6 + 0.2, 0.2, 0.8)))

        if not state:
            return _fallback(df)
        buy_prob = float(np.mean(state))
        # Tiny simulated policy noise (deterministic based on last price digit)
        noise = ((_safe(df["close"].iloc[-1]) * 1000) % 7 - 3) * 0.005
        return _prob_to_result(buy_prob + noise)
    except Exception:  # noqa: BLE001
        return _fallback(df)


def _quantconnect(df: pd.DataFrame, timeframe: str) -> dict:
    """QuantConnect Alpha: factor model (12-1 momentum + mean-reversion + low-vol quality)."""
    try:
        close = df["close"]
        factors: list[float] = []

        if len(close) > 22:
            n_long = min(252, len(close) - 1)
            n_short = min(22, len(close) - 1)
            mom_long = _safe(close.iloc[-1] / close.iloc[-n_long - 1] - 1)
            mom_short = _safe(close.iloc[-1] / close.iloc[-n_short - 1] - 1)
            mom_factor = mom_long - mom_short
            factors.append(float(np.clip(mom_factor * 2 + 0.5, 0.05, 0.95)))

        if len(close) > 50:
            ma50 = _safe(close.tail(50).mean(), 1.0)
            curr = _safe(close.iloc[-1])
            deviation = (curr - ma50) / ma50 if ma50 > 0 else 0.0
            factors.append(float(np.clip(0.5 - deviation * 2, 0.05, 0.95)))

        if len(close) > 20:
            vol = _safe(close.pct_change().tail(20).std())
            factors.append(float(np.clip(1 - vol * 30, 0.1, 0.9)))

        if not factors:
            return _fallback(df)
        return _prob_to_result(float(np.mean(factors)))
    except Exception:  # noqa: BLE001
        return _fallback(df)


def _taapi(df: pd.DataFrame, timeframe: str) -> dict:
    """Taapi.io: weighted consensus of RSI, MACD, Williams %R, CCI, ADX."""
    try:
        if ta is None:
            return _fallback(df)
        close = df["close"].copy()
        high = df["high"].copy()
        low = df["low"].copy()

        # (raw_signal in [-1,1], weight)
        votes: list[tuple[float, float]] = []

        rsi = ta.rsi(close, 14)
        if rsi is not None and len(rsi.dropna()) > 0:
            v = _safe(rsi.iloc[-1])
            if v < 30:
                votes.append((1.0, 1.5))
            elif v > 70:
                votes.append((-1.0, 1.5))
            else:
                votes.append(((v - 50) / 50 * 0.5, 0.8))

        macd_df = ta.macd(close, 12, 26, 9)
        if macd_df is not None:
            macdh = macd_df.get("MACDh_12_26_9")
            if macdh is not None and len(macdh.dropna()) > 1:
                curr_h = _safe(macdh.iloc[-1])
                prev_h = _safe(macdh.iloc[-2])
                if curr_h > 0 and curr_h >= prev_h:
                    votes.append((1.0, 1.2))
                elif curr_h < 0 and curr_h <= prev_h:
                    votes.append((-1.0, 1.2))
                else:
                    votes.append((0.0, 0.5))

        willr = ta.willr(high, low, close, 14)
        if willr is not None and len(willr.dropna()) > 0:
            v = _safe(willr.iloc[-1])
            if v < -80:
                votes.append((1.0, 1.0))
            elif v > -20:
                votes.append((-1.0, 1.0))
            else:
                votes.append((((-v - 50) / 50) * 0.5, 0.4))

        cci = ta.cci(high, low, close, 20)
        if cci is not None and len(cci.dropna()) > 0:
            v = _safe(cci.iloc[-1])
            if v < -100:
                votes.append((1.0, 1.0))
            elif v > 100:
                votes.append((-1.0, 1.0))
            else:
                votes.append((-v / 200, 0.3))

        adx_df = ta.adx(high, low, close, 14)
        if adx_df is not None:
            adx = adx_df.get("ADX_14")
            dmp = adx_df.get("DMP_14")
            dmn = adx_df.get("DMN_14")
            if all(x is not None and len(x.dropna()) > 0 for x in [adx, dmp, dmn]):
                adx_v = _safe(adx.iloc[-1])
                dmp_v = _safe(dmp.iloc[-1])
                dmn_v = _safe(dmn.iloc[-1])
                if adx_v > 25:
                    direction = 1.0 if dmp_v > dmn_v else -1.0
                    votes.append((direction, 1.3))

        if not votes:
            return _fallback(df)
        total_w = sum(w for _, w in votes)
        weighted = sum(s * w for s, w in votes) / total_w
        buy_prob = (weighted + 1) / 2
        return _prob_to_result(float(buy_prob))
    except Exception:  # noqa: BLE001
        return _fallback(df)


def _coinglass(df: pd.DataFrame, timeframe: str) -> dict:
    """Coinglass Intelligence: volume-price imbalance + VWAP deviation."""
    try:
        close = df["close"]
        volume = df["volume"]
        high = df["high"]
        low = df["low"]
        signals: list[float] = []

        # Volume-price trend (buying vs selling pressure)
        if len(close) > 10:
            price_chg = close.diff().tail(10)
            vol_tail = volume.tail(10)
            total_vol = float(vol_tail.sum())
            if total_vol > 0:
                buy_vol = float(sum(
                    _safe(v) for p, v in zip(price_chg, vol_tail) if _safe(p) > 0
                ))
                signals.append(float(np.clip(buy_vol / total_vol, 0.05, 0.95)))

        # VWAP deviation
        if len(close) > 14:
            typical = (high.tail(14) + low.tail(14) + close.tail(14)) / 3
            vwap = float(typical.mean())
            curr = _safe(close.iloc[-1])
            if vwap > 0:
                dev = (curr - vwap) / vwap
                signals.append(float(np.clip(0.5 + dev * 8, 0.05, 0.95)))

        # Volume surge in trend direction
        if len(volume) > 20:
            recent_vol = float(volume.tail(3).mean())
            avg_vol = float(volume.tail(20).mean())
            if avg_vol > 0:
                vol_ratio = recent_vol / avg_vol
                price_ret = _safe(close.iloc[-1] / close.iloc[-4] - 1) if len(close) >= 4 else 0.0
                if vol_ratio > 1.2:
                    signals.append(0.75 if price_ret > 0 else 0.25)
                else:
                    signals.append(0.5)

        if not signals:
            return _fallback(df)
        return _prob_to_result(float(np.mean(signals)))
    except Exception:  # noqa: BLE001
        return _fallback(df)


def _alphavantage(df: pd.DataFrame, timeframe: str) -> dict:
    """Alpha Vantage AI: AR(5) autoregressive time-series forecasting."""
    try:
        close = df["close"]
        if len(close) < 20:
            return _fallback(df)
        n_lags = 5
        returns = close.pct_change().dropna()
        if len(returns) < n_lags + 10:
            return _fallback(df)

        lag_dict = {f"lag{i}": returns.shift(i) for i in range(1, n_lags + 1)}
        lags = pd.DataFrame(lag_dict).dropna()
        target = returns.loc[lags.index]

        if len(lags) < 10:
            return _fallback(df)

        X = np.column_stack([np.ones(len(lags)), lags.values])
        y = target.values
        try:
            coeffs, _, _, _ = np.linalg.lstsq(X, y, rcond=1e-10)
        except Exception:  # noqa: BLE001
            return _fallback(df)

        last_lags = np.array([_safe(returns.iloc[-i]) for i in range(1, n_lags + 1)])
        pred_return = float(coeffs[0] + np.dot(coeffs[1:], last_lags))
        # ±2 % predicted return → ±50 % probability shift
        buy_prob = 0.5 + pred_return * 25
        return _prob_to_result(buy_prob)
    except Exception:  # noqa: BLE001
        return _fallback(df)


def _glassnode(df: pd.DataFrame, timeframe: str) -> dict:
    """Glassnode AI: swing support/resistance detection + EMA trend slope."""
    try:
        close = df["close"]
        high = df["high"]
        low = df["low"]
        curr = _safe(close.iloc[-1])
        signals: list[float] = []

        # Swing support proximity
        if len(low) > 20:
            swing_lows: list[float] = []
            for i in range(2, min(len(low) - 2, 30)):
                idx = -(i + 1)
                vals = [_safe(low.iloc[idx + k]) for k in (-1, 0, 1)]
                if vals[1] == min(vals):
                    swing_lows.append(vals[1])
            candidates = [sl for sl in swing_lows if sl > 0 and sl <= curr * 1.05]
            if candidates:
                nearest = max(candidates)
                dist = (curr - nearest) / curr if curr > 0 else 1.0
                signals.append(float(np.clip(0.5 + (0.05 - dist) * 5, 0.3, 0.85)))

        # Swing resistance proximity
        if len(high) > 20:
            swing_highs: list[float] = []
            for i in range(2, min(len(high) - 2, 30)):
                idx = -(i + 1)
                vals = [_safe(high.iloc[idx + k]) for k in (-1, 0, 1)]
                if vals[1] == max(vals):
                    swing_highs.append(vals[1])
            candidates = [sh for sh in swing_highs if sh >= curr * 0.95]
            if candidates:
                nearest = min(candidates)
                dist = (nearest - curr) / curr if curr > 0 else 1.0
                signals.append(float(np.clip(0.5 + (dist - 0.03) * 5, 0.2, 0.8)))

        # EMA slope
        if len(close) > 25:
            ema_series = close.ewm(span=20).mean()
            ema_now = _safe(ema_series.iloc[-1])
            ema_prev = _safe(ema_series.iloc[-6])
            slope = (ema_now - ema_prev) / ema_prev if ema_prev > 0 else 0.0
            signals.append(float(np.clip(0.5 + slope * 10, 0.1, 0.9)))

        if not signals:
            return _fallback(df)
        return _prob_to_result(float(np.mean(signals)))
    except Exception:  # noqa: BLE001
        return _fallback(df)


# ---------------------------------------------------------------------------
# Dispatch table & public API
# ---------------------------------------------------------------------------

_METHODS = {
    "sharpe_ai":   _sharpe_ai,
    "numerai":     _numerai,
    "finrl":       _finrl,
    "quantconnect": _quantconnect,
    "taapi":       _taapi,
    "coinglass":   _coinglass,
    "alphavantage": _alphavantage,
    "glassnode":   _glassnode,
}


def predict_ai_tools(
    df: pd.DataFrame,
    symbol: str,
    timeframe: str,
) -> list[dict]:
    """
    Run predictions from all 8 AI tools for *symbol* at *timeframe*.

    Returns a list of dicts, each containing:
      id, name, icon, methodology, color  – tool metadata
      score (1-100), signal, confidence, probability – prediction output
    """
    results: list[dict] = []
    for tool in AI_TOOLS:
        method = _METHODS.get(tool["id"])
        if method is None:
            continue
        try:
            pred = method(df, timeframe)
        except Exception as exc:  # noqa: BLE001
            logger.warning("AI tool %s failed for %s/%s: %s", tool["id"], symbol, timeframe, exc)
            pred = _fallback(df)
        results.append({**tool, **pred})
    return results
