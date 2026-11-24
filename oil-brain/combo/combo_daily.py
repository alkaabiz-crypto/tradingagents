"""Combo lab, round 2 (pre-registered 2026-11-24 ~16:20 UTC, before running): the same three layers on DAILY
bars over ~20 years, built on round 1's lessons (trend regime filters and trailing exits did best).
Markets: GLD, SLV, USO, XLE, SPY, QQQ, IWM, TLT, BTC-USD.
Strategy layer: R0 any direction; R2 200-day trend (above -> longs only, below -> shorts only); R2L longs only above SMA200.
Indicator layer (signal at the close, entry at the next open):
  D1 Donchian 20-day breakout   D2 Donchian 55-day breakout (Turtle)   D3 EMA 20/50 cross
  D4 pullback: RSI(2) < 10 in the regime direction (long) / > 90 (short)
Skills layer (trader-exit style, fixed dollar risk per trade):
  T1 stop 2 x ATR(20), trailing at 3 x ATR, no target   T2 stop 2 x ATR, target 4R, max 30 days
  T3 stop 3 x ATR, trailing 3 x ATR, max 60 days
Costs: 5 bp per side (ETFs), 10 bp BTC. One position at a time.
Judged per system on trades: IS entries up to 2013, OOS 2014-2019, HOLDOUT 2020+ (BTC: 2014-2018 / 2019-2021 /
2022+). A system passes if avg R > 0 in OOS and HOLDOUT, post-2014 t >= 2, and avg R > 0 at 2x cost.
Multiple testing: 9 x 3 x 4 x 3 = 324 systems; with that many, ~16 pass t >= 2 by luck at 5%, so survivors
are compared to a random-entry placebo (same exits, random entry days, 200 runs) and need placebo p <= 0.01.
"""
import os, itertools
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); OB = os.path.dirname(HERE)
SRC = {"BTC-USD": "brains/crypto/data/BTC-USD.csv"}


def load(sym):
    p = os.path.join(OB, SRC.get(sym, f"data/{sym}.csv"))
    if not os.path.exists(p): p = os.path.join(OB, "brains/liquidity/data", f"{sym}.csv")
    df = pd.read_csv(p, index_col=0, parse_dates=True)
    df.index = pd.to_datetime(df.index).tz_localize(None).normalize()
    return df[~df.index.duplicated()][["Open", "High", "Low", "Close"]].dropna()


def rsi(x, n):
    d = x.diff(); up = d.clip(lower=0).ewm(alpha=1 / n).mean(); dn = (-d.clip(upper=0)).ewm(alpha=1 / n).mean()
    return 100 - 100 / (1 + up / dn)


def signals(b):
    c = b.Close
    hi20, lo20 = b.High.rolling(20).max().shift(1), b.Low.rolling(20).min().shift(1)
    hi55, lo55 = b.High.rolling(55).max().shift(1), b.Low.rolling(55).min().shift(1)
    up = c.ewm(span=20).mean() > c.ewm(span=50).mean()
    r2 = rsi(c, 2)
    return {"D1": np.where(c > hi20, 1, np.where(c < lo20, -1, 0)),
            "D2": np.where(c > hi55, 1, np.where(c < lo55, -1, 0)),
            "D3": np.where(up & ~up.shift(1, fill_value=False), 1, np.where(~up & up.shift(1, fill_value=False), -1, 0)),
            "D4": np.where(r2 < 10, 1, np.where(r2 > 90, -1, 0))}


def run(b, sig, reg, ex, cost, rng=None):
    O, H, L, C = b.Open.values, b.High.values, b.Low.values, b.Close.values
    tr = pd.concat([b.High - b.Low, (b.High - b.Close.shift()).abs(), (b.Low - b.Close.shift()).abs()], axis=1).max(axis=1)
    A = tr.rolling(20).mean().values
    k0, trail_k, tgt, maxh = {"T1": (2, 3, None, 10**9), "T2": (2, None, 4, 30), "T3": (3, 3, None, 60)}[ex]
    n = len(b); i = 0; out = []
    cand = np.flatnonzero(sig != 0)
    if rng is not None:  # placebo: same number of entry attempts on random days, random-free direction kept by regime
        cand = np.sort(rng.choice(np.arange(220, n - 2), size=min(len(cand), n - 230), replace=False))
    ci = 0
    while ci < len(cand):
        i = cand[ci]; ci += 1
        if i >= n - 1 or np.isnan(A[i]): continue
        side = sig[i] if rng is None else (reg[i] if reg[i] != 0 else (1 if rng.random() < 0.5 else -1))
        if np.isnan(reg[i]) or (reg[i] != 0 and side != reg[i]) or side == 0: continue
        e = O[i + 1]; risk = k0 * A[i]; stop = e - side * risk; target = e + side * tgt * risk if tgt else None
        j = i + 1; px = None
        while j < n:
            if side > 0 and L[j] <= stop: px = min(stop, O[j]) if j > i + 1 else stop; break
            if side < 0 and H[j] >= stop: px = max(stop, O[j]) if j > i + 1 else stop; break
            if target is not None and ((side > 0 and H[j] >= target) or (side < 0 and L[j] <= target)): px = target; break
            if trail_k: stop = max(stop, C[j] - trail_k * A[j]) if side > 0 else min(stop, C[j] + trail_k * A[j])
            if j - i >= maxh: px = C[j]; break
            j += 1
        if px is None: break
        out.append((b.index[i + 1], (side * (px - e) - 2 * cost / 1e4 * e) / risk))
        while ci < len(cand) and cand[ci] <= j: ci += 1   # one position at a time
    return pd.DataFrame(out, columns=["t", "R"])


