#!/usr/bin/env python3
"""Study: the most famous daily / day-trading strategies (rules fixed before running).

A. Intraday momentum (Gao, Han, Li & Zhou; Wen et al. 2021 for crude oil):
   the return from yesterday's close to the end of today's first session
   period predicts the last period. Trade only the last period, in that
   direction, flat otherwise.
     - Oil (CL=F hourly): signal = yesterday's 14:00 New York candle close
       to today's 9:00 candle close; trade the 13:00-14:00 candle (the last
       full hour before the 14:30 settlement). Also the EIA-day version
       (Wen et al. 2023): on Wednesdays use the 10:00 candle (report hour).
     - SPY and QQQ (hourly, 9:30-start candles): signal = yesterday's close
       to today's first-candle close; trade the last candle (15:30-16:00).
   Data: Yahoo, about 2 years. Cost 0.02% per side (futures/ETF level),
   stress 0.05%.
B. Larry Connors' RSI(2) (Connors & Alvarez 2008): buy at the close when
   price is above its 200-day average and RSI(2) < 5; sell at the first close
   above the 5-day average. SPY since 1993, plus QQQ, IWM, DIA (out of
   sample). Cost 0.05% per side.
Pass rules: luck check >= 95% (500 random shifts), positive after costs in
both halves (A) / Sharpe above buy-and-hold in both halves (B).
"""
import datetime as dt
import json
import math
import os
import random
import statistics as st
import urllib.request
from zoneinfo import ZoneInfo

import anomaly_study as A

HERE = os.path.dirname(os.path.abspath(__file__))
ET = ZoneInfo("America/New_York")


def hourly(sym):
    req = urllib.request.Request(
        f"https://query2.finance.yahoo.com/v8/finance/chart/{urllib.request.quote(sym)}?range=730d&interval=60m",
        headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        j = json.load(r)["chart"]["result"][0]
    q = j["indicators"]["quote"][0]
    out = []
    for i, t in enumerate(j["timestamp"]):
        o, c = q["open"][i], q["close"][i]
        if o and c:
            out.append((dt.datetime.fromtimestamp(t, dt.timezone.utc).astimezone(ET), o, c))
    return out


def intraday_trades(bars, sig_end, trade_hour, prev_close_hour, wed_sig_end=None):
    """Return list of (date, signal_return, trade_return)."""
    days = {}
    for t, o, c in bars:
        if t.weekday() < 5:
            days.setdefault(t.date(), {})[t.hour] = (o, c)
    ds = sorted(days)
    out = []
    for k in range(1, len(ds)):
        d, p = ds[k], ds[k - 1]
        se = wed_sig_end if (wed_sig_end is not None and d.weekday() == 2) else sig_end
        if prev_close_hour not in days[p] or se not in days[d] or trade_hour not in days[d]:
            continue
        sig = days[d][se][1] / days[p][prev_close_hour][1] - 1
        o, c = days[d][trade_hour]
        out.append((d, sig, c / o - 1))
    return out


def judge_intraday(trades, cost):
    r = [(1 if s > 0 else -1) * x - 2 * cost for _, s, x in trades if s != 0]
    def stats(rr):
        if not rr:
            return 0, 0, 0
        m, sd = st.mean(rr), st.pstdev(rr)
        return m, (m / sd * math.sqrt(252)) if sd else 0, m / (sd / math.sqrt(len(rr))) if sd else 0
    m, sh, t = stats(r)
    h = len(r) // 2
    m1, _, _ = stats(r[:h])
    m2, _, _ = stats(r[h:])
    # luck: random directions with the same number of longs/shorts (500 shuffles)
    signs = [1 if s > 0 else -1 for _, s, _ in trades if s != 0]
    moves = [x for _, s, x in trades if s != 0]
    rng, beat = random.Random(3), 0
    for _ in range(500):
        sh_ = signs[:]
        rng.shuffle(sh_)
        beat += sum(a * b for a, b in zip(signs, moves)) > sum(a * b for a, b in zip(sh_, moves))
    return dict(n=len(r), mean=m, sharpe=sh, t=t, m1=m1, m2=m2, luck=beat / 500,
                win=sum(1 for x in r if x > 0) / len(r) if r else 0)


def rsi(c, n=2):
    out, g, l = [50.0], 0.0, 0.0
    for i in range(1, len(c)):
        d = c[i] - c[i - 1]
        g = (g * (n - 1) + max(d, 0)) / n
        l = (l * (n - 1) + max(-d, 0)) / n
        out.append(100 if l == 0 else 100 - 100 / (1 + g / l))
    return out


def connors(sym):
    data = A.daily(sym, 725846400)         # 1993
    dates = sorted(data)
    c = [data[d]["c"] for d in dates]
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
            held = 1.0
    r = A.rets(data, dates)
    return A.evaluate(f"Connors RSI(2) on {sym}", r, pos, r, 0.0005, 252, 0.002), dates[0]


def main():
    out = ["# Famous daily / day-trading strategies", "",
           f"Run {dt.datetime.now(dt.timezone.utc):%Y-%m-%d %H:%M} UTC.", "",
           "## A. Intraday momentum (about 2 years of hourly data)", "",
           "| Market / version | Trades | Win rate | Avg per trade (0.02% cost) | Sharpe | t-stat | 1st half / 2nd half avg | "
           "Avg at 0.05% cost | Luck check | Verdict |", "|---|---|---|---|---|---|---|---|---|---|"]
    cl = hourly("CL=F")
    tests = [("Oil (CL=F): overnight+first hour -> 13:00 hour", intraday_trades(cl, 9, 13, 14)),
             ("Oil (CL=F): EIA-day version (Wednesday uses the 10:00 report hour)", intraday_trades(cl, 9, 13, 14, wed_sig_end=10))]
    for sym in ("SPY", "QQQ"):
        b = hourly(sym)
        # Yahoo stock candles start at :30 -> hours 9 (9:30-10:30) ... 15 (15:30-16:00)
        tests.append((f"{sym}: overnight+first hour -> last half hour", intraday_trades(b, 9, 15, 15)))
    for nm, tr in tests:
        j = judge_intraday(tr, 0.0002)
        j5 = judge_intraday(tr, 0.0005)
        ok = j["luck"] >= 0.95 and j["m1"] > 0 and j["m2"] > 0 and j["mean"] > 0
        out.append(f"| {nm} | {j['n']} | {j['win']:.0%} | {j['mean'] * 100:+.3f}% | {j['sharpe']:.2f} | {j['t']:.2f} | "
                   f"{j['m1'] * 100:+.3f}% / {j['m2'] * 100:+.3f}% | {j5['mean'] * 100:+.3f}% | {j['luck']:.0%} | "
                   f"{'**PASS**' if ok else 'fail'} |")
    out += ["", "## B. Connors RSI(2) (daily, since 1993)", "", A.HEAD]
    for sym in ("SPY", "QQQ", "IWM", "DIA"):
        e, d0 = connors(sym)
        out.append(A.row(e).replace(f"| {e['name']} |", f"| {e['name']} (since {d0}) |"))
    text = "\n".join(out) + "\n"
    with open(os.path.join(HERE, "famous_study_results.md"), "w") as fh:
        fh.write(text)
    print(text)


if __name__ == "__main__":
    main()
