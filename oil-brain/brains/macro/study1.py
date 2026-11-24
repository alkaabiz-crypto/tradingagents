"""Study 1 (macro brain), pre-registered 2026-11-24 BEFORE running.

All signals are sampled at the close of the last trading day of each month and held for the
next month (monthly rebalance). Parameters fixed here from the papers / convention, not tuned.
Costs 5 bp per unit turnover (ETFs). Evaluation starts 2007-06-01 (HYG/DBB/UUP history), so
IS is only 2007-06..2013 and contains the GFC.

M1  Dollar -> oil (ECB 2024: oil-dollar correlation changed sign after US became net exporter).
    USO position = -sign(DXY 21d return), long/short. Prediction: FAIL (unstable sign).
M2  Copper/gold growth signal: DBB/GLD 63d change > 0 -> long USO, else flat.
M3  Same copper/gold signal -> long SPY else flat (benchmark SPY).
M4  Credit (Gilchrist & Zakrajsek 2012 idea): HYG/LQD 21d relative return > 0 -> long SPY
    else flat (benchmark SPY).
M5  Same credit signal -> long USO else flat.
M6  Rates momentum: ^TNX 63d change > 0 (reflation) -> long XLE else flat (benchmark XLE).
M7  Stock-bond correlation regime: 63d corr(SPY, TLT daily returns) > 0 (inflation regime)
    -> long XLE / short SPY (dollar neutral), else flat. Benchmark: buy-and-hold XLE-SPY.
M8  Hong, Torous & Valkanov 2007 lead-lag: metals' past-month return predicts the market
    NEGATIVELY. Long SPY if DBB return over last month < 0, else flat (benchmark SPY).
M9  Composite for USO, long/short: mean of sign(cu/au 63d), sign(credit 21d), sign(TNX 63d).

Expected: most fail; long/flat SPY timers rarely beat buy-and-hold Sharpe post-2014.
"""
import numpy as np, pandas as pd
from common import engine, px, ret, monthly

START = "2007-06-01"
uso, spy, xle = ret("USO"), ret("SPY"), ret("XLE")
idx = spy.dropna().index
dxy, dbb, gld = px("DX-Y.NYB"), px("DBB"), px("GLD")
hyg, lqd, tnx, tlt = px("HYG"), px("LQD"), px("^TNX"), ret("TLT")

cugold = np.log(dbb / gld).reindex(idx).ffill()
cu_sig = np.sign(cugold.diff(63))
credit = np.log(hyg / lqd).reindex(idx).ffill()
cr_sig = np.sign(credit.diff(21))
tnx_sig = np.sign(tnx.reindex(idx).ffill().diff(63))
dxy_sig = np.sign(np.log(dxy.reindex(idx).ffill()).diff(21))
corr = spy.rolling(63).corr(tlt.reindex(idx))
dbb_m = np.log(dbb.reindex(idx).ffill()).diff(21)

rows = []
def ev(name, sig, r, bench=None):
    pos = monthly(sig, idx).fillna(0)
    rows.append(engine.evaluate(name, pos, r, 5, bench, START))

ev("M1 -sign(DXY 21d) USO L/S", -dxy_sig, uso)
ev("M2 cu/au 63d up -> USO L/F", (cu_sig > 0).astype(float), uso)
ev("M3 cu/au 63d up -> SPY L/F", (cu_sig > 0).astype(float), spy)
ev("M4 HYG/LQD 21d up -> SPY L/F", (cr_sig > 0).astype(float), spy)
ev("M5 HYG/LQD 21d up -> USO L/F", (cr_sig > 0).astype(float), uso)
ev("M6 TNX 63d up -> XLE L/F", (tnx_sig > 0).astype(float), xle)
spread = (xle - spy)
ev("M7 corr(SPY,TLT)>0 -> XLE-SPY", (corr > 0).astype(float), spread, bench=spread)
ev("M8 DBB 1m down -> SPY L/F (HTV07)", (dbb_m < 0).astype(float), spy)
ev("M9 composite USO L/S", (cu_sig + cr_sig + tnx_sig) / 3, uso)

print(engine.table(rows))
pd.DataFrame(rows).to_csv("study1_results.csv", index=False)
