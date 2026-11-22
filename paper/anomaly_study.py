#!/usr/bin/env python3
"""Study: which well-known academic market anomalies still work?

Tests (rules fixed before running; Yahoo Finance daily data):
  Stocks (SPY, the S&P 500 fund, since 1993):
    1. Turn of the month (McConnell & Xu 2008): hold from the close two days
       before month end to the close of the 3rd trading day of the new month.
    2. Overnight drift (Cooper, Cliff & Gulen; NY Fed "Overnight Drift"):
       buy at each close, sell at the next open.
    3. Halloween / sell in May (Bouman & Jacobsen 2002): hold November-April,
       cash May-October.
    4. IBS reversal: buy at the close when (close-low)/(high-low) < 0.2; sell
       at the first close above the previous day's high.
  Asset allocation (since 2007):
    5. Faber 10-month trend (GTAA, Faber 2007): SPY, EFA, IEF, VNQ, DBC, 20%
       each, held only while the month-end price is above its 10-month
       average; otherwise that 20% is cash.
    6. Dual momentum (Antonacci): each month, if SPY's 12-month return beats
       SHY (cash), hold whichever of SPY/EFA did better over 12 months;
       otherwise hold AGG (bonds).
  Crypto (since 2018; today's large coins, so survivorship bias):
    7. Cross-sectional momentum (Liu, Tsyvinski & Wu): each week hold the 3
       coins with the best 4-week return, equal weight.
    8. Same, but only while BTC is up over the last 28 days (trend filter).

Pass rules (decided before running): (a) luck check >= 95%; (b) Sharpe above
the benchmark's in BOTH halves of the history; (c) positive after costs.
Costs per side: stocks/ETFs 0.05%, crypto 0.10% (stress 0.40% shown too).
Luck check: the strategy's day-by-day positions are slid in time by a random
offset (500 times), which keeps how much and how long it holds but breaks the
timing. Share of those it beats on Sharpe is reported.
"""
import datetime as dt
import json
import math
import os
import random
import statistics as st
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))


def daily(symbol, start=946684800):
    now = int(dt.datetime.now().timestamp())
    url = (f"https://query2.finance.yahoo.com/v8/finance/chart/{urllib.request.quote(symbol)}"
           f"?period1={start}&period2={now}&interval=1d")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        j = json.load(r)["chart"]["result"][0]
    q = j["indicators"]["quote"][0]
    adj = j["indicators"].get("adjclose", [{}])[0].get("adjclose")
    out = {}
    for i, t in enumerate(j["timestamp"]):
        o, h, l, c = (q[k][i] for k in ("open", "high", "low", "close"))
        if None in (o, h, l, c) or c <= 0:
            continue
        a = adj[i] if adj and adj[i] else c
        f = a / c                                  # dividend/split adjustment
        d = dt.datetime.fromtimestamp(t, dt.timezone.utc).date()
        out[d] = dict(o=o * f, h=h * f, l=l * f, c=a)
    return out


def metrics(r, per_year):
    if not r:
        return dict(cagr=0, mdd=0, sharpe=0)
    eq = peak = 1.0
    mdd = 0.0
    for x in r:
        eq *= 1 + x
        peak = max(peak, eq)
        mdd = max(mdd, 1 - eq / peak)
    yrs = len(r) / per_year
    sd = st.pstdev(r)
    return dict(cagr=(eq ** (1 / yrs) - 1) if eq > 0 else -1, mdd=mdd,
                sharpe=(st.mean(r) / sd * math.sqrt(per_year)) if sd > 0 else 0)


def strat_returns(asset_r, pos, cost):
    """pos[i] = exposure held during day i (decided by day i-1's close)."""
    out, prev = [], 0.0
    for r, p in zip(asset_r, pos):
        out.append(p * r - abs(p - prev) * cost)
        prev = p
    return out


