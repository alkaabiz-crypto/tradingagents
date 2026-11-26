"""Batch 24, pre-registered 2026-11-26 before running. Honest optimisation of the BTC NR4 breakout.
Grid (5 x 3 x 3 x 3 x 2 = 270 settings): NR length {3,4,5,6,7}; stop {other side, range middle, other side + 0.5 range};
target {none (close), 1R, 2R}; trend filter {none, 200-day (longs only above, shorts only below), 20-day};
days {all, weekdays}. Daily bars, worst case inside a day: stop counts before target and, if both sides trigger, the
day is a full stop-out on the first side. Cost 3 bp + 2 bp slippage on entries.
Tests: (1) one split: pick the best Sharpe on 2014-2019, report it on 2020-2026 vs the base (NR4, other side, close,
no filter, all days). (2) Walk-forward: each year from 2018, pick the best Sharpe on the previous 3 years, trade it
for that year. A setting replaces the base only if both tests beat the base out of sample.
"""
import itertools, numpy as np, pandas as pd
d = pd.read_csv("data/BTC-USD.csv", parse_dates=["Date"], index_col="Date").dropna(); c, h, l, o = d.Close, d.High, d.Low, d.Open
ph, pl = h.shift(), l.shift(); prg = ph - pl; s200, s20 = c.rolling(200).mean().shift(), c.rolling(20).mean().shift(); wd = c.index.dayofweek < 5
def sh(x): return x.mean() / x.std() * np.sqrt(365) if x.std() > 0 else np.nan
def rule(n, stop, tgt, flt, days):
    rg = h - l; nr = (rg <= rg.rolling(n).min()).shift().fillna(False)
    if days == "wd": nr = nr & wd
    okL = okS = pd.Series(True, index=c.index)
    if flt == "200": okL, okS = o > s200, o < s200
    if flt == "20": okL, okS = o > s20, o < s20
    up, dn = nr & okL & (h >= ph), nr & okS & (l <= pl)
    eL, eS = np.maximum(ph, o) * 1.0002, np.minimum(pl, o) * 0.9998
    off = {"other": 0.0, "mid": -0.5, "wide": 0.5}[stop]
    sL, sS = pl - off * prg, ph + off * prg          # mid: pl + 0.5 rg; wide: pl - 0.5 rg
    rL, rS = eL - sL, sS - eS
    tL = eL + tgt * rL if tgt else None; tS = eS - tgt * rS if tgt else None
    hitSL, hitSS = l <= sL, h >= sS
    xL = np.where(hitSL, sL, np.where(h >= tL, tL, c) if tgt else c); xS = np.where(hitSS, sS, np.where(l <= tS, tS, c) if tgt else c)
    retL, retS = xL / eL - 1, eS / xS - 1
    both = up & dn
    r = np.where(both, np.minimum(sL / eL - 1, eS / sS - 1), np.where(up, retL, np.where(dn, retS, 0.0)))
    return pd.Series(r, index=c.index).fillna(0) - (up | dn) * 3e-4
grid = list(itertools.product((3, 4, 5, 6, 7), ("other", "mid", "wide"), (0, 1, 2), ("none", "200", "20"), ("all", "wd")))
R = {g: rule(*g) for g in grid}; base = (4, "other", 0, "none", "all")
IS = {g: sh(x.loc["2014":"2019"]) for g, x in R.items()}; best = max(IS, key=IS.get)
for nm, g in (("base", base), ("best on 2014-19", best)):
    x = R[g]; print(f"{nm} {g}: in-sample {IS[g]:.2f}; out-of-sample 2020-26 Sharpe {sh(x.loc['2020':]):.2f}, $ at $584 {x.loc['2020':].sum()*584:+.0f}; 2024-26 Sharpe {sh(x.loc['2024':]):.2f}")
oos = pd.Series({g: sh(x.loc["2020":]) for g, x in R.items()})
print(f"share of all 270 settings with OOS Sharpe above base: {(oos > oos[base]).mean():.0%}; median OOS Sharpe {oos.median():.2f}; base OOS {oos[base]:.2f}")
wf, rows = [], []
for y in range(2018, 2027):
    tr = {g: sh(x.loc[str(y - 3):str(y - 1)]) for g, x in R.items()}; g = max(tr, key=tr.get); x = R[g].loc[str(y)]; wf.append(x)
    rows.append(f"{y}: picked {g} -> ${x.sum()*584:+.0f} vs base ${R[base].loc[str(y)].sum()*584:+.0f}")
print("\n".join(rows)); wf = pd.concat(wf)
print(f"walk-forward 2018-26: Sharpe {sh(wf):.2f}, $ {wf.sum()*584:+.0f}; base same years: Sharpe {sh(R[base].loc['2018':]):.2f}, $ {R[base].loc['2018':].sum()*584:+.0f}")
# one-at-a-time effects out of sample (2020-26), others at base
for i, name in enumerate(("NR", "stop", "target", "filter", "days")):
    vals = sorted(set(g[i] for g in grid), key=str)
    print(name, {v: round(oos[tuple(v if j == i else base[j] for j in range(5))], 2) for v in vals})
