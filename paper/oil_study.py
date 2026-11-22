#!/usr/bin/env python3
"""Study: do popular crude-oil trading strategies actually work?

The rules below were written down before running any test. They come from
public strategy write-ups (Quantified Strategies, CXO Advisory,
SentimenTrader, Turtle rules, ORB guides).

Daily strategies are tested on two price series from Yahoo Finance:
  - USO (United States Oil Fund, since 2006): what a retail trader can
    actually buy, including the cost of rolling futures.
  - CL=F (front-month WTI futures, since 2000): the raw oil price. Days with a
    price at or below $1 (April 2020) are skipped.
The intraday strategy uses 2 years of hourly CL=F candles.

Every trade enters at the next bar's open after a signal and pays a cost per
side (0.10% main, 0.30% stress). The whole account goes into each trade.

Luck check: each strategy is compared with 500 random strategies that make the
same number of trades with the same holding times at random dates. If the real
strategy does not beat most of the random ones, its rules add nothing.

Usage: python3 paper/oil_study.py   (writes paper/oil_study_results.md)
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
COST, STRESS = 0.001, 0.003


def yahoo(symbol, rng, interval):
    span = (f"period1=946684800&period2={int(dt.datetime.now().timestamp())}" if rng == "max"
            else f"range={rng}")          # "max" thins daily data, so ask for exact dates
    url = (f"https://query2.finance.yahoo.com/v8/finance/chart/{urllib.request.quote(symbol)}"
           f"?{span}&interval={interval}")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        j = json.load(r)["chart"]["result"][0]
    q = j["indicators"]["quote"][0]
    bars = []
    for i, t in enumerate(j["timestamp"]):
        o, h, lo, c = (q[k][i] for k in ("open", "high", "low", "close"))
        if None in (o, h, lo, c) or min(o, c, lo) <= 1:
            continue
        bars.append(dict(t=t, o=o, h=h, l=lo, c=c))
    return bars


# ---------- indicators ----------
def sma(xs, n, i):
    return sum(xs[i - n + 1:i + 1]) / n if i >= n - 1 else None


def rsi_series(c, n):
    out = [None] * len(c)
    if len(c) <= n:
        return out
    g = sum(max(c[i] - c[i - 1], 0) for i in range(1, n + 1)) / n
    l = sum(max(c[i - 1] - c[i], 0) for i in range(1, n + 1)) / n
    out[n] = 100 if l == 0 else 100 - 100 / (1 + g / l)
    for i in range(n + 1, len(c)):
        d = c[i] - c[i - 1]
        g = (g * (n - 1) + max(d, 0)) / n
        l = (l * (n - 1) + max(-d, 0)) / n
        out[i] = 100 if l == 0 else 100 - 100 / (1 + g / l)
    return out


# ---------- daily strategies: return list of (entry_idx, exit_idx, side) ----------
def run_rules(bars, want):
    """want(i, pos) -> new position (-1, 0, 1) decided at bar i's close.
    Trades fill at bar i+1's open."""
    trades, pos, ent = [], 0, None
    for i in range(len(bars) - 1):
        new = want(i, pos)
        if new != pos:
            if pos != 0:
                trades.append((ent, i + 1, pos))
            pos, ent = new, (i + 1 if new != 0 else None)
    if pos != 0:
        trades.append((ent, len(bars) - 1, pos))
    return trades


