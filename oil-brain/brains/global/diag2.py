"""Diagnostic for study 2 (IS only, 2001-2013; not a rule): does SPY's or the ETF's own day-t return
predict the Asian ETF's next close-to-close, overnight (close t -> open t+1) and intraday
(open t+1 -> close t+1) returns? Slopes and t-stats per ETF."""
import numpy as np, pandas as pd
from lib import load
A = ["EWJ","EWH","EWS","EWT","EWY","FXI","EWA","EWM","INDA","EWG","EWU"]
spy = load("SPY").pct_change()
rows=[]
for s in A:
    c, o = load(s), load(s, "Open")
    cc = c.pct_change(); on = o / c.shift(1) - 1; intra = c / o - 1
    df = pd.DataFrame({"spy": spy, "own": cc, "cc1": cc.shift(-1), "on1": on.shift(-1), "in1": intra.shift(-1)}).loc["2001":"2013"].dropna()
    for x in ["spy", "own"]:
        for y in ["cc1", "on1", "in1"]:
            b = np.polyfit(df[x], df[y], 1)[0]; e = df[y] - b * df[x]
            se = e.std() / (df[x].std() * np.sqrt(len(df)))
            rows.append(dict(etf=s, x=x, y=y, slope=b, t=b / se, n=len(df)))
print(pd.DataFrame(rows).pivot_table(index="etf", columns=["x","y"], values="t").round(1))
