"""
Backtesting engine for TradingApp.

Supports 6 built-in strategies, each returning a standardised result dict:
  - total_return_pct   float
  - max_drawdown_pct   float
  - num_trades         int
  - win_rate_pct       float
  - sharpe_ratio       float
  - trades             list[dict]  (up to *max_trades* open/close/pnl entries)
"""
from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def _compute_sharpe(returns: pd.Series, risk_free: float = 0.0) -> float:
    """Annualised Sharpe ratio from a series of per-trade returns (in %)."""
    if len(returns) < 2:
        return 0.0
    excess = returns - risk_free
    std = excess.std()
    if std == 0:
        return 0.0
    return float(round((excess.mean() / std) * math.sqrt(min(len(returns), 252)), 3))


def _compute_max_drawdown(equity_curve: list[float]) -> float:
    """Maximum drawdown in percent from peak to trough."""
    if len(equity_curve) < 2:
        return 0.0
    peak = equity_curve[0]
    max_dd = 0.0
    for val in equity_curve:
        if val > peak:
            peak = val
        dd = (peak - val) / peak * 100
        if dd > max_dd:
            max_dd = dd
    return round(max_dd, 2)


def _build_result(trades: list[dict], initial_capital: float = 10_000.0, max_trades: int = 50) -> dict:
    """Build standardised backtest result from raw trades list.

    *max_trades* controls how many of the most recent trades are included in the
    returned ``trades`` list (default 50).  All trades are still used for metric
    calculations — only the returned slice is capped.
    """
    if not trades:
        return {
            "total_return_pct": 0.0,
            "max_drawdown_pct": 0.0,
            "num_trades": 0,
            "win_rate_pct": 0.0,
            "sharpe_ratio": 0.0,
            "profit_factor": 0.0,
            "avg_trade_pct": 0.0,
            "trades": [],
        }

    equity = initial_capital
    equity_curve = [initial_capital]
    returns_pct = []
    wins = 0
    total_profit = 0.0
    total_loss = 0.0

    for t in trades:
        pnl_pct = t["pnl_pct"]
        pnl_usd = equity * (pnl_pct / 100)
        equity += pnl_usd
        equity_curve.append(equity)
        returns_pct.append(pnl_pct)
        if pnl_pct > 0:
            wins += 1
            total_profit += pnl_usd
        else:
            total_loss += abs(pnl_usd)

    total_return = round((equity - initial_capital) / initial_capital * 100, 2)
    max_dd = _compute_max_drawdown(equity_curve)
    win_rate = round(wins / len(trades) * 100, 1)
    sharpe = _compute_sharpe(pd.Series(returns_pct))
    profit_factor = round(total_profit / total_loss, 3) if total_loss > 0 else float("inf")
    avg_trade = round(np.mean(returns_pct), 3)

    return {
        "total_return_pct": total_return,
        "max_drawdown_pct": max_dd,
        "num_trades": len(trades),
        "win_rate_pct": win_rate,
        "sharpe_ratio": sharpe,
        "profit_factor": profit_factor,
        "avg_trade_pct": avg_trade,
        "equity_curve": [round(e, 2) for e in equity_curve],
        "trades": trades[-max_trades:],  # return last N for brevity; all trades used in metric calculations
    }


# ---------------------------------------------------------------------------
# Strategy 1 – Moving Average Crossover
# ---------------------------------------------------------------------------

def strategy_ma_crossover(
    df: pd.DataFrame,
    fast: int = 10,
    slow: int = 30,
    direction: str = "both",
) -> dict[str, Any]:
    """
    Enter LONG when fast EMA crosses above slow EMA (vice-versa for SHORT).
    *direction*: 'long' | 'short' | 'both'
    """
    df = df.copy().reset_index(drop=True)
    close = df["close"]
    fast_ma = close.ewm(span=fast, adjust=False).mean()
    slow_ma = close.ewm(span=slow, adjust=False).mean()

    trades = []
    in_trade = None  # dict or None

    for i in range(1, len(df)):
        prev_fast, prev_slow = fast_ma.iloc[i - 1], slow_ma.iloc[i - 1]
        curr_fast, curr_slow = fast_ma.iloc[i], slow_ma.iloc[i]
        price = float(close.iloc[i])
        ts = str(df.index[i]) if hasattr(df.index[i], "__str__") else i

        golden_cross = prev_fast <= prev_slow and curr_fast > curr_slow
        death_cross = prev_fast >= prev_slow and curr_fast < curr_slow

        if in_trade is None:
            if golden_cross and direction in ("long", "both"):
                in_trade = {"side": "LONG", "entry": price, "open_bar": i, "open_time": ts}
            elif death_cross and direction in ("short", "both"):
                in_trade = {"side": "SHORT", "entry": price, "open_bar": i, "open_time": ts}
        else:
            should_close = (in_trade["side"] == "LONG" and death_cross) or \
                           (in_trade["side"] == "SHORT" and golden_cross)
            if should_close:
                entry = in_trade["entry"]
                pnl_pct = (price - entry) / entry * 100 * (1 if in_trade["side"] == "LONG" else -1)
                trades.append({
                    "side": in_trade["side"],
                    "entry_price": round(entry, 4),
                    "close_price": round(price, 4),
                    "pnl_pct": round(pnl_pct, 3),
                    "open_time": in_trade["open_time"],
                    "close_time": ts,
                })
                in_trade = None

    return _build_result(trades)


