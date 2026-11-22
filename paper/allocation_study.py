#!/usr/bin/env python3
"""Study: portfolios like risk parity (rules fixed before running).

Benchmark: 60% SPY / 40% TLT. Reference: account #12 (risk parity SPY/TLT/GLD).
Weights are held constant between monthly rebalances (approximation: daily
returns use the target weights). Costs 0.05% per side on weight changes.

Fixed-mix portfolios (no timing, so no luck check; they pass if Sharpe beats
60/40 in both halves):
 49. Permanent Portfolio (Harry Browne): 25% SPY, TLT, GLD, SHY.
 50. All Weather (Dalio, retail version): 30% SPY, 40% TLT, 15% IEF,
     7.5% GLD, 7.5% DBC.
 51. Golden Butterfly: 20% each SPY, IWN (small-cap value), TLT, SHY, GLD.
 52. Equal thirds SPY/TLT/GLD (shows how much #12's risk weighting adds).
Dynamic portfolios (full pass rules incl. luck check):
 53. Risk parity, 5 assets: SPY, EFA, TLT, GLD, DBC by 1 / 3-month volatility.
 54. Minimum variance SPY/TLT/GLD (3-month covariance, long only, 5% steps).
 55. Equal risk contribution SPY/TLT/GLD (uses correlations, 3-month window).
 56. Risk parity #12 + portfolio volatility target 8% (Harvey et al. 2018):
     scale the whole mix by min(1, 8% / its 3-month volatility), rest cash.
 57. Vigilant Asset Allocation G4 (Keller & Keuning 2017): risky SPY, EFA,
     EEM, AGG; safe LQD, IEF, SHY; 13612W momentum; all risky positive ->
     best risky, else best safe; monthly.
"""
import datetime as dt
import itertools
import math
import os
import statistics as st

import anomaly_study as A
from anomaly_study2 import common
from anomaly_study5 import monthly_weights

HERE = os.path.dirname(os.path.abspath(__file__))
COST = 0.0005


def cov(R, syms, i, n=63):
    m = {s: st.mean(R[s][i - n + 1:i + 1]) for s in syms}
    return {(a, b): sum((R[a][k] - m[a]) * (R[b][k] - m[b]) for k in range(i - n + 1, i + 1)) / n
            for a in syms for b in syms}


def port_var(w, C, syms):
    return sum(w[a] * w[b] * C[(a, b)] for a in syms for b in syms)


def evaluate_weights(name, R, syms, W, bench, static=False):
    P = [[w.get(s, 0.0) for w in W] for s in syms]
    e = A.evaluate(name, [R[s] for s in syms], P, bench, COST, 252, 0.002, multi=True)
    if static:
        e["luck"] = None
        e["passed"] = e["h1"]["sharpe"] > e["b1"]["sharpe"] and e["h2"]["sharpe"] > e["b2"]["sharpe"] and e["all"]["cagr"] > 0
    return e


