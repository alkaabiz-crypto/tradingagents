"""Study 2 (pre-registered 2026-11-24, written before running; after study 1 found 0 of 6).
Same costs, gates, placebo and EW-sector benchmark as study 1. Month-end rebalance throughout.
 S7 time-series momentum per sector (Moskowitz, Ooi & Pedersen 2012): each alive sector
    sign(252-day return), scaled to 10%/yr / N by 63-day vol (cap 3x), long/short. Start 2000.
 S8 sector trend-timing long/flat (Faber 2007): each sector held at 1/N when its month-end close
    is above its 10-month (210-day) average, else cash. Start 2000.
 S9 oil -> energy equities catch-up: position +1 XLE / -1 SPY if USO's 21-day return > 0, else
    -1 XLE / +1 SPY (equities slow to price oil, Driesprong et al. 2008 / underreaction). Start 2006-06.
 S10 oil -> transports: +1 IYT / -1 SPY if USO's 21-day return < 0, else the reverse
    (fuel-cost users gain when oil falls, slowly). Start 2006-06.
 S11 energy sub-industry momentum: among XLE, XOP, OIH, long the best / short the worst
    126-day return (MG99 6m formation), +1/-1. Starts when all three have 300 days (2007).
JETS starts 2015 (no in-sample period), so it is not used for a rule.
"""
import numpy as np, pandas as pd
from lib import *

syms = SECT + ["SPY", "IYT", "XOP", "OIH", "USO"]
px = panel(syms).loc["1998-12-01":]
ret = px.pct_change(fill_method=None)
idx = px.index; me = period_ends(idx, "M")
S = px[SECT]; alive = S.notna().cumsum() >= 300
N = alive.sum(axis=1).replace(0, np.nan)
bench = ret[SECT].where(alive).mean(axis=1)

def full(w):
    return w.reindex(columns=syms).fillna(0)

vol = ret[SECT].rolling(63).std() * np.sqrt(252)
w7 = (np.sign(S.pct_change(252, fill_method=None)) * (0.10 / vol).clip(upper=3)).div(N, axis=0).where(alive).fillna(0)
w8 = (S > S.rolling(210, min_periods=210).mean()).astype(float).div(N, axis=0).where(alive).fillna(0)
oil = np.sign(px["USO"].pct_change(21, fill_method=None))
w9 = pd.DataFrame(0.0, index=idx, columns=syms); w9["XLE"] = oil; w9["SPY"] = -oil
w10 = pd.DataFrame(0.0, index=idx, columns=syms); w10["IYT"] = -oil; w10["SPY"] = oil
E = px[["XLE", "XOP", "OIH"]]; ealive = (E.notna().cumsum() >= 300)
ealive = ealive.where(ealive.all(axis=1), False)
w11 = xs_weights(E.pct_change(126, fill_method=None), ealive, top=1)

W = {"S7 TSMOM 12m per sector": (w7, "2000-01-01"), "S8 Faber 10m SMA long/flat": (w8, "2000-01-01"),
     "S9 oil sign -> XLE minus SPY": (w9, "2006-06-01"), "S10 oil sign -> IYT minus SPY": (w10, "2006-06-01"),
     "S11 XLE/XOP/OIH momentum 6m": (w11, "2007-01-01")}
rows = []
for k, (w, st) in W.items():
    wm = hold(full(w).loc[me], idx).fillna(0)
    o, r = evaluate_w(k, wm, ret.fillna(0), bench, start=st)
    rows.append(o)
show(rows)
pd.DataFrame(rows).to_csv("study2_results.csv", index=False)
