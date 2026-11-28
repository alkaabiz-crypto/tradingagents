"""Batch 6 (pre-registered 2026-11-26): USTEC overnight hold (only above the 200-day) with costs in POINTS,
using the user's figures: normal spread 0.5-3 pts, 5-15+ pts in the first 30-60 s after the 9:30 NY open.
Cost per trade = close-side spread 1 pt + open-side spread S pts, S in {1, 3, 5, 10, 15, 20}; converted to bp with the
USTEC level approximated as QQQ x 41 (NDX/QQQ ratio). A fixed points cost weighs more in early years (lower index).
"""
import numpy as np, pandas as pd
d=pd.read_csv("data/QQQ.csv",parse_dates=["Date"],index_col="Date").dropna()
lvl=d.Close.shift()*41; on=d.Open/d.Close.shift()-1; m=d.Close.shift()>d.Close.rolling(200).mean().shift()
def sh(x): x=x.dropna(); return x.mean()/x.std()*np.sqrt(252)
print(f"USTEC approx level: 2014 {lvl.loc['2014'].mean():.0f}, 2020 {lvl.loc['2020'].mean():.0f}, 2025 {lvl.loc['2025'].mean():.0f}")
print("| open spread | round trip pts | bp in 2025 | Sharpe 2014-19 / 2020-23 / 2024-now | $300 2024-now | breakeven? |")
for S in (1,3,5,10,15,20):
    c=(1+S)/lvl; n=(on-c).where(m,0).fillna(0)
    p=" / ".join(f"{sh(n.loc[a:b]):.2f}" for a,b in (("2014","2019"),("2020","2023"),("2024","2026-11-25")))
    print(f"| {S} pts | {1+S} | {((1+S)/lvl.loc['2025']).mean()*1e4:.1f} | {p} | {300*((1+n.loc['2024':]).prod()-1):+.0f} | {'yes' if sh(n.loc['2024':])>0.3 else 'no'} |")
g=on.where(m).loc["2024":].dropna(); print(f"2024-now gross per night: {g.mean()*1e4:.1f} bp = {(g*lvl.loc['2024':]).mean():.1f} pts; nights {len(g)}")
