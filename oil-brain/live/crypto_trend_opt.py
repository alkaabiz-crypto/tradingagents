"""Optimise the crypto TREND day trade HONESTLY (pre-registered 2026-11-26, before any run; the user asked to
"optimize it more using everything there is in mind").
Danger (MISTAKES A2/A3/E6): picking the best of many settings on the same data makes luck look like skill. So:
1) WALK-FORWARD: each year from 2018, choose the setting with the best Sharpe on ALL EARLIER data only, trade it for
   that year, repeat. The stitched 2018-2026 result is what optimisation really delivers. Compared with the fixed
   base (BTC, SMA50, stop 0.5, full size) and with the fixed "vol-sized BTC+ETH" from btc_trend_improve.py.
2) DEFLATED SHARPE of the full-sample best, at N = 72 (this grid) and N = 1,100 (the whole search that found it).
Grid (72 settings), everything the lab has learnt:
  coins     BTC | BTC+ETH | BTC+ETH+SOL (equal weight over the coins trading that day; SOL from 2020)
  signal    SMA50 sign | ENSEMBLE: position = mean of sign(close - SMA L) for L in 20, 50, 100, 200 (time-series
            momentum, Moskowitz-Ooi-Pedersen 2012; fractional size when the trends disagree)
  stop      0.35 | 0.5 | 0.75 x ATR14
  sizing    full | vol: x min(1, 2% / ATR%)
  candle    none | CLOSE-LOCATION confirm (from CANDLES.md, IBS): long only if yesterday closed in the upper half of
            its range (IBS > 0.5), short only if in the lower half; else flat
Rule each UTC day: entry at the open, stop, out at the close. Costs: costs.py (Exness Standard swap-free: spread +
stop slippage, no commission, no swap), scaled by position size.
PASS for "optimised beats fixed": walk-forward 2018-2026 Sharpe AND return/worst-drop above the base. Research, not
financial advice.        python3 oil-brain/live/crypto_trend_opt.py
"""
import os, sys, math, itertools
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); OB = os.path.dirname(HERE)
sys.path.insert(0, HERE); sys.path.insert(0, OB)
from day_ticket_backrun import full_bars, atr
import costs

COINS = {"BTC": ["BTC-USD"], "BTC+ETH": ["BTC-USD", "ETH-USD"], "BTC+ETH+SOL": ["BTC-USD", "ETH-USD", "SOL-USD"]}
GRID = list(itertools.product(COINS, ["SMA50", "ENSEMBLE"], [0.35, 0.5, 0.75], ["full", "vol"], ["none", "confirm"]))
_bars = {}


def coin(sym, sig, k, size, candle):
    if sym not in _bars:
        d = full_bars(sym); _bars[sym] = d[(d.High > d.Low) & (d.Open > 0)]
    d = _bars[sym]; a = atr(d); c = d.Close
    if sig == "SMA50":
        pos = np.sign(c - c.rolling(50).mean())
    else:
        pos = sum(np.sign(c - c.rolling(L).mean()) for L in (20, 50, 100, 200)) / 4
    if candle == "confirm":
        ibs = (c - d.Low) / (d.High - d.Low); pos = pos.where(((pos > 0) & (ibs > .5)) | ((pos < 0) & (ibs < .5)), 0.0)
    f = pd.DataFrame({"O": d.Open.shift(-1), "H": d.High.shift(-1), "L": d.Low.shift(-1), "C": d.Close.shift(-1),
                      "a": a, "p": pos, "ok": c.rolling(200).mean().notna()}, index=d.index)
    f = f[f[["O", "H", "L", "C", "a", "p"]].notna().all(axis=1) & f.ok & (f.index >= "2014-01-01")]
    s = np.sign(f.p.values); w = np.abs(f.p.values)
    if size == "vol": w = w * np.minimum(1.0, 0.02 / (f.a / f.O).values)
    st = f.O.values - s * k * f.a.values
    hit = np.where(s > 0, f.L.values <= st, np.where(s < 0, f.H.values >= st, False))
    x = np.where(hit, st, f.C.values); g = s * (x / f.O.values - 1)
    cost = (s != 0) * (costs.round_trip(sym) + hit * costs.STOP_SLIPPAGE_BP / 1e4)
    return pd.Series(w * (g - cost), index=f.index + pd.Timedelta(days=1))


