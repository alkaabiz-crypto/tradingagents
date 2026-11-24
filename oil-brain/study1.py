"""Study 1 (pre-registered 2026-11-24, before any run): academic oil signals on daily data.

Traded instruments: USO (real ETF, includes roll costs) for oil rules; SPY for oil->stocks.
Costs: 5 bp per unit of turnover (ETF spread + slippage). Parameters are the papers'
defaults; no tuning.

H1 Driesprong, Jacobsen & Maat (2008): rising oil predicts lower stock returns with a lag.
   Hold SPY next month only if oil (USO) fell over the last month; else cash. Monthly.
H2 Term structure / carry (Gorton, Hayashi & Rouwenhorst 2013; Koijen et al. 2018):
   backwardation earns, contango loses. Proxy: USO minus USL 21-day return (USO rolls the
   front month, USL spreads over 12 months, so USO lagging USL = contango roll drag).
   Long USO when the 21-day spread > 0 (backwardation), short when < 0.
H2b same, long or flat.
H3 Time-series momentum (Moskowitz, Ooi & Pedersen 2012): sign of the 12-month USO return,
   rebalanced monthly, volatility-scaled to 20%/yr (capped at 1x).
H3b same with a 1-month lookback.
H4 Short-term reversal after big days: after a USO day below -2 sd (60-day), long for 1 day.
H5 EIA Wednesday: long USO only on Wednesday (close Tue -> close Wed).
H6 OVX fear: long USO for 5 days after OVX jumps > 20% in a day.
H7 Oil->energy stocks lag: long XLE next day when USO beat XLE by > 1 sd today.
"""
import numpy as np
import pandas as pd
from engine import load, evaluate, table

uso, usl, spy, xle, ovx = (load(s) for s in ["USO", "USL", "SPY", "XLE", "^OVX"])
r_uso, r_spy, r_xle = uso.pct_change(), spy.pct_change(), xle.pct_change()
rows = []

# H1: month-end signal applied to the whole next month.
m_oil = uso.resample("ME").last().pct_change()
sig = (m_oil < 0).astype(float)
pos = sig.reindex(spy.index, method="ffill").shift(0)
# The month-end close is known at that close; the position starts next day via engine shift.
pos = sig.reindex(spy.index).ffill()
rows.append(evaluate("H1 SPY only after oil fell last month", pos, r_spy, start="2006-05-01"))

# H2: carry proxy.
spread = (uso.pct_change(21) - usl.pct_change(21)).dropna()
pos = np.sign(spread)
rows.append(evaluate("H2 USO carry long/short (USO-USL 21d)", pos, r_uso, start="2008-01-15"))
rows.append(evaluate("H2b USO carry long/flat", (spread > 0).astype(float), r_uso, start="2008-01-15"))

# H3: TSMOM, monthly, vol-scaled.
vol = r_uso.rolling(63).std() * np.sqrt(252)
for lb, nm in [(252, "H3 TSMOM 12m"), (21, "H3b TSMOM 1m")]:
    me = uso.index.to_series().groupby(uso.index.to_period("M")).last()
    s = np.sign(uso.pct_change(lb)).loc[me.values]
    sc = (0.20 / vol).clip(upper=1.0).loc[me.values]
    pos = (s * sc).reindex(uso.index).ffill()
    rows.append(evaluate(nm + " vol-scaled", pos, r_uso, start="2007-06-01"))

# H4: reversal after big down day.
z = r_uso / r_uso.rolling(60).std().shift(1)
rows.append(evaluate("H4 long 1d after USO < -2sd day", (z < -2).astype(float), r_uso, start="2006-08-01"))

# H5: Wednesday. Position at Tuesday close, earns Wednesday.
pos = pd.Series((uso.index.day_of_week == 1).astype(float), index=uso.index)
rows.append(evaluate("H5 long USO on Wednesdays only", pos, r_uso))

# H6: OVX jump.
oj = ovx.pct_change().reindex(uso.index)
pos = (oj > 0.20).astype(float).rolling(5, min_periods=1).max()
rows.append(evaluate("H6 long USO 5d after OVX +20% day", pos, r_uso, start="2007-06-01"))

# H7: oil->XLE lag.
gap = (r_uso - r_xle)
zz = gap / gap.rolling(60).std().shift(1)
rows.append(evaluate("H7 long XLE 1d after USO beat XLE >1sd", (zz > 1).astype(float), r_xle, start="2006-08-01"))

print(table(rows))
