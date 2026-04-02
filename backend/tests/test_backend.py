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
from fastapi.testclient import TestClient

from indicators import calculate_indicators, indicator_signals
from ml_predictions import (
    _build_features,
    _build_labels,
    _fallback_prediction,
    predict_all_timeframes,
)
from demo_data import generate_ohlcv, generate_price_info
from data_fetcher import get_ticker, ASSET_MAP
from main import app, _summarize_signals
from backtester import (
    strategy_ma_crossover,
    strategy_rsi_mean_reversion,
    strategy_bollinger_bands,
    strategy_macd,
    strategy_breakout,
    strategy_momentum,
    run_backtest,
    STRATEGY_META,
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


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app, raise_server_exceptions=True)


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

    def test_summarize_signals_buy(self):
        signals = {
            "rsi": ("BUY", 0.8),
            "macd": ("BUY", 0.7),
            "stoch": ("BUY", 0.6),
        }
        result = _summarize_signals(signals)
        assert result["signal"] == "BUY"
        assert result["buy_count"] == 3
        assert 1 <= result["score"] <= 100

    def test_summarize_signals_sell(self):
        signals = {
            "rsi": ("SELL", 0.8),
            "macd": ("SELL", 0.7),
            "stoch": ("SELL", 0.6),
        }
        result = _summarize_signals(signals)
        assert result["signal"] == "SELL"
        assert result["sell_count"] == 3

    def test_summarize_signals_neutral(self):
        signals = {
            "rsi": ("NEUTRAL", 0.5),
            "macd": ("NEUTRAL", 0.5),
        }
        result = _summarize_signals(signals)
        assert result["signal"] == "NEUTRAL"
        assert result["score"] == 50


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


# ---------------------------------------------------------------------------
# Demo data tests
# ---------------------------------------------------------------------------

class TestDemoData:
    def test_generate_ohlcv_shape(self):
        for sym in ["BTC", "ETH", "XAU", "CL"]:
            df = generate_ohlcv(sym)
            assert len(df) == 200
            assert list(df.columns) == ["open", "high", "low", "close", "volume"]

    def test_generate_ohlcv_positive_prices(self):
        df = generate_ohlcv("BTC")
        assert (df["close"] > 0).all()
        assert (df["high"] >= df["low"]).all()

    def test_generate_price_info_structure(self):
        for sym in ["BTC", "ETH", "XAU", "CL"]:
            info = generate_price_info(sym)
            assert info["symbol"] == sym
            assert info["price"] > 0
            assert info["demo"] is True
            assert "change_pct" in info

    def test_get_ticker_mapping(self):
        assert get_ticker("BTC") == "BTC-USD"
        assert get_ticker("ETH") == "ETH-USD"
        assert get_ticker("XAU") == "GC=F"
        assert get_ticker("CL") == "CL=F"
        # Unknown symbol returns the symbol itself
        assert get_ticker("UNKNOWN") == "UNKNOWN"


# ---------------------------------------------------------------------------
# API endpoint tests (HTTP-level via TestClient)
# ---------------------------------------------------------------------------

