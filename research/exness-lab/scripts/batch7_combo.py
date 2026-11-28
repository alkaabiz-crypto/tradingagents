"""Batch 7 (pre-registered 2026-11-26): the $300 split into three $100 sleeves, swap-free, measured costs.
1) USTEC overnight hold above the 200-day, 3.5 pt round trip (user: open spread 1.5-3.5 pts on Exness).
2) BTC Williams breakout k=0.5, weekdays only, 10 bp + 2 bp slip (conservative).
3) IBS (0.2/0.8) x vol target 15% on USTEC, close fill, 1.45 bp.
Sleeves are not rebalanced. Report 2024-01-02..2026-11-25 and 2020-2023 (to see a bad stretch).
"""
import sys, numpy as np, pandas as pd
sys.path.insert(0,"lab"); import famous2_lib as F
q=pd.read_csv("data/QQQ.csv",parse_dates=["Date"],index_col="Date").dropna()
b=pd.read_csv("data/BTC-USD.csv",parse_dates=["Date"],index_col="Date").dropna()
lvl=q.Close.shift()*41; m=q.Close.shift()>q.Close.rolling(200).mean().shift()
s1=((q.Open/q.Close.shift()-1)-3.5/lvl).where(m,0).fillna(0)
R=(b.High-b.Low).shift(); trig=b.Open+0.5*R; hit=(b.High>=trig)&(b.index.dayofweek<5)
s2=pd.Series(np.where(hit,b.Close/np.maximum(trig,b.Open)*(1-2e-4)-1-10e-4,0.0),index=b.index).fillna(0)
c=q.Close; ibs=(c-q.Low)/(q.High-q.Low).replace(0,np.nan); vt=(0.15/(c.pct_change().rolling(20).std()*np.sqrt(252))).clip(upper=1).fillna(0)
p=F.hold_until(ibs<0.2,ibs>0.8)*vt
s3=(p.shift().fillna(0)*c.pct_change()-p.diff().abs().fillna(0).shift().fillna(0)*1.45/2e4).fillna(0)
for a,z in (("2020","2023-12-31"),("2024","2026-11-25")):
    eqs={n:100*(1+s.loc[a:z]).cumprod() for n,s in (("USTEC overnight",s1),("BTC breakout weekdays",s2),("USTEC IBS x vol",s3))}
    tot=pd.concat(eqs,axis=1).ffill().fillna(100).sum(axis=1)
    print(f"## {a}..{z[:4]}")
    for n,e in eqs.items(): print(f"- {n}: ${e.iloc[-1]:.0f}, worst drop {(e/e.cummax()-1).min():.0%}")
    yr=tot.resample("YE").last(); print(f"- TOTAL $300 -> ${tot.iloc[-1]:.0f}; worst drop ${(tot.cummax()-tot).max():.0f} ({(tot/tot.cummax()-1).min():.0%}); year ends {yr.round(0).to_dict()}")
    print(f"- correlation of daily sleeve returns: {pd.concat([s1.loc[a:z],s2.loc[a:z],s3.loc[a:z]],axis=1).dropna().corr().round(2).values.tolist()}")
