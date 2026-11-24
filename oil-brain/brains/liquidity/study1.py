"""Study 1 (pre-registered 2026-11-24, before running): does volume decide continuation vs reversal?
Literature: Campbell, Grossman & Wang (1993 QJE): on the aggregate market, price moves on HIGH volume
reverse more than moves on low volume (liquidity/hedging trades). Llorente, Michaely, Saar & Wang (2002 RFS):
the sign of the return*volume interaction depends on the trading motive: hedging -> reversal on high volume,
informed/speculative -> continuation on high volume (Conrad, Hameed & Niden 1994 for stocks).
Earlier lab work: big USO days CONTINUE (fading +/-2.5 sd days lost, t -2.49 at 5 days).
Relative volume RV = volume_t / mean(volume_{t-50..t-1}); "high" = RV > 1.5, "low" = RV < 1.0 (fixed a priori).
Big day = |r_t| > 2 x 60-day stdev (prior days). Costs 5 bp. Engine unchanged.
Diagnostic (not a rule, no selection): regression r_{t+1} = a + b r_t + c r_t*log(RV_t) per period, SPY and USO.
  CGW predicts c < 0 for SPY.
Rules (3):
 V1 SPY (CGW): if RV_t > 1.5, position = -sign(r_t) for 1 day, else flat.
 V2 USO (Llorente informed-trading / earlier continuation): big day with RV > 1.5 -> follow sign(r_t) for 5 days.
 V3 USO: big day with RV < 1.0 (low volume) -> fade, -sign(r_t), for 5 days.
 Positions known at close t; latest event overrides an open one.
"""
import numpy as np, pandas as pd
from lib import ld, relvol, evaluate, table

def event_pos(r, mask, direction, hold):
    p = pd.Series(np.nan, index=r.index)
    p[mask] = direction * np.sign(r[mask])
    return (p.ffill(limit=hold - 1) if hold > 1 else p).fillna(0)

rows = []
for sym in ["SPY", "USO"]:
    df = ld(sym, None); r = df.Close.pct_change(); rv = relvol(df.Volume)
    x = pd.DataFrame({"y": r.shift(-1), "r": r, "rl": r * np.log(rv)}).dropna()
    x = x[np.isfinite(x.rl)]
    for per, a, b in [("IS", None, "2013-12-31"), ("OOS", "2014", "2019"), ("HOLDOUT", "2020", None)]:
        z = x.loc[a:b]; X = np.c_[np.ones(len(z)), z.r, z.rl]
        beta, res, *_ = np.linalg.lstsq(X, z.y, rcond=None)
        e = z.y - X @ beta; s2 = e.var(); cov = s2 * np.linalg.inv(X.T @ X)
        print(f"diag {sym} {per}: b={beta[1]:+.3f} (t {beta[1]/np.sqrt(cov[1,1]):+.2f}), c={beta[2]:+.3f} (t {beta[2]/np.sqrt(cov[2,2]):+.2f}), n={len(z)}")

spy = ld("SPY", None); rs = spy.Close.pct_change(); rvs = relvol(spy.Volume)
rows.append(evaluate("V1 SPY fade high-volume days 1d (CGW)", event_pos(rs, rvs > 1.5, -1, 1), rs, start="1994-01-01"))
uso = ld("USO", None); ru = uso.Close.pct_change(); rvu = relvol(uso.Volume)
big = ru.abs() > 2 * ru.shift(1).rolling(60).std()
rows.append(evaluate("V2 USO follow big high-volume day 5d", event_pos(ru, big & (rvu > 1.5), 1, 5), ru, start="2006-08-01"))
rows.append(evaluate("V3 USO fade big low-volume day 5d", event_pos(ru, big & (rvu < 1.0), -1, 5), ru, start="2006-08-01"))
print(table(rows))
for nm, m in [("big&high", big & (rvu > 1.5)), ("big&mid", big & (rvu >= 1) & (rvu <= 1.5)), ("big&low", big & (rvu < 1.0))]:
    f5 = ru.rolling(5).sum().shift(-5) * np.sign(ru)
    for per, a, b in [("IS", None, "2013"), ("post", "2014", None)]:
        s = f5[m].loc[a:b].dropna()
        print(f"USO {nm} {per}: n={len(s)}, mean signed next-5d return {s.mean()*100:+.2f}% (t {s.mean()/s.std()*np.sqrt(len(s)):+.2f})")
