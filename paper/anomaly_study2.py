#!/usr/bin/env python3
"""Anomaly study, batch 2 (same pass rules as anomaly_study.py; rules fixed before running).

  9. Volatility-managed S&P 500 (Moreira & Muir 2017): each month hold
     min(1, 15% / last month's yearly volatility) in SPY, rest in cash.
 10. VIX term-structure filter: hold SPY only while the VIX is below the
     3-month VIX (calm, "contango"); otherwise cash. Checked each close.
 11. Sector momentum (Moskowitz & Grinblatt 1999): each month hold the 3 of 9
     sector funds with the best 12-month return excluding the last month.
     Benchmark: SPY.
 12. Multi-asset trend (Moskowitz, Ooi & Pedersen 2012 / Hurst et al.):
     SPY, EFA, EEM, IEF, TLT, GLD, DBC, VNQ, 1/8 each, held only while its
     12-month return is positive; checked monthly. Benchmark: hold all 8.
 13. Our BTC weekly trend rule (trend_paper.py) applied to ETH, which was not
     used to design it: a true out-of-sample test. Benchmark: hold ETH.
 14. The same rule on gold (GLD), weekly. Benchmark: hold GLD.
"""
import datetime as dt
import math
import os
import statistics as st

import anomaly_study as A

HERE = os.path.dirname(os.path.abspath(__file__))


def common(syms, start=946684800):
    data = {s: A.daily(s, start) for s in syms}
    dates = sorted(set.intersection(*(set(v) for v in data.values())))
    return data, dates, {s: A.rets(data[s], dates) for s in syms}


def trend_rule_positions(data, dates, sym, per_year):
    """28/56-day trend with 50% vol cap, rebalanced weekly (as in trend_paper.py)."""
    c = [data[sym][d]["c"] for d in dates]
    r = [0.0] + [c[i] / c[i - 1] - 1 for i in range(1, len(c))]
    pos, cur, wk = [], 0.0, None
    for i, d in enumerate(dates):
        pos.append(cur)
        w = d.isocalendar()[:2]
        if w != wk and i >= 57:
            wk = w
            vol = st.pstdev(r[i - 29:i + 1]) * math.sqrt(per_year)
            cur = (0.5 * (c[i] > c[i - 28]) + 0.5 * (c[i] > c[i - 56])) * (min(1, 0.5 / vol) if vol else 1)
    return pos, r


def main():
    res = []
    # 9. vol-managed SPY
    data, dates, R = common(["SPY"])
    me = set(A.month_ends(dates))
    pos, cur = [], 0.0
    for i, d in enumerate(dates):
        pos.append(cur)
        if i in me and i >= 21:
            vol = st.pstdev(R["SPY"][i - 20:i + 1]) * math.sqrt(252)
            cur = min(1.0, 0.15 / vol) if vol else 1.0
    res.append(("Stocks (SPY since 2000)", A.evaluate("9. Volatility-managed S&P 500", R["SPY"], pos, R["SPY"], 0.0005, 252, 0.002)))
    # 10. VIX term structure
    data, dates, R = common(["SPY", "^VIX", "^VIX3M"])
    pos, cur = [], 0.0
    for d in dates:
        pos.append(cur)
        cur = 1.0 if data["^VIX"][d]["c"] < data["^VIX3M"][d]["c"] else 0.0
    res.append((f"Stocks (VIX3M data since {dates[0]})", A.evaluate("10. VIX term-structure filter (SPY)", R["SPY"], pos, R["SPY"], 0.0005, 252, 0.002)))
    # 11. sector momentum
    secs = ["XLB", "XLE", "XLF", "XLI", "XLK", "XLP", "XLU", "XLV", "XLY"]
    data, dates, R = common(secs + ["SPY"])
    me = A.month_ends(dates)
    me_set = set(me)
    P = {s: [] for s in secs}
    cur, k = {}, 0
    for i, d in enumerate(dates):
        for s in secs:
            P[s].append(cur.get(s, 0.0))
        if i in me_set:
            k = me.index(i)
            if k >= 12:
                i12, i1 = me[k - 12], me[k - 1]
                mom = {s: data[s][dates[i1]]["c"] / data[s][dates[i12]]["c"] - 1 for s in secs}
                top = sorted(secs, key=lambda s: mom[s], reverse=True)[:3]
                cur = {s: (1 / 3 if s in top else 0.0) for s in secs}
    res.append((f"Sectors ({dates[0]} on)", A.evaluate("11. Sector momentum, top 3 of 9 (vs SPY)", [R[s] for s in secs], [P[s] for s in secs], R["SPY"], 0.0005, 252, 0.002, multi=True)))
    # 12. multi-asset trend
    assets = ["SPY", "EFA", "EEM", "IEF", "TLT", "GLD", "DBC", "VNQ"]
    data, dates, R = common(assets)
    me = A.month_ends(dates)
    me_set = set(me)
    P = {s: [] for s in assets}
    cur = {}
    for i, d in enumerate(dates):
        for s in assets:
            P[s].append(cur.get(s, 0.0))
        if i in me_set and i >= 252:
            cur = {s: (1 / 8 if data[s][d]["c"] > data[s][dates[i - 252]]["c"] else 0.0) for s in assets}
    bench = [sum(R[s][i] for s in assets) / 8 for i in range(len(dates))]
    res.append((f"Multi-asset ({dates[0]} on)", A.evaluate("12. Multi-asset 12-month trend, 8 ETFs (vs hold all 8)", [R[s] for s in assets], [P[s] for s in assets], bench, 0.0005, 252, 0.002, multi=True)))
    # 13. ETH with our BTC rule
    data, dates, R = common(["ETH-USD"], int(dt.datetime(2017, 11, 10, tzinfo=dt.timezone.utc).timestamp()))
    pos, r = trend_rule_positions(data, dates, "ETH-USD", 365)
    res.append((f"Crypto (ETH since {dates[0]})", A.evaluate("13. Our BTC trend rule on ETH (out of sample)", r, pos, r, 0.001, 365, 0.004)))
    # 14. gold
    data, dates, R = common(["GLD"])
    pos, r = trend_rule_positions(data, dates, "GLD", 252)
    res.append((f"Gold (GLD since {dates[0]})", A.evaluate("14. Our trend rule on gold (GLD)", r, pos, r, 0.0005, 252, 0.002)))

    out = ["# Academic anomaly study, batch 2", "",
           f"Run {dt.datetime.now(dt.timezone.utc):%Y-%m-%d %H:%M} UTC. Same pass rules as batch 1.", "",
           A.HEAD]
    for grp, e in res:
        out.append(A.row(e).replace(f"| {e['name']} |", f"| {e['name']} ({grp}) |"))
    text = "\n".join(out) + "\n"
    with open(os.path.join(HERE, "anomaly_study2_results.md"), "w") as f:
        f.write(text)
    print(text)


if __name__ == "__main__":
    main()
