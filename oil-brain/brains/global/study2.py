"""Study 2 (pre-registered 2026-11-24 after the IS-only diagnostic diag2.py, before any OOS look):
time-zone / stale-price effect in Asian country ETFs traded in New York.
Literature: Engle & Sarkar (2006) ETF premiums; the stale-NAV literature says the home market
catches up to the US move the next day, so the NAV is predictable, but the ETF's own NY close
already contains the US move. IS diagnostic (2001-2013) found the opposite of continuation:
the ETF's NEXT close-to-close return is NEGATIVELY related to today's SPY return (t -4 to -10)
and to its own return (t -4 to -10): a next-day reversal, likely closing-price noise /
bid-ask bounce / overreaction of the NY close relative to the home market.
Basket: equal weight of EWJ, EWH, EWS, EWT, EWY, FXI, EWA, EWM (each when it trades); INDA
excluded (no IS effect). Daily, positions known at the close of day t, close-to-close returns,
engine.evaluate unchanged, 5 bp per unit turnover (ETF minimum; the 2x gate tests 10 bp).
Benchmark: buy-and-hold the basket. Start 2001-01-01.
T1  pos = -clip(SPY return day t / 1%, -1, 1)   (fade the US day in Asia ETFs)
T2  pos = -clip(basket return day t / 1%, -1, 1) (fade the basket's own day)
Expectation: strong IS, decaying after 2014 as ETF closes became tighter (closing auctions,
more liquidity); daily turnover may eat it. Rules counted: 2 (total 6).
"""
import numpy as np, pandas as pd
from lib import load, panel, evaluate
from engine import table
A = ["EWJ","EWH","EWS","EWT","EWY","FXI","EWA","EWM"]
px = panel(A)
bret = px.pct_change(fill_method=None).mean(axis=1).loc["2001":]
spy = load("SPY").pct_change().reindex(bret.index)
P = {"T1 fade SPY day in Asia basket": -(spy / 0.01).clip(-1, 1),
     "T2 fade own basket day": -(bret / 0.01).clip(-1, 1)}
rows = []
for k, p in P.items():
    o = evaluate(k, p.fillna(0), bret, cost_bps=5, bench=bret, start="2001-01-01"); rows.append(o)
    print(k, "x2cost_post", round(o["x2cost_post"], 3), "exposure", round(o["exposure"], 2))
print(table(rows))
from engine import pnl
for k, p in P.items():
    r = pnl(p.fillna(0), bret, 5); g = pnl(p.fillna(0), bret, 0)
    print(k, "net by year %:", (r.groupby(r.index.year).sum()*100).round(1).to_dict())
    print(k, "gross by year %:", (g.groupby(g.index.year).sum()*100).round(1).to_dict())
pd.DataFrame(rows).to_csv("study2_results.csv", index=False)
