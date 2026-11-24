"""CFD cost stress for the combo survivors (2026-11-24). Same systems as combo_daily.py, plus an overnight
financing charge per calendar day held (Exness swap; real values in MT5 > contract specification).
Spreads: Exness quotes (third-party lists, 2026): XAUUSD ~$0.20 (~0.6 bp), BTCUSD ~$10-30 (~2-5 bp), USOIL ~$0.03-0.05
(~5 bp). We charge the backtest's 5 bp (10 bp BTC) per side, which is at or above those.
Financing scenarios, % a year of the position value, charged per calendar day held:
  0% (swap-free account), 3.5%, 7%, 15% (gold, oil);  0%, 10%, 20%, 30% (BTC, crypto CFD swaps are high).
Reports post-start average R and t (2014+; BTC 2019+)."""
import numpy as np, pandas as pd, os
src = open("combo_daily.py").read()
HERE = os.path.dirname(os.path.abspath(__file__)); OB = os.path.dirname(HERE); SRC = {"BTC-USD": "brains/crypto/data/BTC-USD.csv"}
exec(src[src.index("def load"):src.index("rows = []; rng")])   # load, rsi, signals, run, tt
def run_days(b, sig, reg, ex, cost, fin):
    t = run(b, sig, reg, ex, cost)
    if t.empty: return t
    # rebuild holding days: re-run exits to get the exit dates
    O, H, L, C = b.Open.values, b.High.values, b.Low.values, b.Close.values
    tr = pd.concat([b.High - b.Low, (b.High - b.Close.shift()).abs(), (b.Low - b.Close.shift()).abs()], axis=1).max(axis=1)
    A = tr.rolling(20).mean().values
    k0, trail_k, tgt, maxh = {"T1": (2, 3, None, 10**9), "T2": (2, None, 4, 30), "T3": (3, 3, None, 60)}[ex]
    days, idx = [], {d: i for i, d in enumerate(b.index)}
    for d0 in t.t:
        i = idx[d0] - 1; side = sig[i]
        e = O[i + 1]; risk = k0 * A[i]; stop = e - side * risk; target = e + side * tgt * risk if tgt else None
        j = i + 1
        while j < len(b):
            if (side > 0 and L[j] <= stop) or (side < 0 and H[j] >= stop): break
            if target is not None and ((side > 0 and H[j] >= target) or (side < 0 and L[j] <= target)): break
            if trail_k: stop = max(stop, C[j] - trail_k * A[j]) if side > 0 else min(stop, C[j] + trail_k * A[j])
            if j - i >= maxh: break
            j += 1
        j = min(j, len(b) - 1)
        days.append((b.index[j] - b.index[i + 1]).days + 1); 
        t.loc[t.t == d0, "risk_pct"] = risk / e
    t["days"] = days
    t["R_fin"] = t.R - fin / 365 * t.days / t.risk_pct
    return t
systems = [("BTC-USD", "R2", "D1", "T2", 10, [0, .10, .20, .30], "2019-01-01"),
           ("BTC-USD", "R2", "D2", "T2", 10, [0, .10, .20, .30], "2019-01-01"),
           ("GLD", "R2L", "D4", "T1", 5, [0, .035, .07, .15], "2014-01-01"),
           ("USO", "R2", "D2", "T1", 5, [0, .035, .07, .15], "2014-01-01")]
for sym, rk, ek, xk, cost, fins, start in systems:
    b = load(sym); c = b.Close; s200 = np.sign(c - c.rolling(200).mean()).values
    rg = {"R2": s200, "R2L": np.where(s200 > 0, 1.0, np.where(np.isnan(s200), np.nan, 2.0))}[rk]
    sg = signals(b)[ek]
    line = []
    for fin in fins:
        t = run_days(b, sg, rg, xk, cost, fin); x = t[t.t >= start]
        line.append(f"{fin:>4.0%}/yr: {x.R_fin.mean():+.2f}R t {tt(x.R_fin):.2f}")
    print(f"{sym} {rk} {ek} {xk}: {len(x)} trades, avg hold {x.days.mean():.0f} days, avg stop {x.risk_pct.mean():.1%} | " + " | ".join(line))
