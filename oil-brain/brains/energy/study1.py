"""Study 1 (pre-registered 2026-11-24, before running): slow diffusion between energy equities
and oil at a weekly horizon. Sources: Driesprong, Jacobsen & Maat 2008 JFE (oil news reaches
stocks with a lag); Hong, Torous & Valkanov 2007 JFE (industries lead / information diffuses
slowly); "equity-implied" oil information (stocks price long-dated oil, futures the front).
The 1-day version (oil brain H7: XLE catches up with oil next day) failed; this asks the weekly
question once. All signals are taken at the Friday close and held 5 trading days (one week).
Betas: rolling 252-day daily OLS (with intercept), known at t; hedged returns use yesterday's betas.
Window starts 2007-06-01 (USO starts 2006-04 + 1 year of betas). Costs: 5 bp on outright ETF
trades, 10 bp per unit for hedged two-leg trades.
E1 equities lead oil: XLE residual (XLE on SPY and USO) summed over the past 5 days > 0 ->
   long USO next week, < 0 -> short USO.  Benchmark: USO buy and hold.
E2 oil leads equities: gap = beta_USO * USO_5d - XLE_resid... defined simply as the 5-day sum of
   the XLE residual (as in E1) with the opposite sign: XLE lagged its oil-and-market fitted move
   (residual < 0) -> long XLE hedged with SPY (XLE - beta_SPY * SPY); residual > 0 -> short it.
   Benchmark: the SPY-hedged XLE return held long.
E3 same as E2 on XOP (E&P, higher oil beta), residual of XOP on SPY and USO, hedge with SPY.
Expected: weak. Published lags (Driesprong) are monthly and decayed (oil brain grade C).
"""
from common import *
R = rets(["XLE", "XOP", "USO", "SPY"])
X = R[["SPY", "USO"]]
rows = []
res = {}
for s in ["XLE", "XOP"]:
    B = roll_beta(R[s], X)
    resid = hedged(R[s], X, B)            # residual return (alpha not removed; it is tiny)
    res[s] = (resid.rolling(5).sum(), B)
start = "2007-06-01"
sig1 = weekly(np.sign(res["XLE"][0]))
rows.append(evaluate("E1 XLE residual 5d -> USO next week", sig1, R["USO"], 5, start=start))
for s, nm in [("XLE", "E2"), ("XOP", "E3")]:
    sres, B = res[s]
    bs = roll_beta(R[s], R[["SPY"]])
    h = hedged(R[s], R[["SPY"]], bs)
    sig = weekly(-np.sign(sres))
    rows.append(evaluate(f"{nm} {s} lagged its fitted move -> long {s}-SPY next week", sig, h.dropna(), 10, start=start))
print(table(rows))
