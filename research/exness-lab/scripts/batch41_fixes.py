"""Batch 41, pre-registered 2026-11-28: fixes for Plan A's weak spots. Each leg gets 3-4 textbook filters; the filter is chosen
on 2014-2023 only (highest Sharpe, and it must keep >= 80% of the leg's 2014-23 profit), then 2024-now is the check.
 BTC NR4 and BTC Williams: none | BTC above its 200-day | ADX(14) > 20 | 20-day volatility above its 1-year median.
 10-day low US500: none | above the 200-day | VIX above its 20-day average | exit after 3 days OR a 2% loss (stop).
 ETH above 50-day: none | 2% buffer (enter above 1.02x, exit below 0.98x) | 2 closes above/below to switch.
All filters use data up to the prior close. $ at minimum lots (US500 $1,000, BTC $600, ETH $170), Exness costs."""
import io, contextlib, numpy as np, pandas as pd
with contextlib.redirect_stdout(io.StringIO()): exec(open("lab/batch36_pre2024.py").read())
vix = L("VIX").Close
def adx(d, n=14):
    h, l, c = d.High, d.Low, d.Close; tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1); a = tr.ewm(alpha=1/n, adjust=False).mean()
    up, dn = h.diff(), -l.diff(); pdm = pd.Series(np.where((up > dn) & (up > 0), up, 0), index=d.index); ndm = pd.Series(np.where((dn > up) & (dn > 0), dn, 0), index=d.index)
    pdi = 100 * pdm.ewm(alpha=1/n, adjust=False).mean() / a; ndi = 100 * ndm.ewm(alpha=1/n, adjust=False).mean() / a
    return (100 * (pdi - ndi).abs() / (pdi + ndi)).ewm(alpha=1/n, adjust=False).mean()
b = D["BTC-USD"]; bc = b.Close
BF = {"none": pd.Series(True, index=b.index), "above 200-day": (bc > bc.rolling(200).mean()).shift().fillna(False),
      "ADX > 20": (adx(b) > 20).shift().fillna(False),
      "vol above median": (lambda v: (v > v.rolling(365).median()).shift().fillna(False))(bc.pct_change().rolling(20).std())}
def brk(kind, ok):
    d = b; o, h, l, c = d.Open, d.High, d.Low, d.Close; rg = h - l; cost = (BP["BTC-USD"] + 2) / 1e4
    if kind == "nr4": U, Dn = h.shift(), l.shift(); ok = ok & (rg <= rg.rolling(4).min()).shift().fillna(False)
    else: U, Dn = o + 0.5 * rg.shift(), o - 0.5 * rg.shift()
    up, dn = (h >= U) & ok, (l <= Dn) & ok; eL, eS = np.maximum(U, o), np.minimum(Dn, o)
    r = np.where(up & dn, -(U - Dn) / U, np.where(up, (c - eL) / eL, np.where(dn, (eS - c) / eS, 0))) - (up | dn) * cost
    return pd.Series(r, index=d.index).fillna(0) * 600
s = D["SPY"]; sc = s.Close; sr = sc.pct_change().fillna(0); low10 = (sc <= sc.rolling(10).min()).values
vx = vix.reindex(sc.index).ffill()
def spy_leg(f):
    sig = low10.copy()
    if f == "above 200-day": sig &= (sc > sc.rolling(200).mean()).values
    if f == "VIX above 20-day avg": sig &= (vx > vx.rolling(20).mean()).values
    if f == "2% stop":
        out = np.zeros(len(sig)); left = 0; entry = None; cc = sc.values
        for i in range(len(sig)):
            if left > 0 and entry is not None and cc[i] / entry - 1 < -0.02: left = 0
            out[i] = 1 if left > 0 else 0; left -= 1 if left > 0 else 0
            if sig[i]: left, entry = 3, cc[i]
        pos = out
    else: pos = hold(sig, 3)
    return closehold(s, pos, BP["SPY"]) * 1000
e = D["ETH-USD"]; ec = e.Close; sma = ec.rolling(50).mean()
def eth_leg(f):
    if f == "none": pos = (ec > sma).astype(float).values
    elif f == "2% buffer":
        p, out = 0, []
        for x, m in zip(ec.values, sma.values):
            if np.isnan(m): out.append(0); continue
            if p == 0 and x > 1.02 * m: p = 1
            elif p == 1 and x < 0.98 * m: p = 0
            out.append(p)
        pos = np.array(out, float)
    else:
        a = (ec > sma); p, out = 0, []
        for i in range(len(a)):
            if i > 0 and a.iloc[i] and a.iloc[i - 1]: p = 1
            elif i > 0 and (not a.iloc[i]) and (not a.iloc[i - 1]): p = 0
            out.append(p)
        pos = np.array(out, float)
    return closehold(e, pos, BP["ETH-USD"]) * 170
LEGS = {"BTC NR4": {f: brk("nr4", m) for f, m in BF.items()}, "BTC Williams": {f: brk("w", m) for f, m in BF.items()},
        "10-day low US500": {f: spy_leg(f) for f in ("none", "above 200-day", "VIX above 20-day avg", "2% stop")},
        "ETH above 50-day": {f: eth_leg(f) for f in ("none", "2% buffer", "2-day confirm")}}
def stats(u, a, z):
    u = u.loc[a:z]; e = u.cumsum(); mo = u.groupby(u.index.to_period("M")).sum(); yrs = len(mo) / 12
    return dict(per_year=u.sum() / yrs, dd=(e - e.cummax()).min(), losing_months_per_year=(mo < 0).sum() / yrs, sharpe=u.mean() / u.std() * np.sqrt(365) if u.std() > 0 else np.nan)
pick = {}
for leg, F in LEGS.items():
    print(f"== {leg} ==")
    base = stats(F["none"].loc["2014-10":], "2014-10", "2023")
    best, bs = "none", base["sharpe"]
    for f, u in F.items():
        a, o = stats(u, "2014-10", "2023"), stats(u, "2024", "2026")
        print(f"  {f:22s} 2014-23: ${a['per_year']:+6.0f}/yr drop {a['dd']:6.0f} losing months/yr {a['losing_months_per_year']:.1f} | 2024+: ${o['per_year']:+5.0f}/yr drop {o['dd']:5.0f} losing months/yr {o['losing_months_per_year']:.1f}")
        if f != "none" and a["sharpe"] > bs and a["per_year"] >= 0.8 * base["per_year"]: best, bs = f, a["sharpe"]
    pick[leg] = best; print("  picked:", best)
def combo(sel):
    return pd.concat([LEGS[l][sel[l]] for l in LEGS], axis=1).fillna(0).sum(axis=1)
before, after = combo({l: "none" for l in LEGS}), combo(pick)
print("\n== Plan A before vs after ==", pick)
for lab, u in (("before", before), ("after", after)):
    for a, z in (("2014-10", "2023"), ("2024", "2026")):
        s_ = stats(u, a, z); print(f"  {lab:6s} {a}-{z}: ${s_['per_year']:+.0f}/yr  drop {s_['dd']:.0f}  losing months/yr {s_['losing_months_per_year']:.1f}")
    y = u.loc["2015":].groupby(u.loc["2015":].index.year).sum(); print("   years:", {k: int(v) for k, v in y.items()})
