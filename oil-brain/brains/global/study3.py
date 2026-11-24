"""Study 3 (pre-registered 2026-11-24, before running): US leads other markets, and oil lead-lag.
All monthly: signal at month-end close, held one month, 10 bp per unit turnover, cash earns 0.
Equal-weight country basket = all 20 lib.CTRY ETFs alive at that month-end.
Mechanisms: Rapach, Strauss & Zhou (2013 JF): lagged US returns predict non-US index returns
(slow information diffusion). Driesprong, Jacobsen & Maat (2008 JFE): oil price changes predict
LOWER stock returns next month across countries (investor underreaction). Exporter/importer split:
oil shocks should matter with opposite signs for oil exporters and importers; underreaction
would give continuation of the exporter-minus-importer spread after oil moves.
R1  hold EW country basket if SPY's last-month return > 0, else cash.   bench: EW basket
O1  hold EW basket if WTI (CL=F, shared data) last-month return < 0, else cash.  bench: EW basket
O2  spread: long EW(EWC, EWZ, EWW, NORW*) minus EW(EWJ, EWY, EWT, INDA*), sign = sign of WTI
    last-month return (*when trading). bench: EW basket.
Start 1997-01 (R1, O1 need one month; O2 starts when EWZ/EWT trade, 2000-07).
Expectation: Rapach effect is stronger at monthly frequency pre-2000s; timing rules have
weak placebo power; I expect failures. Rules counted: 3 (total 9).
"""
import numpy as np, pandas as pd
from lib import CTRY, panel, load, month_ends, hold, evaluate_w, show, port
import os
px = panel(CTRY + ["NORW"]); ret = px.pct_change(fill_method=None)
me = month_ends(px.index); pm = px.loc[me]
alive = pm[CTRY].notna()
ew = alive.astype(float).div(alive.sum(axis=1), axis=0).reindex(columns=px.columns).fillna(0)
bench = port(hold(ew, px.index), ret, 10)
spy = load("SPY").reindex(px.index).ffill().loc[me]
oil = pd.read_csv(os.path.join(os.path.dirname(__file__), "..", "..", "data", "CL_F.csv"), index_col=0, parse_dates=True)["Close"]
oilm = oil.reindex(px.index).ffill().loc[me]
s_spy = (spy.pct_change() > 0).astype(float)
s_oil = np.sign(oilm.pct_change()).fillna(0)
w_r1 = ew.mul(s_spy, axis=0)
w_o1 = ew.mul((oilm.pct_change() < 0).astype(float).where(oilm.pct_change().notna(), 0), axis=0)
EX, IM = ["EWC","EWZ","EWW","NORW"], ["EWJ","EWY","EWT","INDA"]
ex = pm[EX].notna(); im = pm[IM].notna()
spread = pd.concat([ex.astype(float).div(ex.sum(axis=1), axis=0), -im.astype(float).div(im.sum(axis=1), axis=0)], axis=1)
spread = spread.reindex(columns=px.columns).fillna(0)
w_o2 = spread.mul(s_oil, axis=0).where((ex.sum(axis=1) >= 3) & (im.sum(axis=1) >= 3), 0)
W = {"R1 US lead: EW basket if SPY 1m>0": w_r1, "O1 Driesprong: EW basket if oil 1m<0": w_o1,
     "O2 exporters-importers x sign(oil 1m)": w_o2}
rows = []; R = {}
for k, wm in W.items():
    w = hold(wm, px.index)
    start = max(pd.Timestamp("1997-01-31"), w.index[(w.abs().sum(axis=1) > 0).values.argmax()])
    o, r = evaluate_w(k, w, ret, bench, cost=10, start=start); o["start"] = str(start.date()); rows.append(o); R[k] = r
show(rows)
for k, r in R.items():
    print(k, "by year %:", (r.groupby(r.index.year).sum() * 100).round(1).to_dict())
pd.DataFrame(rows).to_csv("study3_results.csv", index=False)
