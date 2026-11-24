"""Study 3 (pre-registered 2026-11-24, before running): cross-section of large energy stocks
after removing market and oil exposure.
Universe (16, today's survivors, so there is survivorship bias; HES and MRO are delisted on
Yahoo): XOM CVX COP OXY SLB HAL BKR EOG DVN APA VLO MPC PSX KMI WMB OKE. A stock enters once it
has 252 days of history. Residual = r_i - b' [r_SPY, r_USO], rolling 252-day daily OLS betas,
yesterday's betas (no look-ahead). Long the top third / short the bottom third, equal weights,
gross exposure 1 (0.5 long, 0.5 short). Costs 10 bp per unit of turnover. Engine gates applied
by xs_evaluate (same 6 gates; placebo = circular time shift of the whole weight matrix).
Benchmark: equal-weight universe buy and hold.
C1 residual momentum (Blitz, Huij & Martens 2011 JEF): score = sum of residuals over months
   t-12..t-2 (days 252..22 back) / std of residuals over that window; rebalance at month-end;
   long high, short low.  Start 2008-06-01.
C2 short-term residual reversal (Da, Liu & Schaumburg 2014 Mgmt Sci; within-industry reversal):
   score = 5-day residual sum at the Friday close; long the losers, short the winners; hold one
   week. Start 2008-06-01.
"""
from common import *
U = "XOM CVX COP OXY SLB HAL BKR EOG DVN APA VLO MPC PSX KMI WMB OKE".split()
R = rets(U + ["SPY", "USO"]).loc["2006-04-11":]
X = R[["SPY", "USO"]]
RES = {}
for s in U:
    y = R[s].dropna()
    if len(y) < 300: continue
    B = roll_beta(y, X.loc[y.index])
    RES[s] = hedged(y, X.loc[y.index], B)
RES = pd.DataFrame(RES).reindex(R.index)

def thirds(score):
    W = pd.DataFrame(0.0, index=score.index, columns=score.columns)
    for d, row in score.iterrows():
        row = row.dropna()
        if len(row) < 6: continue
        k = len(row) // 3
        o = row.sort_values()
        W.loc[d, o.index[-k:]] = 0.5 / k
        W.loc[d, o.index[:k]] = -0.5 / k
    return W

cs = RES.shift(22).rolling(231, min_periods=200)
mom = cs.sum() / cs.std()
me = mom.index.to_period("M"); last = pd.Series(mom.index, index=mom.index).groupby(me).transform("max")
mom_m = mom.where(pd.Series(mom.index == last.values, index=mom.index), axis=0)
W1 = thirds(mom_m.dropna(how="all")).reindex(R.index).ffill()
rev = -RES.rolling(5, min_periods=5).sum()
wk = rev.index.to_period("W-FRI"); lastw = pd.Series(rev.index, index=rev.index).groupby(wk).transform("max")
rev_w = rev.where(pd.Series(rev.index == lastw.values, index=rev.index), axis=0)
W2 = thirds(rev_w.dropna(how="all")).reindex(R.index).ffill()
Rs = R[U]
rows = [xs_evaluate("C1 residual momentum 12-1, monthly", W1, Rs, 10, start="2008-06-01"),
        xs_evaluate("C2 residual reversal 5d, weekly", W2, Rs, 10, start="2008-06-01")]
print(table(rows))
for nm, W in [("C1", W1), ("C2", W2)]:
    g = (W.shift(1) * Rs.fillna(0)).sum(axis=1).loc["2008-06-01":]
    print(nm, "gross ann. return by period:", {p: round(float(g.loc[a:b].mean() * 252), 3) for p, a, b in
          [("IS", None, "2013"), ("OOS", "2014", "2019"), ("HO", "2020", None)]},
          "market beta %.2f, oil beta %.2f" % (np.polyfit(R["SPY"].loc[g.index].fillna(0), g, 1)[0],
                                                 np.polyfit(R["USO"].loc[g.index].fillna(0), g, 1)[0]))
