"""Batch 15, pre-registered 2026-11-26 before running. Variants of the USTEC overnight hold (0.05 lot, 3.5 pt RT,
NOTE added before the 2nd run: fixed 3.5 pts overcharges early years (QQQ x 41 was ~1,600 in 2000), so also run with 1.4 bp (= 3.5 pts at today's ~25,000).
USTEC ~ QQQ x 41, swap-free). Base: hold close -> next open only when the close is above the 200-day.
a) skip Friday nights (weekend gap)  b) Friday nights only  c) skip when VIX closed above 30  d) skip when VIX < 15
e) 50-day filter instead of 200  f) 100-day filter  g) no filter. 7 new trials (~195 cumulative).
Report Sharpe 2000-13 / 2014-19 / 2020-23 / 2024-now and $ + worst drop 2024-now and 2025-now. A variant must beat the
base in at least 3 of the 4 periods to be preferred.
"""
import numpy as np, pandas as pd
q = pd.read_csv("data/QQQ.csv", parse_dates=["Date"], index_col="Date").dropna()
v = pd.read_csv("data/VIX.csv", parse_dates=["Date"], index_col="Date").Close.reindex(q.index).ffill()
c, o = q.Close * 41, q.Open * 41; import sys; COST = 3.5 if sys.argv[1] == "pts" else 1.4e-4 * c.shift() * 1.0
g = (0.05 * ((o - c.shift()) - COST)).fillna(0)
def sma(n): return (q.Close > q.Close.rolling(n).mean()).shift().fillna(False)
prev_dow = pd.Series(q.index.dayofweek, index=q.index).shift(); fri = prev_dow == 4; vx = v.shift()
B = sma(200)
V = {"base (200-day)": B, "a skip Fridays": B & ~fri, "b Fridays only": B & fri, "c skip VIX > 30": B & ~(vx > 30),
     "d skip VIX < 15": B & ~(vx < 15), "e 50-day": sma(50), "f 100-day": sma(100), "g no filter": pd.Series(True, index=q.index)}
def sh(x): return x.mean() / x.std() * np.sqrt(252) if x.std() > 0 else np.nan
def st(x): e = x.cumsum(); return f"{x.sum():+.0f} / {(e - e.cummax()).min():.0f}"
print("| variant | 2000-13 | 2014-19 | 2020-23 | 2024-now | $ 2024-now / drop | $ 2025-now / drop | nights/yr |")
for nm, mk in V.items():
    x = g.where(mk, 0)
    s = [sh(x.loc[a:b]) for a, b in (("2000", "2013"), ("2014", "2019"), ("2020", "2023"), ("2024", "2026"))]
    print(f"| {nm} | " + " | ".join(f"{z:.2f}" for z in s) + f" | {st(x.loc['2024':])} | {st(x.loc['2025':])} | {mk.loc['2014':].mean()*252:.0f} |")
