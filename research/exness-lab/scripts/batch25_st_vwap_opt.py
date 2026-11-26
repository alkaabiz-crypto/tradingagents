"""Batch 25, pre-registered 2026-11-26 before running (Hazza: optimise the BTC Supertrend + VWAP pullback, cut the drop).
Only ~2 years of BTC hourly data are reachable (Yahoo, 2024-11-27 ->), so: TUNE on 2024-11-27..2025-11-26, TEST on
2025-11-27..2026-11-26. Base = S4 from Batch 22 (ST 10/3, 1h, no target, unlimited trades per day, no risk cap).
Grid (3x3x3x3x2x3 = 486): ST period {7,10,14}; multiplier {2,3,4}; bar size {1h,2h,4h}; target {none,1.5R,3R};
trades per day {1, unlimited}; max initial risk {none, 1%, 2% of price} (skip wider-stop signals).
Score on the tuning year = P&L / |worst drop| (return over drawdown). Report: base vs the tuned pick on the test year,
the share of settings beating base in the test year, and a daily loss cap check ($15/day at 0.01 lot) on the pick.
Costs $3.20/side + 1 bp slippage, 0.01 lot. Signals act at the next bar open; stop = Supertrend line (trailing).
"""
import itertools, numpy as np, pandas as pd
b = pd.read_csv("intraday/BTC-USD_1h.csv", index_col=0); b.index = pd.to_datetime(b.index, utc=True)
def bars(tf):
    if tf == 1: return b.copy()
    return b.resample(f"{tf}h", origin="start_day").agg({"Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum"}).dropna()
def supertrend(d, n, k):
    h, l, c = d.High, d.Low, d.Close
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1); atr = tr.ewm(alpha=1/n, adjust=False).mean()
    mid = (h + l) / 2; ub, lb = (mid + k * atr).values, (mid - k * atr).values; C = c.values
    fu, fl, st, dr = ub.copy(), lb.copy(), np.zeros(len(C)), np.ones(len(C))
    for i in range(1, len(C)):
        fu[i] = ub[i] if (ub[i] < fu[i-1] or C[i-1] > fu[i-1]) else fu[i-1]
        fl[i] = lb[i] if (lb[i] > fl[i-1] or C[i-1] < fl[i-1]) else fl[i-1]
        dr[i] = 1 if C[i] > fu[i-1] else (-1 if C[i] < fl[i-1] else dr[i-1]); st[i] = fl[i] if dr[i] > 0 else fu[i]
    return st, dr
PRE = {}
for tf in (1, 2, 4):
    d = bars(tf); day = pd.Series(d.index.date, index=d.index)
    v = d.Volume.where(d.Volume > 0); v = v.fillna(v.groupby(day).transform("median")).fillna(1.0)
    vw = (((d.High + d.Low + d.Close) / 3) * v).groupby(day).cumsum() / v.groupby(day).cumsum()
    PRE[tf] = (d, day.values, vw.values)
