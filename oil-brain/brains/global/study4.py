"""Study 4 (pre-registered 2026-11-24, before running; choices from IS results of studies 1-2 only).
T3  Large-day fade (from study 2 IS: gross P&L of T1 is concentrated in high-volatility days and
    small days only pay costs). Asia basket as study 2 (EWJ EWH EWS EWT EWY FXI EWA EWM),
    pos = -sign(SPY day t return) if |SPY day t| > 1.5%, else 0; daily, close-to-close,
    5 bp per unit turnover, engine.evaluate unchanged, bench = basket buy-and-hold, start 2001.
    Threshold 1.5% chosen a priori (about 1.2 daily SD of SPY), not grid-searched.
C1  Short-horizon country momentum (Chan, Hameed & Tong 2000 JFQA find momentum in country
    indices at short horizons): 20 lib.CTRY ETFs, rank on last 1-month return, long top 4,
    short bottom 4, monthly, 10 bp per side, bench = EW basket.
Rules counted: 2 (total 11).
"""
import numpy as np, pandas as pd
from lib import CTRY, load, panel, evaluate, month_ends, hold, xs_weights, evaluate_w, show, port
from engine import table, pnl
A = ["EWJ","EWH","EWS","EWT","EWY","FXI","EWA","EWM"]
bret = panel(A).pct_change(fill_method=None).mean(axis=1).loc["2001":]
spy = load("SPY").pct_change().reindex(bret.index)
p3 = (-np.sign(spy)).where(spy.abs() > 0.015, 0).fillna(0)
o3 = evaluate("T3 fade SPY >1.5% days in Asia basket", p3, bret, cost_bps=5, bench=bret, start="2001-01-01")
print(table([o3])); print("exposure", round(o3["exposure"], 3), "x2cost", round(o3["x2cost_post"], 3))
r3 = pnl(p3, bret, 5); print("T3 by year %:", (r3.groupby(r3.index.year).sum()*100).round(1).to_dict())

px = panel(CTRY); ret = px.pct_change(fill_method=None)
me = month_ends(px.index); pm = px.loc[me]; alive = pm.notna()
bench = port(hold(alive.astype(float).div(alive.sum(axis=1), axis=0), px.index), ret, 10)
w = hold(xs_weights(pm.pct_change(fill_method=None), 4), px.index)
start = w.index[(w.abs().sum(axis=1) > 0).values.argmax()]
o1, r1 = evaluate_w("C1 1m country momentum L/S 4/4", w, ret, bench, cost=10, start=start)
show([o1]); print("C1 by year %:", (r1.groupby(r1.index.year).sum()*100).round(1).to_dict())
pd.DataFrame([o3, o1]).to_csv("study4_results.csv", index=False)