def tt(R): return R.mean() / R.std() * np.sqrt(len(R)) if len(R) > 2 and R.std() > 0 else np.nan


rows = []; rng = np.random.default_rng(7)
for sym in ["GLD", "SLV", "USO", "XLE", "SPY", "QQQ", "IWM", "TLT", "BTC-USD"]:
    b = load(sym); c = b.Close; cost = 10 if sym == "BTC-USD" else 5
    s200 = np.sign(c - c.rolling(200).mean()).values
    regs = {"R0": np.zeros(len(b)), "R2": s200, "R2L": np.where(s200 > 0, 1.0, np.where(np.isnan(s200), np.nan, 2.0))}
    cuts = ("2018-12-31", "2021-12-31") if sym == "BTC-USD" else ("2013-12-31", "2019-12-31")
    post0 = "2019-01-01" if sym == "BTC-USD" else "2014-01-01"
    for (rk, rg), (sk, sg), ex in itertools.product(regs.items(), signals(b).items(), ["T1", "T2", "T3"]):
        t = run(b, sg, rg, ex, cost); t2 = run(b, sg, rg, ex, 2 * cost)
        if len(t) < 10: continue
        IS = t[t.t <= cuts[0]].R; OOS = t[(t.t > cuts[0]) & (t.t <= cuts[1])].R; HO = t[t.t > cuts[1]].R
        post = t[t.t >= post0].R
        rows.append(dict(system=f"{sym} {rk} {sk} {ex}", sym=sym, regime=rk, entry=sk, exit=ex, trades=len(t),
                         IS_R=IS.mean(), OOS_R=OOS.mean(), HO_R=HO.mean(), post_R=post.mean(), post_n=len(post),
                         post_t=tt(post), win=(post > 0).mean(), x2_R=t2[t2.t >= post0].R.mean()))
df = pd.DataFrame(rows)
df["passes"] = (df.OOS_R > 0) & (df.HO_R > 0) & (df.post_t >= 2) & (df.x2_R > 0)
# placebo for the passers: random entry days, same regime and exits
pl = []
for _, r in df[df.passes].iterrows():
    sym = r.sym; b = load(sym); c = b.Close; cost = 10 if sym == "BTC-USD" else 5
    s200 = np.sign(c - c.rolling(200).mean()).values
    rg = {"R0": np.zeros(len(b)), "R2": s200, "R2L": np.where(s200 > 0, 1.0, np.where(np.isnan(s200), np.nan, 2.0))}[r.regime]
    sg = signals(b)[r.entry]; post0 = "2019-01-01" if sym == "BTC-USD" else "2014-01-01"
    sims = []
    for _ in range(200):
        t = run(b, sg, rg, r.exit, cost, rng=rng); x = t[t.t >= post0].R
        sims.append(x.mean() if len(x) else np.nan)
    pl.append((r.system, float(np.mean(np.array(sims) >= r.post_R))))
pmap = dict(pl); df["placebo_p"] = df.system.map(pmap)
df["survivor"] = df.passes & (df.placebo_p <= 0.01)
df.round(3).to_csv(os.path.join(HERE, "combo_daily_results.csv"), index=False)
pd.set_option("display.width", 250)
print(f"{len(df)} systems; {int(df.passes.sum())} pass the period/t/cost gates (luck alone ~{0.05*len(df):.0f} at t>=2); "
      f"{int(df.survivor.sum())} also beat random entries (p <= 0.01).")
print(df.sort_values("post_t", ascending=False).head(15)[["system", "post_n", "win", "IS_R", "OOS_R", "HO_R", "post_R", "post_t", "x2_R", "placebo_p", "survivor"]].round(2).to_string(index=False))
for k in ["regime", "entry", "exit", "sym"]:
    print(f"\npost-2014 avg R by {k}:", df.groupby(k).post_R.mean().round(3).to_dict())
