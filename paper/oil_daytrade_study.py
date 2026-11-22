#!/usr/bin/env python3
"""Study: do short-term (day-trading) crude-oil strategies work?

Rules were written down before any test. Data: about 2 years of hourly WTI
crude oil futures candles (Yahoo Finance CL=F). Times are New York (ET).
The hour-9 candle is 9:00-10:00 ET, and so on. Every trade is closed by the
end of the 14:00 ET candle (around the 14:30 settlement), so nothing is held
overnight, except in the "overnight" benchmark row.

Strategies (from public day-trading guides):
  1. Opening-range breakout: the 9:00 candle sets a range; a later close
     outside it trades in that direction; stop at the other side.
  2. Overnight-range breakout: the 18:00-9:00 overnight high/low; a close
     outside it from 9:00-13:00 trades in that direction; stop at the middle
     of the overnight range.
  3. Same as 2, but only when the overnight range is tighter than its
     20-day median ("tight ranges break out").
  4. Previous-day high/low breakout: a close above yesterday's 9:00-14:00
     high buys (below the low sells); stop 1 ATR away.
  5. Gap fade: if the 9:00 open is more than 0.75% away from yesterday's
     14:00 close, trade back towards it; target = yesterday's close; stop =
     the same distance the other way.
  6. VWAP stretch fade: a close more than 1.5 ATR away from the session VWAP
     (reset 18:00) fades back towards VWAP; stop 1 ATR further out.
  7. Hourly RSI(2) pullback with the 200-hour trend: buy RSI(2) < 10 above
     the 200-hour average (sell RSI(2) > 90 below it); exit above/below the
     5-hour average; stop 2 ATR.
  8. Hourly 9/21 EMA crossover, trading the cross direction; exit on the
     opposite cross.
  9. EIA reaction follow: on Wednesdays, trade in the direction of the
     10:00 candle (the report is at 10:30) if it moved more than 0.3%.
Benchmarks: long every day 9:00 open to 14:00 close; long overnight.

Costs per side: 0.02% (futures, low), 0.10% (main, ETF or CFD).
Luck check: each strategy is compared with 500 random strategies that make
the same number of trades, same direction and same holding time, at random
New York session hours.
"""
import datetime as dt
import json
import os
import random
import statistics as st
import urllib.request
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))
ET = ZoneInfo("America/New_York")
LOW, MAIN = 0.0002, 0.001


