#!/usr/bin/env python3
"""Study: does time-series momentum (trend following) work on BTC and oil?

Textbook rule (Moskowitz, Ooi & Pedersen 2012; Liu & Tsyvinski 2021):
at each rebalance date, look at the return over the past N days.
  - positive -> hold the asset (long)
  - negative -> cash (long/cash version) or short (long/short version)
Optional volatility sizing: hold less when the market is wild, so the
position's expected yearly volatility is at most a target (BTC 50%, oil 25%).
Never more than 100% of the account (no leverage).

Rebalance: BTC weekly, oil monthly. Cost: 0.10% of each change in position.
Data: Yahoo Finance daily closes (BTC-USD since 2014, CL=F since 2000,
USO since 2006).

To avoid picking the luckiest setting, the lookback is chosen on the FIRST
half of the history only, then judged on the SECOND half, which it never saw.

Luck check: the same positions are shuffled between rebalance periods 500
times (same time invested, random timing); the share of shuffles the real
strategy beats on Sharpe ratio is reported.
Carry and the pre-Fed drift are not tested: there is no free data here for
second-month oil futures or for the full FOMC calendar.
"""
import datetime as dt
import json
import math
import os
import random
import statistics as st
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
COST = 0.001


def daily(symbol):
    now = int(dt.datetime.now().timestamp())
    url = (f"https://query2.finance.yahoo.com/v8/finance/chart/{urllib.request.quote(symbol)}"
           f"?period1=946684800&period2={now}&interval=1d")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        j = json.load(r)["chart"]["result"][0]
    cl = j["indicators"]["quote"][0]["close"]
    out = [(dt.datetime.fromtimestamp(t, dt.timezone.utc).date(), c)
           for t, c in zip(j["timestamp"], cl) if c is not None and c > 1]
    return out


def rebalance_days(dates, freq):
    idx, last = [], None
    for i, d in enumerate(dates):
        key = (d.isocalendar()[0], d.isocalendar()[1]) if freq == "W" else (d.year, d.month)
        if key != last:
            idx.append(i)
            last = key
    return idx


def backtest(px, lookback, freq, short, vol_target, per_year):
    """Return list of daily strategy returns and the position used each day."""
    dates = [d for d, _ in px]
    c = [p for _, p in px]
    rets = [0.0] + [c[i] / c[i - 1] - 1 for i in range(1, len(c))]
    rb = set(rebalance_days(dates, freq))
    pos, daily_r, positions = 0.0, [], []
    for i in range(len(c)):
        r = pos * rets[i]                       # position decided earlier earns today's move
        if i in rb and i >= lookback:
            sig = c[i] / c[i - lookback] - 1
            new = 1.0 if sig > 0 else (-1.0 if short else 0.0)
            if vol_target and i >= 30:
                vol = st.pstdev(rets[i - 29:i + 1]) * math.sqrt(per_year)
                new *= min(1.0, vol_target / vol) if vol > 0 else 1.0
            r -= abs(new - pos) * COST
            pos = new
        daily_r.append(r)
        positions.append(pos)
    return daily_r, positions


def metrics(dr, per_year):
    eq = peak = 1.0
    mdd = 0.0
    for r in dr:
        eq *= 1 + r
        peak = max(peak, eq)
        mdd = max(mdd, 1 - eq / peak)
    yrs = len(dr) / per_year
    cagr = eq ** (1 / yrs) - 1 if eq > 0 else -1
    sd = st.pstdev(dr)
    sharpe = (st.mean(dr) / sd) * math.sqrt(per_year) if sd > 0 else 0
    return dict(cagr=cagr, mdd=mdd, sharpe=sharpe, total=eq - 1)


def luck(px, lookback, freq, short, vol_target, per_year, sims=500, seed=3):
    dates = [d for d, _ in px]
    c = [p for _, p in px]
    rets = [0.0] + [c[i] / c[i - 1] - 1 for i in range(1, len(c))]
    dr, pos = backtest(px, lookback, freq, short, vol_target, per_year)
    real = metrics(dr, per_year)["sharpe"]
    rb = rebalance_days(dates, freq)
    blocks = [(a, b) for a, b in zip(rb, rb[1:] + [len(c)])]
    held = [pos[a] for a, _ in blocks]          # position chosen at each rebalance
    rng = random.Random(seed)
    beat = 0
    for _ in range(sims):
        sh = held[:]
        rng.shuffle(sh)
        out, prev = [], 0.0
        for (a, b), p in zip(blocks, sh):
            for i in range(a, b):
                r = prev * rets[i] if i == a else p * rets[i]
                if i == a:
                    r -= abs(p - prev) * COST
                out.append(r)
            prev = p
        beat += real > metrics(out, per_year)["sharpe"]
    return beat / sims


