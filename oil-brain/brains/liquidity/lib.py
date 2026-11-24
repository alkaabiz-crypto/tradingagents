"""Helpers for the liquidity brain. evaluate() is engine.py's, unchanged; port_eval() copies its gates for
multi-asset weights (same as oil-brain/study6.py: placebo shifts all weights by one random lag)."""
import os, sys
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..")))
from engine import evaluate, table, sharpe, tstat, IS_END, OOS_END  # noqa
MD = os.path.join(HERE, "data")

def ld(sym, col="Close"):
    df = pd.read_csv(os.path.join(MD, sym.replace("^", "") + ".csv"), index_col=0, parse_dates=True)
    return df[col] if col else df

def relvol(v, n=50):
    """Volume today / mean volume of the previous n days (known at today's close)."""
    return v / v.shift(1).rolling(n).mean()

def port_ret(w, ret, cost=5):
    w = w.reindex(ret.index).ffill().fillna(0)
    turn = w.diff().abs().sum(axis=1)
    return (w.shift(1) * ret).sum(axis=1) - turn.shift(1).fillna(0) * cost / 1e4

def port_eval(name, w, ret, bench, start, cost=5, n_placebo=300, seed=7):
    ret = ret.loc[start:]; w = w.reindex(ret.index).ffill().fillna(0)
    r = port_ret(w, ret, cost); r2 = port_ret(w, ret, 2 * cost); b = bench.reindex(ret.index).fillna(0)
    post = r.loc["2014-01-01":]; real = sharpe(post)
    rng = np.random.default_rng(seed); n = len(w); beats = 0
    for _ in range(n_placebo):
        k = int(rng.integers(n // 10, n - n // 10))
        ws = pd.DataFrame(np.roll(w.values, k, axis=0), index=w.index, columns=w.columns)
        beats += sharpe(port_ret(ws, ret, cost).loc["2014-01-01":]) < real
    pp = 1 - beats / n_placebo
    out = dict(rule=name, IS=sharpe(r.loc[:IS_END]), OOS=sharpe(r.loc["2014-01-01":OOS_END]), HOLDOUT=sharpe(r.loc["2020-01-01":]),
               post=real, bench_post=sharpe(b.loc["2014-01-01":]), t_post=tstat(post), placebo_p=pp,
               cagr_post=float((1 + post).prod() ** (252 / len(post)) - 1), x2cost_post=float(r2.loc["2014-01-01":].sum()),
               trades_per_year=float(w.diff().abs().sum(axis=1).gt(0).sum() / (len(w) / 252)))
    g = [out["OOS"] > 0.3, out["HOLDOUT"] > 0.3, out["post"] > out["bench_post"], out["t_post"] >= 2, pp <= 0.05, out["x2cost_post"] > 0]
    out["verdict"] = "PASS" if all(g) else f"FAIL ({6 - sum(g)} of 6 gates)"
    return out
