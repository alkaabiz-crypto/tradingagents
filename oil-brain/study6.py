"""Study 6 (pre-registered 2026-11-24): diversified commodity trend and carry (literature grade A).
Universe (Yahoo ETFs, each joins when it has 300 days of history):
  USO, UNG, UGA, GLD, SLV, DBB, DBA, CORN, WEAT, SOYB, PALL, PPLT.
Month-end rebalance; each asset vol-scaled to 15%/yr / N (63-day vol), so equal risk; 5 bp per turnover.
P1 Hurst et al. blend: average of sign(21d), sign(63d), sign(252d) returns.
P2 Moskowitz et al.: sign(252d) only.
P3 carry: for USO/USL and UNG/UNL only, sign(63d front ETF return minus 63d 12-month ETF return)
   (USO lagging USL = contango = short), same sizing. Too few pairs for a cross-section.
P4 P1 + P3 (average of positions where both exist).
Benchmark: DBC buy and hold (broad long-only commodities).
Gates as engine.py; placebo = all assets' positions shifted in time by the same random amount.
"""
import numpy as np, pandas as pd
from engine import load, sharpe, tstat, IS_END, OOS_END
U=["USO","UNG","UGA","GLD","SLV","DBB","DBA","CORN","WEAT","SOYB","PALL","PPLT"]
px=pd.DataFrame({s:load(s) for s in U}).loc["2007-01-01":]
ret=px.pct_change()
vol=ret.rolling(63).std()*np.sqrt(252)
alive=px.notna().cumsum()>=300
N=alive.sum(axis=1).replace(0,np.nan)
me=px.index.to_series().groupby(px.index.to_period("M")).last().values
def monthly(sig):
    w=(sig*(0.15/vol).clip(upper=3)).div(N,axis=0).where(alive)
    return w.loc[me].reindex(px.index).ffill().fillna(0)
s1=sum(np.sign(px.pct_change(k)) for k in (21,63,252))/3
s2=np.sign(px.pct_change(252))
carry=pd.DataFrame(0.0,index=px.index,columns=U)
for f,b in [("USO","USL"),("UNG","UNL")]:
    carry[f]=np.sign(px[f].pct_change(63)-load(b).reindex(px.index).pct_change(63)).fillna(0)
P={"P1 trend blend 1/3/12m":monthly(s1),"P2 trend 12m":monthly(s2),"P3 carry (oil, gas)":monthly(carry),
   "P4 trend blend + carry":monthly(s1.where(carry==0,(s1+carry)/2))}
def port(w,cost=5):
    turn=w.diff().abs().sum(axis=1)
    return (w.shift(1)*ret).sum(axis=1)-turn.shift(1).fillna(0)*cost/1e4
bench=load("DBC").pct_change().reindex(px.index)
rows=[]; rng=np.random.default_rng(7)
for k,w in P.items():
    r=port(w).loc["2008-06-01":]; r2=port(w,10).loc["2008-06-01":]
    post=r.loc["2014-01-01":]; real=sharpe(post); n=len(w); beats=0
    for _ in range(300):
        sh=int(rng.integers(n//10,n-n//10)); ws=pd.DataFrame(np.roll(w.values,sh,axis=0),index=w.index,columns=w.columns)
        beats+= sharpe(port(ws).loc["2014-01-01":])<real
    pp=1-beats/300
    g=[sharpe(r.loc["2014":OOS_END])>0.3,sharpe(r.loc["2020":])>0.3,real>sharpe(bench.loc["2014":]),tstat(post)>=2,pp<=0.05,r2.loc["2014":].sum()>0]
    rows.append(dict(rule=k,IS=sharpe(r.loc[:IS_END]),OOS=sharpe(r.loc["2014":OOS_END]),HOLDOUT=sharpe(r.loc["2020":]),post=real,
        bench_DBC=sharpe(bench.loc["2014":]),t_post=tstat(post),placebo_p=pp,cagr_post=(1+post).prod()**(252/len(post))-1,
        maxdd=((1+post).cumprod()/(1+post).cumprod().cummax()-1).min(),verdict="PASS" if all(g) else f"FAIL ({6-sum(g)} of 6)"))
print(pd.DataFrame(rows).set_index("rule").round(2).to_string())
w=P["P1 trend blend 1/3/12m"]; r=port(w).loc["2014":]
print("\nP1 by year %:", (r.groupby(r.index.year).sum()*100).round(1).to_dict())
print("P1 current positions (latest month-end):", w.iloc[-1][w.iloc[-1]!=0].round(3).to_dict())
