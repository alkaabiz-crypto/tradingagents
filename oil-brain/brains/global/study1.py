"""Study 1 (pre-registered 2026-11-24, before running): cross-country momentum, value proxy, combo.
Universe: the 20 country ETFs in lib.CTRY (adjusted closes); a country is eligible at a month-end
once it has the lookback history. Signals at month-end close, held one month. 10 bp per side
(per unit of turnover). Benchmark: equal-weight basket of all eligible country ETFs (monthly rebal).
Each rule starts at its first non-zero month. Placebo = whole weight matrix shifted in time.
Mechanisms: Asness, Moskowitz & Pedersen (2013) value and momentum in country indices;
Richards (1997) country winner/loser reversal over 3-5 years.
G1  momentum L/S: rank on 12-1 month return (t-12m .. t-1m), long top 4, short bottom 4 (1/4 each).
G2  momentum long-only: equal weight top 5 by 12-1 month return (net long 1.0).
G3  value proxy L/S (AMP non-equity definition, Richards reversal): score = log(mean price of
    months t-66..t-54) - log(price t); long top 4 (biggest 5y losers), short bottom 4.
G4  value+momentum L/S: average of cross-sectional ranks (pct) of G1 and G3 scores, among names
    with both; long top 4, short bottom 4.
Prior expectation: AMP report country-index momentum Sharpe ~0.3-0.4 and value ~0.3; the combo
higher. With 20 ETFs and 10 bp costs I expect t < 3 post-2014. Rules counted: 4 (total 4).
"""
import numpy as np, pandas as pd
from lib import CTRY, panel, month_ends, hold, xs_weights, evaluate_w, show, port

px = panel(CTRY)
ret = px.pct_change(fill_method=None)
me = month_ends(px.index)
pm = px.loc[me]
alive = pm.notna()
ew_w = alive.astype(float).div(alive.sum(axis=1), axis=0)
bench = port(hold(ew_w, px.index), ret, 10)

mom = (pm.shift(1) / pm.shift(12) - 1)
val = np.log(pm.rolling(13).mean().shift(54)) - np.log(pm)
both = mom.notna() & val.notna()
combo = (mom.where(both).rank(axis=1, pct=True) + val.where(both).rank(axis=1, pct=True)) / 2

W = {"G1 mom 12-1 L/S 4/4": xs_weights(mom, 4),
     "G2 mom 12-1 long top5": xs_weights(mom, 5, long_only=True),
     "G3 value 5y-rev L/S 4/4": xs_weights(val, 4),
     "G4 value+mom L/S 4/4": xs_weights(combo, 4)}
rows = []; R = {}
for k, wm in W.items():
    w = hold(wm, px.index)
    start = w.index[(w.abs().sum(axis=1) > 0).values.argmax()]
    o, r = evaluate_w(k, w, ret, bench, cost=10, start=start)
    o["start"] = str(start.date()); rows.append(o); R[k] = r
df = show(rows)
print(df["start"].to_string())
for k, r in R.items():
    print(k, "by year %:", (r.groupby(r.index.year).sum() * 100).round(1).to_dict())
pd.DataFrame(rows).to_csv("study1_results.csv", index=False)
