"""Study 3 (pre-registered 2026-11-24): is the momentum candidate just two crashes?
Re-score study 2's candidates post-2014 with the crash windows removed
(2014-07-01..2016-02-29 and 2020-01-15..2020-06-30), and by calendar year.
Also long-only vs short-only legs. No new parameters."""
import numpy as np, pandas as pd
from engine import load, pnl, sharpe, tstat
uso, usl = load("USO"), load("USL"); r = uso.pct_change(); vol = r.rolling(63).std()*np.sqrt(252)
me = uso.index.to_series().groupby(uso.index.to_period("M")).last()
def tsmom(lb):
    s=np.sign(uso.pct_change(lb)).loc[me.values]; sc=(0.2/vol).clip(upper=1).loc[me.values]
    return (s*sc).reindex(uso.index).ffill().fillna(0)
cands={f"TSMOM {lb}d":tsmom(lb) for lb in [10,21,42,63,126]}
sp=np.sign(uso.pct_change(21)-usl.pct_change(21)).fillna(0)
cands["COMBO carry21+TSMOM21"]=(sp+tsmom(21))/2
crash=((r.index>="2014-07-01")&(r.index<="2016-02-29"))|((r.index>="2020-01-15")&(r.index<="2020-06-30"))
rows=[]
for k,p in cands.items():
    x=pnl(p,r.dropna(),5); post=x.loc["2014-01-01":]; nc=post[~crash[r.index>="2014-01-01"][:len(post)]]
    lo=pnl(p.clip(lower=0),r.dropna(),5).loc["2014-01-01":]; sh=pnl(p.clip(upper=0),r.dropna(),5).loc["2014-01-01":]
    yrs=post.groupby(post.index.year).sum()
    rows.append(dict(rule=k,post=sharpe(post),no_crash=sharpe(nc),t_no_crash=tstat(nc),long_leg=sharpe(lo),short_leg=sharpe(sh),
                     yrs_positive=f"{(yrs>0).sum()}/{len(yrs)}"))
print(pd.DataFrame(rows).set_index("rule").round(2).to_string())
p=cands["TSMOM 42d"]; x=pnl(p,r.dropna(),5).loc["2014-01-01":]
print("\nTSMOM 42d by year (%):", (x.groupby(x.index.year).sum()*100).round(1).to_dict())