STC = {}
def sim(n, k, tf, tgt, per_day, cap, loss_cap=None):
    d, DY, VW = PRE[tf]
    if (n, k, tf) not in STC: STC[(n, k, tf)] = supertrend(d, n, k)
    ST, DR = STC[(n, k, tf)]; O, H, L, C = d.Open.values, d.High.values, d.Low.values, d.Close.values; T = d.index
    last = np.r_[DY[1:] != DY[:-1], True]  # last bar of the day
    out = []; pos = 0; cnt = {}; daypnl = {}
    for i in range(n + 1, len(C) - 1):
        if pos:
            ex = None
            if (pos > 0 and L[i] <= stop) or (pos < 0 and H[i] >= stop): ex = stop if ((pos > 0 and O[i] > stop) or (pos < 0 and O[i] < stop)) else O[i]
            elif target is not None and ((pos > 0 and H[i] >= target) or (pos < 0 and L[i] <= target)): ex = target
            elif last[i]: ex = C[i]
            if ex is not None:
                p = 0.01 * (pos * (ex - entry) - 6.4 - 1e-4 * entry); out.append((T[i], p)); daypnl[eday] = daypnl.get(eday, 0) + p; pos = 0
            else: stop = max(stop, ST[i]) if pos > 0 else min(stop, ST[i])
            continue
        if last[i] or DY[i] != DY[i + 1]: continue
        if per_day == 1 and cnt.get(DY[i], 0) >= 1: continue
        if loss_cap is not None and daypnl.get(DY[i], 0) <= -loss_cap: continue
        same = DY[i] == DY[i - 1]; sig = 0
        if same and DR[i] > 0 and C[i] > VW[i] and C[i-1] <= VW[i-1]: sig = 1
        elif same and DR[i] < 0 and C[i] < VW[i] and C[i-1] >= VW[i-1]: sig = -1
        if not sig: continue
        e = O[i + 1]; s = ST[i]; risk = abs(e - s)
        if (sig > 0 and s >= e) or (sig < 0 and s <= e): continue
        if cap and risk / e > cap: continue
        pos, entry, stop, eday = sig, e, s, DY[i]; target = e + sig * tgt * risk if tgt else None; cnt[DY[i]] = cnt.get(DY[i], 0) + 1
    s = pd.Series([p for _, p in out], index=pd.DatetimeIndex([t for t, _ in out])) if out else pd.Series(dtype=float)
    return s
CUT = pd.Timestamp("2025-11-27", tz="UTC")
def stats(s):
    if len(s) == 0: return 0.0, 0.0, 0
    e = s.cumsum(); return s.sum(), (e - e.cummax()).min(), len(s)
grid = list(itertools.product((7, 10, 14), (2, 3, 4), (1, 2, 4), (0, 1.5, 3), (1, 99), (0, 0.01, 0.02)))
rows = []
for g in grid:
    s = sim(*g); a, b_ = s[s.index < CUT], s[s.index >= CUT]; pa, da, na = stats(a); pb, db, nb = stats(b_)
    rows.append(dict(g=g, tune_pnl=pa, tune_dd=da, tune_n=na, test_pnl=pb, test_dd=db, test_n=nb, score=pa / abs(da) if da < 0 else (pa if pa > 0 else -1)))
df = pd.DataFrame(rows); base = (10, 3, 1, 0, 99, 0); B = df[df.g == base].iloc[0]; P = df.loc[df.score.idxmax()]
fmt = lambda r: f"tune ${r.tune_pnl:+.0f} / drop ${r.tune_dd:.0f} ({r.tune_n} trades) | test ${r.test_pnl:+.0f} / drop ${r.test_dd:.0f} ({r.test_n} trades)"
print("base", base, fmt(B)); print("tuned pick", P.g, fmt(P))
print(f"settings beating base on the test year (P&L): {(df.test_pnl > B.test_pnl).mean():.0%}; with a smaller test drop than base: {(df.test_dd > B.test_dd).mean():.0%}; median test P&L ${df.test_pnl.median():+.0f}")
top = df.sort_values("score", ascending=False).head(10)
print("top 10 by tuning score -> test:"); print(top[["g", "tune_pnl", "tune_dd", "test_pnl", "test_dd", "test_n"]].round(0).to_string(index=False))
for cap in (15, 30):
    s = sim(*P.g, loss_cap=cap); t = s[s.index >= CUT]; print(f"pick + daily loss cap ${cap}: test {stats(t)[0]:+.0f} / drop {stats(t)[1]:.0f}")
    s = sim(*base, loss_cap=cap); t = s[s.index >= CUT]; print(f"base + daily loss cap ${cap}: test {stats(t)[0]:+.0f} / drop {stats(t)[1]:.0f}; tune year {stats(s[s.index < CUT])[0]:+.0f} / {stats(s[s.index < CUT])[1]:.0f}")
df.to_csv("lab/batch25_results.csv", index=False)
