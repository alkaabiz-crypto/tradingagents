"""Study 3 (pre-registered 2026-11-24, written before running; after studies 1-2 found 0 of 11).
S12 energy residual momentum (Blitz, Huij & Martens 2011 idea applied to one sector, the oil
brain's idea-queue item 5). At each month-end: OLS of XLE daily returns on SPY and USO daily
returns over the past 252 days (in-sample residuals, as BHM). Score = sum of residuals over days
t-251..t-21 (12-1, skip the last month) / their std. Hold the hedged portfolio
s * (XLE - b_SPY * SPY - b_USO * USO) with s = sign(score), for one month. 5 bp per unit of
turnover on all three legs (hedge-ratio changes included). Start 2007-06-01 (USO + 252 days).
Benchmark EW sectors (as studies 1-2). Placebo: whole weight matrix time-shifted.
"""
import numpy as np, pandas as pd
from lib import *

syms = SECT + ["SPY", "USO"]
px = panel(syms).loc["1998-12-01":]
ret = px.pct_change(fill_method=None)
idx = px.index; me = period_ends(idx, "M")
alive = px[SECT].notna().cumsum() >= 300
bench = ret[SECT].where(alive).mean(axis=1)
d = ret[["XLE", "SPY", "USO"]].dropna()
W = pd.DataFrame(0.0, index=me, columns=syms)
for t in me:
    win = d.loc[:t].iloc[-252:]
    if len(win) < 252 or win.index[-1] != t:
        continue
    X = np.column_stack([np.ones(252), win["SPY"], win["USO"]]); y = win["XLE"].values
    b = np.linalg.lstsq(X, y, rcond=None)[0]
    e = y - X @ b
    f = e[:-21]
    s = np.sign(f.sum() / f.std(ddof=1))
    W.loc[t, ["XLE", "SPY", "USO"]] = [s, -s * b[1], -s * b[2]]
w = hold(W, idx)
o, r = evaluate_w("S12 XLE residual mom vs SPY+USO", w, ret.fillna(0), bench, start="2007-06-01")
show([o]); print(W.loc["2019-10":"2020-06", ["XLE","SPY","USO"]].round(2))
print("share of months long hedged XLE:", round((W.loc["2007-06":, "XLE"] > 0).mean(), 2))
print("by year %:", (r.groupby(r.index.year).sum() * 100).round(1).to_dict())
pd.DataFrame([o]).to_csv("study3_results.csv", index=False)