def main():
    syms = ["SPY", "TLT", "IEF", "GLD", "DBC", "SHY", "IWN", "EFA", "EEM", "AGG", "LQD"]
    data, dates, R = common(syms)
    n = len(dates)
    bench = [0.6 * R["SPY"][i] + 0.4 * R["TLT"][i] for i in range(n)]
    res = []

    def static(w):
        return [dict(w) for _ in range(n)]
    for nm, w in (("49. Permanent Portfolio", {"SPY": .25, "TLT": .25, "GLD": .25, "SHY": .25}),
                  ("50. All Weather (retail)", {"SPY": .30, "TLT": .40, "IEF": .15, "GLD": .075, "DBC": .075}),
                  ("51. Golden Butterfly", {"SPY": .2, "IWN": .2, "TLT": .2, "SHY": .2, "GLD": .2}),
                  ("52. Equal thirds SPY/TLT/GLD", {"SPY": 1 / 3, "TLT": 1 / 3, "GLD": 1 / 3})):
        res.append(evaluate_weights(nm, R, list(w), static(w), bench, static=True))

    three = ["SPY", "TLT", "GLD"]

    def ivol(i, ss=three):
        if i < 63:
            return None
        inv = {s: 1 / st.pstdev(R[s][i - 62:i + 1]) for s in ss}
        t = sum(inv.values())
        return {s: inv[s] / t for s in ss}
    res.append(evaluate_weights("Reference: risk parity #12 (SPY/TLT/GLD)", R, three, monthly_weights(dates, ivol), bench))
    five = ["SPY", "EFA", "TLT", "GLD", "DBC"]
    res.append(evaluate_weights("53. Risk parity, 5 assets", R, five,
                                monthly_weights(dates, lambda i: ivol(i, five)), bench))
    grid = [w for w in itertools.product(range(0, 21), repeat=2) if w[0] + w[1] <= 20]

    def minvar(i):
        if i < 63:
            return None
        C = cov(R, three, i)
        best = min(grid, key=lambda g: port_var({"SPY": g[0] / 20, "TLT": g[1] / 20, "GLD": 1 - (g[0] + g[1]) / 20}, C, three))
        return {"SPY": best[0] / 20, "TLT": best[1] / 20, "GLD": 1 - (best[0] + best[1]) / 20}
    res.append(evaluate_weights("54. Minimum variance SPY/TLT/GLD", R, three, monthly_weights(dates, minvar), bench))

    def erc(i):
        if i < 63:
            return None
        C = cov(R, three, i)
        w = {s: 1 / 3 for s in three}
        for _ in range(200):                       # simple fixed-point iteration
            mrc = {a: sum(C[(a, b)] * w[b] for b in three) for a in three}
            rc = {a: w[a] * mrc[a] for a in three}
            tot = sum(rc.values())
            w = {a: w[a] * ((tot / 3) / rc[a]) ** 0.5 if rc[a] > 0 else w[a] for a in three}
            sw = sum(w.values())
            w = {a: w[a] / sw for a in three}
        return w
    res.append(evaluate_weights("55. Equal risk contribution SPY/TLT/GLD", R, three, monthly_weights(dates, erc), bench))

    def rp_vt(i):
        w = ivol(i)
        if w is None:
            return None
        pr = [sum(w[s] * R[s][k] for s in three) for k in range(i - 62, i + 1)]
        v = st.pstdev(pr) * math.sqrt(252)
        k = min(1.0, 0.08 / v) if v else 1.0
        return {s: w[s] * k for s in three}
    res.append(evaluate_weights("56. Risk parity #12 + 8% volatility target", R, three, monthly_weights(dates, rp_vt), bench))
    risky, safe = ["SPY", "EFA", "EEM", "AGG"], ["LQD", "IEF", "SHY"]
    me = A.month_ends(dates)

    def vaa(i):
        k = me.index(i)
        if k < 12:
            return None
        def m13612(s):
            p0 = data[s][dates[i]]["c"]
            r = lambda j: p0 / data[s][dates[me[k - j]]]["c"] - 1
            return 12 * r(1) + 4 * r(3) + 2 * r(6) + r(12)
        sc = {s: m13612(s) for s in risky + safe}
        if all(sc[s] > 0 for s in risky):
            return {max(risky, key=sc.get): 1.0}
        return {max(safe, key=sc.get): 1.0}
    res.append(evaluate_weights("57. Vigilant Asset Allocation G4", R, risky + safe, monthly_weights(dates, vaa), bench))

    out = ["# Risk-parity-like portfolio study", "",
           f"Run {dt.datetime.now(dt.timezone.utc):%Y-%m-%d %H:%M} UTC, common history {dates[0]} to {dates[-1]}. "
           "Benchmark 60% SPY / 40% TLT. Fixed mixes have no timing, so they need only beat 60/40 in both halves; "
           "dynamic ones also need the luck check >= 95%.", "", A.HEAD]
    for e in res:
        r = A.row(e)
        if e["luck"] is None:
            r = r.replace("| None |", "| n/a |").replace("| -% |", "| n/a |")
        out.append(r)
    text = "\n".join(out) + "\n"
    with open(os.path.join(HERE, "allocation_study_results.md"), "w") as fh:
        fh.write(text)
    print(text)


if __name__ == "__main__":
    main()
