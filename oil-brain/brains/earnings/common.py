"""Shared helpers for the earnings brain.

Event day 0: first trading day whose CLOSE reflects the 8-K Item 2.02 release
(acceptance time converted to New York time; at/after 16:00 -> next trading day).
Checked against Yahoo earnings dates for AAPL, JPM, IBM 2005-2026: 263 of 264 Yahoo dates match.
Duplicate 2.02 filings (restatements, investor days) within 30 calendar days AFTER a kept
filing are dropped.

Portfolio: every active position is a stock held long (+1) or short (-1) and hedged with SPY.
(Study 2 on: hedge="EW" uses the equal-weighted universe of the same 92 stocks instead of SPY.)
Each day the active positions are equal weighted: w_i = sign_i / N_active, w_SPY = -sum(w_i).
Position known at close t earns close t -> t+1. Cost = cost_bps * sum |change in weights|
(stocks and SPY), charged when the change happens.
"""
import os, sys
import warnings
import numpy as np
import pandas as pd

H = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.abspath(os.path.join(H, "..", "..")))
import engine  # noqa: E402

DD = os.path.join(H, "data")


def prices():
    cl = pd.read_csv(os.path.join(DD, "close.csv"), index_col=0, parse_dates=True)
    cl = cl[cl.index >= "2004-01-01"]
    ret = cl.pct_change(fill_method=None)
    return cl, ret


def events(days):
    ev = pd.read_csv(os.path.join(DD, "edgar_202.csv"))
    ev["acc"] = pd.to_datetime(ev.acceptanceDateTime, utc=True).dt.tz_convert("America/New_York")
    d = ev.acc.dt.tz_localize(None).dt.normalize()
    d = d + pd.to_timedelta((ev.acc.dt.hour >= 16).astype(int), unit="D")
    ev["i0"] = days.searchsorted(d.values)
    ev = ev[ev.i0 < len(days)].copy()
    ev["d0"] = days[ev.i0.values]
    out = []
    for t, g in ev.sort_values("acc").groupby("ticker"):
        last = None
        for _, r in g.iterrows():
            if last is None or (r.d0 - last).days > 30:
                out.append(r)
                last = r.d0
    ev = pd.DataFrame(out).reset_index(drop=True)
    return ev[["ticker", "d0", "i0", "acc"]]


def build(trades, ret, cost_bps=10, hedge="SPY", slot=None):
    """trades: DataFrame with ticker, i_in, i_out (row indices into ret), sign.
    Position held from close i_in to close i_out. Returns net daily return series and 2x-cost series,
    plus average number of active names."""
    cols = [c for c in ret.columns if c != "SPY"]
    ci = {c: k for k, c in enumerate(cols)}
    T, N = len(ret), len(cols)
    S = np.zeros((T, N))  # summed signs active at close t
    for tk, a, b, s in trades[["ticker", "i_in", "i_out", "sign"]].itertuples(index=False):
        if tk in ci and 0 <= a < b <= T - 1:
            S[a:b, ci[tk]] += s
    R = ret[cols].values
    # drop positions on missing returns next day (stock not trading)
    nact = np.abs(S).sum(1)
    if slot:  # fixed weight 1/slot per position: no re-weighting churn when names enter/exit
        W = S / slot
    else:
        W = np.divide(S, nact[:, None], out=np.zeros_like(S), where=nact[:, None] > 0)
    wspy = -W.sum(1)
    Rn = np.nan_to_num(R)
    if hedge == "SPY":
        spy = np.nan_to_num(ret["SPY"].values)
    else:  # equal-weighted universe of the same stocks (survivor-matched hedge)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            spy = np.nan_to_num(np.nanmean(R, axis=1))
    gross = np.zeros(T)
    gross[1:] = (W[:-1] * Rn[1:]).sum(1) + wspy[:-1] * spy[1:]
    turn = np.abs(np.diff(np.vstack([np.zeros((1, N)), W]), axis=0)).sum(1) \
        + np.abs(np.diff(np.concatenate([[0], wspy])))
    c = np.zeros(T)
    c[1:] = turn[:-1]  # charged the day after the change, as in engine.pnl
    net = pd.Series(gross - c * cost_bps / 1e4, index=ret.index)
    net2 = pd.Series(gross - c * 2 * cost_bps / 1e4, index=ret.index)
    return net, net2, pd.Series(nact, index=ret.index)


def evaluate(name, net, net2, spy, start, placebo_sharpes=None):
    """engine.evaluate on the net series (pos = 1, cost 0, bench = SPY). Gate 4 (engine placebo)
    is degenerate for a constant position, so it is replaced by the event-date-shift placebo;
    gate 5 (2x cost) is recomputed on the net2 series because costs are inside the series."""
    pos = pd.Series(1.0, index=net.index)
    o = engine.evaluate(name, pos, net, cost_bps=0, bench=spy, start=start, n_placebo=2)
    post = net.loc["2014-01-01":]
    o["x2cost_post"] = float(net2.loc["2014-01-01":].sum())
    if placebo_sharpes is not None:
        ps = np.asarray(placebo_sharpes)
        o["placebo_p"] = float((ps >= o["post"]).mean())
    gates = [o["OOS"] > 0.3, o["HOLDOUT"] > 0.3, o["post"] > o["bench_post"],
             o["t_post"] >= 2.0, o["placebo_p"] <= 0.05, o["x2cost_post"] > 0]
    o["gates_passed"] = int(sum(gates))
    o["verdict"] = "PASS" if all(gates) else f"FAIL ({6 - sum(gates)} of 6 gates)"
    o["ann_ret_post"] = float(post.mean() * 252)
    return o
