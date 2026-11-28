"""Batch 40b: neighbours of the month-end rebalancing rule: threshold 0/2/3/4% x window 3/5/7 days, US500 and USTEC.
$ per year since 2010 and since 2024 at 0.14 US500 / 0.05 USTEC; years losing."""
import numpy as np, pandas as pd
def L(t): return pd.read_csv(f"data/{t}.csv", parse_dates=["Date"], index_col="Date").dropna().loc[:"2026-11-24"]
tlt = L("TLT").Close
for t, exp, bp in (("SPY", 1000, 1.6), ("QQQ", 1330, 1.4)):
    c = L(t).Close; r = c.pct_change().fillna(0); ix = c.index; tl = tlt.reindex(ix).ffill(); m = pd.Series(ix.to_period("M"), index=ix)
    kb = m.groupby(m).cumcount(ascending=False)
    for W in (3, 5, 7):
        for th in (0.0, 0.02, 0.03, 0.04):
            base_c = c.shift().groupby(m).transform("first"); base_t = tl.shift().groupby(m).transform("first")
            diff = (c / base_c - 1) - (tl / base_t - 1)
            sig = pd.Series(np.where(kb == W, np.where(diff > th, -1, np.where(diff < -th, 1, 0)), np.nan), index=ix)
            p = sig.groupby(m).ffill().where(kb < W, 0).fillna(0)
            u = (p * r - (p.diff().abs() > 0) * bp / 2e4) * exp; u = u.loc["2010":]
            y = u.groupby(u.index.year).sum(); e = u.cumsum()
            print(f"{t} W{W} th{th:.2f}: 2010-23 $/yr {u.loc[:'2023'].sum()/14:+.0f}  2024+ $/yr {u.loc['2024':].sum()/2.9:+.0f}  drop {(e-e.cummax()).min():.0f}  losing yrs {(y<0).sum()}/{len(y)}")
