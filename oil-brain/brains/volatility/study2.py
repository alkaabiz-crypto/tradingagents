"""Study 2: variance risk premium and vol-of-vol. PRE-REGISTERED 2026-11-24, after study 1
(0 of 8) and before running this file. Rules chosen from the literature, not from study 1.

VRP_t = VIX_t^2 - RV21_t^2 (RV21 = 21-day realised vol of the asset, annualised, in vol points).
Bollerslev, Tauchen & Zhou 2009 RFS: high VRP predicts higher equity returns at 1-6 month
horizons; a NEGATIVE VRP (realised above implied) marks acute stress.
Rebalance month-end only (the paper's horizon; keeps turnover low). Costs 5 bp.

P1 SPY long when VRP > 0 at month-end, else flat.                       bench SPY
P2 USO long when OVX^2 - RV21(USO)^2 > 0 at month-end, else flat
   (oil VRP, Trolle & Schwartz 2010: premium exists; sign as in BTZ).    bench USO
P3 SPY long, flat when VVIX > its trailing 252d 90th percentile (daily)
   (vol-of-vol risk is priced, Huang et al. 2019 JFQA; high VVIX = fragile market). bench SPY
P4 SPY long only when VIX/VIX3M < 1 AND VRP > 0 (daily, both regimes calm). bench SPY
P5 USO flat for 21 days after OVX >= 1.5 x its trailing 63d median, else long
   (oil fear spikes keep going: lab study 7 found shocks continue; same 1.5x as T8). bench USO
Expectation: P1 weak positive (BTZ effect is mostly a 2008 story); P2 unknown; P3-P5 likely
lose to buy-and-hold on Sharpe like the study 1 filters.
"""
import numpy as np, pandas as pd
from common import load, vload, evaluate, table, lagcheck

vix, ovx, v3m, vvix = load("^VIX"), load("^OVX"), vload("VIX3M"), vload("VVIX")
spy, uso = load("SPY").pct_change(), load("USO").pct_change()
rv = lambda r: r.rolling(21).std() * np.sqrt(252) * 100

def month_end(sig):
    me = sig.groupby(sig.index.to_period("M")).tail(1)
    return me.reindex(sig.index).ffill()

vrp_s = (vix ** 2 - rv(spy) ** 2).dropna()
vrp_o = (ovx ** 2 - rv(uso) ** 2).dropna()
rules = []
def run(name, pos, ret, st):
    rules.append(evaluate(name, pos, ret, 5, start=st))
    rules.append(lagcheck(name, pos, ret, cost_bps=5, start=st))

run("P1 SPY long if VRP>0 (m-end)", month_end((vrp_s > 0).astype(float)), spy, "1993-03-01")
run("P2 USO long if oil VRP>0 (m-end)", month_end((vrp_o > 0).astype(float)), uso, "2007-06-15")
q90 = vvix.rolling(252).quantile(0.9)
run("P3 SPY flat if VVIX>p90", (~(vvix > q90)).astype(float)[q90.notna()], spy, "2008-01-02")
R = (vix / v3m)
p4 = ((R < 1) & (vix ** 2 - rv(spy) ** 2 > 0)).astype(float)[R.notna()]
run("P4 SPY long if R<1 & VRP>0", p4, spy, "2006-07-18")
spk = (ovx >= 1.5 * ovx.rolling(63).median()).astype(float)
off = spk.replace(0, np.nan).ffill(limit=20).fillna(0)
run("P5 USO flat 21d after OVX spike", (1 - off).loc["2007-08-15":], uso, "2007-08-15")
print(table(rules))
for n, s in [("SPY VRP>0", vrp_s > 0), ("oil VRP>0", vrp_o > 0)]:
    print(n, "share", round(float(s.mean()), 3))
pd.DataFrame(rules).to_csv("study2_results.csv", index=False)
