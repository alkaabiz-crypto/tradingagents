"""Batch 30b, pre-registered after Batch 30: robustness of its passes.
IBS<x hold n (SPY, QQQ, DIA, GLD): x in {0.1,0.15,0.2,0.25,0.3} x n in {1,2,3,4}. 10-day low (SPY): lookback {5,7,10,15,20} x hold {2,3,4,5}.
%R(10) (QQQ): threshold {-80,-85,-90,-95} x hold {1,2,3,4}. A family counts if >= 70% of neighbours have post-2014 Sharpe > 0.3
and all three periods > 0. Also: block bootstrap p (20-day blocks, 1000 draws, seed 5) that post-2014 mean <= 0, year-by-year $
at min lots (US500 0.14 = $1,000, USTEC 0.05 = $1,300, US30 ~$1,000, gold 1 oz = $3,450), worst drop $ 2024-now, and the
combined portfolio of the passes."""
import sys, numpy as np, pandas as pd
src = open("lab/batch30_swing.py").read(); exec(src.split("rows = []")[0])
EXP = {"SPY": 1000, "QQQ": 1300, "DIA": 1000, "GLD": 3450}
rng = np.random.default_rng(5)
def run(t, kind, a, n):
    d = pd.read_csv(f"data/{t}.csv", parse_dates=["Date"], index_col="Date").dropna().loc[:"2026-11-24"]; o, h, l, c = d.Open, d.High, d.Low, d.Close; r = c.pct_change().fillna(0)
    s200 = c > c.rolling(200).mean()
    if kind == "ibs": sig = (c - l) / (h - l).replace(0, np.nan) < a
    elif kind == "low": sig = (c <= c.rolling(a).min()) & s200
    else: sig = (-100 * (h.rolling(10).max() - c) / (h.rolling(10).max() - l.rolling(10).min()) < a) & s200
    pos = hold_n(sig.fillna(False), n); return pos * r - pos.diff().abs().fillna(0) * MK[t] / 2e4
def boot(x):
    v = x.values; L = len(v); m = []
    for _ in range(1000):
        idx = np.concatenate([np.arange(s, s + 20) % L for s in rng.integers(0, L, L // 20 + 1)])[:L]; m.append(v[idx].mean())
    return np.mean(np.array(m) <= 0)
fams = [("IBS<0.2, 2 days", "ibs", 0.2, 2, ["SPY", "QQQ", "DIA", "GLD"], [(a, n) for a in (0.1, 0.15, 0.2, 0.25, 0.3) for n in (1, 2, 3, 4)]),
        ("10-day low, 3 days", "low", 10, 3, ["SPY", "QQQ", "DIA"], [(a, n) for a in (5, 7, 10, 15, 20) for n in (2, 3, 4, 5)]),
        ("%R(10)<-90, 2 days", "wr", -90, 2, ["QQQ", "SPY", "DIA"], [(a, n) for a in (-80, -85, -90, -95) for n in (1, 2, 3, 4)])]
port = {}
for nm, kind, a0, n0, mkts, grid in fams:
    for t in mkts:
        ok = []
        for a, n in grid:
            x = run(t, kind, a, n); post = x.loc["2014":]
            ok.append(sh(post, 252) > 0.3 and all(sh(x.loc[p:q], 252) > 0 for p, q in (("2014", "2019"), ("2020", "2023"), ("2024", "2026"))))
        x = run(t, kind, a0, n0); u = x * EXP[t]; e = u.loc["2024":].cumsum()
        y = u.groupby(u.index.year).sum().loc[2014:]
        print(f"{nm} {t}: neighbours ok {np.mean(ok):.0%}; bootstrap p {boot(x.loc['2014':]):.3f}; $ 2024-now {u.loc['2024':].sum():+.0f}, drop {(e - e.cummax()).min():.0f}; losing years {int((y < 0).sum())}/{len(y)}; per year {y.round(0).astype(int).to_dict()}")
        port[f"{nm} {t}"] = u
P = pd.DataFrame(port).fillna(0); print("pairwise corr (2014+) mean:", round(P.loc["2014":].corr().values[np.triu_indices(len(P.columns), 1)].mean(), 2))
