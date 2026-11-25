"""Neighbour check for the bullish harami (pre-registered 2026-11-25, before running).
Survivor: BULL_HARAMI on QQQ/SPY, hold 5 days, entry next open. Neighbours: first-bar 'big' body >= {0.5, 0.6, 0.7}
of its range x second body < {0.4, 0.5, 0.6} of the first body x trend look-back {3, 5, 10} days x hold {3, 5};
markets SPY, QQQ, IWM, DIA (+ the oil and metal ETFs for the record). Fixed bar: a market HOLDS if >= 70% of the
54 neighbours have post-2014 excess > 0 at 2x cost (10 bp a side) and t >= 2. Research, not financial advice.
"""
import sys, os, itertools
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import candle_study as C

rows = []
for sym in ["SPY", "QQQ", "IWM", "DIA", "USO", "XLE", "GLD"]:
    b = C.load(sym); O, H, L, Cl = b.Open, b.High, b.Low, b.Close
    body, rng = (Cl - O).abs(), H - L
    for big, small, lb, h in itertools.product([0.5, 0.6, 0.7], [0.4, 0.5, 0.6], [3, 5, 10], [3, 5]):
        down = Cl.shift(1) < Cl.shift(1 + lb)
        f = down & (Cl.shift(1) < O.shift(1)) & (body.shift(1) >= big * rng.shift(1)) & (Cl > O) & (O > Cl.shift(1)) \
            & (Cl < O.shift(1)) & (body < small * body.shift(1))
        r = C.fwd(b, h); post = r[r.index >= "2014-01-01"].dropna(); ev = post[f.reindex(post.index).fillna(False)]
        x = ev - post.mean() - 4 * 5e-4
        t = x.mean() / (x.std(ddof=1) / np.sqrt(len(x))) if len(x) > 2 else np.nan
        rows.append(dict(sym=sym, big=big, small=small, lookback=lb, hold=h, n=len(ev), excess_bp_2x=x.mean() * 1e4, t=t))
df = pd.DataFrame(rows); df["ok"] = (df.excess_bp_2x > 0) & (df.t >= 2)
df.to_csv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "harami_neighbours.csv"), index=False)
g = df.groupby("sym").agg(share_ok=("ok", "mean"), share_positive=("excess_bp_2x", lambda s: (s > 0).mean()),
                          median_bp_2x=("excess_bp_2x", "median"), median_t=("t", "median"), median_n=("n", "median"))
g["HOLDS"] = g.share_ok >= 0.7
print(g.round(2).to_string())