def luck_shift(asset_r, pos, cost, per_year, sims=500, seed=5):
    real = metrics(strat_returns(asset_r, pos, cost), per_year)["sharpe"]
    n, rng, beat = len(pos), random.Random(seed), 0
    for _ in range(sims):
        k = rng.randrange(1, n)
        sp = pos[k:] + pos[:k]
        beat += real > metrics(strat_returns(asset_r, sp, cost), per_year)["sharpe"]
    return beat / sims


def evaluate(name, asset_r, pos, bench_r, cost, per_year, stress=None, multi=None):
    """asset_r/pos may be lists of lists (multi-asset); bench_r is a return list."""
    def run(c, lo=0, hi=None):
        if multi:
            cols = [strat_returns(a[lo:hi], p[lo:hi], c) for a, p in zip(asset_r, pos)]
            return [sum(x) for x in zip(*cols)]
        return strat_returns(asset_r[lo:hi], pos[lo:hi], c)
    n = len(bench_r)
    h = n // 2
    allm, a1, a2 = metrics(run(cost), per_year), metrics(run(cost, 0, h), per_year), metrics(run(cost, h), per_year)
    b, b1, b2 = metrics(bench_r, per_year), metrics(bench_r[:h], per_year), metrics(bench_r[h:], per_year)
    st_m = metrics(run(stress), per_year) if stress else None
    if multi:
        shifts, rng, real, beat = 500, random.Random(9), allm["sharpe"], 0
        for _ in range(shifts):
            k = rng.randrange(1, len(pos[0]))   # same shift for every asset, so weights still add up
            cols = [strat_returns(a, p[k:] + p[:k], cost) for a, p in zip(asset_r, pos)]
            beat += real > metrics([sum(x) for x in zip(*cols)], per_year)["sharpe"]
        lk = beat / shifts
    else:
        lk = luck_shift(asset_r, pos, cost, per_year)
    passed = lk >= 0.95 and a1["sharpe"] > b1["sharpe"] and a2["sharpe"] > b2["sharpe"] and allm["cagr"] > 0
    return dict(name=name, all=allm, h1=a1, h2=a2, b=b, b1=b1, b2=b2, stress=st_m, luck=lk, passed=passed)


def rets(series, dates):
    c = [series[d]["c"] for d in dates]
    return [0.0] + [c[i] / c[i - 1] - 1 for i in range(1, len(c))]


def stock_tests():
    spy = daily("SPY")
    dates = sorted(spy)
    r = rets(spy, dates)
    res = []
    # 1. turn of the month: hold days -1..+3 (returns of last day and first 3 days)
    month_idx = {}
    for i, d in enumerate(dates):
        month_idx.setdefault((d.year, d.month), []).append(i)
    hold = set()
    for (y, m), ix in month_idx.items():
        hold.add(ix[-1])
        nxt = month_idx.get((y + (m == 12), m % 12 + 1))
        if nxt:
            hold.update(nxt[:3])
    pos = [1.0 if i in hold else 0.0 for i in range(len(dates))]
    res.append(evaluate("1. Turn of the month (SPY)", r, pos, r, 0.0005, 252, 0.002))
    # 2. overnight drift: close -> next open, every day
    on = [0.0] + [spy[dates[i]]["o"] / spy[dates[i - 1]]["c"] - 1 for i in range(1, len(dates))]
    day = [0.0] + [spy[dates[i]]["c"] / spy[dates[i]]["o"] - 1 for i in range(1, len(dates))]
    cost = 0.0005
    on_r = [x - 2 * cost for x in on]           # buy every close, sell every open
    res.append(dict(name="2. Overnight drift (SPY, hold close to open)", overnight=metrics(on_r, 252),
                    overnight_free=metrics(on, 252), daytime=metrics(day, 252), b=metrics(r, 252)))
    # 3. Halloween
    pos = [1.0 if d.month in (11, 12, 1, 2, 3, 4) else 0.0 for d in dates]
    pos = [pos[i - 1] if i else 0.0 for i in range(len(pos))]   # decided at prior close
    res.append(evaluate("3. Halloween: hold Nov-Apr (SPY)", r, pos, r, 0.0005, 252, 0.002))
    # 4. IBS
    pos, held = [], 0.0
    for i, d in enumerate(dates):
        pos.append(held)
        b = spy[d]
        ibs = (b["c"] - b["l"]) / (b["h"] - b["l"]) if b["h"] > b["l"] else 0.5
        if held and i and b["c"] > spy[dates[i - 1]]["h"]:
            held = 0.0
        elif not held and ibs < 0.2:
            held = 1.0
    res.append(evaluate("4. IBS reversal (SPY)", r, pos, r, 0.0005, 252, 0.002))
    return res, (dates[0], dates[-1])


