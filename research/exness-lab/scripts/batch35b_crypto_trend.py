"""Batch 35b: dollars, drawdown, correlation and years for the Batch 35 passes (crypto trend family + candles).
BTC 0.01 lot ($3.20 per side), ETH 0.1 ETH (lot unverified, 5 bp round trip). Compare with holding."""
import sys, numpy as np, pandas as pd
sys.argv = ["x"]; src = open("lab/batch35_indicators.py").read().split("rng = np.random.default_rng(35)")[0]; exec(src)
res = pd.read_csv("lab/batch35_results.csv"); P = res[res.PASS]
out = {}
for t, q, side_cost in (("BTC-USD", 0.01, 3.2), ("ETH-USD", 0.1, None)):
    d = L(t); c = d.Close; S = signals(d, False)
    for nm in P[P.market == t].rule:
        p = pd.Series(np.nan_to_num(S[nm]), index=c.index).shift().fillna(0)
        cost = side_cost if side_cost else 2.5e-4 * c * q
        usd = p * c.diff().fillna(0) * q - p.diff().abs().fillna(0) * cost
        u = usd.loc["2024":]; e = u.cumsum(); yr = usd.loc["2018":].groupby(usd.loc["2018":].index.year).sum()
        out[(t, nm)] = usd
        print(f"{t} {nm:28s} 2024$ {u.sum():+6.0f} dd24 {(e - e.cummax()).min():6.0f} 2025 {yr.get(2025,0):+5.0f} 2026 {yr.get(2026,0):+5.0f} losing yrs since 2018 {(yr<0).sum()}/{len(yr)} trades/yr {p.diff().abs().loc['2018':].sum()/2/8.9:.0f}")
    h = (c.loc["2024":] - c.loc["2024":].iloc[0]) * q; print(f"{t} HOLD 2024$ {h.iloc[-1]:+.0f} dd {(h - h.cummax()).min():.0f}")
M = pd.DataFrame({f"{a[:3]} {b[:12]}": v.loc["2018":] for (a, b), v in out.items()}).fillna(0)
print("avg pairwise corr of daily $:", round(M.corr().values[np.triu_indices(len(M.columns), 1)].mean(), 2))
d = L("SLV"); S = signals(d, False); p = pd.Series(S["K9 three black crows (short)"], index=d.index).shift().fillna(0)
print("SLV black crows trades/yr", round((p.diff() != 0).loc["2014":].sum() / 2 / 12.9, 1), "expo", round(abs(p).loc["2014":].mean(), 3))
