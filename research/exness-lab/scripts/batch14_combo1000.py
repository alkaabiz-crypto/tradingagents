"""Batch 14, pre-registered 2026-11-26 before running. $1,000 account, fixed minimum lots, swap-free.
Plans: C = USTEC overnight above 200-day at 0.05 lot (3.5 pt round trip); E2 = BTC Williams weekdays + 12m momentum
at 0.01 lot (10 bp + 2 bp, conservative); E1 = same without the filter. Combos C+E1, C+E2.
Report P&L and worst $ drop for 2020-23, 2024-now and 2025-now, worst day, and the correlation of daily P&L.
No new strategy trials (sizing/combination only).
"""
import numpy as np, pandas as pd
qqq = pd.read_csv("data/QQQ.csv", parse_dates=["Date"], index_col="Date").dropna()
btc = pd.read_csv("data/BTC-USD.csv", parse_dates=["Date"], index_col="Date").dropna()
c, o = qqq.Close * 41, qqq.Open * 41; m = (qqq.Close > qqq.Close.rolling(200).mean()).shift().fillna(False)
C = (0.05 * ((o - c.shift()) - 3.5)).where(m, 0).fillna(0)
b = btc; R = (b.High - b.Low).shift(); t = b.Open + 0.5 * R; wd = b.index.dayofweek < 5
mo_ = pd.Series(b.index.to_period("M"), index=b.index); me = mo_ != mo_.shift(-1)
mom = (pd.Series(np.where(me, (b.Close / b.Close.shift(365) - 1) > 0, np.nan), index=b.index).ffill().fillna(0) > 0).shift().fillna(False)
px = np.maximum(t, b.Open)
def bk(mask): hit = (b.High >= t) & wd & mask; return pd.Series(np.where(hit, 0.01 * (b.Close - px) - 0.01 * px * 12e-4, 0.0), index=b.index).fillna(0)
E1, E2 = bk(pd.Series(True, index=b.index)), bk(mom)
P = {"C USTEC overnight": [C], "E1 BTC breakout": [E1], "E2 BTC breakout + momentum": [E2], "C + E1": [C, E1], "C + E2": [C, E2]}
def comb(parts): return pd.concat(parts, axis=1).fillna(0).sum(axis=1)
def stat(x, a, z=None):
    x = x.loc[a:z] if z else x.loc[a:]; e = x.cumsum(); return f"{x.sum():+.0f} / {(e - e.cummax()).min():.0f}"
print("| plan | 2020-23 $ / worst drop | 2024-now | 2025-now | worst day 2020-now |")
for nm, parts in P.items():
    x = comb(parts); print(f"| {nm} | {stat(x,'2020','2023')} | {stat(x,'2024')} | {stat(x,'2025')} | {x.loc['2020':].min():.0f} |")
j = pd.concat([C, E1], axis=1).dropna().loc["2020":]; j = j[(j != 0).any(axis=1)]
print("correlation of daily P&L (days either traded), C vs E1:", round(j.corr().iloc[0, 1], 2))
