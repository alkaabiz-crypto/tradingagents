"""Batch 10 (2026-11-26): stress test of the USTEC overnight hold above the 200-day, in % of exposure, then in $ at
today's 0.05 lot (~$1,300 exposure). Cost 3.5 pts at today's level = ~1.35 bp; to be fair in old years use 1.35 bp.
Bad periods: dot-com 2000-03-10..2002-10-09, GFC 2007-10-01..2009-03-09, Covid 2020-02-19..2020-04-30, 2022 bear.
Compare: plain holding USTEC (0.05 lot). Also BTC breakout (0.01 lot, ~$605) for 2020 and 2022.
"""
import numpy as np, pandas as pd
q=pd.read_csv("data/QQQ.csv",parse_dates=["Date"],index_col="Date").dropna()
m=(q.Close>q.Close.rolling(200).mean()).shift().fillna(False)
on=((q.Open/q.Close.shift()-1)-1.35e-4).where(m,0).fillna(0); hold=q.Close.pct_change().fillna(0)
b=pd.read_csv("data/BTC-USD.csv",parse_dates=["Date"],index_col="Date").dropna()
R=(b.High-b.Low).shift(); t=b.Open+0.5*R; hit=(b.High>=t)&(b.index.dayofweek<5)
bk=pd.Series(np.where(hit,b.Close/np.maximum(t,b.Open)*(1-2e-4)-1-10e-4,0.0),index=b.index).fillna(0)
EXPO={"on":1300,"hold":1300,"bk":605}
P={"Dot-com crash 2000-02":("2000-03-10","2002-10-09"),"Financial crisis 2007-09":("2007-10-01","2009-03-09"),
   "Covid crash 2020":("2020-02-19","2020-04-30"),"2022 bear market":("2022-01-01","2022-12-31"),"Whole history":("1999-03-10","2026-11-25")}
def dd(x): e=(1+x).cumprod(); return (e/e.cummax()-1).min()
print("| Period | Overnight hold: result | worst drop | in $ at 0.05 lot | Holding USTEC: result | worst drop | in $ | BTC breakout worst drop ($ at 0.01) |")
for n,(a,z) in P.items():
    o,h=on.loc[a:z],hold.loc[a:z]; bx=bk.loc[a:z]
    btxt=f"{dd(bx):.0%} (${dd(bx)*605:.0f})" if len(bx)>20 else "no data"
    print(f"| {n} | {(1+o).prod()-1:+.0%} | {dd(o):.0%} | ${dd(o)*1300:.0f} | {(1+h).prod()-1:+.0%} | {dd(h):.0%} | ${dd(h)*1300:.0f} | {btxt} |")
w=on[on!=0]; print(f"worst single night since 1999: {w.min():.1%} on {w.idxmin().date()} (= ${w.min()*1300:.0f} at 0.05 lot); nights below -3%: {(w<-0.03).sum()} of {len(w)}")
for bal in (228,1000):
    print(f"balance ${bal}: 0.05 lot USTEC = {1300/bal:.1f}x leverage; history worst drop {dd(on)*1300/bal:.0%} of the balance; worst night {w.min()*1300/bal:.0%}")
