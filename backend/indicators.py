"""
Technical indicators calculated with pandas-ta.

Provides a single `calculate_indicators(df)` function that returns a
dictionary of 10+ indicator values derived from the OHLCV DataFrame.
"""
import numpy as np
import pandas as pd
import pandas_ta as ta
import logging

logger = logging.getLogger(__name__)


def _safe(val):
    """Convert numpy scalar / NaN to a plain Python float or None."""
    if val is None:
        return None
    if isinstance(val, (pd.Series, np.ndarray)):
        val = val.iloc[-1] if isinstance(val, pd.Series) else val[-1]
    try:
        v = float(val)
        return None if np.isnan(v) or np.isinf(v) else round(v, 6)
    except (TypeError, ValueError):
        return None


def calculate_indicators(df: pd.DataFrame) -> dict:
    """
    Calculate 12 technical indicators from a OHLCV DataFrame.

    Returns a dict whose values are plain Python floats (or None if the
    calculation failed due to insufficient data).
    """
    close  = df["close"]
    high   = df["high"]
    low    = df["low"]
    volume = df["volume"]
    result = {}

    # ------------------------------------------------------------------
    # 1. RSI (14)
    # ------------------------------------------------------------------
    try:
        rsi = ta.rsi(close, length=14)
        result["rsi"] = {"value": _safe(rsi.iloc[-1]), "name": "RSI (14)", "type": "oscillator"}
    except Exception:  # noqa: BLE001
        result["rsi"] = {"value": None, "name": "RSI (14)", "type": "oscillator"}

    # ------------------------------------------------------------------
    # 2. MACD (12, 26, 9)
    # ------------------------------------------------------------------
    try:
        macd_df = ta.macd(close, fast=12, slow=26, signal=9)
        macd_val  = _safe(macd_df["MACD_12_26_9"].iloc[-1])
        macd_sig  = _safe(macd_df["MACDs_12_26_9"].iloc[-1])
        macd_hist = _safe(macd_df["MACDh_12_26_9"].iloc[-1])
        result["macd"] = {
            "value": macd_val,
            "signal": macd_sig,
            "histogram": macd_hist,
            "name": "MACD (12,26,9)",
            "type": "trend",
        }
    except Exception:  # noqa: BLE001
        result["macd"] = {"value": None, "signal": None, "histogram": None,
                          "name": "MACD (12,26,9)", "type": "trend"}

    # ------------------------------------------------------------------
    # 3. Bollinger Bands (20, 2)
    # ------------------------------------------------------------------
    try:
        bb = ta.bbands(close, length=20, std=2)
        result["bbands"] = {
            "upper": _safe(bb["BBU_20_2.0"].iloc[-1]),
            "middle": _safe(bb["BBM_20_2.0"].iloc[-1]),
            "lower": _safe(bb["BBL_20_2.0"].iloc[-1]),
            "bandwidth": _safe(bb["BBB_20_2.0"].iloc[-1]),
            "name": "Bollinger Bands (20,2)",
            "type": "volatility",
        }
    except Exception:  # noqa: BLE001
        result["bbands"] = {"upper": None, "middle": None, "lower": None,
                            "bandwidth": None, "name": "Bollinger Bands (20,2)", "type": "volatility"}

    # ------------------------------------------------------------------
    # 4. EMA 20 & 50
    # ------------------------------------------------------------------
    try:
        ema20 = ta.ema(close, length=20)
        ema50 = ta.ema(close, length=50)
        result["ema"] = {
            "ema20": _safe(ema20.iloc[-1]),
            "ema50": _safe(ema50.iloc[-1]),
            "name": "EMA (20 / 50)",
            "type": "trend",
        }
    except Exception:  # noqa: BLE001
        result["ema"] = {"ema20": None, "ema50": None, "name": "EMA (20/50)", "type": "trend"}

    # ------------------------------------------------------------------
    # 5. SMA 20 & 50
    # ------------------------------------------------------------------
    try:
        sma20 = ta.sma(close, length=20)
        sma50 = ta.sma(close, length=50)
        result["sma"] = {
            "sma20": _safe(sma20.iloc[-1]),
            "sma50": _safe(sma50.iloc[-1]),
            "name": "SMA (20 / 50)",
            "type": "trend",
        }
    except Exception:  # noqa: BLE001
        result["sma"] = {"sma20": None, "sma50": None, "name": "SMA (20/50)", "type": "trend"}

    # ------------------------------------------------------------------
    # 6. Stochastic Oscillator (14, 3, 3)
    # ------------------------------------------------------------------
    try:
        stoch = ta.stoch(high, low, close, k=14, d=3, smooth_k=3)
        result["stoch"] = {
            "k": _safe(stoch["STOCHk_14_3_3"].iloc[-1]),
            "d": _safe(stoch["STOCHd_14_3_3"].iloc[-1]),
            "name": "Stochastic (14,3,3)",
            "type": "oscillator",
        }
    except Exception:  # noqa: BLE001
        result["stoch"] = {"k": None, "d": None,
                           "name": "Stochastic (14,3,3)", "type": "oscillator"}

    # ------------------------------------------------------------------
    # 7. ATR (14)
    # ------------------------------------------------------------------
    try:
        atr = ta.atr(high, low, close, length=14)
        result["atr"] = {"value": _safe(atr.iloc[-1]), "name": "ATR (14)", "type": "volatility"}
    except Exception:  # noqa: BLE001
        result["atr"] = {"value": None, "name": "ATR (14)", "type": "volatility"}

    # ------------------------------------------------------------------
    # 8. ADX (14)
    # ------------------------------------------------------------------
    try:
        adx_df = ta.adx(high, low, close, length=14)
        result["adx"] = {
            "adx": _safe(adx_df["ADX_14"].iloc[-1]),
            "dmp": _safe(adx_df["DMP_14"].iloc[-1]),
            "dmn": _safe(adx_df["DMN_14"].iloc[-1]),
            "name": "ADX (14)",
            "type": "trend",
        }
    except Exception:  # noqa: BLE001
        result["adx"] = {"adx": None, "dmp": None, "dmn": None,
                         "name": "ADX (14)", "type": "trend"}

    # ------------------------------------------------------------------
    # 9. CCI (20) – manual implementation (pandas-ta v0.4.x changed formula)
    # ------------------------------------------------------------------
    try:
        cci_val = _cci_manual(high, low, close, length=20)
        result["cci"] = {"value": cci_val, "name": "CCI (20)", "type": "oscillator"}
    except Exception:  # noqa: BLE001
        result["cci"] = {"value": None, "name": "CCI (20)", "type": "oscillator"}

    # ------------------------------------------------------------------
    # 10. Williams %R (14)
    # ------------------------------------------------------------------
    try:
        willr = ta.willr(high, low, close, length=14)
        result["willr"] = {"value": _safe(willr.iloc[-1]), "name": "Williams %R (14)", "type": "oscillator"}
    except Exception:  # noqa: BLE001
        result["willr"] = {"value": None, "name": "Williams %R (14)", "type": "oscillator"}

    # ------------------------------------------------------------------
    # 11. VWAP (when volume is available)
    # ------------------------------------------------------------------
    try:
        # pandas-ta vwap needs an index with proper datetime info
        vwap_val = _vwap_manual(df)
        result["vwap"] = {"value": vwap_val, "name": "VWAP", "type": "volume"}
    except Exception:  # noqa: BLE001
        result["vwap"] = {"value": None, "name": "VWAP", "type": "volume"}

    # ------------------------------------------------------------------
    # 12. OBV (On Balance Volume)
    # ------------------------------------------------------------------
    try:
        obv = ta.obv(close, volume)
        result["obv"] = {"value": _safe(obv.iloc[-1]), "name": "OBV", "type": "volume"}
    except Exception:  # noqa: BLE001
        result["obv"] = {"value": None, "name": "OBV", "type": "volume"}

    return result


