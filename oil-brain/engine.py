"""Honest backtest engine for the oil brain.

A rule is a function that returns a daily position series (-1..+1) known at the
CLOSE of day t; it earns the instrument's return from close t to close t+1.
Splits are fixed before any test (see BRAIN.md):
  IS       up to 2013-12-31   (rules and parameters may be chosen here only)
  OOS      2014-01-01 .. 2019-12-31
  HOLDOUT  2020-01-01 ..      (looked at once per rule, never tuned on)
PASS needs ALL of:
  1. OOS Sharpe > 0.3 and HOLDOUT Sharpe > 0.3, after costs
  2. post-IS (OOS+HOLDOUT) Sharpe beats the benchmark's (buy and hold of the same instrument,
     or the rule's own benchmark when given)
  3. post-IS t-stat of daily returns >= 2.0
  4. placebo p <= 0.05: the rule beats >= 95% of 500 placebos that keep its positions but
     circularly shift them in time (same exposure and turnover, broken timing)
  5. still positive post-IS at 2x costs
"""
import os
import numpy as np
import pandas as pd

D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
IS_END, OOS_END = "2013-12-31", "2019-12-31"


def load(sym, col="Close"):
    f = os.path.join(D, sym.replace("^", "").replace("=", "_") + ".csv")
    df = pd.read_csv(f, index_col=0, parse_dates=True)
    return df[col] if col else df


def sharpe(r):
    r = r.dropna()
    return float(r.mean() / r.std() * np.sqrt(252)) if len(r) > 20 and r.std() > 0 else np.nan


def tstat(r):
    r = r.dropna()
    return float(r.mean() / r.std() * np.sqrt(len(r))) if len(r) > 20 and r.std() > 0 else np.nan


def pnl(pos, ret, cost_bps):
    pos = pos.reindex(ret.index).ffill().fillna(0)
    turn = pos.diff().abs().fillna(pos.abs())
    return pos.shift(1).fillna(0) * ret - turn.shift(1).fillna(0) * cost_bps / 1e4


def evaluate(name, pos, ret, cost_bps=5, bench=None, start=None, n_placebo=500, seed=7):
    """pos: position at close t (known then). ret: close-to-close returns of the traded instrument."""
    ret = ret.dropna()
    if start:
        ret = ret[ret.index >= start]
    pos = pos.reindex(ret.index).ffill().fillna(0)
    r = pnl(pos, ret, cost_bps)
    r2 = pnl(pos, ret, 2 * cost_bps)
    b = (bench if bench is not None else ret).reindex(ret.index).fillna(0)
    IS, OOS, HO = r.loc[:IS_END], r.loc["2014-01-01":OOS_END], r.loc["2020-01-01":]
    post, post2, bpost = r.loc["2014-01-01":], r2.loc["2014-01-01":], b.loc["2014-01-01":]
    # Placebo: circular shifts of the same position path.
    rng = np.random.default_rng(seed)
    p = pos.values
    n = len(p)
    post_mask = (ret.index >= "2014-01-01")
    real = sharpe(post)
    beats = 0
    for _ in range(n_placebo):
        k = int(rng.integers(n // 10, n - n // 10))
        sp = pd.Series(np.roll(p, k), index=ret.index)
        if sharpe(pnl(sp, ret, cost_bps)[post_mask]) < real:
            beats += 1
    pp = 1 - beats / n_placebo
    out = dict(rule=name, IS=sharpe(IS), OOS=sharpe(OOS), HOLDOUT=sharpe(HO), post=real,
               bench_post=sharpe(bpost), t_post=tstat(post), placebo_p=pp,
               cagr_post=float((1 + post).prod() ** (252 / max(len(post), 1)) - 1),
               x2cost_post=float(post2.sum()), exposure=float(pos.abs().mean()),
               trades_per_year=float(pos.diff().abs().gt(0).sum() / (len(pos) / 252)))
    gates = [out["OOS"] > 0.3, out["HOLDOUT"] > 0.3, out["post"] > out["bench_post"],
             out["t_post"] >= 2.0, pp <= 0.05, out["x2cost_post"] > 0]
    out["verdict"] = "PASS" if all(gates) else f"FAIL ({6 - sum(gates)} of 6 gates)"
    return out


def table(rows):
    df = pd.DataFrame(rows).set_index("rule")
    cols = ["IS", "OOS", "HOLDOUT", "post", "bench_post", "t_post", "placebo_p", "cagr_post",
            "trades_per_year", "verdict"]
    with pd.option_context("display.width", 200, "display.max_columns", 20):
        return df[cols].round(2).to_string()
