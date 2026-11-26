"""Small-trade MOMENTUM on oil, metals and crypto (pre-registered 2026-11-26, before any run). From the candle brain's
open questions: dip-buying failed on oil, gold and BTC; BTC research says crypto leans to momentum. So test the
REVERSE-SIGN versions: follow strength, sell weakness.
Signals at the close (entry AT that close, as in smallwins.py; longs shown, shorts are the mirror):
  M1 IBS > 0.8 (closed near the high)       M2 RSI(2) > 90
  M3 three up closes in a row               M4 close above the upper Bollinger band (20, 2 sd)
  M5 close above the prior 20-day high (breakout)
Exit: after h = 1, 3 or 5 days at the close. One position at a time.
Markets: USO, BNO, XLE, XOP, CL=F (oil); GLD, SLV (metals); BTC-USD, ETH-USD (crypto).
Systems: 5 signals x 2 sides x 3 holds x 9 markets = 270. Costs: ETFs 5 bp a side, futures 2 bp, crypto 10 bp.
Periods: IS < 2014 (crypto < 2018), OOS 2014-2019 (crypto 2018-2021), HOLDOUT 2020+ (crypto 2022+).
PASS (fixed): average trade > 0 net in OOS and HOLDOUT, > 0 at 2x cost post-2014, post-2014 t >= the Sidak 1% bar for
270 systems, random-entry placebo (same count, same hold and side, 500 runs, seed 41) p <= 0.01, then a neighbour
check before any sleeve. Research, not financial advice.
"""
import os, math
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); OB = os.path.dirname(HERE)
MKT = "/tmp/claude-0/-home-user-tradingagents/862edda5-54ef-5bf8-971e-481bdcdf4dee/scratchpad/mkt"
MARKETS = ["USO", "BNO", "XLE", "XOP", "CL=F", "GLD", "SLV", "BTC-USD", "ETH-USD"]


def load(sym):
    p = os.path.join(OB, "data", f"{sym}.csv")
    if not os.path.exists(p):
        p = os.path.join(MKT, f"{sym}.csv")
    d = pd.read_csv(p, index_col=0, parse_dates=True)[["Open", "High", "Low", "Close"]].dropna()
    d.index = pd.to_datetime(d.index).tz_localize(None).normalize(); d = d[~d.index.duplicated()]
    d = d[d.index < pd.Timestamp.now().normalize()]
    return d[(d.High > d.Low) & (d.Close > 0)]


def cost(sym):
    return 1e-3 if sym.endswith("-USD") else 2e-4 if sym.endswith("=F") else 5e-4


def sig(b, side):
    c = b.Close; ibs = (c - b.Low) / (b.High - b.Low)
    d = c.diff(); up = d.clip(lower=0).ewm(alpha=.5).mean(); dn = (-d.clip(upper=0)).ewm(alpha=.5).mean(); r2 = 100 - 100 / (1 + up / dn)
    m, s = c.rolling(20).mean(), c.rolling(20).std()
    u = (d > 0) if side == 1 else (d < 0)
    S = {"M1": ibs > 0.8 if side == 1 else ibs < 0.2, "M2": r2 > 90 if side == 1 else r2 < 10,
         "M3": u & u.shift(1, fill_value=False) & u.shift(2, fill_value=False),
         "M4": c > m + 2 * s if side == 1 else c < m - 2 * s,
         "M5": c > b.High.shift(1).rolling(20).max() if side == 1 else c < b.Low.shift(1).rolling(20).min()}
    return {k: v.fillna(False).values for k, v in S.items()}


def trades(c, flags, side, h, mask):
    out = []; k = 0; n = len(c)
    while k < n - h:
        if mask[k] and flags[k]:
            out.append((k, side * (c[k + h] / c[k] - 1))); k += h
        else:
            k += 1
    return out


def sidak_t(m, alpha=0.01):
    p = 1 - (1 - alpha) ** (1 / m); lo, hi = 0.0, 10.0
    for _ in range(60):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if math.erfc(mid / math.sqrt(2)) > p else (lo, mid)
    return hi


def stat(r):
    return (r.mean() * 1e4, r.mean() / (r.std(ddof=1) / np.sqrt(len(r)))) if len(r) > 2 else (np.nan, np.nan)


def main():
    rows = []; bar = sidak_t(270); rng = np.random.default_rng(41)
    for sym in MARKETS:
        b = load(sym); c = b.Close.values; idx = b.index; cs = cost(sym)
        a, z = ("2018-01-01", "2022-01-01") if sym.endswith("-USD") else ("2014-01-01", "2020-01-01")
        post = idx >= pd.Timestamp(a)
        for side in (1, -1):
            S = sig(b, side)
            for name, f in S.items():
                for h in (1, 3, 5):
                    tr = trades(c, f, side, h, np.ones(len(c), bool))
                    df = pd.DataFrame(tr, columns=["k", "g"]); df["d"] = idx[df.k] if len(df) else []
                    r = lambda m: (df.g[m] - 2 * cs) if len(df) else pd.Series(dtype=float)
                    P = df.d >= pd.Timestamp(a) if len(df) else []
                    o = r((df.d >= pd.Timestamp(a)) & (df.d < pd.Timestamp(z))) if len(df) else pd.Series(dtype=float)
                    ho = r(df.d >= pd.Timestamp(z)) if len(df) else pd.Series(dtype=float)
                    pr = r(P) if len(df) else pd.Series(dtype=float)
                    m, t = stat(pr)
                    row = dict(sym=sym, signal=name, side="long" if side == 1 else "short", hold=h, n=len(pr),
                               IS_bp=stat(r(df.d < pd.Timestamp(a)))[0] if len(df) else np.nan,
                               OOS_bp=stat(o)[0], HO_bp=stat(ho)[0], post_bp=m, post_t=t,
                               post_bp_2x=(pr.mean() - 2 * cs) * 1e4 if len(pr) else np.nan,
                               win=float((pr > 0).mean()) if len(pr) else np.nan, placebo_p=np.nan)
                    if row["OOS_bp"] > 0 and row["HO_bp"] > 0 and row["post_bp_2x"] > 0 and t >= bar:
                        pos = np.where(post)[0][:-h]; sims = []
                        for _ in range(500):
                            ks = rng.choice(pos, size=min(len(pr), len(pos)), replace=False)
                            sims.append((side * (c[ks + h] / c[ks] - 1)).mean() - 2 * cs)
                        row["placebo_p"] = float((np.array(sims) >= pr.mean()).mean())
                    rows.append(row)
    df = pd.DataFrame(rows); df["PASS"] = df.placebo_p <= 0.01
    df.to_csv(os.path.join(HERE, "momentum_small_results.csv"), index=False)
    pd.set_option("display.width", 220)
    print(f"Systems: {len(df)}; luck bar t >= {bar:.2f}; reached the bar with OOS/HOLDOUT/2x cost: {int(df.placebo_p.notna().sum())}; PASS: {int(df.PASS.sum())}")
    print(df.sort_values("post_t", ascending=False).head(15).round(2).to_string(index=False))


if __name__ == "__main__":
    main()
