"""Study 6 (pre-registered 2026-11-24, before running): ETF volume surges as 'dumb money' (Frazzini & Lamont
2008 JFE: retail flows predict low future returns; Ben-David, Franzoni & Moussawi 2018 JF: ETF demand shocks
push prices away and later revert). Retail piled into USO after oil crashes (2008-09, 2020).
Surge = mean dollar volume (Close x Volume) of the last 21 days / mean of the previous 252 days. Month-end
rebalance, 5 bp, fixed threshold 1.5 (a priori).
 E1 USO: surge > 1.5 -> short USO next month, else flat. Start 2007-06.
 E2 XLE: surge > 1.5 -> short XLE next month, else flat. Start 2000-03.
"""
import numpy as np, pandas as pd
from lib import ld, evaluate, table
def surge(sym):
    df = ld(sym, None); dv = df.Close * df.Volume
    s = dv.rolling(21).mean() / dv.shift(21).rolling(252).mean()
    ends = df.index.to_series().groupby(df.index.to_period("M")).last().values
    return s.loc[ends].reindex(df.index).ffill(), df.Close.pct_change()
rows = []
for sym, nm, st in [("USO", "E1", "2007-06-01"), ("XLE", "E2", "2000-03-01")]:
    s, r = surge(sym)
    rows.append(evaluate(f"{nm} short {sym} after dollar-volume surge", -(s > 1.5).astype(float).where(s.notna()), r, start=st))
    print(sym, "share of months in surge: %.2f; latest ratio %.2f" % ((s.dropna() > 1.5).mean(), s.dropna().iloc[-1]))
print(table(rows))