def load():
    req = urllib.request.Request(
        "https://query2.finance.yahoo.com/v8/finance/chart/CL%3DF?range=730d&interval=60m",
        headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        j = json.load(r)["chart"]["result"][0]
    q = j["indicators"]["quote"][0]
    seen, bars = set(), []
    for i, t in enumerate(j["timestamp"]):
        t -= t % 3600
        o, h, lo, c = (q[k][i] for k in ("open", "high", "low", "close"))
        if None in (o, h, lo, c) or t in seen or lo <= 0:
            continue
        seen.add(t)
        et = dt.datetime.fromtimestamp(t, dt.timezone.utc).astimezone(ET)
        bars.append(dict(t=t, et=et, o=o, h=h, l=lo, c=c, v=q["volume"][i] or 0))
    bars.sort(key=lambda b: b["t"])
    return bars


def add_indicators(bars):
    # ATR(14) on hourly bars
    trs = []
    for i, b in enumerate(bars):
        pc = bars[i - 1]["c"] if i else b["o"]
        trs.append(max(b["h"] - b["l"], abs(b["h"] - pc), abs(b["l"] - pc)))
        b["atr"] = sum(trs[-14:]) / len(trs[-14:])
    c = [b["c"] for b in bars]
    # RSI(2)
    g = l = 0.0
    for i, b in enumerate(bars):
        if i == 0:
            b["rsi2"] = 50
            continue
        d = c[i] - c[i - 1]
        g = (g + max(d, 0)) / 2
        l = (l + max(-d, 0)) / 2
        b["rsi2"] = 100 if l == 0 else 100 - 100 / (1 + g / l)
    for n, key in ((200, "sma200"), (5, "sma5")):
        for i, b in enumerate(bars):
            b[key] = sum(c[max(0, i - n + 1):i + 1]) / (min(i + 1, n))
    for n, key in ((9, "ema9"), (21, "ema21")):
        k, e = 2 / (n + 1), c[0]
        for b in bars:
            e = b["c"] * k + e * (1 - k)
            b[key] = e
    # session VWAP, reset at 18:00 ET
    pv = vv = 0.0
    for b in bars:
        if b["et"].hour == 18:
            pv = vv = 0.0
        tp = (b["h"] + b["l"] + b["c"]) / 3
        pv += tp * max(b["v"], 1)
        vv += max(b["v"], 1)
        b["vwap"] = pv / vv


def session_days(bars):
    """Map ET date -> indexes of that date's 9:00-14:00 candles (weekdays)."""
    days = {}
    for i, b in enumerate(bars):
        if b["et"].weekday() < 5 and 9 <= b["et"].hour <= 14:
            days.setdefault(b["et"].date(), []).append(i)
    return {d: ix for d, ix in days.items() if bars[ix[-1]]["et"].hour == 14 and len(ix) >= 5}


def manage(bars, e, side, px, stop, target, last):
    """Hold from candle e's close until stop/target is touched or candle `last`
    closes. Stop is checked before target inside a candle (conservative)."""
    for j in range(e + 1, last + 1):
        b = bars[j]
        if stop is not None and ((side == 1 and b["l"] <= stop) or (side == -1 and b["h"] >= stop)):
            return (e, j, side, px, stop)
        if target is not None and ((side == 1 and b["h"] >= target) or (side == -1 and b["l"] <= target)):
            return (e, j, side, px, target)
    return (e, last, side, px, bars[last]["c"])


def strategies(bars):
    days = session_days(bars)
    dates = sorted(days)
    S = {k: [] for k in (
        "1. Opening-range breakout", "2. Overnight-range breakout",
        "3. Overnight breakout, tight nights only", "4. Previous-day high/low breakout",
        "5. Gap fade", "6. VWAP stretch fade", "7. Hourly RSI(2) pullback with trend",
        "8. Hourly 9/21 EMA crossover", "9. EIA reaction follow (Wednesdays)",
        "Benchmark: long 9:00-14:00 every day", "Benchmark: long overnight (14:00-9:00)")}
    on_ranges = []
    for k, d in enumerate(dates):
        ix = days[d]
        first, last = ix[0], ix[-1]
        # overnight candles: 18:00 previous evening to 8:00 today
        on = [i for i in range(max(0, first - 20), first)
              if bars[first]["t"] - bars[i]["t"] <= 15 * 3600]
        onh = max(bars[i]["h"] for i in on) if on else None
        onl = min(bars[i]["l"] for i in on) if on else None
        prev = days[dates[k - 1]] if k else None

        # benchmarks
        S["Benchmark: long 9:00-14:00 every day"].append((first - 1, last, 1, bars[first]["o"], bars[last]["c"]))
        if prev:
            S["Benchmark: long overnight (14:00-9:00)"].append(
                (prev[-1], first, 1, bars[prev[-1]]["c"], bars[first]["o"]))

        # 1. opening range
        rh, rl = bars[first]["h"], bars[first]["l"]
        for i in ix[1:-1]:
            if bars[i]["c"] > rh:
                S["1. Opening-range breakout"].append(manage(bars, i, 1, bars[i]["c"], rl, None, last)); break
            if bars[i]["c"] < rl:
                S["1. Opening-range breakout"].append(manage(bars, i, -1, bars[i]["c"], rh, None, last)); break

        # 2/3. overnight range
        if onh is not None:
            mid = (onh + onl) / 2
            width = (onh - onl) / mid
            tight = len(on_ranges) >= 20 and width < st.median(on_ranges[-20:])
            on_ranges.append(width)
            for i in ix[:-1]:
                side = 1 if bars[i]["c"] > onh else (-1 if bars[i]["c"] < onl else 0)
                if side:
                    tr = manage(bars, i, side, bars[i]["c"], mid, None, last)
                    S["2. Overnight-range breakout"].append(tr)
                    if tight:
                        S["3. Overnight breakout, tight nights only"].append(tr)
                    break

        # 4. previous-day high/low
        if prev:
            pdh = max(bars[i]["h"] for i in prev)
            pdl = min(bars[i]["l"] for i in prev)
            for i in ix[:-1]:
                b = bars[i]
                if b["c"] > pdh:
                    S["4. Previous-day high/low breakout"].append(manage(bars, i, 1, b["c"], b["c"] - b["atr"], None, last)); break
                if b["c"] < pdl:
                    S["4. Previous-day high/low breakout"].append(manage(bars, i, -1, b["c"], b["c"] + b["atr"], None, last)); break

        # 5. gap fade (enter at the 9:00 open)
        if prev:
            settle = bars[prev[-1]]["c"]
            op = bars[first]["o"]
            gap = op / settle - 1
            if abs(gap) > 0.0075:
                side = -1 if gap > 0 else 1
                stop = op + (op - settle)          # same distance the other way
                S["5. Gap fade"].append(manage(bars, first - 1, side, op, stop, settle, last))

        # 6. VWAP stretch fade (one per day)
        for i in ix[:-1]:
            b = bars[i]
            if b["c"] > b["vwap"] + 1.5 * b["atr"]:
                S["6. VWAP stretch fade"].append(manage(bars, i, -1, b["c"], b["c"] + b["atr"], b["vwap"], last)); break
            if b["c"] < b["vwap"] - 1.5 * b["atr"]:
                S["6. VWAP stretch fade"].append(manage(bars, i, 1, b["c"], b["c"] - b["atr"], b["vwap"], last)); break

        # 7. RSI(2) pullback with 200-hour trend (one per day)
        for i in ix[:-1]:
            b = bars[i]
            side = 1 if (b["c"] > b["sma200"] and b["rsi2"] < 10) else (
                -1 if (b["c"] < b["sma200"] and b["rsi2"] > 90) else 0)
            if side:
                stop = b["c"] - side * 2 * b["atr"]
                tr = manage(bars, i, side, b["c"], stop, None, last)
                # exit early when price crosses the 5-hour average
                for j in range(i + 1, tr[1] + 1):
                    if (side == 1 and bars[j]["c"] > bars[j]["sma5"]) or (side == -1 and bars[j]["c"] < bars[j]["sma5"]):
                        if j < tr[1]:
                            tr = (i, j, side, b["c"], bars[j]["c"])
                        break
                S["7. Hourly RSI(2) pullback with trend"].append(tr)
                break

        # 8. EMA crossover (first cross of the day)
        for i in ix[:-1]:
            a, p = bars[i], bars[i - 1]
            side = 1 if (a["ema9"] > a["ema21"] and p["ema9"] <= p["ema21"]) else (
                -1 if (a["ema9"] < a["ema21"] and p["ema9"] >= p["ema21"]) else 0)
            if side:
                x = last
                for j in range(i + 1, last + 1):
                    if (side == 1 and bars[j]["ema9"] < bars[j]["ema21"]) or (side == -1 and bars[j]["ema9"] > bars[j]["ema21"]):
                        x = j
                        break
                S["8. Hourly 9/21 EMA crossover"].append((i, x, side, a["c"], bars[x]["c"]))
                break

        # 9. EIA reaction follow
        if bars[first]["et"].weekday() == 2:
            r10 = [i for i in ix if bars[i]["et"].hour == 10]
            if r10:
                i = r10[0]
                mv = bars[i]["c"] / bars[i]["o"] - 1
                if abs(mv) > 0.003:
                    side = 1 if mv > 0 else -1
                    S["9. EIA reaction follow (Wednesdays)"].append(
                        manage(bars, i, side, bars[i]["c"], bars[i]["o"], None, last))
    return S


def returns(trades, cost):
    return [s * (x / e - 1) - 2 * cost for _, _, s, e, x in trades]


def stats(rets):
    eq = peak = 1.0
    mdd = 0.0
    for r in rets:
        eq *= 1 + r
        peak = max(peak, eq)
        mdd = max(mdd, 1 - eq / peak)
    w = [r for r in rets if r > 0]
    l = [-r for r in rets if r <= 0]
    return dict(n=len(rets), win=len(w) / len(rets) if rets else 0,
                pf=(sum(w) / sum(l)) if sum(l) > 0 else float("inf"),
                avg=st.mean(rets) if rets else 0, total=eq - 1, mdd=mdd)


def luck(bars, trades, cost, sims=500, seed=11):
    if not trades:
        return None
    real = 1.0
    for r in returns(trades, cost):
        real *= 1 + r
    pool = [i for i, b in enumerate(bars) if b["et"].weekday() < 5 and 9 <= b["et"].hour <= 13]
    rng = random.Random(seed)
    beat = 0
    for _ in range(sims):
        eq = 1.0
        for e, x, s, _, _ in trades:
            ln = max(1, x - e)
            i = rng.choice(pool)
            if i + ln >= len(bars):
                i = pool[0]
            eq *= 1 + s * (bars[i + ln]["c"] / bars[i]["c"] - 1) - 2 * cost
        beat += real > eq
    return beat / sims


def pct(x):
    return f"{x * 100:+.1f}%"


def main():
    bars = load()
    add_indicators(bars)
    S = strategies(bars)
    d0, d1 = bars[0]["et"].date(), bars[-1]["et"].date()
    mid_t = bars[len(bars) // 2]["t"]
    out = ["# Oil day-trading study", "",
           f"Run {dt.datetime.now(dt.timezone.utc):%Y-%m-%d %H:%M} UTC on hourly WTI futures (CL=F), "
           f"{d0} to {d1}. Rules fixed before testing; all trades closed by about 15:00 New York; "
           "whole account per trade.", "",
           "**Luck check** = share of 500 random strategies (same trades, direction and holding "
           "time at random session hours) that the real one beat. 95%+ would suggest a real edge.", "",
           "| Strategy | Trades | Win rate | Avg per trade (0.02% cost) | Total, low cost 0.02% | "
           "Total, main cost 0.10% | Profit factor (low) | Worst drop (low) | "
           "1st half / 2nd half (low) | Luck check (low) |",
           "|---|---|---|---|---|---|---|---|---|---|"]
    for name, tr in S.items():
        lo, mn = stats(returns(tr, LOW)), stats(returns(tr, MAIN))
        h1 = stats(returns([t for t in tr if bars[t[0]]["t"] < mid_t], LOW))["total"]
        h2 = stats(returns([t for t in tr if bars[t[0]]["t"] >= mid_t], LOW))["total"]
        lk = luck(bars, tr, LOW) if not name.startswith("Benchmark") else None
        out.append(f"| {name} | {lo['n']} | {lo['win']:.0%} | {lo['avg'] * 100:+.3f}% | {pct(lo['total'])} | "
                   f"{pct(mn['total'])} | {lo['pf']:.2f} | -{lo['mdd']:.0%} | {pct(h1)} / {pct(h2)} | "
                   f"{'-' if lk is None else format(lk, '.0%')} |")
    out.append("")
    text = "\n".join(out)
    with open(os.path.join(HERE, "oil_daytrade_results.md"), "w") as f:
        f.write(text)
    print(text)


if __name__ == "__main__":
    main()