def _vwap_manual(df: pd.DataFrame) -> float | None:
    """Rolling VWAP over the last 20 bars (simple approximation)."""
    try:
        window = df.tail(20).copy()
        typical = (window["high"] + window["low"] + window["close"]) / 3
        vwap = (typical * window["volume"]).sum() / window["volume"].sum()
        return _safe(vwap)
    except Exception:  # noqa: BLE001
        return None


def _cci_manual(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    length: int = 20,
) -> float | None:
    """
    Commodity Channel Index using the standard Lambert formula:
      CCI = (TP - SMA(TP, n)) / (0.015 * MAD(TP, n))
    Always returns a value in a normalised range regardless of price scale.
    """
    try:
        tp = (high + low + close) / 3
        sma = tp.rolling(length).mean()
        mad = tp.rolling(length).apply(lambda x: np.abs(x - x.mean()).mean(), raw=True)
        cci = (tp - sma) / (0.015 * mad)
        return _safe(cci.iloc[-1])
    except Exception:  # noqa: BLE001
        return None


def indicator_signals(indicators: dict, current_price: float) -> dict:
    """
    Derive simple BUY / SELL / NEUTRAL signals from indicator values.

    Returns a dict mapping indicator key → signal str and strength 0-1.
    """
    signals = {}

    # RSI
    rsi = (indicators.get("rsi") or {}).get("value")
    if rsi is not None:
        if rsi < 30:
            signals["rsi"] = ("BUY", (30 - rsi) / 30)
        elif rsi > 70:
            signals["rsi"] = ("SELL", (rsi - 70) / 30)
        else:
            signals["rsi"] = ("NEUTRAL", 0.5)

    # MACD histogram
    hist = (indicators.get("macd") or {}).get("histogram")
    if hist is not None:
        signals["macd"] = ("BUY", 0.7) if hist > 0 else ("SELL", 0.7)

    # Stochastic
    k = (indicators.get("stoch") or {}).get("k")
    if k is not None:
        if k < 20:
            signals["stoch"] = ("BUY", (20 - k) / 20)
        elif k > 80:
            signals["stoch"] = ("SELL", (k - 80) / 20)
        else:
            signals["stoch"] = ("NEUTRAL", 0.5)

    # EMA trend
    ema20 = (indicators.get("ema") or {}).get("ema20")
    ema50 = (indicators.get("ema") or {}).get("ema50")
    if ema20 and ema50:
        if ema20 > ema50:
            signals["ema"] = ("BUY", min((ema20 - ema50) / ema50 * 100, 1.0))
        else:
            signals["ema"] = ("SELL", min((ema50 - ema20) / ema50 * 100, 1.0))

    # Bollinger Bands position
    bb_upper = (indicators.get("bbands") or {}).get("upper")
    bb_lower = (indicators.get("bbands") or {}).get("lower")
    if bb_upper and bb_lower and current_price:
        bb_range = bb_upper - bb_lower
        if bb_range > 0:
            pos = (current_price - bb_lower) / bb_range
            if pos < 0.2:
                signals["bbands"] = ("BUY", (0.2 - pos) / 0.2)
            elif pos > 0.8:
                signals["bbands"] = ("SELL", (pos - 0.8) / 0.2)
            else:
                signals["bbands"] = ("NEUTRAL", 0.5)

    # ADX trend strength
    adx = (indicators.get("adx") or {}).get("adx")
    dmp = (indicators.get("adx") or {}).get("dmp")
    dmn = (indicators.get("adx") or {}).get("dmn")
    if adx and dmp and dmn and adx > 25:
        if dmp > dmn:
            signals["adx"] = ("BUY", min(adx / 100, 1.0))
        else:
            signals["adx"] = ("SELL", min(adx / 100, 1.0))

    # CCI
    cci = (indicators.get("cci") or {}).get("value")
    if cci is not None:
        if cci < -100:
            signals["cci"] = ("BUY", min((-100 - cci) / 100, 1.0))
        elif cci > 100:
            signals["cci"] = ("SELL", min((cci - 100) / 100, 1.0))
        else:
            signals["cci"] = ("NEUTRAL", 0.5)

    # Williams %R
    willr = (indicators.get("willr") or {}).get("value")
    if willr is not None:
        if willr < -80:
            signals["willr"] = ("BUY", (-80 - willr) / 20)
        elif willr > -20:
            signals["willr"] = ("SELL", (-20 - willr) / -20)
        else:
            signals["willr"] = ("NEUTRAL", 0.5)

    return signals
