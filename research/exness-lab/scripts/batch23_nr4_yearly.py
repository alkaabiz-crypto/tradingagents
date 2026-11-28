"""Batch 23 (Hazza's request, rule unchanged from Batch 21b): BTC NR4 breakout year by year from the start of the data
(2014-09) to 2023, at 3 bp and 10 bp. Shown as % return on the position and as $ at today's 0.01-lot exposure ($584),
so early low-price years are comparable. Also worst drop per year and win rate."""
import numpy as np, pandas as pd
d = pd.read_csv("data/BTC-USD.csv", parse_dates=["Date"], index_col="Date").dropna(); c, h, l, o = d.Close, d.High, d.Low, d.Open
rg = h - l; nr = (rg <= rg.rolling(4).min()).shift().fillna(False); ph, pl = h.shift(), l.shift()
up, dn = nr & (h >= ph), nr & (l <= pl); eL = np.maximum(ph, o) * 1.0002; eS = np.minimum(pl, o) * 0.9998
g = pd.Series(np.where(up & dn, -(ph - pl) / ph, np.where(up, c / eL - 1, np.where(dn, eS / c - 1, 0.0))), index=c.index); tr = up | dn
print("| year | trades | win | % sum 3 bp | $ at $584 (3 bp) | $ at $584 (10 bp) | worst drop $ (3 bp) | buy & hold |")
for y in range(2014, 2027):
    x = g.loc[str(y)]; t = tr.loc[str(y)]; r3 = (x - t * 3e-4) * 584; r10 = (x - t * 10e-4) * 584; e = r3.cumsum()
    print(f"| {y} | {t.sum()} | {(x[t] > 0).mean():.0%} | {(x - t*3e-4).sum():+.1%} | {r3.sum():+.0f} | {r10.sum():+.0f} | {(e - e.cummax()).min():.0f} | {c.loc[str(y)].iloc[-1]/c.loc[str(y)].iloc[0]-1:+.0%} |")
x = (g - tr * 3e-4).loc[:"2023"] * 584; e = x.cumsum(); print(f"2014-2023 total ${x.sum():.0f}, worst drop ${(e-e.cummax()).min():.0f}, losing years {(x.groupby(x.index.year).sum() < 0).sum()}")
