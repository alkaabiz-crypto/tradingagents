#!/usr/bin/env python3
"""Anomaly study, batch 3 (same pass rules; rules fixed before running).

Out-of-sample checks of the two winners:
 15. Our crypto trend rule on 10 other large coins (XRP, LTC, ADA, BNB, LINK,
     DOGE, XLM, TRX, BCH, ETC), 1/10 each. Benchmark: hold all 10.
 16. Volatility-managed Nasdaq 100 (QQQ), same rule as account #8.
 17. Volatility-managed developed markets ex-US (EFA), same rule.
 18. Volatility-managed BTC (15% target is too low for BTC, so 50%, monthly).
 19. Our weekly trend rule on the Nasdaq 100 (QQQ).
New ideas:
 20. Pre-holiday effect (Ariel 1990; Lakonishok & Smidt 1988): hold SPY only
     on the last trading day before a US market holiday.
 21. ETH/BTC rotation: each week hold whichever of BTC/ETH did better over 28
     days, only while it is itself up over 28 days; otherwise cash.
     Benchmark: 50/50 BTC and ETH.
 22. Crypto weekend effect: hold BTC only from Friday close to Sunday close.
 23. Our weekly trend rule on long-term US bonds (TLT).
"""
import datetime as dt
import math
import os
import statistics as st

import anomaly_study as A
from anomaly_study2 import common, trend_rule_positions

HERE = os.path.dirname(os.path.abspath(__file__))
CRYPTO_START = int(dt.datetime(2017, 11, 10, tzinfo=dt.timezone.utc).timestamp())


def vol_managed(r, dates, target, per_year):
    me = set(A.month_ends(dates))
    pos, cur = [], 0.0
    for i in range(len(dates)):
        pos.append(cur)
        if i in me and i >= 21:
            v = st.pstdev(r[i - 20:i + 1]) * math.sqrt(per_year)
            cur = min(1.0, target / v) if v else 1.0
    return pos


def main():
    res = []
    alts = ["XRP-USD", "LTC-USD", "ADA-USD", "BNB-USD", "LINK-USD", "DOGE-USD", "XLM-USD",
            "TRX-USD", "BCH-USD", "ETC-USD"]
    data, dates, R = common(alts, CRYPTO_START)
    P = {}
    for s in alts:
        p, _ = trend_rule_positions(data, dates, s, 365)
        P[s] = [x / len(alts) for x in p]
    bench = [sum(R[s][i] for s in alts) / len(alts) for i in range(len(dates))]
    res.append((f"crypto since {dates[0]}", A.evaluate("15. Trend rule on 10 other coins (vs hold all 10)",
                [R[s] for s in alts], [P[s] for s in alts], bench, 0.001, 365, 0.004, multi=True)))
    for sym, nm in (("QQQ", "16. Vol-managed Nasdaq 100 (QQQ)"), ("EFA", "17. Vol-managed ex-US stocks (EFA)")):
        data, dates, R = common([sym])
        res.append((f"{sym} since {dates[0]}", A.evaluate(nm, R[sym], vol_managed(R[sym], dates, 0.15, 252),
                                                         R[sym], 0.0005, 252, 0.002)))
    data, dates, R = common(["BTC-USD"], CRYPTO_START)
    res.append((f"BTC since {dates[0]}", A.evaluate("18. Vol-managed BTC (50% target)", R["BTC-USD"],
                vol_managed(R["BTC-USD"], dates, 0.5, 365), R["BTC-USD"], 0.001, 365, 0.004)))
    data, dates, R = common(["QQQ"])
    p, r = trend_rule_positions(data, dates, "QQQ", 252)
    res.append((f"QQQ since {dates[0]}", A.evaluate("19. Weekly trend rule on Nasdaq 100 (QQQ)", r, p, r, 0.0005, 252, 0.002)))
    # 20. pre-holiday: next trading day is more than 1 calendar day away and not just a weekend
    data, dates, R = common(["SPY"])
    pos = [0.0]
    for i in range(1, len(dates)):
        prev, cur = dates[i - 1], dates[i]
        gap = (cur - prev).days
        holiday_gap = gap > 3 or (gap > 1 and prev.weekday() != 4)
        # position for day i = held through day i if day i is the last day before a holiday
        pos.append(0.0)
    pre = set()
    for i in range(len(dates) - 1):
        gap = (dates[i + 1] - dates[i]).days
        if gap > 3 or (gap > 1 and dates[i].weekday() != 4):
            pre.add(i)
    pos = [1.0 if i in pre else 0.0 for i in range(len(dates))]
    res.append((f"SPY since {dates[0]}", A.evaluate("20. Pre-holiday effect (SPY)", R["SPY"], pos, R["SPY"], 0.0005, 252, 0.002)))
    # 21. ETH/BTC rotation
    data, dates, R = common(["BTC-USD", "ETH-USD"], CRYPTO_START)
    c = {s: [data[s][d]["c"] for d in dates] for s in ("BTC-USD", "ETH-USD")}
    P = {s: [] for s in c}
    cur, wk = None, None
    for i, d in enumerate(dates):
        for s in c:
            P[s].append(1.0 if cur == s else 0.0)
        w = d.isocalendar()[:2]
        if w != wk and i >= 28:
            wk = w
            m = {s: c[s][i] / c[s][i - 28] - 1 for s in c}
            best = max(m, key=m.get)
            cur = best if m[best] > 0 else None
    bench = [(R["BTC-USD"][i] + R["ETH-USD"][i]) / 2 for i in range(len(dates))]
    res.append((f"crypto since {dates[0]}", A.evaluate("21. ETH/BTC rotation with trend filter (vs 50/50)",
                [R[s] for s in c], [P[s] for s in c], bench, 0.001, 365, 0.004, multi=True)))
    # 22. weekend effect: returns of Saturday and Sunday (Fri close -> Sun close)
    pos = [1.0 if d.weekday() in (5, 6) else 0.0 for d in dates]
    res.append((f"BTC since {dates[0]}", A.evaluate("22. BTC weekend only (Fri-Sun)", R["BTC-USD"], pos,
                R["BTC-USD"], 0.001, 365, 0.004)))
    data, dates, R = common(["TLT"])
    p, r = trend_rule_positions(data, dates, "TLT", 252)
    res.append((f"TLT since {dates[0]}", A.evaluate("23. Weekly trend rule on long bonds (TLT)", r, p, r, 0.0005, 252, 0.002)))

    out = ["# Academic anomaly study, batch 3", "",
           f"Run {dt.datetime.now(dt.timezone.utc):%Y-%m-%d %H:%M} UTC. Same pass rules as batch 1.", "", A.HEAD]
    for grp, e in res:
        out.append(A.row(e).replace(f"| {e['name']} |", f"| {e['name']} ({grp}) |"))
    text = "\n".join(out) + "\n"
    with open(os.path.join(HERE, "anomaly_study3_results.md"), "w") as f:
        f.write(text)
    print(text)


if __name__ == "__main__":
    main()
