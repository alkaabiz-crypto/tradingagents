"""Study 3 (pre-registered 2026-11-24, before running): the high-volume return premium
(Gervais, Kaniel & Mingelgrin 2001 JF): stocks whose trading volume jumps (vs the past 50 days) earn higher
returns over the next month (visibility -> more investors). Applied to the 9 SPDR sector ETFs (1999-).
Volume shock = mean volume of the last 5 days / mean volume of the 45 days before (a 50-day window, as GKM).
Month-end rebalance, hold one month, 5 bp per turnover. Start 2000-03 (window filled).
 G1 long the 3 sectors with the highest shock, short the 3 lowest (1/3 each side, dollar neutral).
 G2 long-only top 3 (1/3 each).
Benchmark for both: equal-weight 9 sectors (strict for G1, which is market neutral).
GKM condition on a small concurrent return; with 9 ETFs we do not filter (too few names).
"""
import numpy as np, pandas as pd
from lib import ld, table, port_eval
S = ["XLE", "XLF", "XLK", "XLU", "XLV", "XLY", "XLP", "XLI", "XLB"]
px = pd.DataFrame({s: ld(s) for s in S}); vol = pd.DataFrame({s: ld(s, "Volume") for s in S})
ret = px.pct_change()
shock = vol.rolling(5).mean() / vol.shift(5).rolling(45).mean()
me = px.index.to_series().groupby(px.index.to_period("M")).last().values
rk = shock.loc[me].rank(axis=1)
top = (rk >= 7).astype(float) / 3; bot = (rk <= 3).astype(float) / 3
W1 = (top - bot).reindex(px.index).ffill().fillna(0); W2 = top.reindex(px.index).ffill().fillna(0)
bench = ret.mean(axis=1)
rows = [port_eval("G1 sectors long high / short low volume shock", W1, ret, bench, "2000-03-01"),
        port_eval("G2 sectors long top-3 volume shock", W2, ret, bench, "2000-03-01")]
print(table(rows))
print("latest top-3:", list(rk.iloc[-1][rk.iloc[-1] >= 7].index), "bottom-3:", list(rk.iloc[-1][rk.iloc[-1] <= 3].index))
