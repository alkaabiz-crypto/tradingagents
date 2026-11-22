#!/usr/bin/env python3
"""Study: the best way to dollar-cost average (DCA) into oil.

Every method gets $100 on the first trading day of each month (a cash pot).
Unspent cash stays in the pot (0% interest) and counts in the final value.
Buys cost 0.05%. Rules fixed before running.

Investments (Yahoo Finance, dividends included):
  USO  WTI front-month futures fund (the usual "USOIL" product)
  USL  WTI 12-month futures fund (spreads the roll)
  BNO  Brent front-month futures fund
  XLE  US energy company stocks (no futures roll; pays dividends)

Methods:
  1. Lump sum: all the money that DCA will invest, invested on day one
     (Vanguard benchmark; the money-weighted return is then the plain CAGR).
  2. Plain DCA: buy $100 every month.
  3. Value averaging (Edleson 1988): keep the holding's value on a path that
     rises $100 a month; buy the shortfall (max $300 a month), sell any
     excess back into the pot.
  4. Enhanced DCA (Dunham & Friesen, return-based): after a down month buy
     $200, after an up month $50 (as far as the pot allows).
  5. Moving-average dip DCA: below the 200-day average buy $200, above $50.
  6. RSI DCA: 14-day RSI < 40 buy $200, > 60 buy $50, else $100.
  7. Trend DCA: buy the whole pot only while the price is above its 200-day
     average; otherwise keep saving (never sells).

Scores: final value / money put in, money-weighted yearly return (IRR), and
the worst drop of the account value. "Beats DCA in both halves" re-runs each
method from the start and from the middle of the history separately. Luck
check (methods 4-7): the same month-by-month buying decisions are shuffled 500
times; share of shuffles the real method beats on final value.
"""
import datetime as dt
import os
import random

import anomaly_study as A

HERE = os.path.dirname(os.path.abspath(__file__))
COST = 0.0005
FUNDS = ["USO", "USL", "BNO", "XLE"]


def months(dates):
    out, last = [], None
    for i, d in enumerate(dates):
        if (d.year, d.month) != last:
            out.append(i)
            last = (d.year, d.month)
    return out


def rsi14(c):
    out = [50.0] * len(c)
    g = l = 0.0
    for i in range(1, len(c)):
        d = c[i] - c[i - 1]
        if i <= 14:
            g += max(d, 0) / 14
            l += max(-d, 0) / 14
        else:
            g = (g * 13 + max(d, 0)) / 14
            l = (l * 13 + max(-d, 0)) / 14
        out[i] = 100 if l == 0 else 100 - 100 / (1 + g / l)
    return out


def irr(flows, final):
    """flows: list of (month_index, amount_in); final value at last month."""
    T = max(m for m, _ in flows) + 1
    def npv(r):
        return sum(-a / (1 + r) ** (m / 12) for m, a in flows) + final / (1 + r) ** (T / 12)
    lo, hi = -0.99, 3.0
    for _ in range(200):
        mid = (lo + hi) / 2
        if npv(mid) > 0:
            lo = mid
        else:
            hi = mid
    return mid


def simulate(c, mi, rule, decisions=None):
    """rule(k, i) -> dollars wanted this month (None = whole pot). Returns stats and the decision list."""
    pot = shares = 0.0
    peak, mdd, flows, dec = 0.0, 0.0, [], []
    vt = 0.0
    month_of = {i: k for k, i in enumerate(mi)}
    for i in range(mi[0], len(c)):
        if i in month_of:
            k = month_of[i]
            pot += 100
            flows.append((k, 100.0))
            want = rule(k, i, shares * c[i]) if decisions is None else decisions[k]
            dec.append(want)
            if want == "VA":
                vt += 100
                gap = vt - shares * c[i]
                if gap > 0:
                    want = min(gap, 300.0)
                else:
                    sell = -gap
                    shares -= sell / c[i]
                    pot += sell * (1 - COST)
                    want = 0.0
            amt = pot if want is None else min(want, pot)
            if amt > 0:
                shares += amt * (1 - COST) / c[i]
                pot -= amt
        val = shares * c[i] + pot
        peak = max(peak, val)
        if peak > 0:
            mdd = max(mdd, 1 - val / peak)
    final = shares * c[-1] + pot
    put_in = 100.0 * len(mi)
    return dict(final=final, put_in=put_in, mult=final / put_in, irr=irr(flows, final), mdd=mdd), dec


