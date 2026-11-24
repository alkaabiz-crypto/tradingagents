"""Shared helpers for the energy brain. engine.py is imported unchanged."""
import os, sys
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, ROOT)
from engine import load as load_shared, evaluate, table, sharpe, tstat, IS_END, OOS_END  # noqa

def px(sym):
    f = os.path.join(HERE, "data", sym + ".csv")
    if os.path.exists(f):
        return pd.read_csv(f, index_col=0, parse_dates=True)["Close"]
    return load_shared(sym)

def rets(syms):
    return pd.concat({s: px(s) for s in syms}, axis=1).pct_change()

def roll_beta(y, X, win=252):
    """Rolling OLS betas of y on columns of X (with intercept), using data up to and including t."""
    df = pd.concat([y.rename("y"), X], axis=1).dropna()
    Y = df["y"].values; Z = np.column_stack([np.ones(len(df)), df[X.columns].values])
    B = np.full((len(df), Z.shape[1] - 1), np.nan)
    for i in range(win, len(df) + 1):
        b = np.linalg.lstsq(Z[i - win:i], Y[i - win:i], rcond=None)[0]
        B[i - 1] = b[1:]
    return pd.DataFrame(B, index=df.index, columns=X.columns)

def hedged(y, X, beta):
    """Return of y minus yesterday's betas times today's X returns (a tradeable hedged position)."""
    b = beta.shift(1)
    return y - (b * X).sum(axis=1, min_count=len(X.columns))

def weekly(sig):
    """Sample a daily signal at the last trading day of each week and hold it for the week."""
    s = sig.copy()
    wk = s.index.to_period("W-FRI")
    last = pd.Series(s.index, index=s.index).groupby(wk).transform("max")
    return s.where(s.index == last.values).ffill()

def monthly(sig):
    s = sig.copy()
    mk = s.index.to_period("M")
    last = pd.Series(s.index, index=s.index).groupby(mk).transform("max")
    return s.where(s.index == last.values).ffill()

def xs_evaluate(name, W, R, cost_bps=10, start=None, n_placebo=500, seed=7, bench=None):
    """Cross-sectional version of engine.evaluate (same gates): W = weights known at close t
    (rows dates, cols assets), R = asset returns. Placebo = circular time shift of the whole
    weight matrix (same exposure and turnover, broken timing)."""
    R = R.copy()
    if start: R = R[R.index >= start]
    W = W.reindex(R.index).ffill().fillna(0)
    Rf = R.fillna(0)
    def pnl(Wm, c):
        g = (Wm.shift(1).fillna(0) * Rf).sum(axis=1)
        turn = Wm.diff().abs().sum(axis=1).fillna(Wm.abs().sum(axis=1))
        return g - turn.shift(1).fillna(0) * c / 1e4
    r = pnl(W, cost_bps); r2 = pnl(W, 2 * cost_bps)
    b = (bench if bench is not None else R.mean(axis=1)).reindex(R.index).fillna(0)
    post_mask = r.index >= "2014-01-01"
    real = sharpe(r[post_mask]); rng = np.random.default_rng(seed); n = len(W); beats = 0
    for _ in range(n_placebo):
        k = int(rng.integers(n // 10, n - n // 10))
        Ws = pd.DataFrame(np.roll(W.values, k, axis=0), index=W.index, columns=W.columns)
        if sharpe(pnl(Ws, cost_bps)[post_mask]) < real: beats += 1
    pp = 1 - beats / n_placebo
    post = r[post_mask]
    out = dict(rule=name, IS=sharpe(r.loc[:IS_END]), OOS=sharpe(r.loc["2014-01-01":OOS_END]),
               HOLDOUT=sharpe(r.loc["2020-01-01":]), post=real, bench_post=sharpe(b[post_mask]),
               t_post=tstat(post), placebo_p=pp,
               cagr_post=float((1 + post).prod() ** (252 / max(len(post), 1)) - 1),
               x2cost_post=float(r2[post_mask].sum()), exposure=float(W.abs().sum(axis=1).mean()),
               trades_per_year=float(W.diff().abs().sum(axis=1).gt(0).sum() / (len(W) / 252)))
    gates = [out["OOS"] > 0.3, out["HOLDOUT"] > 0.3, out["post"] > out["bench_post"],
             out["t_post"] >= 2.0, pp <= 0.05, out["x2cost_post"] > 0]
    out["verdict"] = "PASS" if all(gates) else f"FAIL ({6 - sum(gates)} of 6 gates)"
    return out
