"""Batch 31, pre-registered 2026-11-27 before running. Academic anomalies (published, default parameters).
 A1 Time-series momentum 1 month (Moskowitz, Ooi & Pedersen 2012): long if the past 21-day return > 0 else short, monthly.
 A2 TSMOM 3 months   A3 TSMOM 6 months   (A1-A3 also on FX: close-only rules are safe with Yahoo FX closes)
 A4 Pre-holiday effect (Ariel 1990; Lakonishok & Smidt 1988): hold only the trading day before a US market holiday
    (holidays = weekdays with no SPY bar). Indices, gold.
 A5 52-week-high proximity (George & Hwang 2004, applied in time series): long while the close is within 5% of its 252-day
    high, else flat (checked daily).
 A6 Dual momentum (Antonacci 2014), monthly: hold US500 if its 12-month return beats gold's and is > 0; else gold if
    gold's 12-month return > 0; else flat. One portfolio = one trial.
 A7 Short-term reversal on 1-week returns long/short (Lehmann 1990): weekly, long if last week's return < 0, short if > 0.
 A8 Halloween + 200-day (Bouman & Jacobsen 2002 + trend): long Nov-Apr only when above the 200-day.
Markets: SPY QQQ DIA IWM GLD SLV USO BTC ETH + EURUSD GBPUSD USDJPY AUDUSD (A1-A3, A5, A7 only, close-based).
FX round trip 1.5-2 bp. PASS as Batch 30 (incl. 2x cost), no next-open check for monthly/weekly rules (1-day delay applied
instead: positions use information up to the prior close).
"""
import numpy as np, pandas as pd
MK = {"SPY": 1.6, "QQQ": 1.4, "DIA": 1.3, "IWM": 3.0, "GLD": 1.5, "SLV": 4.4, "USO": 4.0, "BTC-USD": 3.0, "ETH-USD": 5.0,
      "EURUSD": 1.5, "GBPUSD": 2.0, "USDJPY": 1.5, "AUDUSD": 2.0}
FX = {"EURUSD", "GBPUSD", "USDJPY", "AUDUSD"}
def sh(x, ann): x = x.dropna(); return x.mean() / x.std() * np.sqrt(ann) if len(x) > 30 and x.std() > 0 else np.nan
def L(t): return pd.read_csv(f"data/{t}.csv", parse_dates=["Date"], index_col="Date").dropna().loc[:"2026-11-24"]
spy = L("SPY"); bd = pd.bdate_range(spy.index[0], spy.index[-1]); hol = bd.difference(spy.index)
pre_hol = pd.Series(False, index=spy.index)
for hday in hol:
    prev = spy.index[spy.index < hday]
    if len(prev): pre_hol[prev[-1]] = True
def net(c, pos, bp):
    p = pos.shift().fillna(0)  # decided at close t-1
    return p * c.pct_change().fillna(0) - p.diff().abs().fillna(0) * bp / 2e4
rows = []; res = {}
for t, bp in MK.items():
    d = L(t); c = d.Close; ann = 365 if "-USD" in t else (260 if t in FX else 252)
    m = pd.Series(c.index.to_period("M"), index=c.index); me = m != m.shift(-1)
    wk = pd.Series(c.index.to_period("W"), index=c.index); we = wk != wk.shift(-1)
    S = {}
    for nm, n in (("A1 TSMOM 1m", 21), ("A2 TSMOM 3m", 63), ("A3 TSMOM 6m", 126)):
        nn = int(n * 365 / 252) if ann == 365 else n
        S[nm] = pd.Series(np.where(me, np.sign(c / c.shift(nn) - 1), np.nan), index=c.index).ffill().fillna(0)
    hi = c.rolling(365 if ann == 365 else 252).max(); S["A5 near 52-week high"] = (c >= 0.95 * hi).astype(float)
    S["A7 weekly reversal L/S"] = pd.Series(np.where(we, -np.sign(c / c.shift(5 if ann != 365 else 7) - 1), np.nan), index=c.index).ffill().fillna(0)
    if t not in FX:
        if ann == 252: S["A4 pre-holiday"] = pre_hol.reindex(c.index).fillna(False).shift(-1).fillna(False).astype(float)  # hold over the pre-holiday session
        s200 = c > c.rolling(200).mean(); S["A8 Halloween + 200-day"] = (pd.Series(np.isin(c.index.month, [11, 12, 1, 2, 3, 4]), index=c.index) & s200).astype(float)
    for nm, pos in S.items():
        x = net(c, pos, bp); x2 = net(c, pos, 2 * bp); st = "2018" if t == "ETH-USD" else "2014"
        p = [sh(x.loc[st:"2019"], ann), sh(x.loc["2020":"2023"], ann), sh(x.loc["2024":], ann)]; post = x.loc["2014":]; tt = sh(post, ann) * np.sqrt(len(post) / ann)
        bh = sh(c.pct_change().loc["2014":], ann)
        rows.append(dict(rule=nm, market=t, s14=p[0], s20=p[1], s24=p[2], t=tt, bh=bh, exposure=pos.abs().loc["2014":].mean(), pct24=x.loc["2024":].sum(),
                         PASS=all(z > 0.3 for z in p) and tt >= 2 and x2.loc["2014":].sum() > 0))
# A6 dual momentum
s, g = L("SPY").Close, L("GLD").Close; ix = s.index.intersection(g.index); s, g = s[ix], g[ix]
m = pd.Series(ix.to_period("M"), index=ix); me = m != m.shift(-1); rs, rg = s / s.shift(252) - 1, g / g.shift(252) - 1
ch = pd.Series(np.where(me, np.where((rs > rg) & (rs > 0), 1, np.where(rg > 0, 2, 0)), np.nan), index=ix).ffill().fillna(0).shift()
x = np.where(ch == 1, s.pct_change(), np.where(ch == 2, g.pct_change(), 0.0)); x = pd.Series(x, index=ix).fillna(0) - (ch.diff().abs() > 0) * 1.6e-4
p = [sh(x.loc["2014":"2019"], 252), sh(x.loc["2020":"2023"], 252), sh(x.loc["2024":], 252)]; tt = sh(x.loc["2014":], 252) * np.sqrt(len(x.loc["2014":]) / 252)
rows.append(dict(rule="A6 dual momentum US500/gold", market="SPY+GLD", s14=p[0], s20=p[1], s24=p[2], t=tt, bh=sh(s.pct_change().loc["2014":], 252), exposure=(ch > 0).mean(), pct24=x.loc["2024":].sum(), PASS=all(z > 0.3 for z in p) and tt >= 2))
df = pd.DataFrame(rows); df.to_csv("lab/batch31_results.csv", index=False)
print("passes:", int(df.PASS.sum()), "of", len(df)); print(df[df.PASS].round(2).to_string(index=False))
print(df.pivot_table(index="rule", columns="market", values="s24").round(2).to_string())
