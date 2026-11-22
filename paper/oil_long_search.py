#!/usr/bin/env python3
"""Oil day-trading search on ~16 years of hourly WTI (Dukascopy), rules fixed before running.

Part A, the cleanest test: account #17's frozen rule (reversal consensus, buy
only, skip the Wednesday EIA window, New York session, flat by 14:00) was
chosen on 2024-2026 Yahoo data, so 2010-2023 is data it has never seen.
PASS if, on 2010-2023: positive at 0.02% and 0.05% costs, Sharpe > 0.5,
>= 100 trades and luck check >= 99%.

Part B: the same full search as oil_indicator_search.py (15 single
indicators, 105 pairs, 60 pair+filter combos, the reversal consensus) on the
long data: TRAIN = first 60% (about 2010-2019), TEST = last 40%; top 10 per
round go to TEST; same pass rules (99% luck bar).

Usage: python3 paper/oil_long_search.py DATA_DIR
"""
import datetime as dt
import json
import os
import sys

import oil_indicator_search as S
from oil_indicator_search2 import consensus

HERE = os.path.dirname(os.path.abspath(__file__))


def load(path):
    rows = json.load(open(path))
    B = []
    for t, o, h, l, c, v in rows:
        B.append(dict(t=t, et=dt.datetime.fromtimestamp(t, dt.timezone.utc).astimezone(S.ET), o=o, h=h, l=l, c=c, v=v))
    return B


def frozen_rule(B, I):
    sig = [max(x, 0) for x in consensus(I, 2)]
    wed = [not (b["et"].weekday() == 2 and 9 <= b["et"].hour <= 11) for b in B]
    return [x if ok else 0 for x, ok in zip(sig, wed)]


def main():
    B = load(os.path.join(sys.argv[1], "wti_hourly.json"))
    per_year = 252 * 5
    out = ["# Oil day-trading search on 16 years of hourly WTI (Dukascopy)", "",
           f"Run {dt.datetime.now(dt.timezone.utc):%Y-%m-%d %H:%M} UTC. Data {B[0]['et']:%Y-%m-%d} to {B[-1]['et']:%Y-%m-%d}, "
           f"{len(B)} hourly candles.", ""]
    I, _ = S.indicators(B)
    mask = S.allowed_mask(B, True)
    pos = S.positions(frozen_rule(B, I), mask)
    cut = next(i for i, b in enumerate(B) if b["et"].year >= 2024)
    rows = []
    for nm, lo, hi in (("2010-2023 (never seen)", 0, cut), ("2024-2026 (used to choose it)", cut, len(B)),
                       ("2010-2016", 0, next(i for i, b in enumerate(B) if b["et"].year >= 2017)),
                       ("2017-2023", next(i for i, b in enumerate(B) if b["et"].year >= 2017), cut)):
        bb, pp = B[lo:hi], pos[lo:hi]
        m = S.score(S.returns_from(bb, pp, S.COST), pp, per_year)
        m5 = S.score(S.returns_from(bb, pp, S.STRESS), pp, per_year)
        lk = S.luck(bb, pp, S.COST, per_year, m["sharpe"], sims=200) if m["sharpe"] > 0 else 0.0
        ok = m["total"] > 0 and m5["total"] > 0 and m["sharpe"] > 0.5 and m["trades"] >= 100 and lk >= 0.99
        rows.append(f"| {nm} | {m['trades']} | {m['sharpe']:.2f} | {m['total'] * 100:+.1f}% | {m5['total'] * 100:+.1f}% | "
                    f"{lk:.0%} | {('**PASS**' if ok else 'fail') if nm.startswith('2010-2023') else 'info'} |")
    out += ["## Part A: account #17's frozen rule on data it never saw", "",
            "| Period | Trades | Sharpe | Total (0.02%) | Total (0.05%) | Luck | Verdict |", "|---|---|---|---|---|---|---|"] + rows + [""]
    # Part B
    orig_luck = S.luck
    S.luck = lambda *a, **k: orig_luck(*a, **{**k, "sims": 200})
    lines, passes = S.search(B, True, per_year, "Part B: full indicator search on 16 years (TRAIN about 2010-2019)",
                             S.hourly_filters)
    out += lines
    split = int(len(B) * 0.6)
    tr, te, te_s, tep, teB = S.evaluate(B, consensus(I, 2), mask, split, per_year)
    lk = S.luck(teB, tep, S.COST, per_year, te["sharpe"]) if te["sharpe"] > 0 else 0.0
    ok = te["total"] > 0 and te_s["total"] > 0 and te["sharpe"] > 0.5 and te["trades"] >= 40 and lk >= 0.99
    out += ["### Reversal consensus (2+ agree, both sides), pre-chosen", "",
            f"TRAIN Sharpe {tr['sharpe']:.2f}; TEST Sharpe {te['sharpe']:.2f}, total {te['total'] * 100:+.1f}% "
            f"(0.05%: {te_s['total'] * 100:+.1f}%), {te['trades']} trades, luck {lk:.0%}: {'**PASS**' if ok else 'fail'}.", "",
            "## Summary", "", f"Part B passes: {passes or 'none'}", ""]
    text = "\n".join(out)
    with open(os.path.join(HERE, "oil_long_search_results.md"), "w") as fh:
        fh.write(text)
    print(text)


if __name__ == "__main__":
    main()
