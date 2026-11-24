"""Study 3: term structure with memory. PRE-REGISTERED 2026-11-24 after the IS-only diagnostic
(diag_is.py, 2006-07..2013 only) and before running this file.

IS diagnostic: SPY next-day Sharpe was 0.85 in "calm" days (contango and no backwardation in
the previous 63 trading days), vs 0.31 in the 63 days after an inversion ends and 0.32 during
backwardation. Inversions come in clusters (71 exits in IS), so one day of contango after an
inversion is not the all-clear. Idea: fear needs time to decay.

T9  SPY long only if VIX/VIX3M <= 1 on every one of the last 63 trading days; flat otherwise.
T10 Neighbour check, same with 21 days (robustness, counted as a rule; uses the last slot).
Bench SPY buy-and-hold. 5 bp. Expectation: lower exposure, Sharpe near buy-and-hold; a PASS
would need the calm-state premium to hold out of sample.
These are rules 14 and 15 of 15: the budget is spent after this.
"""
import pandas as pd
from common import load, vload, evaluate, table, lagcheck
vix, v3m = load("^VIX"), vload("VIX3M"); spy = load("SPY").pct_change()
R = (vix / v3m).dropna()
rules = []
for n in (63, 21):
    pos = ((R > 1).astype(float).rolling(n, min_periods=1).max() == 0).astype(float)
    name = f"T{9 if n == 63 else 10} SPY long if no inversion in {n}d"
    rules.append(evaluate(name, pos, spy, 5, start="2006-07-18"))
    rules.append(lagcheck(name, pos, spy, cost_bps=5, start="2006-07-18"))
    p = pos.loc["2014":]; print(name, "post-2014 exposure", round(float(p.mean()), 2))
print(table(rules))
# drawdown context (descriptive)
for n in (63,):
    pos = ((R > 1).astype(float).rolling(n, min_periods=1).max() == 0).astype(float)
    from engine import pnl
    r = pnl(pos, spy.loc["2014":], 5); b = spy.loc["2014":]
    dd = lambda x: float(((1 + x).cumprod() / (1 + x).cumprod().cummax() - 1).min())
    print("post-2014 maxDD rule", round(dd(r), 3), "SPY", round(dd(b), 3))
pd.DataFrame(rules).to_csv("study3_results.csv", index=False)