# ---------------------------------------------------------------------------
# Strategy 2 – RSI Mean Reversion
# ---------------------------------------------------------------------------

def strategy_rsi_mean_reversion(
    df: pd.DataFrame,
    period: int = 14,
    oversold: float = 30.0,
    overbought: float = 70.0,
) -> dict[str, Any]:
    """Buy when RSI < oversold, sell when RSI > overbought."""
    df = df.copy().reset_index(drop=True)
    close = df["close"]

    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(span=period, adjust=False).mean()
    avg_loss = loss.ewm(span=period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))

    trades = []
    in_trade = None

    for i in range(period, len(df)):
        price = float(close.iloc[i])
        rsi_val = float(rsi.iloc[i])
        ts = str(df.index[i]) if hasattr(df.index[i], "__str__") else i

        if in_trade is None:
            if rsi_val < oversold:
                in_trade = {"side": "LONG", "entry": price, "open_time": ts}
        else:
            if in_trade["side"] == "LONG" and rsi_val > overbought:
                entry = in_trade["entry"]
                pnl_pct = (price - entry) / entry * 100
                trades.append({
                    "side": "LONG",
                    "entry_price": round(entry, 4),
                    "close_price": round(price, 4),
                    "pnl_pct": round(pnl_pct, 3),
                    "open_time": in_trade["open_time"],
                    "close_time": ts,
                })
                in_trade = None

    return _build_result(trades)


# ---------------------------------------------------------------------------
# Strategy 3 – Bollinger Bands
# ---------------------------------------------------------------------------

def strategy_bollinger_bands(
    df: pd.DataFrame,
    period: int = 20,
    std_dev: float = 2.0,
) -> dict[str, Any]:
    """Buy when close < lower band; exit when close > middle or upper band."""
    df = df.copy().reset_index(drop=True)
    close = df["close"]

    mid = close.rolling(period).mean()
    std = close.rolling(period).std()
    upper = mid + std_dev * std
    lower = mid - std_dev * std

    trades = []
    in_trade = None

    for i in range(period, len(df)):
        price = float(close.iloc[i])
        mid_v = float(mid.iloc[i])
        lower_v = float(lower.iloc[i])
        upper_v = float(upper.iloc[i])
        ts = str(df.index[i]) if hasattr(df.index[i], "__str__") else i

        if in_trade is None:
            if price < lower_v:
                in_trade = {"entry": price, "open_time": ts}
        else:
            if price >= mid_v:
                entry = in_trade["entry"]
                pnl_pct = (price - entry) / entry * 100
                trades.append({
                    "side": "LONG",
                    "entry_price": round(entry, 4),
                    "close_price": round(price, 4),
                    "pnl_pct": round(pnl_pct, 3),
                    "open_time": in_trade["open_time"],
                    "close_time": ts,
                })
                in_trade = None

    return _build_result(trades)


# ---------------------------------------------------------------------------
# Strategy 4 – MACD Crossover
# ---------------------------------------------------------------------------

