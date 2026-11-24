"""Shared helpers for the sectors brain: portfolio P&L with turnover costs and the 6 engine gates,
with the placebo adapted to a weight matrix (whole matrix circularly shifted in time, as study6.py).
Uses engine.sharpe / engine.tstat and the engine's split dates unchanged."""
import os, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from engine import sharpe, tstat, IS_END, OOS_END

D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
SECT = ["XLB", "XLE", "XLF", "XLI", "XLK", "XLP", "XLU", "XLV", "XLY", "XLRE", "XLC"]


def load(sym):
    return pd.read_csv(os.path.join(D, sym + ".csv"), index_col=0, parse_dates=True)["Close"]


def panel(syms):
    return pd.DataFrame({s: load(s) for s in syms})


def period_ends(idx, freq="M"):
    s = idx.to_series()
    return s.groupby(idx.to_period(freq)).last().values


def hold(w_at_rebal, idx):
    """weights set on rebalance dates (known at that close), held until the next rebalance."""
    return w_at_rebal.reindex(idx).ffill().fillna(0)


def port(w, ret, cost):
    ret = ret.reindex(w.index).fillna(0)
    turn = w.diff().abs().sum(axis=1).fillna(w.abs().sum(axis=1))
    return (w.shift(1) * ret).sum(axis=1) - turn.shift(1).fillna(0) * cost / 1e4


def xs_weights(score, alive, top=3, long_high=True, long_only=False):
    """rank score cross-sectionally among alive names; +1/top on top names, -1/top on bottom names."""
    sc = score.where(alive)
    if not long_high:
        sc = -sc
    rk = sc.rank(axis=1, ascending=False)
    n = sc.notna().sum(axis=1)
    w = (rk <= top).astype(float) / top
    if not long_only:
        w = w - (rk > n.values[:, None] - top).astype(float).where(sc.notna(), 0) / top
    return w.where(n >= 2 * top, 0).fillna(0) if not long_only else w.where(n >= top, 0).fillna(0)


def evaluate_w(name, w, ret, bench, cost=5, start=None, n_placebo=500, seed=7):
    if start:
        w = w.loc[start:]
    r = port(w, ret, cost)
    r2 = port(w, ret, 2 * cost)
    b = bench.reindex(r.index).fillna(0)
    post, bpost = r.loc["2014-01-01":], b.loc["2014-01-01":]
    real = sharpe(post)
    rng = np.random.default_rng(seed)
    n = len(w); beats = 0
    for _ in range(n_placebo):
        k = int(rng.integers(n // 10, n - n // 10))
        ws = pd.DataFrame(np.roll(w.values, k, axis=0), index=w.index, columns=w.columns)
        beats += sharpe(port(ws, ret, cost).loc["2014-01-01":]) < real
    pp = 1 - beats / n_placebo
    turn = w.diff().abs().sum(axis=1)
    out = dict(rule=name, IS=sharpe(r.loc[:IS_END]), OOS=sharpe(r.loc["2014-01-01":OOS_END]),
               HOLDOUT=sharpe(r.loc["2020-01-01":]), post=real, bench_post=sharpe(bpost),
               t_post=tstat(post), placebo_p=pp,
               cagr_post=float((1 + post).prod() ** (252 / len(post)) - 1),
               x2cost_post=float(r2.loc["2014-01-01":].sum()),
               turnover_per_year=float(turn.sum() / (len(w) / 252)),
               trades_per_year=float(turn.gt(1e-12).sum() / (len(w) / 252)),
               maxdd=float(((1 + post).cumprod() / (1 + post).cumprod().cummax() - 1).min()))
    g = [out["OOS"] > 0.3, out["HOLDOUT"] > 0.3, real > out["bench_post"], out["t_post"] >= 2.0,
         pp <= 0.05, out["x2cost_post"] > 0]
    out["gates"] = int(sum(g))
    out["verdict"] = ("WINNER" if out["t_post"] >= 3 else "CANDIDATE") if all(g) else f"FAIL ({6-sum(g)} of 6 gates)"
    return out, r


def show(rows):
    df = pd.DataFrame(rows).set_index("rule")
    cols = ["IS", "OOS", "HOLDOUT", "post", "bench_post", "t_post", "placebo_p", "cagr_post",
            "turnover_per_year", "maxdd", "verdict"]
    with pd.option_context("display.width", 250, "display.max_columns", 20):
        print(df[cols].round(2).to_string())
