"""Batch 34b: robustness of gold turn-of-month. Neighbours: start 0/1/2 days before month end x hold through day 2/3/4/5.
$ at XAUUSD 0.01 lot (1 oz, gold ~= GLD x 10.9), spread $0.20 per round trip. Bootstrap, years."""
import numpy as np, pandas as pd
def sh(x, ann=252): x = x.dropna(); return x.mean() / x.std() * np.sqrt(ann) if len(x) > 30 and x.std() > 0 else np.nan
d = pd.read_csv("data/GLD.csv", parse_dates=["Date"], index_col="Date").dropna().loc[:"2026-11-24"]; c = d.Close
m = pd.Series(c.index.to_period("M"), index=c.index); k = m.groupby(m).cumcount() + 1; kb = m.groupby(m).cumcount(ascending=False)  # 0 = last day
r = c.pct_change().fillna(0); g = c * 10.9
for pre in (0, 1, 2):
    for end in (2, 3, 4, 5):
        pos = ((k <= end) | (kb < pre)).astype(float)
        x = pos * r - pos.diff().abs().fillna(0) * 1.5 / 2e4
        usd = pos * g.diff().fillna(0) - pos.diff().abs().fillna(0) * 0.10
        s = [sh(x.loc["2014":"2019"]), sh(x.loc["2020":"2023"]), sh(x.loc["2024":])]; yr = usd.loc["2014":].groupby(usd.loc["2014":].index.year).sum()
        e = usd.loc["2014":].cumsum(); e24 = usd.loc["2024":].cumsum()
        print(f"pre {pre} end {end}: S {s[0]:.2f}/{s[1]:.2f}/{s[2]:.2f} 2024$ {usd.loc['2024':].sum():+.0f} dd24 {(e24-e24.cummax()).min():.0f} dd14 {(e-e.cummax()).min():.0f} losing {(yr<0).sum()}/{len(yr)}")
        if (pre, end) == (0, 3):
            xx = x.loc["2014":].values; rng = np.random.default_rng(1); b = 20; kk = len(xx)//b
            bm = np.array([np.concatenate([xx[s_:s_+b] for s_ in rng.integers(0, len(xx)-b, kk)]).mean() for _ in range(2000)])
            print("  boot p", ((bm - bm.mean()) >= xx.mean()).mean(), "years", yr.round(0).astype(int).to_dict())
            print("  hold gold 0.01 2024$", round(g.iloc[-1] - g.loc['2024':].iloc[0]))
