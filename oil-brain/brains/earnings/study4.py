"""Study 4 (earnings brain): market-level earnings-season premium. PRE-REGISTERED 2026-11-24,
after studies 1-3 and before any study-4 return was computed.

Idea: Savor & Wilson (2016, "Earnings announcements and systematic risk") argue the
announcement premium is compensation for market risk learned from announcers' news; Barber et
al. (2013) find the premium at firm level. If it is a market risk premium, the MARKET itself
should earn more when many large firms announce. This needs one ETF (cheap, 5 bp) and few trades,
which avoids the cost wall that killed studies 2-3.

Rule (1, threshold fixed before looking at returns):
  M1 SPY in earnings season: at close t, count universe stocks whose predicted date P
     (day 0 + 364 calendar days of the event a year earlier; known in advance) falls in trading
     days t+1..t+5. Long SPY if count >= 9 (10% of the 92-stock universe), else flat (cash, 0%).
Engine used natively: pos on SPY returns, cost 5 bp, bench = SPY buy-and-hold, engine's own
circular-shift placebo (the position is time-varying, so it is meaningful here).
Prior: FAIL; a part-time SPY position rarely beats SPY's Sharpe, and the market-level evidence
is weaker than the firm-level one.
"""
import numpy as np
import pandas as pd
from common import prices, events, engine
from study2 import predicted

START = "2005-06-01"


def main():
    cl, ret = prices()
    days = ret.index
    pe = predicted(events(days), days)
    cnt = np.zeros(len(days))
    for ip in pe.iP.values:
        cnt[ip] += 1
    c = pd.Series(cnt, index=days)
    fwd = sum(c.shift(-k) for k in range(1, 6)).fillna(0)
    pos = (fwd >= 9).astype(float)
    o = engine.evaluate("M1 SPY in earnings season (>=9 of 92 due in 5d)", pos, ret["SPY"],
                        cost_bps=5, start=START)
    o["exposure_post"] = float(pos.loc["2014":].mean())
    rows = [o]
    pd.DataFrame(rows).to_csv("study4_results.csv", index=False)
    print(engine.table(rows))
    print("exposure", round(o["exposure"], 2), "x2cost", round(o["x2cost_post"], 3))
    # diagnostic: SPY mean daily return in vs out of season, per period
    s = ret["SPY"]
    p = pos.shift(1)
    for a, b in ((START, "2013"), ("2014", "2019"), ("2020", "2026")):
        x, q = s.loc[a:b], p.loc[a:b]
        print(a, b, "in %.1f bp" % (x[q == 1].mean() * 1e4), "out %.1f bp" % (x[q == 0].mean() * 1e4))


if __name__ == "__main__":
    main()