class TestAPIEndpoints:
    def test_health_check(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json() == {"status": "ok"}

    def test_list_assets(self, client):
        r = client.get("/api/assets")
        assert r.status_code == 200
        assets = r.json()
        assert isinstance(assets, list)
        symbols = {a["symbol"] for a in assets}
        assert {"BTC", "ETH", "BNB", "SOL", "XAU", "CL"}.issubset(symbols)
        for asset in assets:
            assert "symbol" in asset
            assert "name" in asset
            assert "category" in asset
            assert "ticker" in asset

    def test_price_endpoint_returns_data(self, client):
        """Price endpoint must return a usable response (live or demo)."""
        r = client.get("/api/price/BTC")
        assert r.status_code == 200
        data = r.json()
        assert "price" in data
        assert data["price"] is not None
        assert data["price"] > 0

    def test_price_endpoint_all_symbols(self, client):
        for sym in ["BTC", "ETH", "BNB", "SOL", "XAU", "CL"]:
            r = client.get(f"/api/price/{sym}")
            assert r.status_code == 200, f"Price endpoint failed for {sym}: {r.text}"
            data = r.json()
            assert data["price"] > 0

    def test_dashboard_endpoint_btc(self, client):
        r = client.get("/api/dashboard/BTC?timeframe=1h")
        assert r.status_code == 200
        data = r.json()
        assert data["symbol"] == "BTC"
        assert data["timeframe"] == "1h"
        assert "price" in data
        assert "indicators" in data
        assert "indicator_signals" in data
        assert "signal_summary" in data
        assert "predictions" in data
        assert "candles" in data

    def test_dashboard_contains_all_indicator_keys(self, client):
        r = client.get("/api/dashboard/ETH?timeframe=1h")
        assert r.status_code == 200
        data = r.json()
        ind = data["indicators"]
        for key in ["rsi", "macd", "bbands", "ema", "sma", "stoch", "atr", "adx", "cci", "willr", "vwap", "obv"]:
            assert key in ind, f"Missing indicator: {key}"

    def test_dashboard_predictions_all_timeframes(self, client):
        r = client.get("/api/dashboard/BTC?timeframe=1h")
        assert r.status_code == 200
        preds = r.json()["predictions"]
        for tf in ["1m", "3m", "5m", "10m", "15m", "30m", "1h", "24h"]:
            assert tf in preds, f"Missing prediction for timeframe: {tf}"
            p = preds[tf]
            assert 1 <= p["score"] <= 100
            assert p["signal"] in ("BUY", "SELL", "NEUTRAL")

    def test_dashboard_all_symbols(self, client):
        for sym in ["BTC", "ETH", "BNB", "SOL", "XAU", "CL"]:
            r = client.get(f"/api/dashboard/{sym}?timeframe=1h")
            assert r.status_code == 200, f"Dashboard failed for {sym}: {r.text}"

    def test_dashboard_all_timeframes(self, client):
        for tf in ["1m", "5m", "15m", "30m", "1h", "24h"]:
            r = client.get(f"/api/dashboard/BTC?timeframe={tf}")
            assert r.status_code == 200, f"Dashboard failed for timeframe={tf}: {r.text}"

    def test_dashboard_unknown_symbol_returns_400(self, client):
        r = client.get("/api/dashboard/FAKECOIN")
        assert r.status_code == 400

    def test_dashboard_candles_structure(self, client):
        r = client.get("/api/dashboard/BTC?timeframe=1h")
        assert r.status_code == 200
        candles = r.json()["candles"]
        assert len(candles) > 0
        for c in candles[:5]:
            assert "t" in c
            assert "o" in c
            assert "h" in c
            assert "l" in c
            assert "c" in c
            assert "v" in c

    def test_dashboard_signal_summary_structure(self, client):
        r = client.get("/api/dashboard/BTC?timeframe=1h")
        assert r.status_code == 200
        summary = r.json()["signal_summary"]
        assert "signal" in summary
        assert summary["signal"] in ("BUY", "SELL", "NEUTRAL")
        assert "score" in summary
        assert 1 <= summary["score"] <= 100
        assert "buy_count" in summary
        assert "sell_count" in summary
        assert "neutral_count" in summary

    def test_dashboard_indicator_signals_structure(self, client):
        r = client.get("/api/dashboard/BTC?timeframe=1h")
        assert r.status_code == 200
        signals = r.json()["indicator_signals"]
        assert isinstance(signals, dict)
        for key, val in signals.items():
            assert "signal" in val
            assert "strength" in val
            assert val["signal"] in ("BUY", "SELL", "NEUTRAL")

    def test_dashboard_price_is_positive(self, client):
        r = client.get("/api/dashboard/BTC?timeframe=1h")
        assert r.status_code == 200
        price = r.json()["price"]
        assert price is not None
        assert price["price"] > 0

    def test_response_is_json_serializable(self, client):
        """Ensure the full dashboard response can be serialized to JSON without errors."""
        import json
        r = client.get("/api/dashboard/BTC?timeframe=1h")
        assert r.status_code == 200
        # TestClient already decoded JSON; re-encode to verify all values are serializable
        assert json.dumps(r.json()) is not None


# ---------------------------------------------------------------------------
# Backtesting strategy tests
# ---------------------------------------------------------------------------

class TestBacktestStrategies:
    """Unit tests for every built-in backtesting strategy."""

    def _make_trending_df(self, n: int = 300, trend: float = 0.5) -> pd.DataFrame:
        """Trending series (upward by default)."""
        rng = np.random.default_rng(99)
        close = 100.0 + np.cumsum(rng.normal(trend, 1.5, n))
        close = np.clip(close, 1.0, None)
        high   = close + rng.uniform(0.1, 1.5, n)
        low    = close - rng.uniform(0.1, 1.5, n)
        open_  = close + rng.normal(0, 0.3, n)
        volume = rng.uniform(1e6, 1e7, n)
        idx = pd.date_range("2023-01-01", periods=n, freq="1h")
        return pd.DataFrame(
            {"open": open_, "high": high, "low": low, "close": close, "volume": volume},
            index=idx,
        )

    def _assert_valid_result(self, result: dict):
        assert "total_return_pct" in result
        assert "max_drawdown_pct" in result
        assert "num_trades" in result
        assert "win_rate_pct" in result
        assert "sharpe_ratio" in result
        assert "profit_factor" in result
        assert "avg_trade_pct" in result
        assert isinstance(result["trades"], list)
        assert result["max_drawdown_pct"] >= 0
        assert 0 <= result["win_rate_pct"] <= 100

    def test_ma_crossover_result_structure(self):
        df = self._make_trending_df()
        result = strategy_ma_crossover(df, fast=5, slow=20)
        self._assert_valid_result(result)

    def test_ma_crossover_direction_long_only(self):
        df = self._make_trending_df()
        result = strategy_ma_crossover(df, fast=5, slow=20, direction="long")
        for trade in result["trades"]:
            assert trade["side"] == "LONG"

    def test_ma_crossover_direction_short_only(self):
        df = self._make_trending_df()
        result = strategy_ma_crossover(df, fast=5, slow=20, direction="short")
        for trade in result["trades"]:
            assert trade["side"] == "SHORT"

    def test_rsi_mean_reversion_result_structure(self):
        df = self._make_trending_df()
        result = strategy_rsi_mean_reversion(df, period=14, oversold=30, overbought=70)
        self._assert_valid_result(result)

    def test_rsi_mean_reversion_all_trades_long(self):
        df = self._make_trending_df()
        result = strategy_rsi_mean_reversion(df)
        for trade in result["trades"]:
            assert trade["side"] == "LONG"

    def test_bollinger_bands_result_structure(self):
        df = self._make_trending_df()
        result = strategy_bollinger_bands(df, period=20, std_dev=2.0)
        self._assert_valid_result(result)

    def test_bollinger_bands_all_trades_long(self):
        df = self._make_trending_df()
        result = strategy_bollinger_bands(df)
        for trade in result["trades"]:
            assert trade["side"] == "LONG"

    def test_macd_result_structure(self):
        df = self._make_trending_df()
        result = strategy_macd(df, fast=12, slow=26, signal=9)
        self._assert_valid_result(result)

    def test_breakout_result_structure(self):
        df = self._make_trending_df()
        result = strategy_breakout(df, lookback=20, stop_loss_pct=2.0, take_profit_pct=4.0)
        self._assert_valid_result(result)

    def test_breakout_exit_reason_present(self):
        df = self._make_trending_df()
        result = strategy_breakout(df)
        for trade in result["trades"]:
            if "exit_reason" in trade:
                assert trade["exit_reason"] in ("SL", "TP")

    def test_momentum_result_structure(self):
        df = self._make_trending_df()
        result = strategy_momentum(df, roc_period=10, threshold=1.5, hold_bars=5)
        self._assert_valid_result(result)

    def test_run_backtest_dispatcher(self):
        df = self._make_trending_df()
        for strategy_id in ["ma_crossover", "rsi_mean_reversion", "bollinger_bands",
                             "macd", "breakout", "momentum"]:
            result = run_backtest(strategy_id, df, {})
            self._assert_valid_result(result)

    def test_run_backtest_unknown_strategy_raises(self):
        df = self._make_trending_df()
        with pytest.raises(ValueError):
            run_backtest("nonexistent_strategy", df, {})

    def test_strategy_meta_structure(self):
        assert len(STRATEGY_META) >= 5
        for meta in STRATEGY_META:
            assert "id" in meta
            assert "name" in meta
            assert "description" in meta
            assert "params" in meta
            for param in meta["params"]:
                assert "name" in param
                assert "label" in param
                assert "type" in param
                assert "default" in param

    def test_no_trade_returns_empty_result(self):
        # Very flat data – MA crossover should produce few/no trades
        n = 50
        close = np.full(n, 100.0)
        idx = pd.date_range("2024-01-01", periods=n, freq="1h")
        df = pd.DataFrame({
            "open": close, "high": close + 0.001,
            "low": close - 0.001, "close": close, "volume": np.ones(n) * 1e6,
        }, index=idx)
        result = strategy_ma_crossover(df)
        assert result["num_trades"] == 0
        assert result["total_return_pct"] == 0.0

    def test_equity_curve_length(self):
        df = self._make_trending_df()
        result = strategy_ma_crossover(df)
        if result["num_trades"] > 0:
            assert len(result["equity_curve"]) == result["num_trades"] + 1


# ---------------------------------------------------------------------------
# Backtesting API endpoint tests
# ---------------------------------------------------------------------------

class TestBacktestAPI:
    def test_list_strategies(self, client):
        r = client.get("/api/backtest/strategies")
        assert r.status_code == 200
        data = r.json()
        assert "strategies" in data
        assert len(data["strategies"]) >= 5

    def test_backtest_default_strategy(self, client):
        r = client.post("/api/backtest/BTC?strategy=ma_crossover&timeframe=1h")
        assert r.status_code == 200
        data = r.json()
        assert data["symbol"] == "BTC"
        assert data["strategy"] == "ma_crossover"
        assert "result" in data
        result = data["result"]
        assert "total_return_pct" in result
        assert "num_trades" in result
        assert "win_rate_pct" in result
        assert "sharpe_ratio" in result

    def test_backtest_all_strategies(self, client):
        strategies = ["ma_crossover", "rsi_mean_reversion", "bollinger_bands",
                      "macd", "breakout", "momentum"]
        for strat in strategies:
            r = client.post(f"/api/backtest/BTC?strategy={strat}&timeframe=1h")
            assert r.status_code == 200, f"Backtest failed for strategy {strat}: {r.text}"
            assert "result" in r.json()

    def test_backtest_with_custom_params(self, client):
        import json
        params = json.dumps({"fast": 5, "slow": 15})
        r = client.post(f"/api/backtest/ETH?strategy=ma_crossover&timeframe=1h&params={params}")
        assert r.status_code == 200
        data = r.json()
        assert data["params"]["fast"] == 5

    def test_backtest_unknown_symbol_returns_400(self, client):
        r = client.post("/api/backtest/FAKECOIN?strategy=ma_crossover")
        assert r.status_code == 400

    def test_backtest_unknown_strategy_returns_400(self, client):
        r = client.post("/api/backtest/BTC?strategy=nonexistent_strategy")
        assert r.status_code == 400

    def test_backtest_all_symbols(self, client):
        for sym in ["BTC", "ETH", "SOL", "XAU", "CL"]:
            r = client.post(f"/api/backtest/{sym}?strategy=rsi_mean_reversion&timeframe=1h")
            assert r.status_code == 200, f"Backtest failed for {sym}"

