"""Batch 32, pre-registered 2026-11-27 before running. More documented effects.
 C1 Options-expiration week (Stivers & Sun 2013 'OPEX'): hold Monday open..Friday close of the week with the 3rd Friday
    (implemented close-to-close: from the prior Friday's close to the 3rd Friday's close).
 C2 Down-Friday -> Monday (weekend reversal, Lakonishok & Maberly 1990 variant): if Friday closes down, buy the Friday close,
    sell Monday's close.
 C3 Connors R3: RSI(2) falls 3 days in a row, the first reading < 60 and the last < 10, above the 200-day; exit RSI(2) > 70.
 C4 VIX regime: hold while VIX closed below 20 the previous day (Whaley; low-vol regime).
 C5 Overnight hold (close -> next open) above the 200-day on gold, silver, oil (index version is the USTEC/US500 plan).
 C6 Day session only (open -> close) on gold, silver, oil.
Markets C1-C4: SPY QQQ DIA IWM GLD. 5 x 4... = 4x5 + 2x3 = 26 trials. PASS as Batch 31 (2x cost positive, t >= 2,
Sharpe > 0.3 in 2014-19 / 2020-23 / 2024-now), plus post-2014 Sharpe above buy-and-hold for always-in-style rules (C4).
"""
import numpy as np, pandas as pd
MK = {"SPY": 1.6, "QQQ": 1.4, "DIA": 1.3, "IWM": 3.0, "GLD": 1.5, "SLV": 4.4, "USO": 4.0}
def sh(x, ann=252): x = x.dropna(); return x.mean() / x.std() * np.sqrt(ann) if len(x) > 30 and x.std() > 0 else np.nan
def L(t): return pd.read_csv(f"data/{t}.csv", parse_dates=["Date"], index_col="Date").dropna().loc[:"2026-11-24"]
def rsi(c, n):
    d = c.diff(); u = d.clip(lower=0).ewm(alpha=1/n, adjust=False).mean(); v = (-d.clip(upper=0)).ewm(alpha=1/n, adjust=False).mean(); return 100 - 100 / (1 + u / v)
vix = L("VIX").Close; rows = []
def add(nm, t, x, x2, bh=None, cmp=False):
    p = [sh(x.loc["2014":"2019"]), sh(x.loc["2020":"2023"]), sh(x.loc["2024":])]; post = x.loc["2014":]; tt = sh(post) * np.sqrt(len(post) / 252)
    ok = all(z > 0.3 for z in p) and tt >= 2 and x2.loc["2014":].sum() > 0 and (not cmp or sh(post) > bh)
    rows.append(dict(rule=nm, market=t, s14=p[0], s20=p[1], s24=p[2], t=tt, bh=bh, pct24=x.loc["2024":].sum(), PASS=ok))
for t in ("SPY", "QQQ", "DIA", "IWM", "GLD"):
    d = L(t); c = d.Close; r = c.pct_change().fillna(0); bp = MK[t]; bh = sh(r.loc["2014":])
    def net(pos, m=1): p = pos.astype(float); return p * r - p.diff().abs().fillna(0) * bp * m / 2e4   # pos[i]=1: hold over day i
    idx = c.index; dom = pd.Series(idx.day, index=idx); fri = pd.Series(idx.dayofweek == 4, index=idx)
    third_fri = fri & (dom >= 15) & (dom <= 21); wk = pd.Series(idx.to_period("W"), index=idx)
    opex_weeks = set(wk[third_fri]); hold = wk.isin(opex_weeks)
    add("C1 OPEX week", t, net(hold), net(hold, 2))
    down_fri = fri & (r < 0); mon = pd.Series(idx.dayofweek == 0, index=idx); h2 = mon & down_fri.shift().fillna(False)
    add("C2 down Friday -> Monday", t, net(h2), net(h2, 2))
    r2 = rsi(c, 2); s200 = c > c.rolling(200).mean(); ent = (r2 < r2.shift()) & (r2.shift() < r2.shift(2)) & (r2.shift(2) < r2.shift(3)) & (r2.shift(2) < 60) & (r2 < 10) & s200
    pos, out = 0, []
    for e, x_ in zip(ent.values, (r2 > 70).values):
        out.append(pos)
        if pos == 0 and e: pos = 1
        elif pos == 1 and x_: pos = 0
    add("C3 Connors R3", t, net(pd.Series(out, index=idx)), net(pd.Series(out, index=idx), 2))
    v = vix.reindex(idx).ffill(); add("C4 VIX < 20 regime", t, net((v.shift() < 20)), net((v.shift() < 20), 2), bh, True)
for t in ("GLD", "SLV", "USO"):
    d = L(t); c, o = d.Close, d.Open; bp = MK[t]; s200 = (c > c.rolling(200).mean()).shift().fillna(False)
    on = (o / c.shift() - 1).where(s200, 0).fillna(0); add("C5 overnight above 200-day", t, on - s200 * bp / 1e4, on - s200 * 2 * bp / 1e4)
    day = (c / o - 1).fillna(0); add("C6 day session only", t, day - bp / 1e4, day - 2 * bp / 1e4)
df = pd.DataFrame(rows); df.to_csv("lab/batch32_results.csv", index=False); print("passes:", int(df.PASS.sum()), "of", len(df)); print(df.round(2).to_string(index=False))
