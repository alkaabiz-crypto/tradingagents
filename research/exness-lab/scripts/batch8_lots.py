"""Batch 8 (2026-11-26): do the sleeves fit Exness's 0.01-lot minimum? Assumptions (user: USTEC 1 lot = $1/pt;
US500 assumed the same, unverified): position value of 0.01 lot = 0.01 x index level dollars.
Levels: USTEC ~ QQQ x 41, US500 ~ SPY x 10 (dividend-adjusted proxies, so slightly low).
Backtest 2024-now, swap-free, whole 0.01 lots only (round down; if under 0.01 lot, no trade), costs in points:
US500 overnight above 200-day: 1.0 pt round trip (0.4 pt normal spread, wider at the open, assumed);
US500 IBS x vol target: 0.8 pt round trip. Sleeves $150 + $150 = the $300.
"""
import sys, numpy as np, pandas as pd
sys.path.insert(0,"lab"); import famous2_lib as F
for t,mult in (("QQQ",41),("SPY",10)):
    d=pd.read_csv(f"data/{t}.csv",parse_dates=["Date"],index_col="Date"); L=d.Close.iloc[-1]*mult
    print(f"{t}->{'USTEC' if t=='QQQ' else 'US500'} level ~{L:,.0f}: 0.01 lot = ${0.01*L:,.0f} of exposure")
b=pd.read_csv("data/BTC-USD.csv",parse_dates=["Date"],index_col="Date"); print(f"BTCUSD ~${b.Close.iloc[-1]:,.0f}: 0.01 lot (0.01 BTC, contract unverified) = ${0.01*b.Close.iloc[-1]:,.0f}")
d=pd.read_csv("data/SPY.csv",parse_dates=["Date"],index_col="Date").dropna().loc["2023":]
lvl=d.Close*10; c=d.Close
m=(c>c.rolling(200).mean()).shift().fillna(False)
ibs=(c-d.Low)/(d.High-d.Low).replace(0,np.nan); vt=(0.15/(c.pct_change().rolling(20).std()*np.sqrt(252))).clip(upper=1).fillna(0)
pi=(F.hold_until(ibs<0.2,ibs>0.8)*vt)
eq1,eq2=150.0,150.0; out=[]; days=d.loc["2024":].index; prev=None; lots2_prev=0
for day in days:
    i=d.index.get_loc(day); pc=lvl.iloc[i-1]; o=d.Open.iloc[i]*10; cl=lvl.iloc[i]
    # overnight: decided at prior close, exits at today's open
    if m.iloc[i]:
        lots=np.floor(eq1/(0.01*pc))*0.01
        eq1+=lots*((o-pc)-1.0)
    # IBS x vt: position held close->close, target exposure = pi(prior close) * eq2
    tgt=np.floor(pi.iloc[i-1]*eq2/(0.01*pc))*0.01
    eq2+=tgt*(cl-pc)-abs(tgt-lots2_prev)*0.4; lots2_prev=tgt
    out.append((day,eq1,eq2))
o=pd.DataFrame(out,columns=["d","a","b"]).set_index("d"); tot=o.a+o.b
print(f"US500 overnight $150 -> ${o.a.iloc[-1]:.0f}; IBS x vol $150 -> ${o.b.iloc[-1]:.0f}; total ${tot.iloc[-1]:.0f}, worst drop ${(tot.cummax()-tot).max():.0f}")
