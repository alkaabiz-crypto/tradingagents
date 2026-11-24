"""Study 1: VIX term structure as a risk-off regime. PRE-REGISTERED 2026-11-24, before running.

Signal R_t = VIX_t / VIX3M_t (close t). R > 1 = backwardation = near-term fear above 3-month
fear (Johnson 2017 JFQA: slope summarises risk premia; practitioners treat inversion as
risk-off). VIX3M starts 2006-07, so IS = 2006-07..2013 (contains 2008).
Threshold fixed at 1.0 (the natural definition, not tuned). Costs 5 bp. Long/flat rules.

T1 SPY long, flat when R > 1.                              bench: SPY buy-and-hold
T2 QQQ same.                                               bench: QQQ
T3 IWM same.                                               bench: IWM
T4 SPY long, flat when VIX9D/VIX > 1 (short-end inversion; VIX9D starts 2011, IS short).
T5 TLT long only when R > 1 (flight to quality), else flat. bench: TLT
T6 USO long, flat when R > 1 (risk-off hits oil demand).  bench: USO
T7 GLD long only when R > 1, else flat.                   bench: GLD
T8 "Buy the fear spike": long SPY for 21 trading days after any close with
   VIX >= 1.5 x its trailing 63-day median; flat otherwise. bench: SPY

Expectation (prior): T1-T3 cut drawdowns but give up rebounds (inversions cluster at bottoms),
so Sharpe vs buy-and-hold is a coin flip; T5/T7 low exposure; T8 positive but sparse.
Each rule also reported with the signal lagged one extra day (VIX closes 16:15, after SPY);
the lag check is not a new rule.
"""
import pandas as pd
from common import load, vload, evaluate, table, lagcheck

vix, v3m, v9d = load("^VIX"), vload("VIX3M"), vload("VIX9D")
R = (vix / v3m).dropna()
R9 = (v9d / vix).dropna()
rets = {s: load(s).pct_change() for s in ["SPY", "QQQ", "IWM", "TLT", "USO", "GLD"]}
start = "2006-07-18"

def longflat_off(sig):   # long unless sig is true
    return (~sig).astype(float)

rules = []
def run(name, pos, sym, st=start):
    ret = rets[sym]
    rules.append(evaluate(name, pos, ret, 5, start=st))
    rules.append(lagcheck(name, pos, ret, cost_bps=5, start=st))

run("T1 SPY flat if VIX/VIX3M>1", longflat_off(R > 1), "SPY")
run("T2 QQQ flat if VIX/VIX3M>1", longflat_off(R > 1), "QQQ")
run("T3 IWM flat if VIX/VIX3M>1", longflat_off(R > 1), "IWM")
run("T4 SPY flat if VIX9D/VIX>1", longflat_off(R9 > 1), "SPY", "2011-01-05")
run("T5 TLT long if VIX/VIX3M>1", (R > 1).astype(float), "TLT")
run("T6 USO flat if VIX/VIX3M>1", longflat_off(R > 1), "USO")
run("T7 GLD long if VIX/VIX3M>1", (R > 1).astype(float), "GLD")
med = vix.rolling(63).median()
spike = (vix >= 1.5 * med).astype(float)
t8 = spike.replace(0, float("nan")).ffill(limit=20).fillna(0)
run("T8 SPY 21d after VIX spike", t8.loc[start:], "SPY")
print(table(rules))
print("share of days R>1 (2006-):", round(float((R > 1).mean()), 3), " spike-hold exposure:", round(float(t8.loc[start:].mean()), 3))
pd.DataFrame(rules).to_csv("study1_results.csv", index=False)
