"""Improving the QQQ IBS dip: more gain, fewer/smaller losses (pre-registered 2026-11-25, before any run).

Baseline (live sleeve): IBS < 0.2 -> buy at the close; sell at the first close with IBS > 0.5 or the 5th close.
To avoid tuning on the test data, CHOICES ARE MADE ON 2000-2013 ONLY (QQQ from 1999-03; first trades after
200 days). 2014-2026 is used once, to check the chosen versions.
Variants (each = one entry filter x one exit x one sizing):
  Entry filters: F0 none (baseline) | F1 wide-range day: today's range > its 10-day average range |
    F2 narrow-range day: range < 10-day average (the opposite, for the record) | F3 uptrend: close > 200-day average |
    F4 high volume: volume > 20-day average | F5 calm market: VIX close < 30 | F6 down day: close < prior close |
    F7 not in a crash: close > 0.9 x 200-day average
  Exits: X0 baseline (IBS > 0.5 or 5 days) | X1 first up close (or 5 days) | X2 close above the prior day's high
    (or 5 days) | X3 after 1 day | X4 baseline + stop-loss at 2 x ATR(14) below entry (checked on daily lows)
  Sizing: S0 full sleeve each trade | S1 volatility-scaled: invest min(1, 1% / (ATR(14)/close)) of the sleeve
    (smaller when the market is jumpy)
Systems: 8 x 5 x 2 = 80. Costs 5 bp a side (≈ ETF; USTEC is cheaper on spread but pays swaps, see ibs_ustec.py).
Measures per period: trades, win rate, average net trade (bp), t, worst trade, total return of the sleeve,
max drawdown of the sleeve, return / max drawdown ("MAR").
SELECTION (fixed): rank the 79 non-baseline systems by 2000-2013 MAR; keep the top 3 that also have 2000-2013
average trade >= the baseline's and max drawdown <= the baseline's. VERDICT on 2014-2026: a chosen version is an
IMPROVEMENT if its MAR beats the baseline's AND its max drawdown is smaller AND its average trade is still > 0 at
2x cost; it must then also improve on NQ futures (2014-2026) and must not be worse than the baseline on SPY.
Also reported: the 2014-2026 table for all 80 (for learning only, never for choosing). Research, not advice.
"""
import os, itertools
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); OB = os.path.dirname(HERE)
COST = 5e-4
FILTERS = ["F0", "F1", "F2", "F3", "F4", "F5", "F6", "F7"]
EXITS = ["X0", "X1", "X2", "X3", "X4"]
SIZES = ["S0", "S1"]
NAMES = {"F0": "no filter", "F1": "wide-range day", "F2": "narrow-range day", "F3": "uptrend", "F4": "high volume",
         "F5": "VIX<30", "F6": "down day", "F7": "not in crash", "X0": "IBS>0.5", "X1": "first up close",
         "X2": "close>prior high", "X3": "1 day", "X4": "IBS>0.5 + 2ATR stop", "S0": "full size", "S1": "vol-scaled"}


def load(path):
    d = pd.read_csv(path, index_col=0, parse_dates=True)
    d.index = pd.to_datetime(d.index).tz_localize(None).normalize()
    return d[~d.index.duplicated()].dropna(subset=["Open", "High", "Low", "Close"])


def prep(b, vix):
    c = b.Close; rng = (b.High - b.Low)
    f = pd.DataFrame(index=b.index)
    f["ibs"] = ((c - b.Low) / rng.replace(0, np.nan)).fillna(0.5)
    f["sma200"] = c.rolling(200).mean()
    tr = pd.concat([rng, (b.High - c.shift()).abs(), (b.Low - c.shift()).abs()], axis=1).max(axis=1)
    f["atr"] = tr.rolling(14).mean()
    F = {"F0": pd.Series(True, index=b.index), "F1": rng > rng.rolling(10).mean(), "F2": rng < rng.rolling(10).mean(),
         "F3": c > f.sma200, "F4": (b.Volume > b.Volume.rolling(20).mean()) if "Volume" in b and b.Volume.sum() > 0 else pd.Series(True, index=b.index),
         "F5": vix.reindex(b.index, method="ffill") < 30, "F6": c < c.shift(), "F7": c > 0.9 * f.sma200}
    return f, {k: v.fillna(False).values for k, v in F.items()}


