"""Study 2 (pre-registered 2026-11-24, after study 1, before running): Nagel (2012) VIX conditioning.
Nagel: reversal profits are a return to liquidity provision and the expected return rises with VIX.
Study 1 showed the unconditional weekly reversal (R1, R3) is gross ~0 after 2014 and net negative.
Base book = R3 (industry-adjusted weekly reversal, the DLS 2014 version), same costs/benchmark/placebo.
 R4 Nagel scaling: R3 weights x (VIX_t / mean VIX over the past 252 days), capped at 3,
    VIX read at the rebalance close and held with the weights for the week.
 R5 Nagel regime switch: R3 only in weeks where VIX close at rebalance > 25, else flat (cash).
Diagnostic (not a rule): mean weekly gross R3 return by VIX bucket at formation, IS vs post-2014.
Expectation: if Nagel holds, gross return per week rises with VIX in both periods; R5 trades
rarely, so t-stat will be low even if per-trade edge is real.
"""
from lib import *
we = week_ends(px.index)
r5 = px.pct_change(5, fill_method=None)
base = neutral(-r5, SECT)
scale = (vix / vix.rolling(252).mean()).clip(upper=3).fillna(1)
R4 = hold(base.mul(scale, axis=0), we)
R5 = hold(base.mul((vix > 25).astype(float), axis=0), we)
rows = []
for k, w in {"R4 R3 x VIX/1y-mean": R4, "R5 R3 only if VIX>25": R5}.items():
    o, r = evaluate_w(k, w); rows.append(o)
    p = r.loc["2005-07":]
    print(k, "net % by year:", (p.groupby(p.index.year).sum() * 100).round(1).to_dict())
show(rows).to_csv("study2_results.csv")
# diagnostic: weekly gross return of R3 by VIX bucket
R3 = hold(base, we)
_, g, _ = port(R3.loc[START:], 0, ret.loc[START:])
wk = g.groupby(g.index.to_period("W-FRI")).sum()
v = vix.loc[we].loc[START:]; v.index = v.index.to_period("W-FRI")
v = v.shift(1).reindex(wk.index)   # VIX at the formation close (prior week end)
b = pd.cut(v, [0, 15, 20, 25, 35, 100])
for lab, sl in [("IS", slice(None, "2013-12")), ("post", slice("2014-01", None))]:
    x = wk.loc[sl]; bb = b.loc[sl]
    t = x.groupby(bb, observed=True).agg(["mean", "std", "count"])
    t["t"] = t["mean"] / t["std"] * np.sqrt(t["count"]); t["mean_bp"] = t["mean"] * 1e4
    print(lab, "gross weekly R3 by VIX bucket (cost per week ~ 14 bp at 5 bp):\n", t[["mean_bp", "t", "count"]].round(2))
