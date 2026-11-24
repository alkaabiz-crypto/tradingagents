"""Study 7 (pre-registered 2026-11-24): extreme-day fades, Brent-WTI spread, crack spread. USO-based.
X1-X3 fade a USO day beyond +/-2.5 x its 20-day sd (literature: reversal stronger in high vol):
  hold 1, 3, 5 days, all days.  X4/X5: hold 3 days, only when OVX above / below its 252-day median.
S1 Brent-WTI: z = 60-day z-score of log(BNO/USO). z > 2: long USO / short BNO; z < -2: the reverse;
   exit when z crosses 0. Judged on the spread return (traded both legs: 2 x 5 bp).
C1 crack: z = 60-day z-score of log(UGA/USO) (gasoline over crude). z > 1: long USO, z < -1: short,
   else flat (wide margins pull crude demand up).
Daily engine gates (placebo, OOS/HOLDOUT, t, 2x costs).
"""
import numpy as np, pandas as pd
from engine import load, evaluate, table
uso,bno,uga,ovx=(load(s) for s in ["USO","BNO","UGA","^OVX"]); r=uso.pct_change()
z=r/r.rolling(20).std().shift(1)
ev=pd.Series(0.0,index=r.index); ev[z>2.5]=-1; ev[z<-2.5]=1
def hold(e,h):
    out=pd.Series(0.0,index=e.index)
    for i in np.flatnonzero(e.values): out.iloc[i:i+h]=e.iloc[i]
    return out
rows=[evaluate(f"X{k} fade +/-2.5sd day, hold {h}d",hold(ev,h),r,start="2006-06-01",n_placebo=300) for k,h in [(1,1),(2,3),(3,5)]]
hi=(ovx>ovx.rolling(252).median()).reindex(r.index).fillna(False).astype(bool)
rows.append(evaluate("X4 fade, hold 3d, OVX high",hold(ev.where(hi,0),3),r,start="2008-06-01",n_placebo=300))
rows.append(evaluate("X5 fade, hold 3d, OVX low",hold(ev.where(~hi,0),3),r,start="2008-06-01",n_placebo=300))
lr=np.log(bno/uso).dropna(); zs=(lr-lr.rolling(60).mean())/lr.rolling(60).std()
pos=pd.Series(np.nan,index=zs.index); pos[zs>2]=1; pos[zs<-2]=-1; pos[(zs*zs.shift(1))<0]=0; pos=pos.ffill().fillna(0)
spr=(r-bno.pct_change()).reindex(zs.index)
rows.append(evaluate("S1 Brent-WTI z>2 reversion (USO-BNO)",pos,spr,cost_bps=10,start="2010-09-01",n_placebo=300))
lc=np.log(uga/uso).dropna(); zc=(lc-lc.rolling(60).mean())/lc.rolling(60).std()
pos=pd.Series(0.0,index=zc.index); pos[zc>1]=1; pos[zc<-1]=-1
rows.append(evaluate("C1 crack spread z>1 long USO",pos,r,start="2008-06-01",n_placebo=300))
print(table(rows))
