"""Study 1 (pre-registered 2026-11-24, written before running): cross-sectional sector rules.
Universe: the SPDR sector ETFs XLB XLE XLF XLI XLK XLP XLU XLV XLY (Dec 1998), plus XLRE (2015)
and XLC (2018); a name joins once it has 300 days of history (S5: 36 month-ends of history).
Weights set at the close of the rebalance day, held to the next rebalance; 5 bp per unit of
turnover (sum of |weight change|); 10 bp stress. Long/short legs: +1/3 on each of the top 3,
-1/3 on each of the bottom 3 (gross 2, dollar neutral). Start 2000-01-01.
Benchmark (gate 2) for every rule: equal-weight buy-and-hold of the alive sectors (daily rebalanced).
Placebo: the whole weight matrix circularly shifted in time (500 shifts), as study6.py.
Parameters come from the papers, not from a search:
 S1 industry momentum (Moskowitz & Grinblatt 1999): score = 126-day return (6m formation),
    month-end rebalance, long top 3 / short bottom 3.
 S2 monthly industry reversal (Jegadeesh 1990 style at industry level): score = 21-day return,
    month-end, long the 3 losers / short the 3 winners. (MG99 actually report 1-month industry
    MOMENTUM, so the expected sign is uncertain; pre-registered as the reversal side.)
 S3 weekly industry reversal (Lehmann 1990 / Lo-MacKinlay): score = 5-day return, rebalance at
    the last trading day of each week, long 3 losers / short 3 winners.
 S4 52-week-high momentum (George & Hwang 2004): score = close / max(close over 252 days),
    month-end, long top 3 / short bottom 3.
 S5 residual momentum (Blitz, Huij & Martens 2011): month-end; regress each sector's monthly
    return on SPY's over the past 36 months; score = sum of residuals in months t-11..t-1
    (skip the latest month) divided by their std. Long top 3 / short bottom 3.
 S6 long-only rotation (the practitioner version): hold the top 3 by 12-1 month return
    (252-day return skipping the latest 21 days), equal weight, month-end. Benchmark EW sectors.
Expected: momentum weak post-2009 (literature on momentum decay); reversal uncertain.
"""
import numpy as np, pandas as pd
from lib import *

px = panel(SECT + ["SPY"]).loc["1998-12-01":]
spy = px.pop("SPY")
ret = px.pct_change(fill_method=None)
alive = px.notna().cumsum() >= 300
bench = ret.where(alive).mean(axis=1)
idx = px.index
me = period_ends(idx, "M"); we = period_ends(idx, "W")

def at(scores, ends, **kw):
    w = xs_weights(scores.loc[ends], alive.loc[ends], **kw)
    return hold(w, idx)

# S5 residual momentum on monthly data
mpx = px.loc[me]; mret = mpx.pct_change(fill_method=None); mspy = spy.loc[me].pct_change()
res_score = pd.DataFrame(np.nan, index=me, columns=px.columns)
for i in range(36, len(me)):
    win = slice(i - 35, i + 1)  # last 36 monthly returns ending at month i
    x = mspy.iloc[win].values
    for j, c in enumerate(px.columns):
        y = mret[c].iloc[win].values
        if np.isnan(y).any() or np.isnan(x).any():
            continue
        b = np.polyfit(x, y, 1)
        e = y - np.polyval(b, x)
        f = e[-12:-1]  # months t-11..t-1
        res_score.iat[i, j] = f.sum() / f.std(ddof=1) if f.std() > 0 else np.nan
res_score = res_score.astype(float)
res_alive = res_score.notna()

W = {
 "S1 industry mom 6m (MG99)": at(px.pct_change(126, fill_method=None), me),
 "S2 industry reversal 1m": at(px.pct_change(21, fill_method=None), me, long_high=False),
 "S3 industry reversal 1w": at(px.pct_change(5, fill_method=None), we, long_high=False),
 "S4 52w-high (GH04)": at(px / px.rolling(252, min_periods=252).max(), me),
 "S5 residual mom (BHM11)": hold(xs_weights(res_score, res_alive), idx),
 "S6 long-only top3 12-1m": at(px.shift(21) / px.shift(252) - 1, me, long_only=True),
}
rows = []
for k, w in W.items():
    o, r = evaluate_w(k, w, ret, bench, start="2000-01-01")
    rows.append(o)
show(rows)
print("EW bench IS/OOS/HO Sharpe:", round(sharpe(bench.loc["2000":IS_END]), 2), round(sharpe(bench.loc["2014":OOS_END]), 2), round(sharpe(bench.loc["2020":]), 2))
pd.DataFrame(rows).to_csv("study1_results.csv", index=False)