def month_ends(dates):
    out = []
    for i, d in enumerate(dates):
        if i + 1 == len(dates) or dates[i + 1].month != d.month:
            out.append(i)
    return out


def allocation_tests():
    syms = ["SPY", "EFA", "IEF", "VNQ", "DBC", "SHY", "AGG"]
    data = {s: daily(s) for s in syms}
    dates = sorted(set.intersection(*(set(v) for v in data.values())))
    R = {s: rets(data[s], dates) for s in syms}
    me = month_ends(dates)
    res = []
    # 5. Faber GTAA5
    five = ["SPY", "EFA", "IEF", "VNQ", "DBC"]
    pos = {s: [0.0] * len(dates) for s in five}
    for s in five:
        cur = 0.0
        me_set = set(me)
        mcl = []
        for i, d in enumerate(dates):
            pos[s][i] = cur
            if i in me_set:
                mcl.append(data[s][d]["c"])
                if len(mcl) >= 10:
                    cur = 0.2 if mcl[-1] > sum(mcl[-10:]) / 10 else 0.0
    bench = [sum(R[s][i] for s in five) / 5 for i in range(len(dates))]
    res.append(evaluate("5. Faber 10-month trend, 5 ETFs (vs equal-weight hold)",
                        [R[s] for s in five], [pos[s] for s in five], bench, 0.0005, 252, 0.002, multi=True))
    # 6. Dual momentum
    hold_sym = {s: [0.0] * len(dates) for s in ("SPY", "EFA", "AGG")}
    cur, me_set = None, set(me)
    for i, d in enumerate(dates):
        for s in hold_sym:
            hold_sym[s][i] = 1.0 if cur == s else 0.0
        if i in me_set and i >= 252:
            r12 = {s: data[s][d]["c"] / data[s][dates[i - 252]]["c"] - 1 for s in ("SPY", "EFA", "SHY")}
            if r12["SPY"] > r12["SHY"]:
                cur = "SPY" if r12["SPY"] >= r12["EFA"] else "EFA"
            else:
                cur = "AGG"
    res.append(evaluate("6. Dual momentum SPY/EFA/AGG (vs SPY)", [R[s] for s in hold_sym],
                        [hold_sym[s] for s in hold_sym], R["SPY"], 0.0005, 252, 0.002, multi=True))
    return res, (dates[0], dates[-1])


