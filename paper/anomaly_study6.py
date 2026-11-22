#!/usr/bin/env python3
"""Anomaly study, batch 6 (same pass rules; rules fixed before running).

More out-of-sample checks of the winning rules on new markets:
 40. Vol-managed long US bonds (TLT)     41. Vol-managed emerging markets (EEM)
 42. Vol-managed real estate (VNQ)
 43. Weekly trend rule on the US dollar (UUP)  (currency trend, MOP 2012)
 44. Weekly trend rule on a commodity basket (DBC)
New ideas:
 45. Risk-on filter: hold BTC only while SPY is above its 200-day average
     (BTC tends to fall with stocks). Benchmark: hold BTC.
 46. Country momentum (Asness, Moskowitz & Pedersen 2013): each month hold
     the 3 of 10 country funds (EWJ EWG EWU EWC EWA EWZ EWH EWS EWW EWL) with
     the best 12-month return excluding the last month. Benchmark: hold all 10.
 47. Multi-asset trend done the MOP way: 8 ETFs, each 1/8 x min(1, 10% / its
     3-month volatility) when its 12-month return is positive, else cash.
     Benchmark: hold all 8.
 48. Risk parity with a trend filter: account #12, but any fund below its
     200-day average is held as cash. Benchmark: 60/40.
"""
import datetime as dt
import math
import os
import statistics as st

import anomaly_study as A
from anomaly_study2 import common, trend_rule_positions
from anomaly_study3 import vol_managed, CRYPTO_START
from anomaly_study5 import monthly_weights

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    res = []
    for sym, nm in (("TLT", "40. Vol-managed long bonds (TLT)"), ("EEM", "41. Vol-managed emerging markets (EEM)"),
                    ("VNQ", "42. Vol-managed real estate (VNQ)")):
        data, dates, R = common([sym])
        res.append((f"{sym} since {dates[0]}", A.evaluate(nm, R[sym], vol_managed(R[sym], dates, 0.15, 252),
                                                         R[sym], 0.0005, 252, 0.002)))
    for sym, nm in (("UUP", "43. Weekly trend rule on the US dollar (UUP)"),
                    ("DBC", "44. Weekly trend rule on commodities (DBC)")):
        data, dates, R = common([sym])
        p, r = trend_rule_positions(data, dates, sym, 252)
        res.append((f"{sym} since {dates[0]}", A.evaluate(nm, r, p, r, 0.0005, 252, 0.002)))
    # 45. BTC with SPY risk-on filter (BTC trades every day; use SPY's last close)
    btc = A.daily("BTC-USD", int(dt.datetime(2014, 9, 17, tzinfo=dt.timezone.utc).timestamp()))
    spy = A.daily("SPY")
    bd = sorted(btc)
    sd = sorted(spy)
    sc = [spy[d]["c"] for d in sd]
    above = {}
    for i in range(200, len(sd)):
        above[sd[i]] = sc[i] > sum(sc[i - 199:i + 1]) / 200
    pos, last = [], False
    k = 0
    for d in bd:
        pos.append(1.0 if last else 0.0)
        while k < len(sd) and sd[k] <= d:
            last = above.get(sd[k], False)
            k += 1
    r = A.rets(btc, bd)
    res.append((f"BTC since {bd[0]}", A.evaluate("45. BTC only while SPY is above its 200-day average", r, pos, r,
                0.001, 365, 0.004)))
    # 46. country momentum
    ctry = ["EWJ", "EWG", "EWU", "EWC", "EWA", "EWZ", "EWH", "EWS", "EWW", "EWL"]
    data, dates, R = common(ctry)
    me = A.month_ends(dates)

    def cm(i):
        k = me.index(i)
        if k < 12:
            return None
        i12, i1 = me[k - 12], me[k - 1]
        mom = {s: data[s][dates[i1]]["c"] / data[s][dates[i12]]["c"] - 1 for s in ctry}
        return {s: 1 / 3 for s in sorted(ctry, key=lambda s: mom[s], reverse=True)[:3]}
    W = monthly_weights(dates, cm)
    bench = [sum(R[s][i] for s in ctry) / 10 for i in range(len(dates))]
    res.append((f"countries since {dates[0]}", A.evaluate("46. Country momentum, top 3 of 10 (vs hold all 10)",
                [R[s] for s in ctry], [[w.get(s, 0.0) for w in W] for s in ctry], bench, 0.0005, 252, 0.002, multi=True)))
    # 47. MOP multi-asset trend with vol scaling
    assets = ["SPY", "EFA", "EEM", "IEF", "TLT", "GLD", "DBC", "VNQ"]
    data, dates, R = common(assets)

    def mop(i):
        if i < 252:
            return None
        w = {}
        for s in assets:
            if data[s][dates[i]]["c"] > data[s][dates[i - 252]]["c"]:
                v = st.pstdev(R[s][i - 62:i + 1]) * math.sqrt(252)
                w[s] = min(1.0, 0.10 / v) / 8 if v else 1 / 8
        return w
    W = monthly_weights(dates, mop)
    bench = [sum(R[s][i] for s in assets) / 8 for i in range(len(dates))]
    res.append((f"multi-asset since {dates[0]}", A.evaluate("47. Multi-asset trend with vol scaling (vs hold all 8)",
                [R[s] for s in assets], [[w.get(s, 0.0) for w in W] for s in assets], bench, 0.0005, 252, 0.002, multi=True)))
    # 48. risk parity + 200-day filter per fund
    F = ("SPY", "TLT", "GLD")
    data, dates, R = common(list(F))
    c = {s: [data[s][d]["c"] for d in dates] for s in F}

    def rpf(i):
        if i < 200:
            return None
        inv = {s: 1 / st.pstdev(R[s][i - 62:i + 1]) for s in F}
        tot = sum(inv.values())
        return {s: inv[s] / tot for s in F if c[s][i] > sum(c[s][i - 199:i + 1]) / 200}
    W = monthly_weights(dates, rpf)
    bench = [0.6 * R["SPY"][i] + 0.4 * R["TLT"][i] for i in range(len(dates))]
    res.append((f"since {dates[0]}", A.evaluate("48. Risk parity + 200-day filter per fund (vs 60/40)",
                [R[s] for s in F], [[w.get(s, 0.0) for w in W] for s in F], bench, 0.0005, 252, 0.002, multi=True)))
    out = ["# Academic anomaly study, batch 6", "",
           f"Run {dt.datetime.now(dt.timezone.utc):%Y-%m-%d %H:%M} UTC. Same pass rules as batch 1.", "", A.HEAD]
    for grp, e in res:
        out.append(A.row(e).replace(f"| {e['name']} |", f"| {e['name']} ({grp}) |"))
    text = "\n".join(out) + "\n"
    with open(os.path.join(HERE, "anomaly_study6_results.md"), "w") as fh:
        fh.write(text)
    print(text)


if __name__ == "__main__":
    main()
