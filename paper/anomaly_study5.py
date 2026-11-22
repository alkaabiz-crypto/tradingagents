#!/usr/bin/env python3
"""Anomaly study, batch 5 (same pass rules; rules fixed before running).

Out-of-sample checks of account #10's rule (volatility-managed + 200-day filter):
 31. Gold (GLD)        32. Ex-US stocks (EFA)        33. Small caps (IWM)
 34. BTC: 200-day filter alone (hold BTC only above its 200-day average).
 35. Vol-managed ETH (50% target, monthly), out of sample for test 18.
New ideas:
 36. Low-volatility sectors (Baker, Bradley & Wurgler 2011; Haugen): each
     month hold the 3 of 9 sector funds with the lowest 6-month volatility.
     Benchmark: SPY.
 37. Risk parity (Asness, Frazzini & Pedersen 2012): SPY, TLT and GLD
     weighted by 1 / their 3-month volatility, rebalanced monthly.
     Benchmark: 60% SPY / 40% TLT.
 38. Stock/bond momentum switch: each month hold SPY if its 12-month return
     beats TLT's, else TLT. Benchmark: 60/40.
 39. Fear buying (VIX spikes): when the VIX closes above 30, hold SPY for the
     next 20 trading days.
"""
import datetime as dt
import math
import os
import statistics as st

import anomaly_study as A
from anomaly_study2 import common
from anomaly_study3 import vol_managed, CRYPTO_START
from anomaly_study4 import sma_filter

HERE = os.path.dirname(os.path.abspath(__file__))


def combo(sym, start=946684800):
    data, dates, R = common([sym], start)
    vm = vol_managed(R[sym], dates, 0.15, 252)
    f = sma_filter(data, dates, sym)
    return R[sym], [a * b for a, b in zip(vm, f)], dates


def monthly_weights(dates, fn):
    """fn(i) -> dict of weights, called at each month end; returns daily weight dict lists."""
    me = set(A.month_ends(dates))
    cur, out = {}, []
    for i in range(len(dates)):
        out.append(dict(cur))
        if i in me:
            w = fn(i)
            if w is not None:
                cur = w
    return out


def main():
    res = []
    for sym, nm in (("GLD", "31. Vol-managed + 200-day, gold (GLD)"),
                    ("EFA", "32. Vol-managed + 200-day, ex-US stocks (EFA)"),
                    ("IWM", "33. Vol-managed + 200-day, small caps (IWM)")):
        r, p, dates = combo(sym)
        res.append((f"{sym} since {dates[0]}", A.evaluate(nm, r, p, r, 0.0005, 252, 0.002)))
    data, dates, R = common(["BTC-USD"], int(dt.datetime(2014, 9, 17, tzinfo=dt.timezone.utc).timestamp()))
    res.append((f"BTC since {dates[0]}", A.evaluate("34. BTC above its 200-day average only", R["BTC-USD"],
                sma_filter(data, dates, "BTC-USD"), R["BTC-USD"], 0.001, 365, 0.004)))
    data, dates, R = common(["ETH-USD"], CRYPTO_START)
    res.append((f"ETH since {dates[0]}", A.evaluate("35. Vol-managed ETH (50% target)", R["ETH-USD"],
                vol_managed(R["ETH-USD"], dates, 0.5, 365), R["ETH-USD"], 0.001, 365, 0.004)))
    # 36. low-vol sectors
    secs = ["XLB", "XLE", "XLF", "XLI", "XLK", "XLP", "XLU", "XLV", "XLY"]
    data, dates, R = common(secs + ["SPY"])

    def lowvol(i):
        if i < 126:
            return None
        v = {s: st.pstdev(R[s][i - 125:i + 1]) for s in secs}
        low = sorted(secs, key=lambda s: v[s])[:3]
        return {s: 1 / 3 for s in low}
    W = monthly_weights(dates, lowvol)
    res.append((f"sectors since {dates[0]}", A.evaluate("36. Low-volatility sectors, 3 of 9 (vs SPY)",
                [R[s] for s in secs], [[w.get(s, 0.0) for w in W] for s in secs], R["SPY"],
                0.0005, 252, 0.002, multi=True)))
    # 37/38. risk parity and stock/bond switch
    data, dates, R = common(["SPY", "TLT", "GLD"])
    bench = [0.6 * R["SPY"][i] + 0.4 * R["TLT"][i] for i in range(len(dates))]

    def rp(i):
        if i < 63:
            return None
        inv = {s: 1 / st.pstdev(R[s][i - 62:i + 1]) for s in ("SPY", "TLT", "GLD")}
        tot = sum(inv.values())
        return {s: inv[s] / tot for s in inv}
    W = monthly_weights(dates, rp)
    res.append((f"since {dates[0]}", A.evaluate("37. Risk parity SPY/TLT/GLD (vs 60/40)",
                [R[s] for s in ("SPY", "TLT", "GLD")], [[w.get(s, 0.0) for w in W] for s in ("SPY", "TLT", "GLD")],
                bench, 0.0005, 252, 0.002, multi=True)))

    def switch(i):
        if i < 252:
            return None
        m = {s: data[s][dates[i]]["c"] / data[s][dates[i - 252]]["c"] - 1 for s in ("SPY", "TLT")}
        return {max(m, key=m.get): 1.0}
    W = monthly_weights(dates, switch)
    res.append((f"since {dates[0]}", A.evaluate("38. Stock/bond momentum switch (vs 60/40)",
                [R[s] for s in ("SPY", "TLT")], [[w.get(s, 0.0) for w in W] for s in ("SPY", "TLT")],
                bench, 0.0005, 252, 0.002, multi=True)))
    # 39. fear buying
    data, dates, R = common(["SPY", "^VIX"])
    pos, left = [], 0
    for d in dates:
        pos.append(1.0 if left > 0 else 0.0)
        left = max(0, left - 1)
        if data["^VIX"][d]["c"] > 30:
            left = 20
    res.append((f"SPY since {dates[0]}", A.evaluate("39. Buy SPY for 20 days after VIX > 30", R["SPY"], pos,
                R["SPY"], 0.0005, 252, 0.002)))
    out = ["# Academic anomaly study, batch 5", "",
           f"Run {dt.datetime.now(dt.timezone.utc):%Y-%m-%d %H:%M} UTC. Same pass rules as batch 1.", "", A.HEAD]
    for grp, e in res:
        out.append(A.row(e).replace(f"| {e['name']} |", f"| {e['name']} ({grp}) |"))
    text = "\n".join(out) + "\n"
    with open(os.path.join(HERE, "anomaly_study5_results.md"), "w") as fh:
        fh.write(text)
    print(text)


if __name__ == "__main__":
    main()
