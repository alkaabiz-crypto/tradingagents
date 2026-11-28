"""Batch 36 (2026-11-27): every paper strategy, rules frozen, before 2024. Daily % returns x TODAY's min-lot exposure,
so old years are comparable to now. Exposure: USTEC 0.05 lot $1,330 (QQQ x41 x0.05), US500 0.14 $1,000, US30 0.1 $4,960,
BTC 0.01 $600, ETH 0.1 $170. Costs as before. Periods: 2000-09, 2010-13, 2014-19, 2020-23 (pre-2024) and 2024-now."""
import numpy as np, pandas as pd
def L(t): return pd.read_csv(f"data/{t}.csv", parse_dates=["Date"], index_col="Date").dropna().loc[:"2026-11-24"]
def rsi(c, n):
    d = c.diff(); u = d.clip(lower=0).ewm(alpha=1/n, adjust=False).mean(); v = (-d.clip(upper=0)).ewm(alpha=1/n, adjust=False).mean(); return 100 - 100 / (1 + u / v)
def hold(sig, n):
    s = np.asarray(sig, bool); out = np.zeros(len(s)); left = 0
    for i in range(len(s)):
        if s[i]: left = n
        out[i] = 1 if left > 0 else 0; left -= 1 if left > 0 else 0
    return out
def closehold(d, pos, bp):  # pos[t] = position after close t
    p = pd.Series(pos, index=d.index).shift().fillna(0); return p * d.Close.pct_change().fillna(0) - (p.diff() > 0) * bp / 1e4
EXP = {"QQQ": 1330, "SPY": 1000, "DIA": 4960, "BTC-USD": 600, "ETH-USD": 170}; BP = {"QQQ": 1.4, "SPY": 1.6, "DIA": 1.3, "BTC-USD": 1.1, "ETH-USD": 5}
D = {t: L(t) for t in EXP}; R = {}
def ibs(d): return ((d.Close - d.Low) / (d.High - d.Low)).values < 0.2
def wr(d): return (-100 * (d.High.rolling(10).max() - d.Close) / (d.High.rolling(10).max() - d.Low.rolling(10).min())).values < -90
def r3(c):
    r2 = rsi(c, 2); ent = (r2 < r2.shift()) & (r2.shift() < r2.shift(2)) & (r2.shift(2) < r2.shift(3)) & (r2.shift(2) < 60) & (r2 < 10) & (c > c.rolling(200).mean())
    pos, out = 0, []
    for e, x in zip(ent.values, (r2 > 70).values):
        if pos == 0 and e: pos = 1
        elif pos == 1 and x: pos = 0
        out.append(pos)
    return np.array(out, float)
for nm, t, pos in (("IBS USTEC", "QQQ", lambda d: hold(ibs(d), 2)), ("IBS US30", "DIA", lambda d: hold(ibs(d), 2)), ("IBS US500", "SPY", lambda d: hold(ibs(d), 2)),
                   ("%R USTEC", "QQQ", lambda d: hold(wr(d), 2)), ("%R US500", "SPY", lambda d: hold(wr(d), 2)), ("Connors R3 US500", "SPY", lambda d: r3(d.Close)),
                   ("10-day low US500", "SPY", lambda d: hold((d.Close <= d.Close.rolling(10).min()).values, 3))):
    R[nm] = (t, closehold(D[t], pos(D[t]), BP[t]))
for nm, t in (("BTC TRIX trend", "BTC-USD"), ("ETH above 50-day", "ETH-USD")):
    c = D[t].Close
    if "TRIX" in nm:
        e = c.ewm(span=15, adjust=False).mean().ewm(span=15, adjust=False).mean().ewm(span=15, adjust=False).mean(); tr = e.pct_change(); pos = (tr > tr.ewm(span=9, adjust=False).mean()).values.astype(float)
    else: pos = (c > c.rolling(50).mean()).values.astype(float)
    R[nm] = (t, closehold(D[t], pos, BP[t]))
# breakouts (worst case when both hit), slippage 2 bp
for nm, t, kind in (("BTC NR4", "BTC-USD", "nr4"), ("BTC Williams (T1)", "BTC-USD", "w"), ("ETH Williams (T2)", "ETH-USD", "w")):
    d = D[t]; o, h, l, c = d.Open, d.High, d.Low, d.Close; rg = h - l; cost = (BP[t] + 2) / 1e4
    if kind == "nr4": U, Dn = h.shift(), l.shift(); ok = (rg <= rg.rolling(4).min()).shift().fillna(False)
    else: U, Dn = o + 0.5 * rg.shift(), o - 0.5 * rg.shift(); ok = pd.Series(True, index=d.index)
    up, dn = (h >= U) & ok, (l <= Dn) & ok
    eL = np.maximum(U, o); eS = np.minimum(Dn, o)
    r = np.where(up & dn, -(U - Dn) / U, np.where(up, (c - eL) / eL, np.where(dn, (eS - c) / eS, 0))) - (up | dn) * cost
    R[nm] = (t, pd.Series(r, index=d.index).fillna(0))
q = D["QQQ"]; s200 = (q.Close > q.Close.rolling(200).mean())
on = ((q.Open.shift(-1) / q.Close - 1) - 1.4e-4 - 2e-4).where(s200, 0).shift().fillna(0)  # booked on the exit day
R["USTEC overnight"] = ("QQQ", on)
P = [("2000-09", "2000", "2009"), ("2010-13", "2010", "2013"), ("2014-19", "2014", "2019"), ("2020-23", "2020", "2023"), ("2024-now", "2024", "2026")]
rows = []
for nm, (t, r) in R.items():
    usd = r * EXP[t]; row = {"strategy": nm}
    for lab, a, b in P:
        u = usd.loc[a:b]
        if len(u) < 200 or (u != 0).sum() < 5: row[lab] = ""; continue
        e = u.cumsum(); row[lab] = f"{u.sum():+.0f} / {(e - e.cummax()).min():.0f}"
    pre = usd.loc[:"2023"]; pre = pre[pre.index >= pre[pre != 0].index[0]] if (pre != 0).any() else pre
    yr = pre.groupby(pre.index.year).sum(); row["losing yrs pre-2024"] = f"{(yr < 0).sum()}/{len(yr)}"; row["first year"] = yr.index[0]
    row["worst yr pre-2024"] = f"{yr.min():+.0f} ({yr.idxmin()})"
    rows.append(row)
df = pd.DataFrame(rows); print(df.to_string(index=False)); df.to_csv("lab/batch36_results.csv", index=False)
