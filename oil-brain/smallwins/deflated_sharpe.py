"""Deflated Sharpe ratio (Bailey & Lopez de Prado 2014) for the live QQQ IBS sleeve (pre-registered 2026-11-26).
Question: after counting how many systems the lab tried before finding it, is the QQQ IBS dip still better than the
best of that many lucky systems? Per-trade returns 2014-2026 (436 trades, 5 bp a side). Trials N: 144 (the smallwins
round where it was found), and stress cases 1,000 and 10,000 (every candle/small-win system the lab ever tried).
PASS (fixed): DSR >= 0.95 at N = 144. Research, not financial advice.
"""
import os, sys, math
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import smallwins as W

def Phi(x): return 0.5 * math.erfc(-x / math.sqrt(2))
def Phi_inv(p):
    lo, hi = -10.0, 10.0
    for _ in range(80):
        mid = (lo + hi) / 2; lo, hi = (mid, hi) if Phi(mid) < p else (lo, mid)
    return (lo + hi) / 2

b = W.load("QQQ"); i = W.indicators(b); t = W.trades("S1", 1, b, i, W.entries("S1", 1, i, b.Close))
r = (t[t.date >= "2014-01-01"].gross - 2 * W.COST).values
T = len(r); sr = r.mean() / r.std(ddof=1)
sk = float(pd.Series(r).skew()); ku = float(pd.Series(r).kurt()) + 3
g = 0.5772156649
print(f"QQQ IBS 2014-2026: {T} trades, Sharpe per trade {sr:.3f}, skew {sk:.2f}, kurtosis {ku:.2f}")
for N in (144, 1000, 10000):
    v = 1.0 / T  # variance of a Sharpe estimate under the null, per trade
    sr0 = math.sqrt(v) * ((1 - g) * Phi_inv(1 - 1 / N) + g * Phi_inv(1 - 1 / (N * math.e)))
    dsr = Phi((sr - sr0) * math.sqrt(T - 1) / math.sqrt(1 - sk * sr + (ku - 1) / 4 * sr ** 2))
    print(f"N = {N:>6}: luck Sharpe {sr0:.3f} -> deflated Sharpe probability {dsr:.3f} {'PASS' if dsr >= 0.95 else 'fail'}")
