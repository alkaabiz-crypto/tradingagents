#!/usr/bin/env python3
"""Round 4 of the oil indicator search (rules fixed before running).

Round 1-3 showed the mean-reversion group was mildly positive on TEST while
trend indicators lost. Instead of picking the luckiest pair, test ONE family
rule decided in advance:
  Reversal consensus: count how many of the 6 reversal indicators (RSI(14)
  30/70, RSI(2) 10/90, Bollinger 2-sd, Stochastic 20/80, CCI +-100, VWAP
  stretch) point the same way; trade that way when at least K agree (K = 2
  and K = 3 reported; K = 2 is the pre-chosen main rule); flat otherwise.
  Variants (reported, but only the main rule can PASS): long side only;
  skip the Wednesday EIA window.
Same TRAIN/TEST split and pass rules as oil_indicator_search.py, judged on TEST.
"""
import datetime as dt
import os

import oil_indicator_search as S

HERE = os.path.dirname(os.path.abspath(__file__))
REV = ["RSI(14) 30/70 reversal", "RSI(2) 10/90 reversal", "Bollinger 2-sd reversal",
       "Stochastic 20/80 reversal", "CCI -100/+100 reversal", "VWAP stretch reversal"]


def consensus(I, k):
    n = len(I[REV[0]])
    out = []
    for i in range(n):
        up = sum(1 for r in REV if I[r][i] == 1)
        dn = sum(1 for r in REV if I[r][i] == -1)
        out.append(1 if up >= k and up > dn else (-1 if dn >= k and dn > up else 0))
    return out


def run(B, intraday, per_year, label):
    I, extra = S.indicators(B)
    mask = S.allowed_mask(B, intraday)
    split = int(len(B) * 0.6)
    rows = []
    wed = [not (b["et"].weekday() == 2 and 9 <= b["et"].hour <= 11) for b in B] if intraday else [True] * len(B)
    variants = {
        "MAIN: reversal consensus, 2+ agree": consensus(I, 2),
        "3+ agree": consensus(I, 3),
        "2+ agree, long side only": [max(x, 0) for x in consensus(I, 2)],
        "2+ agree, skip Wednesday EIA window": [x if ok else 0 for x, ok in zip(consensus(I, 2), wed)],
    }
    for nm, sig in variants.items():
        tr, te, te_s, tep, teB = S.evaluate(B, sig, mask, split, per_year)
        lk = S.luck(teB, tep, S.COST, per_year, te["sharpe"]) if te["sharpe"] > 0 else 0.0
        ok = nm.startswith("MAIN") and te["total"] > 0 and te_s["total"] > 0 and te["sharpe"] > 0.5 \
            and te["trades"] >= 40 and lk >= 0.99
        rows.append(f"| {nm} | {tr['sharpe']:.2f} | {te['sharpe']:.2f} | {te['total'] * 100:+.1f}% | "
                    f"{te_s['total'] * 100:+.1f}% | {te['trades']} | {lk:.0%} | "
                    f"{'**PASS**' if ok else ('fail' if nm.startswith('MAIN') else 'info only')} |")
    return [f"## {label}", "", f"TRAIN to {B[split]['et']:%Y-%m-%d}, TEST after.", "",
            "| Rule | TRAIN Sharpe | TEST Sharpe | TEST total (0.02%) | TEST total (0.05%) | TEST trades | Luck (TEST) | Verdict |",
            "|---|---|---|---|---|---|---|---|"] + rows + [""]


def main():
    out = ["# Oil indicator search, round 4: one pre-chosen reversal-consensus rule", "",
           f"Run {dt.datetime.now(dt.timezone.utc):%Y-%m-%d %H:%M} UTC.", ""]
    hb = S.yahoo("730d", "60m")
    out += run(hb, True, 252 * 5, "Hourly WTI, New York session (day trading)")
    db = S.yahoo("max", "1d")
    for b in db:
        b["et"] = b["et"].replace(hour=12)
    out += run(db, False, 252, "Daily WTI since 2000 (swing)")
    text = "\n".join(out)
    with open(os.path.join(HERE, "oil_indicator_search2_results.md"), "w") as fh:
        fh.write(text)
    print(text)


if __name__ == "__main__":
    main()