def series(cfg):
    cs, sig, k, size, candle = cfg
    return pd.concat([coin(s, sig, k, size, candle) for s in COINS[cs]], axis=1).mean(axis=1).dropna()


def stats(r):
    e = (1 + r).cumprod(); dd = (e / e.cummax() - 1).min(); cagr = e.iloc[-1] ** (365 / len(r)) - 1
    return dict(day_pct=r.mean() * 100, year_pct=cagr * 100, worst_drop=dd * 100, MAR=cagr / abs(dd),
                sharpe=r.mean() / r.std() * np.sqrt(365))


def Phi(x): return 0.5 * math.erfc(-x / math.sqrt(2))


def Phi_inv(p):
    lo, hi = -10.0, 10.0
    for _ in range(80):
        mid = (lo + hi) / 2; lo, hi = (mid, hi) if Phi(mid) < p else (lo, mid)
    return (lo + hi) / 2


def dsr(r, N):
    T = len(r); sr = r.mean() / r.std(ddof=1); sk = float(r.skew()); ku = float(r.kurt()) + 3; g = 0.5772156649
    sr0 = math.sqrt(1 / T) * ((1 - g) * Phi_inv(1 - 1 / N) + g * Phi_inv(1 - 1 / (N * math.e)))
    return Phi((sr - sr0) * math.sqrt(T - 1) / math.sqrt(1 - sk * sr + (ku - 1) / 4 * sr ** 2))


def main():
    S = {cfg: series(cfg) for cfg in GRID}
    full = pd.DataFrame([dict(cfg=" / ".join(map(str, c)), **stats(r)) for c, r in S.items()]).sort_values("sharpe", ascending=False)
    wf, picks = [], []
    for y in range(2018, 2027):
        tr = {c: r[r.index < f"{y}-01-01"] for c, r in S.items()}
        best = max(tr, key=lambda c: tr[c].mean() / tr[c].std())
        picks.append((y, " / ".join(map(str, best))))
        wf.append(S[best][(S[best].index >= f"{y}-01-01") & (S[best].index < f"{y + 1}-01-01")])
    wf = pd.concat(wf)
    base = S[("BTC", "SMA50", 0.5, "full", "none")]; fixed2 = S[("BTC+ETH", "SMA50", 0.5, "vol", "none")]
    cut = lambda r: r[r.index >= "2018-01-01"]
    pd.set_option("display.width", 220)
    print("Top 10 of 72 on the full sample (IN-SAMPLE, flattering):"); print(full.head(10).round(2).to_string(index=False))
    print("\nWalk-forward picks (chosen on earlier data only):")
    for y, p in picks: print(f"  {y}: {p}")
    out = pd.DataFrame([dict(version=n, **stats(cut(r))) for n, r in
                        (("BASE fixed (BTC SMA50 0.5 full)", base), ("FIXED vol-sized BTC+ETH", fixed2),
                         ("WALK-FORWARD optimised", wf))])
    print("\n2018-2026, out of sample for the walk-forward:"); print(out.round(2).to_string(index=False))
    late = pd.DataFrame([dict(version=n, **stats(r[r.index >= "2022-01-01"])) for n, r in
                         (("BASE", base), ("FIXED vol BTC+ETH", fixed2), ("WALK-FORWARD", wf))])
    print("\n2022-2026 only:"); print(late.round(2).to_string(index=False))
    b = S[max(S, key=lambda c: S[c].mean() / S[c].std())]
    print(f"\nDeflated Sharpe of the full-sample best: N=72 {dsr(b, 72):.3f} | N=1,100 {dsr(b, 1100):.3f} (>= 0.95 = proven)")
    w, bb = stats(cut(wf)), stats(cut(base))
    print("VERDICT:", "optimised BEATS the base out of sample" if w["sharpe"] > bb["sharpe"] and w["MAR"] > bb["MAR"]
          else "optimising does NOT beat the base out of sample")
    full.to_csv(os.path.join(HERE, "crypto_trend_opt_results.csv"), index=False)


if __name__ == "__main__":
    main()
