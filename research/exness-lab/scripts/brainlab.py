"""Shared helpers for Batches 47+ (candle and oil brains). Brains come from the repo package
tradingagents.analytics (single source of truth)."""
import sys, numpy as np, pandas as pd
sys.path.insert(0, "/home/user/tradingagents")
from tradingagents.analytics import candles as CB, oil as OB  # noqa
END = "2026-11-27"
def L(t):
    d = pd.read_csv(f"data/{t}.csv", parse_dates=["Date"], index_col="Date")
    d = d[["Open", "High", "Low", "Close"]].dropna(); d = d[(d.High >= d.Low) & (d.Close > 0)]
    return d.loc[:END]
# Exness market -> (hold proxy, intraday/bar proxy, $ exposure at min lot today, round-trip cost bp)
MK = {
    "US500": ("SPY", "SPY", 1000, 1.6), "USTEC": ("QQQ", "QQQ", 1330, 1.4), "US30": ("DIA", "DIA", 500, 1.3),
    "XAU": ("GLD", "GLD", 3640, 1.5), "XAG": ("SLV", "SLV", 2160, 8.0),
    "USOIL": ("USO", "CL=F", 830, 8.0), "UKOIL": ("BNO", "BZ=F", 950, 8.0),
    "BTC": ("BTC-USD", "BTC-USD", 595, 1.1), "ETH": ("ETH-USD", "ETH-USD", 165, 5.0),
    "EURUSD": ("EURUSD=X", "EURUSD=X", 1100, 2.0), "GBPUSD": ("GBPUSD=X", "GBPUSD=X", 1300, 3.0),
    "USDJPY": ("JPY=X", "JPY=X", 1000, 2.5), "AUDUSD": ("AUDUSD=X", "AUDUSD=X", 650, 3.0), "USDCAD": ("CAD=X", "CAD=X", 1000, 3.0),
}
PER = [("2007-13", "2007", "2013"), ("2014-19", "2014", "2019"), ("2020-23", "2020", "2023"), ("2024-now", "2024", END)]
_cache = {}
def D(t):
    if t not in _cache: _cache[t] = L(t)
    return _cache[t]
def hold(sig, n):
    """sig[t] (+1/-1/0) at close t -> position held for the next n days (re-triggers extend)."""
    s = np.asarray(sig, float); out = np.zeros(len(s)); left = 0; side = 0
    for i in range(len(s)):
        if s[i] != 0: left, side = n, np.sign(s[i])
        out[i] = side if left > 0 else 0; left -= 1 if left > 0 else 0
    return out
def pos_ret(d, pos, bp):
    """pos[t] = position after close t; daily return on close t-1 -> t, cost bp per round trip (half per side change)."""
    p = pd.Series(np.asarray(pos, float), index=d.index).shift().fillna(0)
    return p * d.Close.pct_change().fillna(0) - p.diff().abs().fillna(p.abs()) * bp / 2e4
def straddle(d, U, Dn, ok, bp, slip=2.0, side=0):
    """Stop entries at U (buy) / Dn (sell) on ok days, exit at close, other level is the stop; both hit = full-range loss."""
    o, h, l, c = d.Open, d.High, d.Low, d.Close; cost = (bp + slip) / 1e4
    sd = np.broadcast_to(np.asarray(side, float), (len(d),))
    up = (h >= U) & ok & (sd >= 0); dn = (l <= Dn) & ok & (sd <= 0)
    eL, eS = np.maximum(U, o), np.minimum(Dn, o)
    both = up & dn; up = up & ~both; dn = dn & ~both
    r = np.where(both, -(U - Dn) / U, np.where(up, np.where(l <= Dn, (Dn - eL) / eL, (c - eL) / eL),
                 np.where(dn, np.where(h >= U, (eS - U) / eS, (eS - c) / eS), 0))) - (up | dn) * cost
    return pd.Series(r, index=d.index).fillna(0)
def sharpe(r):
    r = r[r.index >= r[r != 0].index[0]] if (r != 0).any() else r
    return float(r.mean() / r.std() * np.sqrt(252)) if r.std() > 0 else 0.0
def tstat(r):
    r = r[r != 0]; return float(r.mean() / r.std() * np.sqrt(len(r))) if len(r) > 2 and r.std() > 0 else 0.0
def stats(r, exp):
    """r = daily % returns of the rule; $ = r x exposure."""
    row = {}; ok = True
    for lab, a, b in PER:
        u = r.loc[a:b]
        if (u != 0).sum() < 10: row[lab] = None; continue
        row[lab] = round(sharpe(u), 2)
    usd = r.loc["2014":] * exp; e = usd.cumsum()
    row["pre_sh_ok"] = all(row[k] is not None and row[k] > 0.3 for k in ("2014-19", "2020-23"))
    row["recent_ok"] = row["2024-now"] is not None and row["2024-now"] > 0.3
    row["t_post14"] = round(tstat(r.loc["2014":]), 2)
    row["usd_pre_yr"] = round(float(r.loc["2014":"2023"].sum() * exp / 10), 0)
    rec = r.loc["2024":] * exp; row["usd_24_yr"] = round(float(rec.sum() / (len(rec) / 252)), 0) if len(rec) else 0
    row["drop14"] = round(float((e - e.cummax()).min()), 0)
    row["trades_yr"] = round(float(((r != 0) & (r.shift().fillna(0) == 0)).loc["2014":].sum() / 12.9), 1)
    return row
def shift_p(pos_or_mask, builder, n=300, seed=0, a="2007", b="2023"):
    """Random-timing control: circularly shift the signal and rebuild returns; p = share of shifts with Sharpe >= actual."""
    rng = np.random.default_rng(seed); x = np.asarray(pos_or_mask); N = len(x)
    act = sharpe(builder(x).loc[a:b]); cnt = 0
    for k in rng.integers(20, N - 20, n):
        if sharpe(builder(np.roll(x, k)).loc[a:b]) >= act: cnt += 1
    return (cnt + 1) / (n + 1)
def bh(p, q=0.10):
    p = np.asarray(p); o = np.argsort(p); m = len(p); thr = q * (np.arange(1, m + 1)) / m
    passed = np.zeros(m, bool); k = np.where(p[o] <= thr)[0]
    if len(k): passed[o[: k.max() + 1]] = True
    return passed