def crypto_tests():
    coins = ["BTC-USD", "ETH-USD", "XRP-USD", "LTC-USD", "BCH-USD", "ADA-USD", "XLM-USD",
             "LINK-USD", "DOGE-USD", "TRX-USD", "BNB-USD", "ETC-USD"]
    start = int(dt.datetime(2017, 11, 15, tzinfo=dt.timezone.utc).timestamp())
    data = {c: daily(c, start) for c in coins}
    dates = sorted(set.intersection(*(set(v) for v in data.values())))
    R = {c: rets(data[c], dates) for c in coins}
    bench = [sum(R[c][i] for c in coins) / len(coins) for i in range(len(dates))]
    res = []
    for filt in (False, True):
        pos = {c: [0.0] * len(dates) for c in coins}
        cur = {}
        for i, d in enumerate(dates):
            for c in coins:
                pos[c][i] = cur.get(c, 0.0)
            if d.weekday() == 6 and i >= 56:             # decide each Sunday close
                mom = {c: data[c][d]["c"] / data[c][dates[i - 28]]["c"] - 1 for c in coins}
                top = sorted(coins, key=lambda c: mom[c], reverse=True)[:3]
                ok = (data["BTC-USD"][d]["c"] / data["BTC-USD"][dates[i - 28]]["c"] - 1) > 0
                cur = {c: (1 / 3 if (c in top and (ok or not filt)) else 0.0) for c in coins}
        nm = "8. Crypto top-3 momentum + BTC trend filter" if filt else "7. Crypto top-3 momentum"
        res.append(evaluate(nm + " (vs equal-weight 12 coins)", [R[c] for c in coins],
                            [pos[c] for c in coins], bench, 0.001, 365, 0.004, multi=True))
    # also compare against BTC alone
    return res, (dates[0], dates[-1]), metrics(R["BTC-USD"], 365)


def pct(x):
    return f"{x * 100:+.1f}%"


def row(e):
    s = e["stress"]
    return (f"| {e['name']} | {pct(e['all']['cagr'])} | -{e['all']['mdd']:.0%} | {e['all']['sharpe']:.2f} | "
            f"{e['b']['sharpe']:.2f} | {e['h1']['sharpe']:.2f} vs {e['b1']['sharpe']:.2f} | "
            f"{e['h2']['sharpe']:.2f} vs {e['b2']['sharpe']:.2f} | {pct(s['cagr']) if s else '-'} | "
            f"{'n/a' if e['luck'] is None else format(e['luck'], '.0%')} | {'**PASS**' if e['passed'] else 'fail'} |")


HEAD = ("| Test | Per year | Worst drop | Sharpe | Benchmark Sharpe | 1st half Sharpe (vs bench) | "
        "2nd half Sharpe (vs bench) | Per year at stress cost | Luck check | Verdict |\n"
        "|---|---|---|---|---|---|---|---|---|---|")


def main():
    out = ["# Academic anomaly study", "",
           f"Run {dt.datetime.now(dt.timezone.utc):%Y-%m-%d %H:%M} UTC. Rules and pass rules fixed before "
           "running. PASS = luck check >= 95%, Sharpe above the benchmark in BOTH halves, and positive "
           "after costs.", ""]
    s, (d0, d1) = stock_tests()
    out += [f"## Stocks: SPY ({d0} to {d1}); benchmark = holding SPY", "", HEAD]
    for e in s:
        if "overnight" in e:
            continue
        out.append(row(e))
    o = [e for e in s if "overnight" in e][0]
    out += ["", f"**2. Overnight drift:** holding SPY only overnight earned {pct(o['overnight_free']['cagr'])} a "
            f"year before costs (daytime only: {pct(o['daytime']['cagr'])}), but buying every close and "
            f"selling every open at 0.05% per side gives {pct(o['overnight']['cagr'])} a year. "
            f"Holding SPY: {pct(o['b']['cagr'])} a year.", ""]
    a, (d0, d1) = allocation_tests()
    out += [f"## Asset allocation ({d0} to {d1})", "", HEAD] + [row(e) for e in a] + [""]
    c, (d0, d1), btc = crypto_tests()
    out += [f"## Crypto ({d0} to {d1}); benchmark = equal-weight 12 coins", "",
            f"Holding BTC alone over this period: {pct(btc['cagr'])} a year, worst drop -{btc['mdd']:.0%}, "
            f"Sharpe {btc['sharpe']:.2f}.", "", HEAD] + [row(e) for e in c] + [""]
    text = "\n".join(out)
    with open(os.path.join(HERE, "anomaly_study_results.md"), "w") as f:
        f.write(text)
    print(text)


if __name__ == "__main__":
    main()