def strategy_macd(
    df: pd.DataFrame,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> dict[str, Any]:
    """Trade based on MACD line crossing the signal line."""
    df = df.copy().reset_index(drop=True)
    close = df["close"]

    ema_fast = close.ewm(span=fast, adjust=False).mean()
    ema_slow = close.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()

    trades = []
    in_trade = None

    for i in range(slow + signal, len(df)):
        price = float(close.iloc[i])
        prev_m, prev_s = float(macd_line.iloc[i - 1]), float(signal_line.iloc[i - 1])
        curr_m, curr_s = float(macd_line.iloc[i]), float(signal_line.iloc[i])
        ts = str(df.index[i]) if hasattr(df.index[i], "__str__") else i

        bullish_cross = prev_m <= prev_s and curr_m > curr_s
        bearish_cross = prev_m >= prev_s and curr_m < curr_s

        if in_trade is None:
            if bullish_cross:
                in_trade = {"side": "LONG", "entry": price, "open_time": ts}
            elif bearish_cross:
                in_trade = {"side": "SHORT", "entry": price, "open_time": ts}
        else:
            should_close = (in_trade["side"] == "LONG" and bearish_cross) or \
                           (in_trade["side"] == "SHORT" and bullish_cross)
            if should_close:
                entry = in_trade["entry"]
                pnl_pct = (price - entry) / entry * 100 * (1 if in_trade["side"] == "LONG" else -1)
                trades.append({
                    "side": in_trade["side"],
                    "entry_price": round(entry, 4),
                    "close_price": round(price, 4),
                    "pnl_pct": round(pnl_pct, 3),
                    "open_time": in_trade["open_time"],
                    "close_time": ts,
                })
                in_trade = None

    return _build_result(trades)


# ---------------------------------------------------------------------------
# Strategy 5 – Breakout (Donchian Channel)
# ---------------------------------------------------------------------------

def strategy_breakout(
    df: pd.DataFrame,
    lookback: int = 20,
    stop_loss_pct: float = 2.0,
    take_profit_pct: float = 4.0,
) -> dict[str, Any]:
    """
    Enter LONG when price breaks above the *lookback*-period high.
    Enter SHORT when price breaks below the *lookback*-period low.
    Exit on stop-loss or take-profit.
    """
    df = df.copy().reset_index(drop=True)
    close = df["close"]

    roll_high = close.rolling(lookback).max().shift(1)
    roll_low = close.rolling(lookback).min().shift(1)

    trades = []
    in_trade = None

    for i in range(lookback + 1, len(df)):
        price = float(close.iloc[i])
        high_v = float(roll_high.iloc[i])
        low_v = float(roll_low.iloc[i])
        ts = str(df.index[i]) if hasattr(df.index[i], "__str__") else i

        if in_trade is None:
            if price > high_v:
                in_trade = {
                    "side": "LONG", "entry": price,
                    "sl": price * (1 - stop_loss_pct / 100),
                    "tp": price * (1 + take_profit_pct / 100),
                    "open_time": ts,
                }
            elif price < low_v:
                in_trade = {
                    "side": "SHORT", "entry": price,
                    "sl": price * (1 + stop_loss_pct / 100),
                    "tp": price * (1 - take_profit_pct / 100),
                    "open_time": ts,
                }
        else:
            hit_sl = (in_trade["side"] == "LONG" and price <= in_trade["sl"]) or \
                     (in_trade["side"] == "SHORT" and price >= in_trade["sl"])
            hit_tp = (in_trade["side"] == "LONG" and price >= in_trade["tp"]) or \
                     (in_trade["side"] == "SHORT" and price <= in_trade["tp"])
            if hit_sl or hit_tp:
                entry = in_trade["entry"]
                pnl_pct = (price - entry) / entry * 100 * (1 if in_trade["side"] == "LONG" else -1)
                trades.append({
                    "side": in_trade["side"],
                    "entry_price": round(entry, 4),
                    "close_price": round(price, 4),
                    "pnl_pct": round(pnl_pct, 3),
                    "exit_reason": "TP" if hit_tp else "SL",
                    "open_time": in_trade["open_time"],
                    "close_time": ts,
                })
                in_trade = None

    return _build_result(trades)


# ---------------------------------------------------------------------------
# Strategy 6 – Momentum / Rate of Change
# ---------------------------------------------------------------------------

def strategy_momentum(
    df: pd.DataFrame,
    roc_period: int = 10,
    threshold: float = 1.5,
    hold_bars: int = 5,
) -> dict[str, Any]:
    """
    Enter LONG when ROC exceeds +threshold; SHORT when ROC < -threshold.
    Hold for *hold_bars* bars then close.
    """
    df = df.copy().reset_index(drop=True)
    close = df["close"]

    roc = close.pct_change(roc_period) * 100

    trades = []
    in_trade = None

    for i in range(roc_period + 1, len(df)):
        price = float(close.iloc[i])
        roc_val = float(roc.iloc[i])
        ts = str(df.index[i]) if hasattr(df.index[i], "__str__") else i

        if in_trade is None:
            if not math.isnan(roc_val):
                if roc_val > threshold:
                    in_trade = {"side": "LONG", "entry": price, "open_bar": i, "open_time": ts}
                elif roc_val < -threshold:
                    in_trade = {"side": "SHORT", "entry": price, "open_bar": i, "open_time": ts}
        else:
            if i - in_trade["open_bar"] >= hold_bars:
                entry = in_trade["entry"]
                pnl_pct = (price - entry) / entry * 100 * (1 if in_trade["side"] == "LONG" else -1)
                trades.append({
                    "side": in_trade["side"],
                    "entry_price": round(entry, 4),
                    "close_price": round(price, 4),
                    "pnl_pct": round(pnl_pct, 3),
                    "open_time": in_trade["open_time"],
                    "close_time": ts,
                })
                in_trade = None

    return _build_result(trades)


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------

STRATEGIES: dict[str, Any] = {
    "ma_crossover":       strategy_ma_crossover,
    "rsi_mean_reversion": strategy_rsi_mean_reversion,
    "bollinger_bands":    strategy_bollinger_bands,
    "macd":               strategy_macd,
    "breakout":           strategy_breakout,
    "momentum":           strategy_momentum,
}

STRATEGY_META = [
    {
        "id": "ma_crossover",
        "name": "MA Crossover",
        "description": "Fast EMA crosses above/below slow EMA",
        "params": [
            {"name": "fast",      "label": "Fast EMA",  "type": "int",   "default": 10,  "min": 2,   "max": 50},
            {"name": "slow",      "label": "Slow EMA",  "type": "int",   "default": 30,  "min": 5,   "max": 200},
            {"name": "direction", "label": "Direction", "type": "select","default": "both",
             "options": ["long", "short", "both"]},
        ],
    },
    {
        "id": "rsi_mean_reversion",
        "name": "RSI Mean Reversion",
        "description": "Buy oversold (< threshold), sell overbought (> threshold)",
        "params": [
            {"name": "period",     "label": "RSI Period",  "type": "int",   "default": 14, "min": 5,  "max": 50},
            {"name": "oversold",   "label": "Oversold",    "type": "float", "default": 30, "min": 10, "max": 45},
            {"name": "overbought", "label": "Overbought",  "type": "float", "default": 70, "min": 55, "max": 90},
        ],
    },
    {
        "id": "bollinger_bands",
        "name": "Bollinger Bands",
        "description": "Buy at lower band, exit at middle band",
        "params": [
            {"name": "period",  "label": "Period",   "type": "int",   "default": 20, "min": 5,  "max": 100},
            {"name": "std_dev", "label": "Std Dev",  "type": "float", "default": 2.0,"min": 1.0,"max": 3.5},
        ],
    },
    {
        "id": "macd",
        "name": "MACD Crossover",
        "description": "Trade MACD line crossing signal line",
        "params": [
            {"name": "fast",   "label": "Fast EMA",   "type": "int", "default": 12, "min": 5,  "max": 30},
            {"name": "slow",   "label": "Slow EMA",   "type": "int", "default": 26, "min": 10, "max": 60},
            {"name": "signal", "label": "Signal EMA", "type": "int", "default": 9,  "min": 3,  "max": 20},
        ],
    },
    {
        "id": "breakout",
        "name": "Donchian Breakout",
        "description": "Enter on channel breakout with SL/TP",
        "params": [
            {"name": "lookback",        "label": "Lookback",        "type": "int",   "default": 20, "min": 5,  "max": 100},
            {"name": "stop_loss_pct",   "label": "Stop Loss %",     "type": "float", "default": 2.0,"min": 0.5,"max": 10.0},
            {"name": "take_profit_pct", "label": "Take Profit %",   "type": "float", "default": 4.0,"min": 1.0,"max": 20.0},
        ],
    },
    {
        "id": "momentum",
        "name": "Momentum / ROC",
        "description": "Enter on strong momentum, hold fixed bars",
        "params": [
            {"name": "roc_period", "label": "ROC Period",   "type": "int",   "default": 10, "min": 3,  "max": 50},
            {"name": "threshold",  "label": "Threshold %",  "type": "float", "default": 1.5,"min": 0.5,"max": 10.0},
            {"name": "hold_bars",  "label": "Hold Bars",    "type": "int",   "default": 5,  "min": 1,  "max": 50},
        ],
    },
]


def run_backtest(strategy_id: str, df: pd.DataFrame, params: dict) -> dict:
    """Run a named strategy with given params dict and return the result."""
    if strategy_id not in STRATEGIES:
        raise ValueError(f"Unknown strategy: {strategy_id}")
    fn = STRATEGIES[strategy_id]
    # Only pass params that the function accepts
    import inspect
    sig = inspect.signature(fn)
    valid_params = {k: v for k, v in params.items() if k in sig.parameters}
    return fn(df, **valid_params)
