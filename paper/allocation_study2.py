#!/usr/bin/env python3
"""Study batch 8: macro warning signals and adding BTC to safe portfolios.
Rules fixed before running; same pass rules (luck check >= 95% for timing
rules, Sharpe above the benchmark in both halves, positive after costs).

Macro signals (benchmark: hold SPY):
 58. Yield-curve filter (Estrella & Mishkin 1998): hold SPY while the 10-year
     Treasury yield (^TNX) is above the 3-month yield (^IRX); when the curve
     inverts hold IEF (7-10y Treasuries) instead.
 59. Credit risk-on filter: hold SPY while high-yield bonds are beating
     Treasuries (HYG/IEF above its 50-day average); else IEF.
 60. Gold with a real-yield signal: hold GLD while inflation-protected bonds
     (TIP) are above their 50-day average (falling real yields); else cash.
     Benchmark: hold GLD.
 61. Sharpe momentum rotation: each month hold whichever of SPY/TLT/GLD had
     the best 3-month return divided by volatility. Benchmark: 60/40.
Adding BTC (since 2014; benchmark 60/40; #12 risk parity shown for reference):
 62. Risk parity SPY/TLT/GLD/BTC (1 / 3-month volatility, monthly).
 63. Minimum variance SPY/TLT/GLD/BTC (BTC capped at 10%).
 64. Equal thirds SPY/TLT/GLD plus a fixed 5% BTC (fixed mix).
"""
import datetime as dt
import itertools
import math
import os
import statistics as st

import anomaly_study as A
from anomaly_study2 import common
from anomaly_study5 import monthly_weights
from allocation_study import cov, port_var, evaluate_weights

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    res = []
    data, dates, R = common(["SPY", "IEF", "^TNX", "^IRX"])
    P = {"SPY": [], "IEF": []}
    cur = "SPY"
    for d in dates:
        P["SPY"].append(1.0 if cur == "SPY" else 0.0)
        P["IEF"].append(1.0 if cur == "IEF" else 0.0)
        cur = "SPY" if data["^TNX"][d]["c"] > data["^IRX"][d]["c"] else "IEF"
    res.append((f"since {dates[0]}", A.evaluate("58. Yield-curve filter: SPY, IEF when inverted (vs SPY)",
                [R["SPY"], R["IEF"]], [P["SPY"], P["IEF"]], R["SPY"], 0.0005, 252, 0.002, multi=True)))
    data, dates, R = common(["SPY", "IEF", "HYG"])
    ratio = [data["HYG"][d]["c"] / data["IEF"][d]["c"] for d in dates]
    P = {"SPY": [], "IEF": []}
    cur = None
    for i, d in enumerate(dates):
        P["SPY"].append(1.0 if cur == "SPY" else 0.0)
        P["IEF"].append(1.0 if cur == "IEF" else 0.0)
        if i >= 50:
            cur = "SPY" if ratio[i] > sum(ratio[i - 49:i + 1]) / 50 else "IEF"
    res.append((f"since {dates[0]}", A.evaluate("59. Credit risk-on filter: SPY, IEF when credit weakens (vs SPY)",
                [R["SPY"], R["IEF"]], [P["SPY"], P["IEF"]], R["SPY"], 0.0005, 252, 0.002, multi=True)))
    data, dates, R = common(["GLD", "TIP"])
    tc = [data["TIP"][d]["c"] for d in dates]
    pos = [0.0]
    for i in range(1, len(dates)):
        pos.append(1.0 if i - 1 >= 50 and tc[i - 1] > sum(tc[i - 50:i]) / 50 else 0.0)
    res.append((f"since {dates[0]}", A.evaluate("60. Gold only while TIP is above its 50-day average (vs GLD)",
                R["GLD"], pos, R["GLD"], 0.0005, 252, 0.002)))
    three = ["SPY", "TLT", "GLD"]
    data, dates, R = common(three)
    bench = [0.6 * R["SPY"][i] + 0.4 * R["TLT"][i] for i in range(len(dates))]

    def sharpe_mom(i):
        if i < 63:
            return None
        sc = {s: (data[s][dates[i]]["c"] / data[s][dates[i - 63]]["c"] - 1) / st.pstdev(R[s][i - 62:i + 1]) for s in three}
        return {max(sc, key=sc.get): 1.0}
    e = evaluate_weights("61. Sharpe momentum rotation SPY/TLT/GLD (vs 60/40)", R, three, monthly_weights(dates, sharpe_mom), bench)
    res.append((f"since {dates[0]}", e))

    four = ["SPY", "TLT", "GLD", "BTC-USD"]
    data, dates, R = common(four, int(dt.datetime(2014, 9, 17, tzinfo=dt.timezone.utc).timestamp()))
    bench = [0.6 * R["SPY"][i] + 0.4 * R["TLT"][i] for i in range(len(dates))]

    def ivol(i, ss):
        if i < 63:
            return None
        inv = {s: 1 / st.pstdev(R[s][i - 62:i + 1]) for s in ss}
        t = sum(inv.values())
        return {s: inv[s] / t for s in ss}
    res.append((f"since {dates[0]}", evaluate_weights("Reference: risk parity #12 over the same years", R, three,
                monthly_weights(dates, lambda i: ivol(i, three)), bench)))
    res.append((f"since {dates[0]}", evaluate_weights("62. Risk parity SPY/TLT/GLD/BTC (vs 60/40)", R, four,
                monthly_weights(dates, lambda i: ivol(i, four)), bench)))
    grid = [g for g in itertools.product(range(21), repeat=3) if sum(g) <= 20]

    def mv4(i):
        if i < 63:
            return None
        C = cov(R, four, i)
        best = None
        for g in grid:
            w = {"SPY": g[0] / 20, "TLT": g[1] / 20, "GLD": g[2] / 20}
            w["BTC-USD"] = 1 - sum(g) / 20
            if w["BTC-USD"] > 0.10 + 1e-9:
                continue
            v = port_var(w, C, four)
            if best is None or v < best[0]:
                best = (v, w)
        return best[1]
    res.append((f"since {dates[0]}", evaluate_weights("63. Minimum variance SPY/TLT/GLD/BTC, BTC max 10% (vs 60/40)",
                R, four, monthly_weights(dates, mv4), bench)))
    w = {"SPY": .95 / 3, "TLT": .95 / 3, "GLD": .95 / 3, "BTC-USD": .05}
    res.append((f"since {dates[0]}", evaluate_weights("64. Equal thirds + 5% BTC, fixed (vs 60/40)", R, four,
                [dict(w) for _ in dates], bench, static=True)))
    w3 = {s: 1 / 3 for s in three}
    res.append((f"since {dates[0]}", evaluate_weights("Reference: equal thirds without BTC, same years", R, three,
                [dict(w3) for _ in dates], bench, static=True)))
    out = ["# Study batch 8: macro signals and adding BTC", "",
           f"Run {dt.datetime.now(dt.timezone.utc):%Y-%m-%d %H:%M} UTC. Same pass rules.", "", A.HEAD]
    for grp, e in res:
        out.append(A.row(e).replace(f"| {e['name']} |", f"| {e['name']} ({grp}) |"))
    text = "\n".join(out) + "\n"
    with open(os.path.join(HERE, "allocation_study2_results.md"), "w") as fh:
        fh.write(text)
    print(text)


if __name__ == "__main__":
    main()
