"""Batch 4, pre-registered 2026-11-26 before running. More famous daily rules, published defaults, swap-free costs.
1 Gap fade: open gaps down > 0.5% vs prior close -> buy the open, out at the close (day trade). Up gaps: sell.
2 Gap and go: the reverse of 1.
3 Inside-day breakout: after an inside day, buy-stop at its high / sell-stop at its low next day, out at the close
  (both touched = worse side).
4 Raschke Holy Grail: ADX(14) > 30 and +DI > -DI, low touches the 20-day EMA -> buy-stop at that day's high next day,
  hold until close < 20-day EMA.
5 Connors cumulative RSI: 2-day sum of RSI(2) < 35 and close > 200-day -> buy at the close; out when RSI(2) > 65.
Markets: US500, USTEC, US30, US2000, XAUUSD, XAGUSD, BTCUSD (BTC 10 bp). 5 x 7 = 35 trials (cumulative ~150).
PASS as famous2.
"""
import sys, numpy as np, pandas as pd
sys.path.insert(0, sys.argv[2]); import famous2_lib as F
D = sys.argv[1]
MK = {"SPY": 1.5, "QQQ": 1.5, "DIA": 2.0, "IWM": 3.0, "GLD": 1.0, "SLV": 6.0, "BTC-USD": 10.0}
def sh(x, ann): x = x.dropna(); return x.mean() / x.std() * np.sqrt(ann) if len(x) > 30 and x.std() > 0 else np.nan
rows = []
for t, bp in MK.items():
    d = pd.read_csv(f"{D}/{t}.csv", parse_dates=["Date"], index_col="Date").dropna(); ann = 365 if t == "BTC-USD" else 252
    c, h, l, o = d.Close, d.High, d.Low, d.Open; pc = c.shift(); cost = bp / 1e4; slip = 2e-4
    gap = o / pc - 1; oc = c / o - 1
    S = {}
    S["Gap fade (0.5%)"] = pd.Series(np.where(gap < -0.005, oc - cost, np.where(gap > 0.005, -oc - cost, 0.0)), index=c.index)
    S["Gap and go (0.5%)"] = pd.Series(np.where(gap > 0.005, oc - cost, np.where(gap < -0.005, -oc - cost, 0.0)), index=c.index)
    inside = ((h < h.shift()) & (l > l.shift())).shift().fillna(False).astype(bool)
    ph, pl = h.shift(), l.shift(); up = inside & (h > ph); dn = inside & (l < pl)
    lr = c / np.maximum(ph, o) * (1 - slip) - 1 - cost; sr = np.minimum(pl, o) / c * (1 - slip) - 1 - cost
    S["Inside-day breakout"] = pd.Series(np.where(up & dn, np.minimum(lr, sr), np.where(up, lr, np.where(dn, sr, 0.0))), index=c.index)
    # ADX
    upm, dnm = h.diff(), -l.diff()
    pdm = np.where((upm > dnm) & (upm > 0), upm, 0.0); ndm = np.where((dnm > upm) & (dnm > 0), dnm, 0.0)
    tr = pd.concat([h - l, (h - pc).abs(), (l - pc).abs()], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1 / 14, adjust=False).mean()
    pdi = 100 * pd.Series(pdm, index=c.index).ewm(alpha=1 / 14, adjust=False).mean() / atr
    ndi = 100 * pd.Series(ndm, index=c.index).ewm(alpha=1 / 14, adjust=False).mean() / atr
    adx = (100 * (pdi - ndi).abs() / (pdi + ndi)).ewm(alpha=1 / 14, adjust=False).mean()
    e20 = c.ewm(span=20, adjust=False).mean()
    setup = (adx > 30) & (pdi > ndi) & (l <= e20)
    pos, out, entry_lvl, ret = 0, [], np.nan, []
    for i in range(len(c)):
        r = 0.0
        if pos == 0 and i > 0 and setup.iloc[i - 1] and h.iloc[i] >= h.iloc[i - 1]:
            fill = max(h.iloc[i - 1], o.iloc[i]) * (1 + slip); r = c.iloc[i] / fill - 1 - cost / 2; pos = 1
        elif pos == 1:
            r = c.iloc[i] / c.iloc[i - 1] - 1
            if c.iloc[i] < e20.iloc[i]: r -= cost / 2; pos = 0
        ret.append(r)
    S["Raschke Holy Grail"] = pd.Series(ret, index=c.index)
    r2 = F.rsi(c, 2); cum = r2 + r2.shift()
    p = F.hold_until((cum < 35) & (c > c.rolling(200).mean()), r2 > 65)
    S["Connors cumulative RSI(2)"] = p.shift().fillna(0) * c.pct_change().fillna(0) - p.diff().abs().fillna(0).shift().fillna(0) * cost / 2
    bh = c.pct_change().fillna(0)
    for nm, x in S.items():
        x = x.fillna(0)
        res = dict(strategy=nm, market=t, oos=sh(x.loc["2014":"2019"], ann), ho=sh(x.loc["2020":"2023"], ann),
                   recent=sh(x.loc["2024":], ann), post14=sh(x.loc["2014":], ann), bh=sh(bh.loc["2014":], ann),
                   t=sh(x.loc["2014":], ann) * np.sqrt(len(x.loc["2014":]) / ann),
                   usd300_recent=300 * ((1 + x.loc["2024":]).prod() - 1))
        res["PASS"] = res["oos"] > 0.3 and res["ho"] > 0.3 and res["recent"] > 0.3 and res["post14"] > res["bh"] and res["t"] >= 2
        rows.append(res)
df = pd.DataFrame(rows); df.to_csv(sys.argv[3], index=False)
print("passes:", int(df.PASS.sum()), "of", len(df))
print(df[df.PASS].round(2).to_string())
print(df.groupby("strategy").agg(passes=("PASS", "sum"), med_post14=("post14", "median"), med_recent=("recent", "median"), med_usd=("usd300_recent", "median")).round(2).to_string())
