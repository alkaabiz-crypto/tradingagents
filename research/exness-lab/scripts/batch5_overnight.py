"""Batch 5 (pre-registered 2026-11-26): ideas the old lab dropped on costs, re-tested at measured Exness costs.
A) Overnight premium: buy at the US close, sell at the next US open (index CFDs, swap-free = no financing).
   Variants fixed in advance: every night; only nights when close > 200-day average; only Mon-Thu nights (skip weekends).
   Round-trip costs: 0 (gross), measured spread + 1 bp slippage, and 3 bp, 5 bp (open spreads are wider).
B) Lab QQQ IBS sleeve (IBS < 0.2, exit first close with IBS > 0.5) on USTEC/US500/US30 at Exness costs.
Pass bar as famous2 (Sharpe > 0.3 in 2014-19, 2020-23, 2024-now; post-2014 t >= 2; positive at 2x cost).
"""
import sys, numpy as np, pandas as pd
sys.path.insert(0, "lab"); import famous2_lib as F
def sh(x): x=x.dropna(); return x.mean()/x.std()*np.sqrt(252) if x.std()>0 else np.nan
def per(x): return " / ".join(f"{sh(x.loc[a:b]):.2f}" for a,b in (("2014","2019"),("2020","2023"),("2024","2026-11-25")))
EX={"SPY":1.6,"QQQ":1.45,"DIA":1.26}
print("## A) overnight premium")
print("| market | variant | gross bp/night | net @measured Sharpe 14-19/20-23/24-now | post-14 t | net @3 bp | net @5 bp | $300 2024-now @measured |")
for t,c0 in EX.items():
    d=pd.read_csv(f"data/{t}.csv",parse_dates=["Date"],index_col="Date").dropna()
    on=(d.Open/d.Close.shift()-1)
    s200=d.Close.rolling(200).mean().shift()
    wk=pd.Series(d.index.dayofweek,index=d.index)
    gap_days=pd.Series(d.index,index=d.index).diff().dt.days
    V={"every night":pd.Series(True,index=d.index),"close above 200-day":(d.Close.shift()>s200),"weekday nights only":gap_days==1}
    for nm,m in V.items():
        g=on.where(m,0).fillna(0)
        def net(c): return g-np.where(m,c/1e4,0)
        n=net(c0); x=n.loc["2014":]
        print(f"| {t} | {nm} | {g[m].loc['2014':].mean()*1e4:.1f} | {per(n)} | {sh(x)*np.sqrt(len(x)/252):.1f} | {sh(net(3).loc['2014':]):.2f} | {sh(net(5).loc['2014':]):.2f} | {300*((1+n.loc['2024':]).prod()-1):+.0f} |")
print("\n## B) lab IBS sleeve (exit IBS > 0.5), close fill")
for t,c0 in EX.items():
    d=pd.read_csv(f"data/{t}.csv",parse_dates=["Date"],index_col="Date").dropna(); c=d.Close
    ibs=(c-d.Low)/(d.High-d.Low).replace(0,np.nan); p=F.hold_until(ibs<0.2,ibs>0.5)
    for cc in (c0,2*c0):
        n=(p.shift().fillna(0)*c.pct_change()-p.diff().abs().fillna(0).shift().fillna(0)*cc/2e4).fillna(0)
        x=n.loc["2014":]; bh=c.pct_change().loc["2014":]
        print(f"- {t} at {cc:.1f} bp: Sharpe {per(n)}; post-14 {sh(x):.2f} (t {sh(x)*np.sqrt(len(x)/252):.1f}) vs hold {sh(bh):.2f}; $300 2024-now {300*((1+n.loc['2024':]).prod()-1):+.0f}")