def daily_strategies(bars):
    c = [b["c"] for b in bars]
    hi = [b["h"] for b in bars]
    lo = [b["l"] for b in bars]
    r2, r14 = rsi_series(c, 2), rsi_series(c, 14)
    month = [dt.datetime.fromtimestamp(b["t"], dt.timezone.utc).month for b in bars]

    def ma_cross(long_short):
        def f(i, pos):
            a, b = sma(c, 50, i), sma(c, 200, i)
            if b is None:
                return 0
            return 1 if a > b else (-1 if long_short else 0)
        return f

    def donchian(long_short):
        def f(i, pos):
            if i < 21:
                return 0
            h20, l20 = max(hi[i - 20:i]), min(lo[i - 20:i])
            h10, l10 = max(hi[i - 10:i]), min(lo[i - 10:i])
            if pos == 1 and c[i] < l10:
                pos = 0
            if pos == -1 and c[i] > h10:
                pos = 0
            if pos == 0 and c[i] > h20:
                return 1
            if pos == 0 and long_short and c[i] < l20:
                return -1
            return pos
        return f

    def rsi2(i, pos):
        s200, s5 = sma(c, 200, i), sma(c, 5, i)
        if s200 is None or r2[i] is None:
            return 0
        if pos == 1:
            return 0 if c[i] > s5 else 1
        return 1 if (c[i] > s200 and r2[i] < 10) else 0

    def rsi14(i, pos):
        if r14[i] is None:
            return 0
        if pos == 1:
            return 0 if r14[i] > 50 else 1
        return 1 if r14[i] < 30 else 0

    def bollinger(i, pos):
        m = sma(c, 20, i)
        if m is None:
            return 0
        sd = st.pstdev(c[i - 19:i + 1])
        if pos == 1:
            return 0 if c[i] > m else 1
        return 1 if c[i] < m - 2 * sd else 0

    def season_spring(i, pos):          # long March-April, flat otherwise
        nxt = month[i + 1] if i + 1 < len(month) else month[i]
        return 1 if nxt in (3, 4) else 0

    def season_short_novdec(i, pos):    # short November-December
        nxt = month[i + 1] if i + 1 < len(month) else month[i]
        return -1 if nxt in (11, 12) else 0

    return {
        "50/200-day trend, long only": run_rules(bars, ma_cross(False)),
        "50/200-day trend, long and short": run_rules(bars, ma_cross(True)),
        "Turtle 20/10-day breakout, long only": run_rules(bars, donchian(False)),
        "Turtle 20/10-day breakout, long and short": run_rules(bars, donchian(True)),
        "RSI(2) dip-buy above 200-day avg": run_rules(bars, rsi2),
        "RSI(14) oversold (<30, exit >50)": run_rules(bars, rsi14),
        "Bollinger band dip-buy": run_rules(bars, bollinger),
        "Seasonal: long March-April": run_rules(bars, season_spring),
        "Seasonal: short Nov-Dec": run_rules(bars, season_short_novdec),
    }


# ---------- intraday: opening-range breakout on hourly CL=F ----------
def orb_trades(hbars):
    """First New York hour (9:00-10:00 ET) sets the range. A later hourly
    close above the high buys, below the low sells short. Stop = other side
    of the range. Exit at the 14:00 ET bar close (before the 14:30 settle).
    One trade per day. Returns list of (entry_px, exit_px, side, et_date)."""
    days = {}
    for b in hbars:
        t = dt.datetime.fromtimestamp(b["t"], dt.timezone.utc).astimezone(ET)
        if t.weekday() < 5:
            days.setdefault(t.date(), []).append((t.hour, b))
    out = []
    for d, rows in sorted(days.items()):
        rows.sort(key=lambda x: x[0])
        rng = [b for h, b in rows if h == 9]
        later = [(h, b) for h, b in rows if 10 <= h <= 14]
        if not rng or len(later) < 3:
            continue
        rh, rl = rng[0]["h"], rng[0]["l"]
        side = entry = None
        for k, (h, b) in enumerate(later):
            if side is None:
                if h < 14 and b["c"] > rh:
                    side, entry, stop = 1, b["c"], rl
                elif h < 14 and b["c"] < rl:
                    side, entry, stop = -1, b["c"], rh
                continue
            if side == 1 and b["l"] <= stop:
                out.append((entry, stop, 1, d)); break
            if side == -1 and b["h"] >= stop:
                out.append((entry, stop, -1, d)); break
            if h == 14:
                out.append((entry, b["c"], side, d)); break
        else:
            if side is not None:
                out.append((entry, later[-1][1]["c"], side, d))
    return out


# ---------- scoring ----------
def trade_returns(bars, trades, cost):
    rets = []
    for e, x, side in trades:
        pe, px = bars[e]["o"], bars[x]["o"] if x < len(bars) else bars[-1]["c"]
        rets.append(side * (px / pe - 1) - 2 * cost)
    return rets


def stats(rets, years):
    eq, peak, mdd = 1.0, 1.0, 0.0
    for r in rets:
        eq *= 1 + r
        peak = max(peak, eq)
        mdd = max(mdd, 1 - eq / peak)
    wins = [r for r in rets if r > 0]
    losses = [-r for r in rets if r <= 0]
    pf = sum(wins) / sum(losses) if losses and sum(losses) > 0 else float("inf")
    cagr = eq ** (1 / years) - 1 if years > 0 and eq > 0 else -1.0
    return dict(total=eq - 1, cagr=cagr, mdd=mdd, n=len(rets),
                win=len(wins) / len(rets) if rets else 0, pf=pf)


def luck_check(bars, trades, cost, sims=500, seed=7):
    """Share of random strategies (same count, same holding lengths, random
    start dates, same long/short mix) that the real one beats."""
    if not trades:
        return None
    rng = random.Random(seed)
    real = 1.0
    for r in trade_returns(bars, trades, cost):
        real *= 1 + r
    lengths = [x - e for e, x, _ in trades]
    sides = [s for _, _, s in trades]
    n = len(bars)
    beaten = 0
    for _ in range(sims):
        eq = 1.0
        for ln, sd in zip(lengths, sides):
            e = rng.randrange(0, max(1, n - ln - 1))
            eq *= 1 + sd * (bars[e + ln]["o"] / bars[e]["o"] - 1) - 2 * cost
        beaten += real > eq
    return beaten / sims


