"""Study 5 (pre-registered 2026-11-24, from the literature review):
W1 Wen, Indriawan, Lien & Xu (2023, Energy Journal): on EIA Wednesdays the 10:30-11:30 USO move
   predicts the last half hour. Trade USO 15:30 -> 16:00 in the sign of r(10:30-11:30). Control: other days.
W1b same, only when |r1| above its median (paper's filter).
W2 Wen, Gong, Ma & Xu (2021): on non-EIA days, overnight+first hour (prev close -> 10:30) predicts
   the last half hour. Trade 15:30 -> 16:00 in its sign.
Hourly Yahoo bars, ~730 days. Cost 2 bp round trip (penny-spread USO; the literature review's
retail floor) and 5 bp stress. Gate: t >= 2 at 2 bp and still positive at 5 bp.
BM Boons & Porras Prado (2019) basis-momentum proxy: 252d USO return minus 252d USL return,
   month-end, long USO if > 0 else short. Also 63d. Daily engine gates.
"""
import numpy as np, pandas as pd, yfinance as yf
from engine import load, evaluate, table
b=yf.Ticker("USO").history(period="730d",interval="1h"); b.index=b.index.tz_convert("America/New_York")
b=b[(b.index.strftime("%H:%M")>="09:30")&(b.index.strftime("%H:%M")<="15:30")]
rec=[]; prev=None
for d,g in b.groupby(b.index.date):
    g=g.sort_index(); hh=list(g.index.strftime("%H:%M"))
    if "10:30" in hh and "15:30" in hh and prev is not None:
        r1=g.Close.iloc[hh.index("10:30")]/g.Open.iloc[hh.index("10:30")]-1
        r0=g.Open.iloc[hh.index("10:30")]/prev-1
        last=g.Close.iloc[hh.index("15:30")]/g.Open.iloc[hh.index("15:30")]-1
        rec.append(dict(d=d,wd=pd.Timestamp(d).day_of_week,r1=r1,r0=r0,last=last))
    prev=g.Close.iloc[-1]
x=pd.DataFrame(rec); med=x.r1.abs().median()
def rep(name,m,sig):
    for c in (2,5):
        y=(np.sign(sig[m])*x.last[m]-c/1e4)
        print(f"{name:45} cost {c}bp  n {len(y):4}  mean {y.mean()*1e4:6.2f} bp  t {y.mean()/y.std()*np.sqrt(len(y)):5.2f}  win {100*(y>0).mean():3.0f}%")
print(f"USO hourly {x.d.min()} to {x.d.max()}")
wed=x.wd==2
rep("W1 EIA Wed: sign(10:30-11:30) -> last 30m",wed,x.r1)
rep("W1 control, other days",~wed,x.r1)
rep("W1b EIA Wed, |r1| > median",wed&(x.r1.abs()>med),x.r1)
rep("W2 non-EIA: sign(prev close->10:30) -> last 30m",~wed,x.r0)
rep("W2 control, Wednesdays",wed,x.r0)
uso,usl=load("USO"),load("USL"); r=uso.pct_change()
me=uso.index.to_series().groupby(uso.index.to_period("M")).last()
rows=[]
for lb in (252,63):
    bm=(uso.pct_change(lb)-usl.pct_change(lb)).loc[me.values]
    rows.append(evaluate(f"BM basis-momentum {lb}d L/S monthly",np.sign(bm).reindex(uso.index).ffill(),r,start="2009-01-02",n_placebo=300))
    rows.append(evaluate(f"BM basis-momentum {lb}d long/flat",(bm>0).astype(float).reindex(uso.index).ffill(),r,start="2009-01-02",n_placebo=300))
print(table(rows))