def methods(c, sma200, ret_m, rsi):
    return {
        "2. Plain DCA ($100/month)": lambda k, i, v: 100.0,
        "3. Value averaging": lambda k, i, v: "VA",
        "4. Enhanced DCA (more after a down month)": lambda k, i, v: 200.0 if ret_m(k) < 0 else 50.0,
        "5. Dip DCA (more below the 200-day average)": lambda k, i, v: 200.0 if c[i] < sma200[i] else 50.0,
        "6. RSI DCA": lambda k, i, v: 200.0 if rsi[i] < 40 else (50.0 if rsi[i] > 60 else 100.0),
        "7. Trend DCA (buy only above the 200-day average)": lambda k, i, v: None if c[i] > sma200[i] else 0.0,
    }


def run_fund(sym):
    data = A.daily(sym)
    dates = sorted(data)
    c = [data[d]["c"] for d in dates]
    sma200 = [sum(c[max(0, i - 199):i + 1]) / min(i + 1, 200) for i in range(len(c))]
    rsi = rsi14(c)
    mi_all = [i for i in months(dates) if i >= 200]          # start once the 200-day average exists

    def ret_m_for(mi):
        return lambda k: (c[mi[k] - 1] / c[mi[k - 1]] - 1) if k > 0 else 0.0
    out = {"sym": sym, "from": dates[mi_all[0]], "to": dates[-1], "rows": []}
    half = len(mi_all) // 2
    for nm in list(methods(c, sma200, ret_m_for(mi_all), rsi)) + ["1. Lump sum (same total, day one)"]:
        res = {}
        for label, mi in (("all", mi_all), ("h1", mi_all[:half]), ("h2", mi_all[half:])):
            cc = c[:mi[-1] + 21] if label == "h1" else c       # first half ends ~1 month after its last buy
            if nm.startswith("1."):
                total = 100.0 * len(mi)
                start = mi[0]
                final = total * (1 - COST) * cc[-1] / cc[start]
                yrs = (len(cc) - start) / 252
                peak, mdd = 0.0, 0.0
                for x in cc[start:]:
                    peak = max(peak, x)
                    mdd = max(mdd, 1 - x / peak)
                res[label] = dict(final=final, put_in=total, mult=final / total,
                                  irr=(final / total) ** (1 / yrs) - 1, mdd=mdd)
                continue
            rule = methods(cc, sma200, ret_m_for(mi), rsi)[nm]
            res[label], dec = simulate(cc, mi, rule)
            if label == "all":
                decisions = dec
        luck = None
        if nm[0] in "4567":
            rng = random.Random(4)
            beat = 0
            for _ in range(500):
                d2 = decisions[:]
                rng.shuffle(d2)
                beat += res["all"]["final"] > simulate(c, mi_all, None, decisions=d2)[0]["final"]
            luck = beat / 500
        out["rows"].append((nm, res, luck))
    return out


def pct(x):
    return f"{x * 100:+.1f}%"


def main():
    lines = ["# Oil DCA study", "",
             f"Run {dt.datetime.now(dt.timezone.utc):%Y-%m-%d %H:%M} UTC. $100 a month; 0.05% per buy; unspent "
             "cash counts at 0% interest. Money-weighted return = the yearly return on the money actually put in.", ""]
    summary = []
    for sym in FUNDS:
        f = run_fund(sym)
        base = {k: v for k, v in [(n, r) for n, r, _ in f["rows"]]}["2. Plain DCA ($100/month)"]
        lines += [f"## {sym} ({f['from']} to {f['to']})", "",
                  "| Method | Money in | Final value | Value / money in | Money-weighted return | Worst drop | "
                  "Beats plain DCA (1st half / 2nd half) | Luck check |",
                  "|---|---|---|---|---|---|---|---|"]
        for nm, r, luck in f["rows"]:
            a = r["all"]
            b1 = "-" if nm.startswith("2.") else ("yes" if r["h1"]["final"] / r["h1"]["put_in"] > base["h1"]["final"] / base["h1"]["put_in"] else "no")
            b2 = "-" if nm.startswith("2.") else ("yes" if r["h2"]["final"] / r["h2"]["put_in"] > base["h2"]["final"] / base["h2"]["put_in"] else "no")
            lines.append(f"| {nm} | ${a['put_in']:,.0f} | ${a['final']:,.0f} | {a['mult']:.2f}x | {pct(a['irr'])} | "
                         f"-{a['mdd']:.0%} | {b1} / {b2} | {'-' if luck is None else format(luck, '.0%')} |")
            summary.append((sym, nm, a["irr"], b1, b2, luck))
        lines.append("")
    text = "\n".join(lines)
    with open(os.path.join(HERE, "dca_study_results.md"), "w") as fh:
        fh.write(text)
    print(text)


if __name__ == "__main__":
    main()
