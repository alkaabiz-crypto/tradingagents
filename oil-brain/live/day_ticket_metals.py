"""Unseen-market check of the v3 lead (pre-registered 2026-11-26, before any run; the user said "ok do that").
Lead from day_ticket_v3.py: FUTURES + IBS direction, stop 0.5 ATR, no target, out at the close (+8.5 bp, t 2.5,
mostly silver). ONE fixed rule, no tuning:
  signal at day i's close: IBS < 0.2 -> LONG, IBS > 0.8 -> SHORT, else no trade; entry at day i+1's open;
  stop 0.5 x ATR14; out at that day's close; both touched = stop; 2 bp a side (futures).
Unseen markets: GC=F gold, HG=F copper, PL=F platinum, PA=F palladium. Period 2014+ (as v3), split in half by date.
PASS (fixed, one hypothesis): pooled net mean > 0 in both halves and at 2x cost, pooled t >= 2, random-direction
placebo (same days, same exit, 2000 runs, seed 81) p <= 0.05, and >= 3 of the 4 metals positive.
If it passes: a paper sleeve proposal only (silver + the metals), never real money. Research, not financial advice.
    python3 oil-brain/live/day_ticket_metals.py
"""
import os, sys
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from day_ticket_v2 import gross, daily, tstat
from day_ticket_v3 import panel

METALS = ["GC=F", "HG=F", "PL=F", "PA=F"]; COST = 2e-4


def main():
    P = panel(METALS, np.random.default_rng(80)); s = P["s_IBS"].values; on = s != 0; P = P[on]; s = s[on]
    O, H, L, C, a = (P[c].values for c in "OHLCa")
    gl, gs = gross(O, H, L, C, a, np.ones(len(P)), 0.5, None), gross(O, H, L, C, a, -np.ones(len(P)), 0.5, None)
    g = np.where(s > 0, gl, gs); net, net2 = daily(P.index, g - 2 * COST), daily(P.index, g - 4 * COST)
    mid = net.index[len(net) // 2]
    rng = np.random.default_rng(81)
    sims = np.array([daily(P.index, np.where(rng.random(len(g)) < .5, gl, gs) - 2 * COST).mean() for _ in range(2000)])
    p = float((sims >= net.mean()).mean())
    per = {}
    for sym in METALS:
        m = (P.sym == sym).values; r = daily(P.index[m], g[m] - 2 * COST)
        lg = (g[m & (s > 0)] - 2 * COST).mean() * 1e4; sh = (g[m & (s < 0)] - 2 * COST).mean() * 1e4
        per[sym] = r.mean() * 1e4
        print(f"{sym:5s} trades {m.sum():5d}  net {r.mean() * 1e4:+6.1f} bp  t {tstat(r):5.2f}  long {lg:+6.1f}  short {sh:+6.1f}")
    h1, h2 = net[net.index < mid].mean() * 1e4, net[net.index >= mid].mean() * 1e4; t = tstat(net)
    ok = h1 > 0 and h2 > 0 and net2.mean() > 0 and t >= 2 and p <= 0.05 and sum(v > 0 for v in per.values()) >= 3
    print(f"\nPOOLED trade-days {len(net)}  net {net.mean() * 1e4:+.1f} bp  t {t:.2f}  1st half {h1:+.1f}  2nd half {h2:+.1f}  "
          f"2x cost {net2.mean() * 1e4:+.1f}  win {(g - 2 * COST > 0).mean():.0%}  placebo p {p:.3f}")
    print("VERDICT:", "PASS - propose a paper sleeve" if ok else "FAIL - the silver lead does not carry to other metals")


if __name__ == "__main__":
    main()
