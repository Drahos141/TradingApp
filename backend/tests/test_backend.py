"""
Unit tests for the TradingApp backend.
Run with: pytest backend/tests/
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import pandas as pd
import pytest

from indicators import calculate_indicators, indicator_signals
from ml_predictions import (
    _build_features,
    _build_labels,
    _fallback_prediction,
    predict_all_timeframes,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_df(n: int = 120) -> pd.DataFrame:
    """Create a synthetic OHLCV DataFrame for testing."""
    rng = np.random.default_rng(42)
    close = 100.0 + np.cumsum(rng.normal(0, 1, n))
    high   = close + rng.uniform(0.1, 2.0, n)
    low    = close - rng.uniform(0.1, 2.0, n)
    open_  = close + rng.normal(0, 0.5, n)
    volume = rng.uniform(1e6, 1e7, n)

    idx = pd.date_range("2024-01-01", periods=n, freq="1h")
    return pd.DataFrame(
        {"open": open_, "high": high, "low": low, "close": close, "volume": volume},
        index=idx,
    )


# ---------------------------------------------------------------------------
# Indicator tests
# ---------------------------------------------------------------------------

class TestIndicators:
    def test_returns_all_keys(self):
        df = _make_df()
        result = calculate_indicators(df)
        expected_keys = {"rsi", "macd", "bbands", "ema", "sma", "stoch",
                         "atr", "adx", "cci", "willr", "vwap", "obv"}
        assert expected_keys.issubset(result.keys())

    def test_rsi_in_valid_range(self):
        df = _make_df()
        result = calculate_indicators(df)
        rsi = result["rsi"]["value"]
        if rsi is not None:
            assert 0 <= rsi <= 100, f"RSI out of range: {rsi}"

    def test_stoch_in_valid_range(self):
        df = _make_df()
        result = calculate_indicators(df)
        k = result["stoch"]["k"]
        if k is not None:
            assert 0 <= k <= 100

    def test_ema_values_close_to_price(self):
        df = _make_df()
        result = calculate_indicators(df)
        ema20 = result["ema"]["ema20"]
        current_price = float(df["close"].iloc[-1])
        if ema20 is not None:
            # EMA should be in the same ballpark as price (within 50%)
            assert abs(ema20 - current_price) / current_price < 0.5

    def test_macd_has_histogram(self):
        df = _make_df()
        result = calculate_indicators(df)
        assert "histogram" in result["macd"]

    def test_indicator_signals_returns_dict(self):
        df = _make_df()
        indicators = calculate_indicators(df)
        signals = indicator_signals(indicators, float(df["close"].iloc[-1]))
        assert isinstance(signals, dict)
        for key, (sig, strength) in signals.items():
            assert sig in ("BUY", "SELL", "NEUTRAL")
            assert 0.0 <= strength <= 1.5  # allow slightly above 1 for edge cases


# ---------------------------------------------------------------------------
# ML prediction tests
# ---------------------------------------------------------------------------

class TestMLPredictions:
    def test_build_features_returns_dataframe(self):
        df = _make_df()
        feats = _build_features(df)
        assert isinstance(feats, pd.DataFrame)
        assert len(feats) > 0

    def test_build_labels_binary(self):
        df = _make_df()
        labels = _build_labels(df, forward_bars=3)
        unique_vals = set(labels.dropna().unique())
        assert unique_vals.issubset({0, 1})

    def test_fallback_prediction_structure(self):
        df = _make_df()
        result = _fallback_prediction(df)
        assert "score" in result
        assert "signal" in result
        assert "confidence" in result
        assert 1 <= result["score"] <= 100
        assert result["signal"] in ("BUY", "SELL", "NEUTRAL")

    def test_predict_all_timeframes_returns_all_keys(self):
        df = _make_df(200)
        timeframes = ["1m", "5m", "1h", "24h"]
        result = predict_all_timeframes(df, "BTC", timeframes)
        for tf in timeframes:
            assert tf in result
            assert 1 <= result[tf]["score"] <= 100
            assert result[tf]["signal"] in ("BUY", "SELL", "NEUTRAL")
