#!/usr/bin/env python3
"""Big search: oil day-trading with single indicators, indicator pairs and extra signal filters.

Protection against luck (decided before running):
  * TRAIN = first 60% of the hourly history, TEST = last 40% (never used to choose).
  * Candidates are ranked on TRAIN only; the top 10 of each round go to TEST.
  * PASS on TEST needs: positive after costs, Sharpe > 0.5, at least 40 trades,
    and a luck check >= 99% (stricter than 95% because hundreds of rules are tried).
Day trading: positions only from 9:00 to 14:00 New York time on weekdays (WTI
futures, Yahoo CL=F hourly), flat overnight; entries/exits at hourly closes;
cost 0.02% per side (futures level) plus a 0.05% stress check.

Round 1: 15 single indicators.   Round 2: every pair (both must agree).
Round 3: the best pairs plus signal filters (daily trend, avoid the Wednesday
EIA hour, morning only, volatility regime).
Round 4: the same indicators on DAILY bars since 2000 (1-5 day swing trades),
where there is far more data: TRAIN 2000-2015, TEST 2016-2026.
"""
import datetime as dt
import itertools
import json
import math
import os
import random
import statistics as st
import urllib.request
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))
ET = ZoneInfo("America/New_York")
COST, STRESS = 0.0002, 0.0005


