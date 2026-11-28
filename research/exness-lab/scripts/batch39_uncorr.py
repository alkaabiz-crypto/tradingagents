"""Batch 39, pre-registered 2026-11-28: ideas that should NOT move with BTC Williams (Hazza: more uncorrelated candidates).
 G1/G2 gap down > 0.5% on US500 (SPY) / USTEC (QQQ): buy the open, sell the close (day session only).
 G3/G4 gap up > 0.5% on US500 / USTEC: short the open, cover the close.
 W1/W2 BTC / ETH weekend hold: long from Friday's UTC close to Sunday's UTC close, only above the 50-day.
 PR1 ETH/BTC ratio: 20-day z-score < -2 -> long ETH / short BTC (equal $), > 2 -> reverse; exit when z crosses 0.
 PR2 USTEC/US500 ratio (QQQ/SPY), same rule.  PR3 US30/US500 ratio (DIA/SPY), same rule.
Bar as Batch 38: Sharpe > 0.3 in 2010(BTC 2015, ETH 2018)-19, 2020-23, 2024-now; t >= 2; 2x cost positive; beats 500
random-timing shifts (BH q < 0.10 across these 9). $ at: US500 $1,000, USTEC $1,330, pairs $1,000 per leg, crypto $600 per leg.
Also reports correlation of daily $ with plan A (10-day low US500 + BTC NR4 + BTC Williams + ETH above 50-day)."""
import io, contextlib, numpy as np, pandas as pd
from math import erf, sqrt
with contextlib.redirect_stdout(io.StringIO()): exec(open("lab/batch38b_minlot.py").read().split("res = []")[0])
planA = U[["10-day low US500", "BTC NR4", "BTC Williams (T1)", "ETH above 50-day"]].sum(axis=1)
rng = np.random.default_rng(39); rows = []; SER = {}
def dd(x): e = np.cumsum(np.asarray(x)); return (e - np.maximum.accumulate(e)).min()
def evaluate(nm, ret, pos, start, ann, exp, cost_r):
    """ret: daily strategy return series (already includes position), pos: exposure series for shuffling, cost_r: per-day cost series."""
    ix = ret.index; per = [(ix >= start) & (ix < "2020"), (ix >= "2020") & (ix < "2024"), ix >= "2024"]; post = ix >= start
    x = (ret - cost_r).values; x2 = (ret - 2 * cost_r).values
    s = [x[k].mean() / x[k].std() * np.sqrt(ann) for k in per]; S0 = x[post].mean() / x[post].std() * np.sqrt(ann)
    raw = UNDER[nm][post]; pp = pos.values[post]; cc = cost_r.values[post]; nul = []
    for k in rng.integers(60, len(pp) - 60, 500):
        q = np.roll(pp, k); cq = np.roll(cc, k); z = q * raw - cq; nul.append(z.mean() / z.std() * np.sqrt(ann))
    nul = np.array(nul); z = (S0 - nul.mean()) / nul.std(); usd = pd.Series(x * exp, index=ix); SER[nm] = usd
    rows.append(dict(rule=nm, s_a=s[0], s20=s[1], s24=s[2], t=S0 * np.sqrt(post.sum() / ann), x2=x2[post].sum() > 0, z=z, p=0.5 * (1 - erf(z / sqrt(2))),
                     usd_pre=usd[post & (ix < "2024")].sum(), dd_pre=dd(usd[post & (ix < "2024")]), usd24=usd[ix >= "2024"].sum(), dd24=dd(usd[ix >= "2024"]),
                     expo=(pos[post] != 0).mean(), corrA=usd.reindex(planA.index).fillna(0).loc["2014":].corr(planA)))
UNDER = {}
for nm, t, exp, bp, side in (("G1 US500 gap down: buy open", "SPY", 1000, 1.6, 1), ("G2 USTEC gap down: buy open", "QQQ", 1330, 1.4, 1),
                             ("G3 US500 gap up: short open", "SPY", 1000, 1.6, -1), ("G4 USTEC gap up: short open", "QQQ", 1330, 1.4, -1)):
    d = D[t]; gap = d.Open / d.Close.shift() - 1; day = (d.Close / d.Open - 1).fillna(0)
    pos = (((gap < -0.005) if side == 1 else (gap > 0.005)).astype(float) * side)
    UNDER[nm] = day.values; evaluate(nm, pos * day, pos, "2010", 252, exp, pos.abs() * (bp + 2) / 1e4)  # +2 bp open slippage
for nm, t in (("W1 BTC weekend above 50-day", "BTC-USD"), ("W2 ETH weekend above 50-day", "ETH-USD")):
    c = D[t].Close; r = c.pct_change().fillna(0); ok = (c > c.rolling(50).mean()).shift().fillna(False)
    dow = pd.Series(c.index.dayofweek, index=c.index); pos = (dow.isin([5, 6]) & ok.groupby((dow == 5).cumsum()).transform("first")).astype(float)
    UNDER[nm] = r.values; cost = (pos.diff() > 0) * (3.2 / 600 if "BTC" in t else 5e-4) * 1.0
    evaluate(nm, pos * r, pos, "2015" if "BTC" in t else "2018", 365, 600 if "BTC" in t else 170, cost)
for nm, a, b, bp, start, ann, exp in (("PR1 ETH/BTC ratio reversion", "ETH-USD", "BTC-USD", 5 + 1.1, "2018", 365, 600), ("PR2 USTEC/US500 ratio reversion", "QQQ", "SPY", 3.0, "2010", 252, 1000),
                                      ("PR3 US30/US500 ratio reversion", "DIA", "SPY", 2.9, "2010", 252, 1000)):
    ca, cb = D[a].Close, D[b].Close; ix = ca.index.intersection(cb.index); ca, cb = ca[ix], cb[ix]; lr = np.log(ca / cb); z = (lr - lr.rolling(20).mean()) / lr.rolling(20).std()
    pos, out = 0, []
    for zz in z.values:
        if pos == 0 and zz < -2: pos = 1
        elif pos == 0 and zz > 2: pos = -1
        elif (pos == 1 and zz >= 0) or (pos == -1 and zz <= 0): pos = 0
        out.append(pos)
    p = pd.Series(out, index=ix, dtype=float).shift().fillna(0); spread = (ca.pct_change() - cb.pct_change()).fillna(0)
    UNDER[nm] = spread.values; evaluate(nm, p * spread, p, start, ann, exp, (p.diff().abs() > 0) * bp / 2e4 * 2)
df = pd.DataFrame(rows); n = len(df); sp = np.sort(df.p.values); ok = sp <= 0.10 * np.arange(1, n + 1) / n; cut = sp[np.where(ok)[0].max()] if ok.any() else -1
df["PASS"] = df[["s_a", "s20", "s24"]].gt(0.3).all(axis=1) & (df.t >= 2) & df.x2 & (df.p <= cut)
pd.set_option("display.width", 250); print(df.round(2).to_string(index=False)); df.to_csv("lab/batch39_results.csv", index=False)
for nm in df[df.PASS].rule:
    u = SER[nm]; print(nm, {y: int(v) for y, v in u.loc["2010":].groupby(u.loc["2010":].index.year).sum().items()})
