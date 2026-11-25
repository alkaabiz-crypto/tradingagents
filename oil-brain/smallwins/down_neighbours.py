"""Neighbour check for '3 down closes' (pre-registered 2026-11-25, before running). After the C4 seed fix,
smallwins.py passes SPY and QQQ '3 down closes -> buy at the close, sell at the first up close or after 5 days'
(placebo p 0.005). Neighbours: N down closes in a row in {2, 3, 4} x max days in {3, 5, 7}, on SPY, QQQ, IWM, DIA
(IWM/DIA unseen for this rule). Fixed bar: a market HOLDS if >= 70% of its 9 neighbours have post-2014 average > 0 at
2x cost (10 bp a side) and t >= 2. Research, not financial advice.
"""
import os, sys, itertools
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import smallwins as W

rows = []
for sym in ["SPY", "QQQ", "IWM", "DIA"]:
    b = W.load(sym); c = b.Close.values; n = len(c); ok = b.Close.rolling(200).mean().notna().values
    dn = np.r_[False, c[1:] < c[:-1]]
    for N, md in itertools.product([2, 3, 4], [3, 5, 7]):
        run = pd.Series(dn).rolling(N).sum().values == N; out = []; k = 0
        while k < n - 1:
            if ok[k] and run[k]:
                j = next((j for j in range(k + 1, min(k + 1 + md, n)) if c[j] > c[j - 1]), min(k + md, n - 1))
                out.append((b.index[k], c[j] / c[k] - 1)); k = j
            else:
                k += 1
        r = np.array([g for d, g in out if d >= pd.Timestamp("2014-01-01")]) - 4 * W.COST
        t = r.mean() / (r.std(ddof=1) / np.sqrt(len(r)))
        rows.append(dict(sym=sym, N=N, maxd=md, n=len(r), bp_2x=r.mean() * 1e4, t=t, ok=(r.mean() > 0) & (t >= 2)))
df = pd.DataFrame(rows); df.to_csv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "down_neighbours.csv"), index=False)
g = df.groupby("sym").agg(share_ok=("ok", "mean"), median_bp_2x=("bp_2x", "median"), median_t=("t", "median"), trades=("n", "median"))
g["HOLDS"] = g.share_ok >= 0.7
print(g.round(2).to_string())
