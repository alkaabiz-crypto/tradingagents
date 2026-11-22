#!/usr/bin/env python3
"""Anomaly study, batch 4 (same pass rules; rules fixed before running).

 24. 200-day average filter on SPY (Siegel; Faber): hold SPY only while the
     close is above its 200-day average, checked daily.
 25. Volatility-managed SPY + 200-day filter: the account #8 rule, but cash
     whenever SPY is below its 200-day average.
 26. Same combination on QQQ.
 27. Volatility-managed small caps (IWM), same rule as #8 (out of sample).
 28. Volatility-managed gold (GLD), same rule (out of sample).
 29. Weekly short-term reversal (Lehmann 1990, index version): after a week
     in which SPY fell more than 2%, hold SPY for the next week.
 30. BTC + ETH weekly trend accounts together, 50/50 (accounts #6 + #7).
     Benchmark: 50/50 hold BTC and ETH.
"""
import datetime as dt
import os

import anomaly_study as A
from anomaly_study2 import common, trend_rule_positions
from anomaly_study3 import vol_managed, CRYPTO_START

HERE = os.path.dirname(os.path.abspath(__file__))


def sma_filter(data, dates, sym, n=200):
    c = [data[sym][d]["c"] for d in dates]
    pos = [0.0]
    for i in range(1, len(c)):
        pos.append(1.0 if i - 1 >= n and c[i - 1] > sum(c[i - n:i]) / n else 0.0)
    return pos


def main():
    res = []
    data, dates, R = common(["SPY"])
    f = sma_filter(data, dates, "SPY")
    res.append((f"SPY since {dates[0]}", A.evaluate("24. 200-day average filter (SPY)", R["SPY"], f, R["SPY"], 0.0005, 252, 0.002)))
    vm = vol_managed(R["SPY"], dates, 0.15, 252)
    res.append((f"SPY since {dates[0]}", A.evaluate("25. Vol-managed SPY + 200-day filter", R["SPY"],
                [a * b for a, b in zip(vm, f)], R["SPY"], 0.0005, 252, 0.002)))
    data, dates, R = common(["QQQ"])
    f = sma_filter(data, dates, "QQQ")
    vm = vol_managed(R["QQQ"], dates, 0.15, 252)
    res.append((f"QQQ since {dates[0]}", A.evaluate("26. Vol-managed QQQ + 200-day filter", R["QQQ"],
                [a * b for a, b in zip(vm, f)], R["QQQ"], 0.0005, 252, 0.002)))
    for sym, nm in (("IWM", "27. Vol-managed small caps (IWM)"), ("GLD", "28. Vol-managed gold (GLD)")):
        data, dates, R = common([sym])
        res.append((f"{sym} since {dates[0]}", A.evaluate(nm, R[sym], vol_managed(R[sym], dates, 0.15, 252),
                                                         R[sym], 0.0005, 252, 0.002)))
    data, dates, R = common(["SPY"])
    c = [data["SPY"][d]["c"] for d in dates]
    pos, cur, wk, wk_start = [], 0.0, None, None
    for i, d in enumerate(dates):
        w = d.isocalendar()[:2]
        if w != wk:                       # first day of a new week: decide from last week
            if wk is not None and wk_start is not None:
                cur = 1.0 if c[i - 1] / c[wk_start] - 1 < -0.02 else 0.0
            wk, wk_start = w, i - 1 if i else 0
        pos.append(cur)
    res.append((f"SPY since {dates[0]}", A.evaluate("29. Weekly reversal: buy after a -2% week (SPY)", R["SPY"], pos,
                R["SPY"], 0.0005, 252, 0.002)))
    data, dates, R = common(["BTC-USD", "ETH-USD"], CRYPTO_START)
    pb, _ = trend_rule_positions(data, dates, "BTC-USD", 365)
    pe, _ = trend_rule_positions(data, dates, "ETH-USD", 365)
    bench = [(R["BTC-USD"][i] + R["ETH-USD"][i]) / 2 for i in range(len(dates))]
    res.append((f"crypto since {dates[0]}", A.evaluate("30. BTC + ETH weekly trend, 50/50 (vs 50/50 hold)",
                [R["BTC-USD"], R["ETH-USD"]], [[x / 2 for x in pb], [x / 2 for x in pe]], bench,
                0.001, 365, 0.004, multi=True)))
    out = ["# Academic anomaly study, batch 4", "",
           f"Run {dt.datetime.now(dt.timezone.utc):%Y-%m-%d %H:%M} UTC. Same pass rules as batch 1.", "", A.HEAD]
    for grp, e in res:
        out.append(A.row(e).replace(f"| {e['name']} |", f"| {e['name']} ({grp}) |"))
    text = "\n".join(out) + "\n"
    with open(os.path.join(HERE, "anomaly_study4_results.md"), "w") as fh:
        fh.write(text)
    print(text)


if __name__ == "__main__":
    main()