def simulate(b, f, filt, ex, size, start, end):
    s = (b.index >= pd.Timestamp(start)) & (b.index < pd.Timestamp(end))
    C, H, L, O = b.Close.values, b.High.values, b.Low.values, b.Open.values
    ibs, atr, ok = f.ibs.values, f.atr.values, f.sma200.notna().values
    n = len(C); trades = []; eq = 1.0; curve = []; k = 0
    while k < n - 1:
        if s[k] and ok[k] and ibs[k] < 0.2 and filt[k]:
            e = C[k]; w = 1.0 if size == "S0" else min(1.0, 0.01 / (atr[k] / e)); stop = e - 2 * atr[k]
            j, px = None, None
            for jj in range(k + 1, min(k + 6, n)):
                if ex == "X4" and L[jj] <= stop:
                    j, px = jj, min(stop, O[jj]); break
                done = {"X0": ibs[jj] > 0.5, "X4": ibs[jj] > 0.5, "X1": C[jj] > C[jj - 1], "X2": C[jj] > H[jj - 1], "X3": True}[ex]
                if done:
                    j, px = jj, C[jj]; break
            if j is None:
                j = min(k + 5, n - 1); px = C[j]
            r = px / e - 1 - 2 * COST
            eq *= 1 + w * r; trades.append(dict(date=b.index[k], r=r, w=w)); curve.append(eq); k = j
        else:
            k += 1
    t = pd.DataFrame(trades)
    if t.empty:
        return None
    cv = pd.Series(curve); dd = float((cv / cv.cummax() - 1).min()); dd = min(dd, 0.0)
    tot = eq - 1; wr = t.r * t.w
    return dict(trades=len(t), win=round((t.r > 0).mean(), 3), avg_bp=round(t.r.mean() * 1e4, 1),
                avg_bp_2x=round((t.r.mean() - 2 * COST) * 1e4, 1),
                t=round(wr.mean() / (wr.std(ddof=1) / np.sqrt(len(wr))), 2) if len(wr) > 2 else np.nan,
                worst_bp=round(t.r.min() * 1e4), worst_sleeve_bp=round(wr.min() * 1e4), total=round(tot, 3),
                maxdd=round(dd, 3), MAR=round(tot / abs(dd), 2) if dd < 0 else np.nan)


def table(b, vix, start, end):
    f, F = prep(b, vix); rows = []
    for fi, ex, sz in itertools.product(FILTERS, EXITS, SIZES):
        r = simulate(b, f, F[fi], ex, sz, start, end)
        if r:
            rows.append(dict(sys=f"{fi}{ex}{sz}", name=f"{NAMES[fi]} / {NAMES[ex]} / {NAMES[sz]}", **r))
    return pd.DataFrame(rows).set_index("sys")


def main():
    vix = load(os.path.join(OB, "data/VIX.csv")).Close
    qqq = load(os.path.join(OB, "data/QQQ.csv")); spy = load(os.path.join(OB, "data/SPY.csv"))
    import yfinance as yf
    nq = yf.Ticker("NQ=F").history(period="max")[["Open", "High", "Low", "Close", "Volume"]]
    nq.index = nq.index.tz_localize(None).normalize(); nq = nq[~nq.index.duplicated()]
    nq = nq[nq.index < pd.Timestamp.now().normalize()]
    IS = table(qqq, vix, "2000-01-01", "2014-01-01"); POST = table(qqq, vix, "2014-01-01", "2027-01-01")
    NQ = table(nq, vix, "2014-01-01", "2027-01-01"); SPY = table(spy, vix, "2014-01-01", "2027-01-01")
    base = "F0X0S0"; bi = IS.loc[base]
    pool = IS.drop(index=base)
    pool = pool[(pool.avg_bp >= bi.avg_bp) & (pool.maxdd >= bi.maxdd)].sort_values("MAR", ascending=False)
    chosen = list(pool.index[:3])
    pd.set_option("display.width", 260); pd.set_option("display.max_rows", 200); pd.set_option("display.max_colwidth", 60)
    cols = ["name", "trades", "win", "avg_bp", "t", "worst_bp", "worst_sleeve_bp", "total", "maxdd", "MAR"]
    print("CHOSEN ON 2000-2013 (QQQ):"); print(IS.loc[[base] + chosen, cols].to_string())
    print("\nCHECK ON 2014-2026 (QQQ) — never used for choosing:"); print(POST.loc[[base] + chosen, cols + ["avg_bp_2x"]].to_string())
    print("\nCHECK ON NQ FUTURES 2014-2026:"); print(NQ.loc[[base] + chosen, cols].to_string())
    print("\nCHECK ON SPY 2014-2026:"); print(SPY.loc[[base] + chosen, cols].to_string())
    verdict = []
    for s in chosen:
        p, q, n, sp = POST.loc[s], POST.loc[base], NQ.loc[s], NQ.loc[base]
        imp = (p.MAR > q.MAR) and (p.maxdd > q.maxdd) and (p.avg_bp_2x > 0) and (n.MAR > sp.MAR) and (n.maxdd > sp.maxdd) \
            and (SPY.loc[s].MAR >= SPY.loc[base].MAR)
        verdict.append((s, IS.loc[s, "name"], imp))
    print("\nVERDICT:"); [print(f"  {s} {nm}: {'IMPROVEMENT' if v else 'not an improvement'}") for s, nm, v in verdict]
    for name, df in [("is", IS), ("post", POST), ("nq", NQ), ("spy", SPY)]:
        df.to_csv(os.path.join(HERE, f"ibs_improve_{name}.csv"))
    print("\nFor learning only (2014-2026 QQQ, top 12 by MAR — NOT used for choosing):")
    print(POST.sort_values("MAR", ascending=False).head(12)[cols].to_string())


if __name__ == "__main__":
    main()
