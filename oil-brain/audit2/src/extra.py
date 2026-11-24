import sys
import numpy as np, pandas as pd
sys.path.insert(0, sys.argv[1] + "/src")
import engine
from engine import load, backtest, stats, period, indicators, simulate_from
ROOT=sys.argv[1]; gld=load(ROOT+"/data/GLD_raw.csv")
# reconciliation variants
src=open(ROOT+"/src/engine.py").read()
def bt_noexitday(df):
    ind=indicators(df); o,h,l,c=(df[x].values for x in ["Open","High","Low","Close"]); atr=ind.atr.values
    sig=((df.Close>ind.sma)&(ind.rsi<10)).values; d=df.index; tr=[]; i=0; n=len(c)
    while i<n-1:
        if sig[i] and not np.isnan(atr[i]):
            x,xp,ep,_=simulate_from(o,h,l,c,atr,i,i+1,2,3); tr.append(dict(entry_date=d[i+1],R=(xp-ep-5e-4*(ep+xp))/(2*atr[i]))); i=x+1; continue
        i+=1
    return pd.DataFrame(tr)
t=bt_noexitday(gld); print("no re-entry on exit-day close: 2014-now", stats(period(t,"2014-01-01")))
t=backtest(gld); 
for end in ["2025-12-31","2026-06-30"]:
    print("2014-",end, stats(period(t,"2014-01-01",end)))
# non-overlapping placebo across full 2014-now window
ind=indicators(gld); o,h,l,c=(gld[x].values for x in ["Open","High","Low","Close"]); atr=ind.atr.values; d=gld.index
el=((gld.Close>ind.sma).values)&(d>="2014-01-01")&~np.isnan(atr)
real=period(t,"2014-01-01"); N=len(real); rm=real.R.mean()
rng=np.random.default_rng(7)
def run(q):
    rs=[]; i=0; n=len(c)
    while i<n-1:
        if el[i] and rng.random()<q:
            x,xp,ep,_=simulate_from(o,h,l,c,atr,i,i+1,2,3); rs.append((xp-ep-5e-4*(ep+xp))/(2*atr[i])); i=x; continue
        i+=1
    return rs
for q in [0.05,0.08,0.12]:
    print(q, np.mean([len(run(q)) for _ in range(30)]))