def pct(x):
    return f"{x * 100:+.1f}%"


def study(name, px, freq, lookbacks, vol_target, per_year):
    half = len(px) // 2
    first, second = px[:half], px[half:]
    bh_all = metrics([0.0] + [px[i][1] / px[i - 1][1] - 1 for i in range(1, len(px))], per_year)
    bh_2 = metrics([0.0] + [second[i][1] / second[i - 1][1] - 1 for i in range(1, len(second))], per_year)
    lines = [f"## {name} ({px[0][0]} to {px[-1][0]})", "",
             f"Buy and hold: {pct(bh_all['cagr'])} a year, worst drop -{bh_all['mdd']:.0%}, "
             f"Sharpe {bh_all['sharpe']:.2f}. Second half only: {pct(bh_2['cagr'])} a year, "
             f"worst drop -{bh_2['mdd']:.0%}, Sharpe {bh_2['sharpe']:.2f}.", "",
             "| Rule | Lookback | Per year (all) | Worst drop | Sharpe | 1st half Sharpe | "
             "2nd half per year | 2nd half worst drop | 2nd half Sharpe | Luck check |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    best = None
    for short in (False, True):
        for vt in (None, vol_target):
            for lb in lookbacks:
                a = metrics(backtest(px, lb, freq, short, vt, per_year)[0], per_year)
                f1 = metrics(backtest(first, lb, freq, short, vt, per_year)[0], per_year)
                s2 = metrics(backtest(second, lb, freq, short, vt, per_year)[0], per_year)
                lk = luck(px, lb, freq, short, vt, per_year)
                rule = ("long/short" if short else "long/cash") + (" + vol sizing" if vt else "")
                lines.append(f"| {rule} | {lb} days | {pct(a['cagr'])} | -{a['mdd']:.0%} | {a['sharpe']:.2f} | "
                             f"{f1['sharpe']:.2f} | {pct(s2['cagr'])} | -{s2['mdd']:.0%} | {s2['sharpe']:.2f} | {lk:.0%} |")
                cand = (f1["sharpe"], rule, lb, short, vt, s2, lk)
                if best is None or cand[0] > best[0]:
                    best = cand
    f1s, rule, lb, short, vt, s2, lk = best
    lines += ["", f"**Chosen on the first half only:** {rule}, {lb}-day lookback "
              f"(first-half Sharpe {f1s:.2f}). **On the unseen second half:** {pct(s2['cagr'])} a year, "
              f"worst drop -{s2['mdd']:.0%}, Sharpe {s2['sharpe']:.2f} vs buy and hold Sharpe "
              f"{bh_2['sharpe']:.2f}. Luck check {lk:.0%}.", ""]
    return lines, dict(rule=rule, lookback=lb, short=short, vol_target=vt, second=s2, bh2=bh_2, luck=lk)


def main():
    out = ["# Trend-following (time-series momentum) study", "",
           f"Run {dt.datetime.now(dt.timezone.utc):%Y-%m-%d %H:%M} UTC. 0.10% cost per position change. "
           "No leverage. Sharpe = return per unit of risk (higher is better; buy and hold is the bar).", ""]
    picks = {}
    btc = daily("BTC-USD")
    l, picks["BTC"] = study("BTC (weekly rebalance)", btc, "W", (7, 14, 28, 56, 91, 182, 365), 0.5, 365)
    out += l
    for sym in ("CL=F", "USO"):
        px = daily(sym)
        l, picks[sym] = study(f"Oil {sym} (monthly rebalance)", px, "M", (21, 63, 126, 252), 0.25, 252)
        out += l
    text = "\n".join(out)
    with open(os.path.join(HERE, "edge_study_results.md"), "w") as f:
        f.write(text)
    print(text)
    json.dump({k: {kk: vv for kk, vv in v.items() if kk not in ("second", "bh2")} for k, v in picks.items()},
              open(os.path.join(HERE, "edge_study_picks.json"), "w"), indent=2)


if __name__ == "__main__":
    main()
