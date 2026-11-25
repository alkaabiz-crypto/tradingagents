"""Neighbour check for the small-wins survivors (pre-registered 2026-11-25, before running).
Survivors (smallwins.py, placebo p <= 0.01): QQQ IBS dip, SPY IBS dip, SPY RSI2 dip, SPY RSI2 dip + trend,
SPY below Bollinger. Checked here on SPY, QQQ, IWM and DIA (DIA is new, an out-of-sample market):
  IBS dip: entry IBS < {0.10, 0.15, 0.20, 0.25, 0.30} x exit IBS > {0.4, 0.5, 0.6} (max 5 days)
  RSI2 dip (+ trend and without): entry RSI(2) < {5, 10, 15, 20, 25} x max days {5, 10}
Fixed bar: a family HOLDS on a market if >= 70% of its neighbours have post-2014 average trade > 0 at 2x cost
(10 bp a side) and t >= 2. Research, not financial advice.
"""
import os, sys
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import smallwins as W

START = pd.Timestamp("2014-01-01")


def run_ibs(b, i, th_in, th_out):
    c = b.Close.values; ibs = i.ibs.values; ok = i.sma200.notna().values; n = len(c); out = []; k = 0
    while k < n - 1:
        if ok[k] and ibs[k] < th_in:
            j = next((j for j in range(k + 1, min(k + 6, n)) if ibs[j] > th_out), min(k + 5, n - 1))
            out.append((b.index[k], c[j] / c[k] - 1)); k = j
        else:
            k += 1
    return out


def run_rsi(b, i, th, maxd, trend):
    c = b.Close.values; r = i.rsi2.values; s5 = i.sma5.values; s200 = i.sma200.values; n = len(c); out = []; k = 0
    while k < n - 1:
        if not np.isnan(s200[k]) and r[k] < th and (not trend or c[k] > s200[k]):
            j = next((j for j in range(k + 1, min(k + 1 + maxd, n)) if c[j] > s5[j]), min(k + maxd, n - 1))
            out.append((b.index[k], c[j] / c[k] - 1)); k = j
        else:
            k += 1
    return out


def score(tr):
    r = np.array([g for d, g in tr if d >= START]) - 2 * 2 * W.COST  # 2x cost
    if len(r) < 10:
        return np.nan, np.nan, len(r)
    return r.mean() * 1e4, r.mean() / (r.std(ddof=1) / np.sqrt(len(r))), len(r)


def main():
    rows = []
    for sym in ["SPY", "QQQ", "IWM", "DIA"]:
        b = W.load(sym); i = W.indicators(b)
        for a in [0.10, 0.15, 0.20, 0.25, 0.30]:
            for z in [0.4, 0.5, 0.6]:
                m, t, n = score(run_ibs(b, i, a, z)); rows.append(dict(sym=sym, family="IBS dip", p1=a, p2=z, avg_bp_2x=m, t=t, n=n))
        for trend in (False, True):
            for th in [5, 10, 15, 20, 25]:
                for md in [5, 10]:
                    m, t, n = score(run_rsi(b, i, th, md, trend))
                    rows.append(dict(sym=sym, family="RSI2 dip" + (" + trend" if trend else ""), p1=th, p2=md, avg_bp_2x=m, t=t, n=n))
    df = pd.DataFrame(rows); df["ok"] = (df.avg_bp_2x > 0) & (df.t >= 2)
    df.to_csv(os.path.join(HERE, "neighbours_results.csv"), index=False)
    g = df.groupby(["family", "sym"]).agg(neighbours=("ok", "size"), share_ok=("ok", "mean"), median_bp_2x=("avg_bp_2x", "median"),
                                           median_t=("t", "median"), trades=("n", "median")).reset_index()
    g["HOLDS"] = g.share_ok >= 0.7
    pd.set_option("display.width", 200)
    print(g.round(2).to_string(index=False))


if __name__ == "__main__":
    main()
