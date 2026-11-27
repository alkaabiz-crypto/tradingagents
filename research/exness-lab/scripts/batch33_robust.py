"""Batch 33, pre-registered 2026-11-27: robustness of the Batch 31/32 passes.
 BTC near-52-week-high (A5): neighbours band 3/5/7/10% x lookback 180/365/500 days. $ at 0.01 lot, cost $6.40 per round trip.
 Connors R3 on US500: neighbours last RSI(2) < 5/10/15 x exit > 60/70/80, also on QQQ/DIA; next-open entry check.
 $ at US500 0.14 lot (SPY x10 points, $0.14/pt). 20-day block bootstrap p (mean <= 0). Years losing.
"""
import numpy as np, pandas as pd
def sh(x, ann): x = x.dropna(); return x.mean() / x.std() * np.sqrt(ann) if len(x) > 30 and x.std() > 0 else np.nan
def L(t): return pd.read_csv(f"data/{t}.csv", parse_dates=["Date"], index_col="Date").dropna().loc[:"2026-11-24"]
def boot(x, n=2000, b=20, seed=1):
    x = x.values; rng = np.random.default_rng(seed); k = len(x) // b; m = []
    for _ in range(n):
        st = rng.integers(0, len(x) - b, k); m.append(np.concatenate([x[s:s + b] for s in st]).mean())
    m = np.array(m); return (m - m.mean() + 0 <= -x.mean()).mean()  # centred: P(mean<=0 under null)
def dd(eq): return (eq - eq.cummax()).min()
print("== BTC near 52-week high ==")
c = L("BTC-USD").Close
for lb in (180, 365, 500):
    for band in (0.03, 0.05, 0.07, 0.10):
        pos = (c >= (1 - band) * c.rolling(lb).max()).astype(float); p = pos.shift().fillna(0)
        usd = p * c.diff().fillna(0) * 0.01 - p.diff().abs().fillna(0) * 3.2
        r = p * c.pct_change().fillna(0) - p.diff().abs().fillna(0) * 1.5e-4
        s = [sh(r.loc["2014":"2019"], 365), sh(r.loc["2020":"2023"], 365), sh(r.loc["2024":], 365)]
        yr = usd.loc["2014":].groupby(usd.loc["2014":].index.year).sum()
        print(f"lb {lb} band {band:.2f}: S {s[0]:.2f}/{s[1]:.2f}/{s[2]:.2f} 2024$ {usd.loc['2024':].sum():+.0f} dd24 {dd(usd.loc['2024':].cumsum()):.0f} "
              f"losing yrs {(yr<0).sum()}/{len(yr)} trades/yr {p.diff().abs().loc['2014':].sum()/2/12.9:.1f} expo {p.loc['2014':].mean():.2f}"
              + (f" boot p {boot(r.loc['2014':]):.3f}" if (lb, band) == (365, 0.05) else ""))
        if (lb, band) == (365, 0.05): print("  years $:", yr.round(0).astype(int).to_dict())
bh = c.pct_change().loc["2024":]; print("BTC hold 0.01 lot 2024$:", round((c.iloc[-1] - c.loc['2024':].iloc[0]) * 0.01), "dd", round(dd((c.loc['2024':] - c.loc['2024':].iloc[0]) * 0.01)))
def rsi(c, n):
    d = c.diff(); u = d.clip(lower=0).ewm(alpha=1/n, adjust=False).mean(); v = (-d.clip(upper=0)).ewm(alpha=1/n, adjust=False).mean(); return 100 - 100 / (1 + u / v)
print("== Connors R3 ==")
for t, bp, mult, lot in (("SPY", 1.6, 10, 0.14), ("QQQ", 1.4, 41, 0.05), ("DIA", 1.3, 100, 0.1)):
    d = L(t); c, o = d.Close, d.Open
    r2 = rsi(c, 2); s200 = c > c.rolling(200).mean()
    for lo in (5, 10, 15):
        for ex in (60, 70, 80):
            ent = (r2 < r2.shift()) & (r2.shift() < r2.shift(2)) & (r2.shift(2) < r2.shift(3)) & (r2.shift(2) < 60) & (r2 < lo) & s200
            pos, out = 0, []
            for e, x_ in zip(ent.values, (r2 > ex).values):
                out.append(pos)
                if pos == 0 and e: pos = 1
                elif pos == 1 and x_: pos = 0
            p = pd.Series(out, index=c.index, dtype=float)
            r = p * c.pct_change().fillna(0) - p.diff().abs().fillna(0) * bp / 2e4
            usd = p * c.diff().fillna(0) * mult * lot - p.diff().abs().fillna(0) * bp / 2e4 * c * mult * lot
            # next-open: entry at next open instead of close (lose/gain the overnight gap on entry day), exit unchanged
            st = (p.diff() == 1); gap = (o / c.shift() - 1)
            rn = r - (st * gap).fillna(0)
            s = [sh(r.loc["2014":"2019"], 252), sh(r.loc["2020":"2023"], 252), sh(r.loc["2024":], 252)]
            yr = usd.loc["2014":].groupby(usd.loc["2014":].index.year).sum()
            tt = sh(r.loc["2014":], 252) * np.sqrt(len(r.loc["2014":]) / 252)
            base = (lo, ex) == (10, 70)
            print(f"{t} lo {lo} ex {ex}: S {s[0]:.2f}/{s[1]:.2f}/{s[2]:.2f} t {tt:.2f} nextopen S {sh(rn.loc['2014':],252):.2f} 2024$ {usd.loc['2024':].sum():+.0f} "
                  f"dd {dd(usd.loc['2014':].cumsum()):.0f} losing {(yr<0).sum()}/{len(yr)} trades/yr {st.loc['2014':].sum()/12.9:.1f}" + (f" boot p {boot(r.loc['2014':]):.3f}" if base else ""))
