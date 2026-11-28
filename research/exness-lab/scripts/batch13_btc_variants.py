"""Batch 13, pre-registered 2026-11-26 before running. Variants of BTC Williams weekdays (rule 1) and rule 2 (+12m momentum).
a) Hold winners: if the trade closes in profit, hold to the next day's close too.
b) Trade only when 20-day realised vol is above its 1-year median.   c) only when below it.
d) Trigger at open + 0.5 x ATR(14) instead of the prior day's range.
4 variants x 2 = 8 new trials (Batch total ~180 cumulative). 3 bp round trip + 2 bp stop slippage. PASS as before.
"""
import sys, numpy as np, pandas as pd
d = pd.read_csv(f"{sys.argv[1]}/BTC-USD.csv", parse_dates=["Date"], index_col="Date").dropna()
c, h, l, o = d.Close, d.High, d.Low, d.Open; cost = 3e-4
def sh(x): x = x.dropna(); return x.mean() / x.std() * np.sqrt(365) if len(x) > 30 and x.std() > 0 else np.nan
m = pd.Series(c.index.to_period("M"), index=c.index); me = m != m.shift(-1); wd = c.index.dayofweek < 5
mo = (pd.Series(np.where(me, (c / c.shift(365) - 1) > 0, np.nan), index=c.index).ffill().fillna(0) > 0).shift().fillna(False)
vol = c.pct_change().rolling(20).std(); hv = (vol > vol.rolling(365).median()).shift().fillna(False)
tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1); atr = tr.ewm(alpha=1/14, adjust=False).mean().shift()
def will(trig, mask, hold_win=False):
    hit = (h >= trig) & wd & mask; fill = np.maximum(trig, o) * (1 + 2e-4)
    r = pd.Series(np.where(hit, c / fill - 1 - cost, 0.0), index=c.index).fillna(0)
    if hold_win:
        nxt = (c.shift(-1) / c - 1).fillna(0); extra = ((r > 0) & hit).shift().fillna(False) & ~hit
        r = r - np.where(hit & (r > 0), -0.0, 0) ; r = r + np.where(extra, nxt.shift(), 0.0)
    return r
base = o + 0.5 * (h - l).shift(); T = pd.Series(True, index=c.index); bh = c.pct_change().fillna(0).loc["2014":]
V = {"base": (base, T, False), "a hold winners": (base, T, True), "b high vol only": (base, hv, False),
     "c low vol only": (base, ~hv, False), "d ATR trigger": (o + 0.5 * atr, T, False)}
print(f"| variant | filter | 2014-19 | 2020-23 | 2024-now | post-2014 | t | $ 2024-now at 0.01 lot | PASS |  (B&H post-2014 {sh(bh):.2f})")
for nm, (trig, mask, hw) in V.items():
    for fn, f in (("none", T), ("12m mom", mo)):
        x = will(trig, mask & f, hw); p = x.loc["2014":]
        s = [sh(x.loc["2014":"2019"]), sh(x.loc["2020":"2023"]), sh(x.loc["2024":])]; t = sh(p) * np.sqrt(len(p) / 365)
        usd = (x.loc["2024":] * 0.01 * c.loc["2024":]).sum()
        ok = all(v > .3 for v in s) and sh(p) > sh(bh) and t >= 2
        print(f"| {nm} | {fn} | " + " | ".join(f"{v:.2f}" for v in s) + f" | {sh(p):.2f} | {t:.1f} | {usd:.0f} | {ok} |")
