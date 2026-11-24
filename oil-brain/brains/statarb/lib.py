"""Shared helpers for brain statarb. Gates replicate engine.evaluate for a weight MATRIX
(engine.py imported unchanged for sharpe, tstat, splits, shared data)."""
import os, sys, json
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..")))
from engine import load, sharpe, tstat, IS_END, OOS_END  # noqa

px = pd.read_csv(os.path.join(HERE, "data/close.csv"), index_col=0, parse_dates=True)
px = px.drop(columns=[c for c in ["BK", "MMC", "EQR"] if c in px]).loc["2004-06-01":]
ret = px.pct_change(fill_method=None)
SECT = pd.Series(json.load(open(os.path.join(HERE, "data/sectors.json"))))
SECT = SECT.reindex(px.columns)
vix = load("^VIX").reindex(px.index).ffill()
spy = load("SPY").reindex(px.index).ffill().pct_change(fill_method=None)
START = "2005-07-01"   # first date counted (all rules); IS = 2005-07..2013


def neutral(sig, groups=None):
    """Dollar-neutral weights from a cross-sectional signal: demean (within groups if given),
    scale so long side = 1 and short side = 1 (gross 2)."""
    s = sig.copy()
    if groups is not None:
        s = s - s.T.groupby(groups).transform("mean").T
    else:
        s = s.sub(s.mean(axis=1), axis=0)
    g = s.abs().sum(axis=1).replace(0, np.nan)
    return s.div(g, axis=0).mul(2).fillna(0)


def week_ends(idx):
    s = idx.to_series()
    return s.groupby(s.dt.to_period("W-FRI")).last().values


def hold(w, days):
    """Keep weights only on rebalance days, forward fill between."""
    return w.loc[days].reindex(w.index).ffill().fillna(0)


def port(w, cost_bps=5.0, R=None):
    R = ret if R is None else R
    w = w.reindex(R.index).fillna(0)
    turn = w.diff().abs().sum(axis=1)
    turn.iloc[0] = w.iloc[0].abs().sum()
    gross = (w.shift(1) * R.fillna(0)).sum(axis=1)
    return gross - turn.shift(1).fillna(0) * cost_bps / 1e4, gross, turn


def evaluate_w(name, w, cost_bps=5.0, bench=None, start=START, n_placebo=500, seed=7):
    bench = spy if bench is None else bench
    w = w.loc[start:]
    R = ret.loc[start:]
    r, gross, turn = port(w, cost_bps, R)
    r2 = port(w, 2 * cost_bps, R)[0]
    post, post2 = r.loc["2014-01-01":], r2.loc["2014-01-01":]
    real = sharpe(post)
    Wv = w.values; Rv = R.fillna(0).values; n = len(Wv)
    rng = np.random.default_rng(seed); beats = 0
    m = R.index >= "2014-01-01"
    tv = np.abs(np.diff(Wv, axis=0)).sum(1)
    for _ in range(n_placebo):
        k = int(rng.integers(n // 10, n - n // 10))
        Ws = np.roll(Wv, k, axis=0)
        g = (Ws[:-1] * Rv[1:]).sum(1)
        t = np.abs(np.diff(Ws, axis=0)).sum(1)
        rr = np.r_[0, g - np.r_[Ws[0:1].__abs__().sum(), t[:-1]] * cost_bps / 1e4]
        if sharpe(pd.Series(rr[m])) < real:
            beats += 1
    pp = 1 - beats / n_placebo
    b = bench.reindex(R.index).fillna(0)
    out = dict(rule=name, IS=sharpe(r.loc[:IS_END]), OOS=sharpe(r.loc["2014-01-01":OOS_END]),
               HOLDOUT=sharpe(r.loc["2020-01-01":]), post=real, bench_post=sharpe(b.loc["2014-01-01":]),
               t_post=tstat(post), placebo_p=pp,
               cagr_post=float((1 + post).prod() ** (252 / len(post)) - 1),
               x2cost_post=float(post2.sum()),
               gross_IS=sharpe(gross.loc[:IS_END]), gross_post=sharpe(gross.loc["2014-01-01":]),
               net10_post=sharpe(post2), turn_yr=float(turn.mean() * 252),
               trades_per_year=float((w.diff().abs().sum(axis=1) > 0).sum() / (len(w) / 252)))
    gates = [out["OOS"] > 0.3, out["HOLDOUT"] > 0.3, out["post"] > out["bench_post"],
             out["t_post"] >= 2.0, pp <= 0.05, out["x2cost_post"] > 0]
    out["verdict"] = "PASS" if all(gates) else f"FAIL ({6 - sum(gates)} of 6 gates)"
    out["winner"] = bool(all(gates) and out["t_post"] >= 3)
    return out, r


COLS = ["IS", "OOS", "HOLDOUT", "post", "bench_post", "t_post", "placebo_p", "cagr_post",
        "gross_IS", "gross_post", "net10_post", "turn_yr", "verdict"]


def show(rows):
    df = pd.DataFrame(rows).set_index("rule")
    with pd.option_context("display.width", 250, "display.max_columns", 30):
        print(df[COLS].round(2).to_string())
    return df