def fmt_pct(x):
    return f"{x * 100:+.1f}%"


def main():
    out = ["# Oil strategy study", "",
           f"Run {dt.datetime.now(dt.timezone.utc):%Y-%m-%d %H:%M} UTC. Rules fixed before testing. "
           "Whole account in each trade; next-bar-open fills; 0.10% cost per side (0.30% stress).",
           "",
           "**Luck check** = share of 500 random strategies (same number of trades and holding "
           "times, random dates) that the real strategy beat. Around 50% = no better than chance; "
           "95%+ = unlikely to be luck.", ""]
    for sym, rng_ in (("USO", "max"), ("CL=F", "max")):
        bars = yahoo(sym, rng_, "1d")
        if sym == "CL=F":
            bars = [b for b in bars if b["t"] >= dt.datetime(2000, 1, 1, tzinfo=dt.timezone.utc).timestamp()]
        y0 = dt.datetime.fromtimestamp(bars[0]["t"], dt.timezone.utc)
        y1 = dt.datetime.fromtimestamp(bars[-1]["t"], dt.timezone.utc)
        years = (y1 - y0).days / 365.25
        bh = bars[-1]["c"] / bars[0]["o"] - 1
        bh_cagr = (1 + bh) ** (1 / years) - 1
        out += [f"## Daily strategies on {sym} ({y0:%Y-%m-%d} to {y1:%Y-%m-%d}, {years:.1f} years)", "",
                f"Buy and hold: {fmt_pct(bh)} total, {fmt_pct(bh_cagr)} a year.", "",
                "| Strategy | Trades | Win rate | Profit factor | Total | Per year | Worst drop | "
                "Per year at stress cost | 1st half / 2nd half per year | Luck check |",
                "|---|---|---|---|---|---|---|---|---|---|"]
        mid = len(bars) // 2
        for name, trades in daily_strategies(bars).items():
            s = stats(trade_returns(bars, trades, COST), years)
            s3 = stats(trade_returns(bars, trades, STRESS), years)
            h1 = [t for t in trades if t[0] < mid]
            h2 = [t for t in trades if t[0] >= mid]
            a = stats(trade_returns(bars, h1, COST), years / 2)["cagr"]
            b = stats(trade_returns(bars, h2, COST), years / 2)["cagr"]
            lk = luck_check(bars, trades, COST)
            out.append(f"| {name} | {s['n']} | {s['win']:.0%} | {s['pf']:.2f} | {fmt_pct(s['total'])} | "
                       f"{fmt_pct(s['cagr'])} | -{s['mdd']:.0%} | {fmt_pct(s3['cagr'])} | "
                       f"{fmt_pct(a)} / {fmt_pct(b)} | {"-" if lk is None else format(lk, ".0%")} |")
        out.append("")

    hb = yahoo("CL=F", "730d", "60m")
    ot = orb_trades(hb)
    days = sorted({d for *_, d in ot})
    yrs = (days[-1] - days[0]).days / 365.25 if days else 1
    out += [f"## Intraday: opening-range breakout on hourly CL=F ({days[0]} to {days[-1]})", "",
            "First New York hour sets the range; trade a close outside it; stop at the other side; "
            "exit by 14:00 New York.", "",
            "| Variant | Trades | Win rate | Profit factor | Total | Worst drop | Total at stress cost |",
            "|---|---|---|---|---|---|---|"]
    variants = {
        "All days, long and short": ot,
        "Long only": [t for t in ot if t[2] == 1],
        "Skip Wednesdays (EIA report)": [t for t in ot if t[3].weekday() != 2],
    }
    for name, tr in variants.items():
        for cost_label, cost in (("main", COST), ("stress", STRESS)):
            rets = [s * (x / e - 1) - 2 * cost for e, x, s, _ in tr]
            if cost_label == "main":
                s = stats(rets, yrs)
            else:
                s3 = stats(rets, yrs)
        out.append(f"| {name} | {s['n']} | {s['win']:.0%} | {s['pf']:.2f} | {fmt_pct(s['total'])} | "
                   f"-{s['mdd']:.0%} | {fmt_pct(s3['total'])} |")
    out.append("")
    text = "\n".join(out)
    with open(os.path.join(HERE, "oil_study_results.md"), "w") as f:
        f.write(text)
    print(text)


if __name__ == "__main__":
    main()
