"""Batch 26, pre-registered 2026-11-26 before running. More breakout theories as one-day trades on daily bars,
7 markets, 2014-now. Two-sided rules: buy-stop at the upper level / sell-stop at the lower level, the other level is the
stop, exit at the close; if both trade in one day -> worst case (full loss of the level distance). One-sided rules exit at
the close. Costs round-trip bp as before + 2 bp stop slippage. 12 rules x 7 markets = 84 trials (cumulative ~600).
 B1 NR4 breakout (BTC lead, now on every market)       B2 NR7 breakout             B3 NR4 + inside day (Crabel NR4ID)
 B4 Prior 2-day high/low breakout                      B5 Prior-week high/low breakout (levels fixed each week)
 B6 Donchian 20-day high/low breakout (day trade)      B7 Bollinger squeeze: bandwidth(20,2) lowest of 120 days ->
    break of yesterday's high/low                      B8 Keltner (20-EMA +/- 1.5 ATR) breakout
 B9 Three narrow days (each range < 0.75 ATR) -> break of the 3-day range
 B10 Monthly-open breakout: open of the month +/- 0.5 ATR  B11 Range expansion: yesterday's range > 1.5 ATR -> break of
    yesterday's high/low in its close direction only   B12 NR4 long only (BTC long side, for markets that trend up)
PASS: Sharpe > 0.3 in 2014-19, 2020-23 and 2024-now, post-2014 t >= 2, beats 0 at 2x cost.
"""
import numpy as np, pandas as pd
MK = {"SPY": 1.6, "QQQ": 1.4, "DIA": 1.3, "IWM": 3.0, "GLD": 1.5, "SLV": 4.4, "BTC-USD": 3.0}
def sh(x, ann): x = x.dropna(); return x.mean() / x.std() * np.sqrt(ann) if len(x) > 30 and x.std() > 0 else np.nan
def two(o, h, l, c, U, D, act, slip=2e-4):
    up, dn = act & (h >= U), act & (l <= D); eL, eS = np.maximum(U, o) * (1 + slip), np.minimum(D, o) * (1 - slip)
    r = np.where(up & dn, np.minimum(D / eL - 1, eS / U - 1), np.where(up, c / eL - 1, np.where(dn, eS / c - 1, 0.0)))
    return pd.Series(np.nan_to_num(r), index=c.index), (up | dn)
def one(o, h, l, c, lvl, side, act, slip=2e-4):
    if side > 0: hit = act & (h >= lvl); e = np.maximum(lvl, o) * (1 + slip); r = np.where(hit, c / e - 1, 0.0)
    else: hit = act & (l <= lvl); e = np.minimum(lvl, o) * (1 - slip); r = np.where(hit, e / c - 1, 0.0)
    return pd.Series(np.nan_to_num(r), index=c.index), hit
rows = []
for t, bp in MK.items():
    d = pd.read_csv(f"data/{t}.csv", parse_dates=["Date"], index_col="Date").dropna(); ann = 365 if t == "BTC-USD" else 252
    o, h, l, c = d.Open, d.High, d.Low, d.Close; ph, pl = h.shift(), l.shift(); rg = h - l
    tr = pd.concat([rg, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1); atr = tr.ewm(alpha=1/14, adjust=False).mean().shift()
    T = pd.Series(True, index=c.index); S = {}
    nr4 = (rg <= rg.rolling(4).min()).shift().fillna(False); nr7 = (rg <= rg.rolling(7).min()).shift().fillna(False)
    ins = ((h < h.shift()) & (l > l.shift())).shift().fillna(False)
    S["B1 NR4"] = two(o, h, l, c, ph, pl, nr4); S["B2 NR7"] = two(o, h, l, c, ph, pl, nr7); S["B3 NR4 + inside day"] = two(o, h, l, c, ph, pl, nr4 & ins)
    S["B4 2-day range"] = two(o, h, l, c, h.rolling(2).max().shift(), l.rolling(2).min().shift(), T)
    wk = pd.Series(c.index.to_period("W"), index=c.index); wh = h.groupby(wk).max(); wl = l.groupby(wk).min()
    pw = wk.map(lambda p: p - 1); S["B5 prior-week range"] = two(o, h, l, c, pw.map(wh).astype(float), pw.map(wl).astype(float), T)
    S["B6 Donchian 20 day-trade"] = two(o, h, l, c, h.rolling(20).max().shift(), l.rolling(20).min().shift(), T)
    m20, sd = c.rolling(20).mean(), c.rolling(20).std(); bw = (4 * sd / m20); sq = (bw <= bw.rolling(120).min()).shift().fillna(False)
    S["B7 Bollinger squeeze"] = two(o, h, l, c, ph, pl, sq)
    e20 = c.ewm(span=20, adjust=False).mean().shift(); S["B8 Keltner 1.5 ATR"] = two(o, h, l, c, e20 + 1.5 * atr, e20 - 1.5 * atr, T)
    narrow = (rg < 0.75 * tr.ewm(alpha=1/14, adjust=False).mean()); n3 = (narrow & narrow.shift() & narrow.shift(2)).shift().fillna(False)
    S["B9 three narrow days"] = two(o, h, l, c, h.rolling(3).max().shift(), l.rolling(3).min().shift(), n3)
    mo = pd.Series(c.index.to_period("M"), index=c.index); mopen = mo.map(o.groupby(mo).first()).astype(float)
    S["B10 monthly-open +/- 0.5 ATR"] = two(o, h, l, c, mopen + 0.5 * atr, mopen - 0.5 * atr, T)
    big = (rg > 1.5 * tr.ewm(alpha=1/14, adjust=False).mean()).shift().fillna(False); upc = (c > o).shift().fillna(False)
    a1, h1 = one(o, h, l, c, ph, 1, big & upc); a2, h2 = one(o, h, l, c, pl, -1, big & ~upc); S["B11 range expansion follow"] = (a1 + a2, h1 | h2)
    S["B12 NR4 long only"] = one(o, h, l, c, ph, 1, nr4)
    for nm, (r, hit) in S.items():
        for mult in (1, 2):
            x = (r - hit * bp * mult / 1e4).fillna(0)
            if mult == 1:
                p = [sh(x.loc[a:b], ann) for a, b in (("2014", "2019"), ("2020", "2023"), ("2024", "2026"))]; post = x.loc["2014":]
                tt = sh(post, ann) * np.sqrt(len(post) / ann); rec = dict(rule=nm, market=t, s14=p[0], s20=p[1], s24=p[2], t=tt, trades_yr=hit.loc["2014":].mean() * ann)
            else: rec["post_2x"] = x.loc["2014":].sum(); rec["PASS"] = all(v > 0.3 for v in p) and tt >= 2 and rec["post_2x"] > 0
        rows.append(rec)
df = pd.DataFrame(rows); df.to_csv("lab/batch26_results.csv", index=False)
print("passes:", int(df.PASS.sum()), "of", len(df)); print(df[df.PASS].round(2).to_string(index=False))
print(df.pivot(index="rule", columns="market", values="s24").round(2).to_string())
