"""Study 2 (pre-registered 2026-11-24, before running): Amihud (2002 JFM) illiquidity in the time series.
Amihud: market illiquidity ILLIQ = mean over the month of |r_d| / dollar volume_d. Expected illiquidity raises
expected returns; an unexpected rise lowers prices at once (stronger for small stocks = flight to liquidity),
so after an illiquidity shock expected returns are higher. ETF proxy: ILLIQ from the ETF's own |r|/(Close*Volume).
Dollar volume trends strongly, so the signal is the ratio of this month's ILLIQ to the mean of the previous
12 months (a priori, no tuning). Month-end rebalance, signal known at the last close of the month. 5 bp.
Rules (3):
 A1 SPY: ratio > 1 -> long SPY next month, else flat (bench SPY).
 A2 IWM: same with IWM's own ILLIQ (Amihud: effect stronger in small firms), bench IWM.
 A3 size spread: SPY ratio > 1 -> long IWM / short SPY next month, else flat (bench: IWM-SPY buy and hold).
"""
import numpy as np, pandas as pd
from lib import ld, evaluate, table, port_eval

def illiq_ratio(sym):
    df = ld(sym, None); r = df.Close.pct_change()
    d = (r.abs() / (df.Close * df.Volume)).replace(np.inf, np.nan)
    m = d.groupby(df.index.to_period("M")).mean()
    ratio = m / m.shift(1).rolling(12).mean()
    me = df.index.to_series().groupby(df.index.to_period("M")).last()
    s = pd.Series(ratio.values, index=me.values).reindex(df.index).ffill()
    return s, r

rows = []
s, r = illiq_ratio("SPY"); rows.append(evaluate("A1 SPY long after illiquidity shock", (s > 1).astype(float), r, start="1995-01-01"))
si, ri = illiq_ratio("IWM"); rows.append(evaluate("A2 IWM long after own illiquidity shock", (si > 1).astype(float), ri, start="2001-08-01"))
ret = pd.DataFrame({"IWM": ri, "SPY": r}).dropna()
w = pd.DataFrame({"IWM": (s > 1).astype(float), "SPY": -(s > 1).astype(float)}).reindex(ret.index)
rows.append(port_eval("A3 long IWM/short SPY after SPY illiquidity shock", w, ret, ret.IWM - ret.SPY, "2001-08-01"))
print(table(rows))
print("share of months with ratio>1: SPY %.2f, IWM %.2f" % ((s.dropna() > 1).mean(), (si.dropna() > 1).mean()))
# Diagnostic: next-month SPY return by ratio tercile, IS vs post
me = r.index.to_series().groupby(r.index.to_period("M")).last().values
nm = (1 + r).groupby(r.index.to_period("M")).prod().shift(-1) - 1
x = pd.DataFrame({"ratio": s.loc[me].values, "next": nm.values}, index=me).dropna()
for per, a, b in [("IS", None, "2013"), ("post", "2014", None)]:
    z = x.loc[a:b]; print(per, (z.groupby(pd.qcut(z.ratio, 3, labels=["low", "mid", "high"]), observed=True).next.mean() * 100).round(2).to_dict())
