"""Candle brain: candlestick patterns read in context.

A pattern on its own carries little information (single textbook patterns failed the
lab's tests). This module tags each bar with its shape *and* where it happened:
trend (vs the 50/200-day averages), location (at an N-day low or high), and range
regime (narrow or wide vs recent bars). ``pattern_stats`` then measures, on the
instrument's own history up to the bar being read, what followed that pattern in
that context, so a report never quotes an edge the data does not show.

All functions take a daily OHLC frame with columns Open, High, Low, Close (index or
``Date`` column sorted ascending) and use only data up to each bar.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

PATTERNS = (
    "doji", "hammer", "shooting_star", "bull_engulfing", "bear_engulfing",
    "inside_bar", "outside_up", "outside_down", "key_reversal_up", "key_reversal_down",
    "nr4", "nr7", "wide_range", "bull_marubozu", "bear_marubozu",
    "morning_star", "evening_star", "three_white_soldiers", "three_black_crows",
    "close_near_high", "close_near_low",
)


def _frame(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()
    if "Date" in d.columns:
        d = d.set_index(pd.to_datetime(d["Date"])).drop(columns="Date")
    return d.sort_index()[["Open", "High", "Low", "Close"]].astype(float)


def candle_features(df: pd.DataFrame) -> pd.DataFrame:
    """Per-bar shape and context features (no look-ahead)."""
    d = _frame(df)
    o, h, l, c = d.Open, d.High, d.Low, d.Close
    rng = (h - l).replace(0, np.nan)
    body = c - o
    f = pd.DataFrame(index=d.index)
    f["body_frac"] = body.abs() / rng
    f["ibs"] = (c - l) / rng  # close location in the bar, 0 = low, 1 = high
    f["upper_wick"] = (h - np.maximum(o, c)) / rng
    f["lower_wick"] = (np.minimum(o, c) - l) / rng
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    atr = tr.rolling(14).mean()
    f["range_atr"] = (h - l) / atr.shift()
    f["gap_atr"] = (o - c.shift()) / atr.shift()
    f["trend_200"] = np.sign(c - c.rolling(200).mean())
    f["trend_50"] = np.sign(c - c.rolling(50).mean())
    f["at_10d_low"] = l <= l.rolling(10).min()
    f["at_10d_high"] = h >= h.rolling(10).max()
    f["at_20d_low"] = l <= l.rolling(20).min()
    f["at_20d_high"] = h >= h.rolling(20).max()
    f["dist_20d_low_atr"] = (c - l.rolling(20).min()) / atr
    f["dist_20d_high_atr"] = (h.rolling(20).max() - c) / atr
    f["atr_pct_rank"] = (atr / c).rolling(252, min_periods=60).rank(pct=True)
    return f


def detect_patterns(df: pd.DataFrame) -> pd.DataFrame:
    """Boolean frame, one column per name in PATTERNS."""
    d = _frame(df)
    o, h, l, c = d.Open, d.High, d.Low, d.Close
    f = candle_features(d)
    rng = h - l
    body = c - o
    bull, bear = body > 0, body < 0
    p = pd.DataFrame(index=d.index)
    p["doji"] = f.body_frac < 0.1
    p["hammer"] = (f.lower_wick >= 0.6) & (f.ibs >= 0.6)
    p["shooting_star"] = (f.upper_wick >= 0.6) & (f.ibs <= 0.4)
    p["bull_engulfing"] = bull & bear.shift(fill_value=False) & (c >= o.shift()) & (o <= c.shift())
    p["bear_engulfing"] = bear & bull.shift(fill_value=False) & (o >= c.shift()) & (c <= o.shift())
    p["inside_bar"] = (h < h.shift()) & (l > l.shift())
    outside = (h > h.shift()) & (l < l.shift())
    p["outside_up"] = outside & (f.ibs >= 0.7)
    p["outside_down"] = outside & (f.ibs <= 0.3)
    p["key_reversal_up"] = (l < l.shift()) & (c > h.shift())
    p["key_reversal_down"] = (h > h.shift()) & (c < l.shift())
    p["nr4"] = rng <= rng.rolling(4).min()
    p["nr7"] = rng <= rng.rolling(7).min()
    p["wide_range"] = f.range_atr >= 2.0
    p["bull_marubozu"] = bull & (f.body_frac >= 0.9)
    p["bear_marubozu"] = bear & (f.body_frac >= 0.9)
    small_mid = f.body_frac.shift() < 0.3
    p["morning_star"] = bear.shift(2, fill_value=False) & (f.body_frac.shift(2) > 0.5) & small_mid & bull & (c > (o.shift(2) + c.shift(2)) / 2)
    p["evening_star"] = bull.shift(2, fill_value=False) & (f.body_frac.shift(2) > 0.5) & small_mid & bear & (c < (o.shift(2) + c.shift(2)) / 2)
    up3 = bull & bull.shift(fill_value=False) & bull.shift(2, fill_value=False) & (c > c.shift()) & (c.shift() > c.shift(2))
    dn3 = bear & bear.shift(fill_value=False) & bear.shift(2, fill_value=False) & (c < c.shift()) & (c.shift() < c.shift(2))
    p["three_white_soldiers"] = up3 & (f.ibs >= 0.7)
    p["three_black_crows"] = dn3 & (f.ibs <= 0.3)
    p["close_near_high"] = f.ibs >= 0.9
    p["close_near_low"] = f.ibs <= 0.1
    return p.fillna(False).astype(bool)[list(PATTERNS)]


def context_labels(df: pd.DataFrame) -> pd.DataFrame:
    """Readable context per bar: trend, location and range regime."""
    f = candle_features(df)
    ctx = pd.DataFrame(index=f.index)
    ctx["trend"] = np.select([f.trend_200 > 0, f.trend_200 < 0], ["uptrend", "downtrend"], "unknown")
    ctx["location"] = np.select([f.at_20d_low, f.at_20d_high, f.at_10d_low, f.at_10d_high],
                                ["20-day low", "20-day high", "10-day low", "10-day high"], "mid-range")
    ctx["range"] = np.select([f.range_atr < 0.6, f.range_atr > 1.6], ["narrow", "wide"], "normal")
    return ctx


def pattern_stats(df: pd.DataFrame, pattern: str, horizon: int = 2, context: dict | None = None,
                  as_of: str | pd.Timestamp | None = None) -> dict:
    """What followed ``pattern`` (optionally in ``context``) on this instrument's own history.

    Forward return = close(t+horizon)/close(t) - 1, counted only for signals whose
    outcome was known by ``as_of``. Compares against all bars over the same history
    (the base rate) and gives a t-statistic of the difference.
    """
    d = _frame(df)
    if as_of is not None:
        d = d.loc[: pd.Timestamp(as_of)]
    pats = detect_patterns(d)
    if pattern not in pats.columns:
        raise ValueError(f"unknown pattern {pattern!r}; choose from {', '.join(PATTERNS)}")
    mask = pats[pattern].copy()
    if context:
        ctx = context_labels(d)
        for k, v in context.items():
            mask &= ctx[k] == v
    fwd = d.Close.shift(-horizon) / d.Close - 1
    known = fwd.notna()
    sig, base = fwd[mask & known], fwd[known]
    n = int(len(sig))
    out = {"pattern": pattern, "context": context or {}, "horizon_days": horizon, "signals": n,
           "avg_fwd_pct": None, "base_avg_pct": round(float(base.mean()) * 100, 3) if len(base) else None,
           "hit_rate": None, "t_vs_base": None}
    if n >= 2:
        diff = sig - base.mean()
        sd = float(sig.std(ddof=1))
        # signals overlap when horizon > 1; deflate the count by the horizon
        n_eff = max(n / max(horizon, 1), 1.0)
        out["avg_fwd_pct"] = round(float(sig.mean()) * 100, 3)
        out["hit_rate"] = round(float((sig > 0).mean()), 3)
        out["t_vs_base"] = round(float(diff.mean()) / (sd / math.sqrt(n_eff)), 2) if sd > 0 else None
    return out


def candle_report(df: pd.DataFrame, as_of: str | pd.Timestamp | None = None, horizon: int = 2,
                  min_signals: int = 15) -> str:
    """Markdown: the latest bar's patterns, its context, and the history behind each."""
    d = _frame(df)
    if as_of is not None:
        d = d.loc[: pd.Timestamp(as_of)]
    if len(d) < 30:
        return "Not enough price history for a candle read (need at least 30 daily bars)."
    pats, ctx, f = detect_patterns(d), context_labels(d), candle_features(d)
    day = d.index[-1]
    active = [p for p in PATTERNS if bool(pats[p].iloc[-1])]
    c = ctx.iloc[-1]
    lines = [f"## Candle read for {day.date()}",
             f"- Bar: O {d.Open.iloc[-1]:.4g} H {d.High.iloc[-1]:.4g} L {d.Low.iloc[-1]:.4g} C {d.Close.iloc[-1]:.4g}; "
             f"close location {f.ibs.iloc[-1]:.2f} of the range, range {f.range_atr.iloc[-1]:.2f}x ATR(14).",
             f"- Context: {c.trend}, at {c.location}, {c.range} range.",
             f"- Patterns on this bar: {', '.join(active) if active else 'none'}.", "",
             f"| Pattern | In this context? | Signals | Avg {horizon}-day move | Base | Hit rate | t vs base |",
             "|---|---|---|---|---|---|---|"]
    for p in active:
        for ctx_on in (False, True):
            st = pattern_stats(d, p, horizon, {"trend": c.trend, "location": c.location} if ctx_on else None)
            if st["signals"] < 2:
                lines.append(f"| {p} | {'yes' if ctx_on else 'any'} | {st['signals']} | n/a | | | |")
                continue
            lines.append(f"| {p} | {'yes' if ctx_on else 'any'} | {st['signals']} | {st['avg_fwd_pct']:+.2f}% | "
                         f"{st['base_avg_pct']:+.2f}% | {st['hit_rate']:.0%} | {st['t_vs_base']} |")
    lines += ["", f"Read: a pattern is only evidence when it has at least {min_signals} past signals and |t| >= 2; "
              "otherwise treat it as noise. Stats use this instrument's history up to this bar only."]
    return "\n".join(lines)
