#!/usr/bin/env python3
"""Study: Connors RSI(2) on a basket of markets (rules fixed before running).

famous_study.py showed RSI(2) timing is real on SPY (luck 99%) but invests
only ~25% of the time. Running it on many markets at once keeps more money at
work. Rule per fund (Connors & Alvarez 2008): buy at the close when price is
above its 200-day average and RSI(2) < 5; sell at the first close above the
5-day average. Each fund has a fixed 1/N slot of the account (no leverage).
Cost 0.05% per side (stress 0.20%). Benchmark: hold all N funds equally.

 1. Stock basket: SPY QQQ IWM DIA EFA EEM (6 slots)
 2. Mixed basket: SPY QQQ IWM EFA EEM TLT GLD XLE (8 slots, includes oil stocks)
 3. Oil basket: XLE USO BNO (3 slots), benchmark hold the three
 4. Sector basket: the 9 SPDR sectors (9 slots), benchmark hold all 9
"""
import datetime as dt
import os

import anomaly_study as A
from anomaly_study2 import common
from famous_study import rsi

HERE = os.path.dirname(os.path.abspath(__file__))


def rsi2_positions(c, slot):
    r2 = rsi(c)
    pos, held = [], 0.0
    for i in range(len(c)):
        pos.append(held)
        if i < 200:
            continue
        s200 = sum(c[i - 199:i + 1]) / 200
        s5 = sum(c[i - 4:i + 1]) / 5
        if held and c[i] > s5:
            held = 0.0
        elif not held and c[i] > s200 and r2[i] < 5:
            held = slot
    return pos


def basket(name, syms):
    data, dates, R = common(syms)
    n = len(syms)
    P = [rsi2_positions([data[s][d]["c"] for d in dates], 1 / n) for s in syms]
    bench = [sum(R[s][i] for s in syms) / n for i in range(len(dates))]
    e = A.evaluate(name, [R[s] for s in syms], P, bench, 0.0005, 252, 0.002, multi=True)
    invested = sum(sum(p[i] for p in P) for i in range(len(dates))) / len(dates)
    return e, dates[0], invested


def main():
    out = ["# Connors RSI(2) basket study", "",
           f"Run {dt.datetime.now(dt.timezone.utc):%Y-%m-%d %H:%M} UTC. Same pass rules (luck >= 95%, Sharpe above "
           "holding the same funds in both halves, positive after costs).", "",
           A.HEAD.replace("| Verdict |", "| Verdict | Avg % invested |").replace("|---|\n", "|---|---|\n", 0)
           .replace("|---|---|---|---|---|---|---|---|---|---|", "|---|---|---|---|---|---|---|---|---|---|---|")]
    for nm, syms in (("1. Stock basket (6)", ["SPY", "QQQ", "IWM", "DIA", "EFA", "EEM"]),
                     ("2. Mixed basket (8, incl. oil stocks XLE)", ["SPY", "QQQ", "IWM", "EFA", "EEM", "TLT", "GLD", "XLE"]),
                     ("3. Oil basket (XLE, USO, BNO)", ["XLE", "USO", "BNO"]),
                     ("4. Sector basket (9 SPDR sectors)", ["XLB", "XLE", "XLF", "XLI", "XLK", "XLP", "XLU", "XLV", "XLY"])):
        e, d0, inv = basket(nm, syms)
        out.append(A.row(e).replace(f"| {e['name']} |", f"| {e['name']} (since {d0}) |") + f" {inv * 100:.0f}% |")
    text = "\n".join(out) + "\n"
    with open(os.path.join(HERE, "rsi2_basket_results.md"), "w") as fh:
        fh.write(text)
    print(text)


if __name__ == "__main__":
    main()
