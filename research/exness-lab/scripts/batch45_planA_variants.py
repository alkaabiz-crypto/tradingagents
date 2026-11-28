"""Batch 45, pre-registered 2026-11-28 (Hazza: Plan A with and without Bitcoin, and Bitcoin with exits before risk grows).
$ = % moves x today's minimum-lot exposure (US500 $1,000, US30 $500, BTC $600 per 0.01, ETH $170), Exness costs, so every year is
comparable with today. Picked on 2014-10..2023 (higher Sharpe, keeps >= 80% of profit), checked on 2024-now.
 V1 Plan A as is.
 V2 no Bitcoin: 10-day low US500 + ETH above 50-day.   V2b: V2 + IBS US30 + Connors R3 US500 (both already on paper).
 V3 Plan A with Bitcoin exits (each alone):
   a one BTC trade a day (NR4 on NR4 days, Williams otherwise), so never 0.02 BTC
   b tighter stop: half the distance to the other order (worst case if the day's range touches it)
   c monthly loss cap: no BTC trades for the rest of a month once BTC legs are down $60 in it
   d skip BTC when 10-day volatility > 1.5 x its 100-day volatility
   e skip the next BTC day after 2 losing BTC days in a row"""
import io, contextlib, numpy as np, pandas as pd
with contextlib.redirect_stdout(io.StringIO()): exec(open("lab/batch41_fixes.py").read().split("def stats")[0])
b = D["BTC-USD"]; o, h, l, c = b.Open, b.High, b.Low, b.Close; rg = h - l; cost = (BP["BTC-USD"] + 2) / 1e4
def brk_days(kind, stop_frac=1.0):
    if kind == "nr4": U, Dn = h.shift(), l.shift(); ok = (rg <= rg.rolling(4).min()).shift().fillna(False)
    else: U, Dn = o + 0.5 * rg.shift(), o - 0.5 * rg.shift(); ok = pd.Series(True, index=b.index)
    up, dn = (h >= U) & ok, (l <= Dn) & ok; eL, eS = np.maximum(U, o), np.minimum(Dn, o); W = (U - Dn)
    sL, sS = eL - stop_frac * W, eS + stop_frac * W
    if stop_frac >= 1:
        r = np.where(up & dn, -(U - Dn) / U, np.where(up, (c - eL) / eL, np.where(dn, (eS - c) / eS, 0)))
    else:  # worst case: long stopped if low <= stop, short if high >= stop; both triggers -> take the first-listed loss of both sides
        rl = np.where(l <= sL, (sL - eL) / eL, (c - eL) / eL); rs = np.where(h >= sS, (eS - sS) / eS, (eS - c) / eS)
        r = np.where(up & dn, np.minimum(rl, rs) + np.minimum(0, np.where(h >= sS, (eS - sS) / eS, (eS - c) / eS)), np.where(up, rl, np.where(dn, rs, 0)))
    return pd.Series(r, index=b.index).fillna(0) * 600 - (up | dn).astype(float) * cost * 600, (up | dn)
nr4, t_n = brk_days("nr4"); wil, t_w = brk_days("w"); is_nr4 = (rg <= rg.rolling(4).min()).shift().fillna(False)
other = {k: LEGS[k]["none"] for k in ("10-day low US500", "ETH above 50-day")}; other["IBS US30"] = R["IBS US30"][1] * 500; other["Connors R3 US500"] = R["Connors R3 US500"][1] * 1000
def plan(btc, extra=("10-day low US500", "ETH above 50-day")):
    parts = [other[k] for k in extra] + ([btc] if btc is not None else []); return pd.concat(parts, axis=1, sort=True).fillna(0).sum(axis=1)
btc_base = nr4 + wil
def gate(btc_series, allow): return btc_series.where(allow, 0)
# a
va = pd.Series(np.where(is_nr4, nr4, wil), index=b.index)
# b
nb, _ = brk_days("nr4", 0.5); wb, _ = brk_days("w", 0.5); vb = nb + wb
# c monthly cap (sequential)
vals = btc_base.values; mo = btc_base.index.to_period("M"); out = np.zeros(len(vals)); cur, mtd, stop = None, 0, False
for i in range(len(vals)):
    if mo[i] != cur: cur, mtd, stop = mo[i], 0, False
    if not stop: out[i] = vals[i]; mtd += vals[i]; stop = mtd <= -60
vc = pd.Series(out, index=btc_base.index)
# d vol spike
v10, v100 = c.pct_change().rolling(10).std(), c.pct_change().rolling(100).std(); vd = gate(btc_base, ~((v10 > 1.5 * v100).shift().fillna(False).astype(bool)))
# e skip after 2 losses
out = np.zeros(len(vals)); losses = 0; traded = ((t_n | t_w).values)
for i in range(len(vals)):
    if losses >= 2: losses = 0; continue
    out[i] = vals[i]
    if traded[i]: losses = losses + 1 if vals[i] < 0 else 0
ve = pd.Series(out, index=btc_base.index)
V = {"V1 Plan A as is": plan(btc_base), "V2 no Bitcoin (US500 10-day low + ETH)": plan(None), "V2b no Bitcoin + IBS US30 + Connors R3": plan(None, ("10-day low US500", "ETH above 50-day", "IBS US30", "Connors R3 US500")),
     "V3a one BTC trade a day": plan(va), "V3b tighter BTC stop": plan(vb), "V3c BTC monthly loss cap $60": plan(vc), "V3d skip BTC on volatility spikes": plan(vd), "V3e skip after 2 BTC losses": plan(ve)}
def st(u, a, z):
    u = u.loc[a:z]; e = u.cumsum(); m = u.groupby(u.index.to_period("M")).sum(); yrs = len(m) / 12
    return u.sum() / yrs, (e - e.cummax()).min(), (m < 0).sum(), len(m), u.mean() / u.std()
base = st(V["V1 Plan A as is"], "2014-10", "2023")
for k, u in V.items():
    a, o_ = st(u, "2014-10", "2023"), st(u, "2024", "2026")
    pick = k.startswith("V3") and a[4] > base[4] and a[0] >= 0.8 * base[0]
    y = u.loc["2015":"2026"].groupby(u.loc["2015":"2026"].index.year).sum()
    print(f"{k}{'  <- PICK' if pick else ''}\n  2014-23: ${a[0]:+.0f}/yr ({a[0]/30:.0f}%), worst drop {a[1]:.0f}, losing months {a[2]}/{a[3]} | 2024+: ${o_[0]:+.0f}/yr ({o_[0]/30:.0f}%), worst drop {o_[1]:.0f}, losing months {o_[2]}/{o_[3]}")
    print("  years:", ", ".join(f"{yy} {v:+.0f}" for yy, v in y.items()))
# index-only history for V2 before crypto
u = plan(None, ("10-day low US500",)).loc["2000":"2013"]; print("US500 10-day low alone 2000-13 years:", ", ".join(f"{yy} {v:+.0f}" for yy, v in u.groupby(u.index.year).sum().items()))
