"""Batch 9 (2026-11-26): sizing with Exness minimum lots verified from Hazza's account (coordinator note):
US500 $1/pt, min 0.14 lot; USTEC $1/pt, min 0.05 lot; BTCUSD 1 BTC/lot, min 0.01; swap-free, leverage 1:200.
Fixed minimum lots (no compounding), P&L in dollars = lots x points. Levels: US500 ~ SPY x 10, USTEC ~ QQQ x 41.
Costs: US500 overnight 1.0 pt round trip; USTEC overnight 3.5 pt; USTEC IBS 2.5 pt per round trip; BTC 10 bp + 2 bp.
Account $1,000. Worst drop in dollars vs the $300 limit. Periods 2020-2023 (includes 2022 bear) and 2024-now.
"""
import sys, numpy as np, pandas as pd
sys.path.insert(0,"lab"); import famous2_lib as F
spy=pd.read_csv("data/SPY.csv",parse_dates=["Date"],index_col="Date").dropna()
qqq=pd.read_csv("data/QQQ.csv",parse_dates=["Date"],index_col="Date").dropna()
btc=pd.read_csv("data/BTC-USD.csv",parse_dates=["Date"],index_col="Date").dropna()
def onight(d,mult,lots,rt):
    c=d.Close*mult; o=d.Open*mult; m=(d.Close>d.Close.rolling(200).mean()).shift().fillna(False)
    return (lots*((o-c.shift())-rt)).where(m,0).fillna(0)
def hold(d,mult,lots): return (lots*(d.Close*mult).diff()).fillna(0)
def ibs(d,mult,lots,rt):
    c=d.Close; i=(c-d.Low)/(d.High-d.Low).replace(0,np.nan); p=F.hold_until(i<0.2,i>0.8)
    return (lots*(p.shift().fillna(0)*(c*mult).diff()-p.diff().abs().fillna(0).shift().fillna(0)*rt/2)).fillna(0)
def bk(d,lots):
    R=(d.High-d.Low).shift(); t=d.Open+0.5*R; hit=(d.High>=t)&(d.index.dayofweek<5)
    px=np.maximum(t,d.Open); return pd.Series(np.where(hit,lots*(d.Close-px)-lots*px*12e-4,0.0),index=d.index).fillna(0)
S={"US500 hold 0.14":hold(spy,10,0.14),"US500 overnight 0.14":onight(spy,10,0.14,1.0),
   "USTEC overnight 0.05":onight(qqq,41,0.05,3.5),"USTEC IBS 0.05":ibs(qqq,41,0.05,2.5),"BTC breakout 0.01":bk(btc,0.01)}
L={"US500 hold 0.14":spy.Close*10*0.14,"US500 overnight 0.14":spy.Close*10*0.14,"USTEC overnight 0.05":qqq.Close*41*0.05,"USTEC IBS 0.05":qqq.Close*41*0.05,"BTC breakout 0.01":btc.Close*0.01}
combos={"A US500 hold":["US500 hold 0.14"],"B US500 overnight":["US500 overnight 0.14"],"C USTEC overnight":["USTEC overnight 0.05"],
 "D USTEC IBS":["USTEC IBS 0.05"],"E BTC breakout":["BTC breakout 0.01"],"F US500 overnight + BTC breakout":["US500 overnight 0.14","BTC breakout 0.01"],
 "G USTEC overnight + BTC breakout":["USTEC overnight 0.05","BTC breakout 0.01"],"H US500 overnight + USTEC IBS + BTC":["US500 overnight 0.14","USTEC IBS 0.05","BTC breakout 0.01"]}
print("| Plan on $1,000 | max exposure (x account, 2026) | 2020-23 P&L | 2020-23 worst drop | 2024-now P&L | 2024-now worst drop | worst day 2020-now |")
print("|---|---|---|---|---|---|---|")
for nm,parts in combos.items():
    pnl=pd.concat([S[p] for p in parts],axis=1).fillna(0).sum(axis=1)
    expo=sum(L[p].iloc[-1] for p in parts)/1000
    r=[]
    for a,z in (("2020","2023-12-31"),("2024","2026-11-25")):
        eq=1000+pnl.loc[a:z].cumsum(); r+= [f"{eq.iloc[-1]-1000:+.0f}", f"-${(eq.cummax()-eq).max():.0f}"]
    print(f"| {nm} | {expo:.1f}x | {r[0]} | {r[1]} | {r[2]} | {r[3]} | -${-pnl.loc['2020':].min():.0f} |")
