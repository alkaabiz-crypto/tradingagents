"""Batch 11b robustness of rules 2/3 (Williams weekdays + trend filter). Pre-registered after Batch 11, before this run.
Neighbours: k in 0.3..0.8 x momentum lookback 6/9/12 months (filter rule 2). Per-year $ at 0.01 lot.
Block bootstrap (20-day blocks, 1000 draws, seed 7) p-value that post-2014 Sharpe <= buy-and-hold's. 3 bp cost.
"""
import sys, numpy as np, pandas as pd
d = pd.read_csv(f"{sys.argv[1]}/BTC-USD.csv", parse_dates=["Date"], index_col="Date").dropna()
c, h, l, o = d.Close, d.High, d.Low, d.Open; cost = 3e-4; rng = np.random.default_rng(7)
def sh(x): x = x.dropna(); return x.mean() / x.std() * np.sqrt(365) if x.std() > 0 else np.nan
m = pd.Series(c.index.to_period("M"), index=c.index); me = m != m.shift(-1); wd = c.index.dayofweek < 5
def mom(n): return (pd.Series(np.where(me, (c / c.shift(n) - 1) > 0, np.nan), index=c.index).ffill().fillna(0) > 0).shift().fillna(False)
def will(k, filt):
    trig = o + k * (h - l).shift(); hit = (h >= trig) & wd & filt
    pct = pd.Series(np.where(hit, c / np.maximum(trig, o) * (1 - 2e-4) - 1 - cost, 0.0), index=c.index).fillna(0)
    usd = pd.Series(np.where(hit, 0.01 * (c - np.maximum(trig, o) * (1 + 2e-4)) - cost * 0.01 * c, 0.0), index=c.index).fillna(0)
    return pct, usd
bh = c.pct_change().fillna(0).loc["2014":]
print("| k | 6m filter | 9m filter | 12m filter | no filter |  (post-2014 Sharpe; B&H %.2f)" % sh(bh))
for k in (0.3, 0.4, 0.5, 0.6, 0.7, 0.8):
    print(f"| {k} | " + " | ".join(f"{sh(will(k, f)[0].loc['2014':]):.2f}" for f in (mom(182), mom(273), mom(365), pd.Series(True, index=c.index))) + " |")
for nm, f in (("12m filter", mom(365)), ("no filter", pd.Series(True, index=c.index))):
    p, u = will(0.5, f)
    print(f"\n{nm}: $ per year at 0.01 lot:", u.groupby(u.index.year).sum().round(0).to_dict())
    print(f"{nm}: Sharpe per year:", {y: round(sh(g), 2) for y, g in p.groupby(p.index.year)})
    a, b = p.loc["2014":].values, bh.values; L = len(a); out = []
    for _ in range(1000):
        idx = np.concatenate([np.arange(s, s + 20) % L for s in rng.integers(0, L, L // 20 + 1)])[:L]
        out.append(sh(pd.Series(a[idx])) - sh(pd.Series(b[idx])))
    print(f"{nm}: bootstrap p = {np.mean(np.array(out) <= 0):.3f}; trades/yr {(p.loc['2014':] != 0).mean()*365:.0f}")
    u24 = u.loc["2024":]; e = u24.cumsum(); print(f"{nm}: 2024-now ${u24.sum():.0f}, worst drop ${(e - e.cummax()).min():.0f}, longest losing streak (trades) ", end="")
    t = u24[u24 != 0]; s = (t < 0).astype(int); print(int(s.groupby((s != s.shift()).cumsum()).sum().max()))