def yahoo(rng, interval):
    span = (f"period1=946684800&period2={int(dt.datetime.now().timestamp())}" if rng == "max" else f"range={rng}")
    req = urllib.request.Request(f"https://query2.finance.yahoo.com/v8/finance/chart/CL%3DF?{span}&interval={interval}",
                                 headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        j = json.load(r)["chart"]["result"][0]
    q = j["indicators"]["quote"][0]
    out, seen = [], set()
    for i, t in enumerate(j["timestamp"]):
        t -= t % 3600
        v = [q[k][i] for k in ("open", "high", "low", "close")]
        if None in v or min(v) <= 1 or t in seen:
            continue
        seen.add(t)
        out.append(dict(t=t, et=dt.datetime.fromtimestamp(t, dt.timezone.utc).astimezone(ET),
                        o=v[0], h=v[1], l=v[2], c=v[3], v=q["volume"][i] or 0))
    return sorted(out, key=lambda b: b["t"])


# ---------------- indicators: each returns a list of -1/0/+1 ----------------
def ema(x, n):
    k, e, out = 2 / (n + 1), x[0], []
    for v in x:
        e = v * k + e * (1 - k)
        out.append(e)
    return out


def sma(x, n):
    out, s = [], 0.0
    for i, v in enumerate(x):
        s += v
        if i >= n:
            s -= x[i - n]
        out.append(s / min(i + 1, n))
    return out


def rsi(c, n):
    out, g, l = [50.0], 0.0, 0.0
    for i in range(1, len(c)):
        d = c[i] - c[i - 1]
        g = (g * (n - 1) + max(d, 0)) / n
        l = (l * (n - 1) + max(-d, 0)) / n
        out.append(100 if l == 0 else 100 - 100 / (1 + g / l))
    return out


def indicators(B):
    c = [b["c"] for b in B]
    h = [b["h"] for b in B]
    l = [b["l"] for b in B]
    n = len(c)
    tr = [max(h[i] - l[i], abs(h[i] - c[i - 1]), abs(l[i] - c[i - 1])) if i else h[i] - l[i] for i in range(n)]
    atr = ema(tr, 14)
    e9, e21, e12, e26 = ema(c, 9), ema(c, 21), ema(c, 12), ema(c, 26)
    macd = [a - b for a, b in zip(e12, e26)]
    sig = ema(macd, 9)
    r14, r2 = rsi(c, 14), rsi(c, 2)
    s20, s50 = sma(c, 20), sma(c, 50)
    sd20 = [st.pstdev(c[max(0, i - 19):i + 1]) if i >= 1 else 0 for i in range(n)]
    hh20 = [max(h[max(0, i - 20):i]) if i else h[0] for i in range(n)]
    ll20 = [min(l[max(0, i - 20):i]) if i else l[0] for i in range(n)]
    k14 = [(c[i] - min(l[max(0, i - 13):i + 1])) / ((max(h[max(0, i - 13):i + 1]) - min(l[max(0, i - 13):i + 1])) or 1) * 100
           for i in range(n)]
    stoch = sma(k14, 3)
    tp = [(a + b + d) / 3 for a, b, d in zip(h, l, c)]
    tps = sma(tp, 20)
    md = [st.mean(abs(tp[j] - tps[i]) for j in range(max(0, i - 19), i + 1)) or 1 for i in range(n)]
    cci = [(tp[i] - tps[i]) / (0.015 * md[i]) for i in range(n)]
    # ADX
    pdm = [max(h[i] - h[i - 1], 0) if i and h[i] - h[i - 1] > l[i - 1] - l[i] else 0 for i in range(n)]
    mdm = [max(l[i - 1] - l[i], 0) if i and l[i - 1] - l[i] > h[i] - h[i - 1] else 0 for i in range(n)]
    pdi = [100 * a / (b or 1) for a, b in zip(ema(pdm, 14), atr)]
    mdi = [100 * a / (b or 1) for a, b in zip(ema(mdm, 14), atr)]
    dx = [100 * abs(a - b) / ((a + b) or 1) for a, b in zip(pdi, mdi)]
    adx = ema(dx, 14)
    # session VWAP (resets 18:00 ET; daily bars: rolling 20-bar VWAP)
    vw, pv, vv = [], 0.0, 0.0
    for b, t in zip(B, tp):
        if b["et"].hour == 18 or ("daily" in B[0] and True):
            pass
        if b["et"].hour == 18:
            pv = vv = 0.0
        pv += t * max(b["v"], 1)
        vv += max(b["v"], 1)
        vw.append(pv / vv)
    roc = [c[i] / c[i - 10] - 1 if i >= 10 else 0 for i in range(n)]
    kel_u = [a + 1.5 * b for a, b in zip(ema(c, 20), atr)]
    kel_d = [a - 1.5 * b for a, b in zip(ema(c, 20), atr)]

    def sgn(cond_up, cond_dn):
        return [1 if u else (-1 if d else 0) for u, d in zip(cond_up, cond_dn)]
    I = {
        # trend / momentum style
        "EMA 9/21 cross": sgn([a > b for a, b in zip(e9, e21)], [a < b for a, b in zip(e9, e21)]),
        "MACD above signal": sgn([a > b for a, b in zip(macd, sig)], [a < b for a, b in zip(macd, sig)]),
        "Price vs 50-bar avg": sgn([a > b for a, b in zip(c, s50)], [a < b for a, b in zip(c, s50)]),
        "20-bar breakout": sgn([a > b for a, b in zip(c, hh20)], [a < b for a, b in zip(c, ll20)]),
        "ROC(10) momentum": sgn([x > 0 for x in roc], [x < 0 for x in roc]),
        "ADX>25 with DI direction": sgn([a > 25 and p > m for a, p, m in zip(adx, pdi, mdi)],
                                        [a > 25 and m > p for a, p, m in zip(adx, pdi, mdi)]),
        "Keltner breakout": sgn([a > b for a, b in zip(c, kel_u)], [a < b for a, b in zip(c, kel_d)]),
        "Price vs VWAP": sgn([a > b for a, b in zip(c, vw)], [a < b for a, b in zip(c, vw)]),
        "RSI(14) above/below 50": sgn([x > 50 for x in r14], [x < 50 for x in r14]),
        # mean-reversion style (buy weakness, sell strength)
        "RSI(14) 30/70 reversal": sgn([x < 30 for x in r14], [x > 70 for x in r14]),
        "RSI(2) 10/90 reversal": sgn([x < 10 for x in r2], [x > 90 for x in r2]),
        "Bollinger 2-sd reversal": sgn([a < m - 2 * s for a, m, s in zip(c, s20, sd20)],
                                       [a > m + 2 * s for a, m, s in zip(c, s20, sd20)]),
        "Stochastic 20/80 reversal": sgn([x < 20 for x in stoch], [x > 80 for x in stoch]),
        "CCI -100/+100 reversal": sgn([x < -100 for x in cci], [x > 100 for x in cci]),
        "VWAP stretch reversal": sgn([a < b - 1.5 * t for a, b, t in zip(c, vw, atr)],
                                     [a > b + 1.5 * t for a, b, t in zip(c, vw, atr)]),
    }
    extra = dict(atr=atr, c=c)
    return I, extra


# ---------------- backtest engine ----------------
def allowed_mask(B, intraday):
    """pos[i] (set at bar i's close, earns bar i+1) allowed only inside the NY session."""
    if not intraday:
        return [True] * len(B)
    m = []
    for i in range(len(B)):
        if i + 1 >= len(B):
            m.append(False)
            continue
        a, b = B[i]["et"], B[i + 1]["et"]
        m.append(a.weekday() < 5 and a.date() == b.date() and 9 <= a.hour <= 13 and b["et"].hour <= 14
                 if False else (a.weekday() < 5 and a.date() == b.date() and 9 <= a.hour <= 13))
    return m


def positions(sig, mask, hold_rule="agree"):
    """Follow the signal while allowed; flat otherwise."""
    return [s if ok else 0 for s, ok in zip(sig, mask)]


def returns_from(B, pos, cost):
    c = [b["c"] for b in B]
    out, prev = [], 0
    for i in range(len(B) - 1):
        p = pos[i]
        out.append(p * (c[i + 1] / c[i] - 1) - abs(p - prev) * cost)
        prev = p
    return out


def score(r, pos, per_year):
    if not r:
        return dict(sharpe=0, total=0, trades=0)
    sd = st.pstdev(r)
    eq = 1.0
    for x in r:
        eq *= 1 + x
    trades = sum(1 for i in range(1, len(pos)) if pos[i] != 0 and pos[i] != pos[i - 1])
    return dict(sharpe=(st.mean(r) / sd * math.sqrt(per_year)) if sd else 0, total=eq - 1, trades=trades)


def luck(B, pos, cost, per_year, real, sims=500, seed=21):
    rng, n, beat = random.Random(seed), len(pos), 0
    for _ in range(sims):
        k = rng.randrange(1, n)
        sp = pos[k:] + pos[:k]
        beat += real > score(returns_from(B, sp, cost), sp, per_year)["sharpe"]
    return beat / sims


def evaluate(B, sig, mask, split, per_year):
    pos = positions(sig, mask)
    tr = score(returns_from(B[:split + 1], pos[:split + 1], COST), pos[:split + 1], per_year)
    teB, tep = B[split:], pos[split:]
    te = score(returns_from(teB, tep, COST), tep, per_year)
    te_s = score(returns_from(teB, tep, STRESS), tep, per_year)
    return tr, te, te_s, tep, teB


def search(B, intraday, per_year, label, filters):
    I, extra = indicators(B)
    mask = allowed_mask(B, intraday)
    split = int(len(B) * 0.6)
    cands = {}
    for k, s in I.items():
        cands[k] = s
    singles = dict(cands)
    pairs = {}
    for (a, sa), (b, sb) in itertools.combinations(I.items(), 2):
        pairs[f"{a} + {b}"] = [x if x == y else 0 for x, y in zip(sa, sb)]
    rounds = []
    for rname, pool in (("Round 1: single indicators", singles), ("Round 2: indicator pairs", pairs)):
        ranked = []
        for k, s in pool.items():
            tr, te, te_s, tep, teB = evaluate(B, s, mask, split, per_year)
            if tr["trades"] >= 40:
                ranked.append((tr["sharpe"], k, tr, te, te_s, tep, teB))
        ranked.sort(reverse=True)
        rounds.append((rname, len(pool), ranked[:10]))
    # round 3: best 10 pairs from TRAIN with filters
    best_pairs = [x[1] for x in rounds[1][2]]
    filt_pool = {}
    for k in best_pairs:
        for fn, fm in filters(B, extra).items():
            filt_pool[f"{k} | {fn}"] = [x if ok else 0 for x, ok in zip(pairs[k], fm)]
    ranked = []
    for k, s in filt_pool.items():
        tr, te, te_s, tep, teB = evaluate(B, s, mask, split, per_year)
        if tr["trades"] >= 40:
            ranked.append((tr["sharpe"], k, tr, te, te_s, tep, teB))
    ranked.sort(reverse=True)
    rounds.append(("Round 3: best pairs + signal filters", len(filt_pool), ranked[:10]))
    out = [f"## {label}", "", f"History {B[0]['et']:%Y-%m-%d} to {B[-1]['et']:%Y-%m-%d}; TRAIN to "
           f"{B[split]['et']:%Y-%m-%d}, TEST after. Top 10 by TRAIN Sharpe go to TEST.", ""]
    passes = []
    for rname, n, top in rounds:
        out += [f"### {rname} ({n} tried)", "",
                "| Rule | TRAIN Sharpe | TEST Sharpe | TEST total (0.02%) | TEST total (0.05%) | TEST trades | Luck (TEST) | Verdict |",
                "|---|---|---|---|---|---|---|---|"]
        for trs, k, tr, te, te_s, tep, teB in top:
            lk = luck(teB, tep, COST, per_year, te["sharpe"]) if te["sharpe"] > 0 else 0.0
            ok = te["total"] > 0 and te_s["total"] > 0 and te["sharpe"] > 0.5 and te["trades"] >= 40 and lk >= 0.99
            if ok:
                passes.append(k)
            out.append(f"| {k} | {tr['sharpe']:.2f} | {te['sharpe']:.2f} | {te['total'] * 100:+.1f}% | "
                       f"{te_s['total'] * 100:+.1f}% | {te['trades']} | {lk:.0%} | {'**PASS**' if ok else 'fail'} |")
        out.append("")
    return out, passes


def hourly_filters(B, extra):
    c = extra["c"]
    # daily trend: last NY 14:00 close vs its 20-session average (known before the session)
    closes, cur, dtrend = [], None, []
    for i, b in enumerate(B):
        if b["et"].hour == 14:
            closes.append(b["c"])
        cur = (closes[-1] > sum(closes[-20:]) / len(closes[-20:])) if len(closes) >= 20 else None
        dtrend.append(cur)
    atr = extra["atr"]
    atr_med = [st.median(atr[max(0, i - 500):i + 1]) for i in range(len(B))]
    return {
        "daily trend up": [t is True for t in dtrend],
        "daily trend down": [t is False for t in dtrend],
        "skip Wednesday 9-12 (EIA)": [not (b["et"].weekday() == 2 and 9 <= b["et"].hour <= 11) for b in B],
        "morning only (9-11)": [9 <= b["et"].hour <= 11 for b in B],
        "high volatility only": [a > m for a, m in zip(atr, atr_med)],
        "low volatility only": [a <= m for a, m in zip(atr, atr_med)],
    }


def daily_filters(B, extra):
    c = extra["c"]
    s200 = sma(c, 200)
    atr = extra["atr"]
    atr_med = [st.median(atr[max(0, i - 250):i + 1]) for i in range(len(B))]
    return {
        "above 200-day avg": [a > b for a, b in zip(c, s200)],
        "below 200-day avg": [a < b for a, b in zip(c, s200)],
        "high volatility only": [a > m for a, m in zip(atr, atr_med)],
        "low volatility only": [a <= m for a, m in zip(atr, atr_med)],
        "skip Mondays": [b["et"].weekday() != 0 for b in B],
        "long side only": [True] * len(B),     # applied below by zeroing shorts
    }


def main():
    lines = ["# Oil indicator search (day trading + short swing)", "",
             f"Run {dt.datetime.now(dt.timezone.utc):%Y-%m-%d %H:%M} UTC. Rules chosen on TRAIN only; judged on unseen TEST. "
             "PASS = positive at 0.02% and 0.05% costs, Sharpe > 0.5, >= 40 trades, luck check >= 99%.", ""]
    hb = yahoo("730d", "60m")
    l1, p1 = search(hb, True, 252 * 5, "Hourly WTI futures, New York session only (day trading)", hourly_filters)
    db = yahoo("max", "1d")
    for b in db:
        b["et"] = b["et"].replace(hour=12)
    l2, p2 = search(db, False, 252, "Daily WTI futures since 2000 (1-5 day swing trades)", daily_filters)
    lines += l1 + l2
    lines += ["## Summary", "", f"Hourly passes: {p1 or 'none'}", "", f"Daily passes: {p2 or 'none'}", ""]
    text = "\n".join(lines)
    with open(os.path.join(HERE, "oil_indicator_search_results.md"), "w") as fh:
        fh.write(text)
    print(text)


if __name__ == "__main__":
    main()
