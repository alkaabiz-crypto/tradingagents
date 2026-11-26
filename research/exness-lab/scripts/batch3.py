"""Batch 3, pre-registered 2026-11-26 before running. Swap-free Exness costs (costs.py estimates; BTC at 10 bp).
A) BTC Williams breakout deep check (k = 0.5 fixed): long only vs long+short (sell-stop at open - 0.5 x range;
   both touched = worse side); weekdays vs weekends; Sharpe by 2-year block; with a 200-day filter (longs only
   above it). New trials: 3 (short side, weekend split is descriptive, 200-day filter).
B) IBS (0.2/0.8) x volatility target (15%, 20-day) on US500, USTEC, US30, XAUUSD, close fill and next-open fill.
C) Halloween / sell in May: long Nov-Apr, flat May-Oct, on US500, USTEC, US30, US2000, XAUUSD, BTC.
D) BTC day-of-week: long open->close only on the weekday with the best 2014-2019 mean, tested 2020-now.
PASS bar as famous2 (Sharpe > 0.3 in 2014-19, 2020-23, 2024-now; beats buy-and-hold Sharpe post-2014).
"""
import sys, numpy as np, pandas as pd
sys.path.insert(0, sys.argv[2]); import famous2_lib as F
D = sys.argv[1]
def load(t): return pd.read_csv(f"{D}/{t}.csv", parse_dates=["Date"], index_col="Date").dropna()
def sh(x, ann): x = x.dropna(); return x.mean() / x.std() * np.sqrt(ann) if len(x) > 30 and x.std() > 0 else np.nan
def per(x, ann): return " / ".join(f"{sh(x.loc[a:b], ann):.2f}" for a, b in (("2014", "2019"), ("2020", "2023"), ("2024", "2026-11-25")))

print("## A) BTC Williams breakout, k=0.5, 10 bp + 2 bp slip")
d = load("BTC-USD"); c, h, l, o = d.Close, d.High, d.Low, d.Open; R = (h - l).shift(); bp = 10
up_t, dn_t = o + 0.5 * R, o - 0.5 * R
up, dn = h >= up_t, l <= dn_t
lr = c / np.maximum(up_t, o) * (1 - 2e-4) - 1 - bp / 1e4
sr = np.minimum(dn_t, o) / c * (1 - 2e-4) - 1 - bp / 1e4
long_only = pd.Series(np.where(up, lr, 0.0), index=c.index).fillna(0)
both = pd.Series(np.where(up & dn, np.minimum(lr, sr), np.where(up, lr, np.where(dn, sr, 0.0))), index=c.index).fillna(0)
s200 = c.rolling(200).mean().shift()
filt = pd.Series(np.where(up & (o > s200), lr, 0.0), index=c.index).fillna(0)
print(f"- long only: Sharpe 2014-19 / 20-23 / 24-now = {per(long_only, 365)}")
print(f"- long + short: {per(both, 365)}")
print(f"- long only above 200-day: {per(filt, 365)}")
wk = long_only.index.dayofweek >= 5
print(f"- weekdays only: {per(long_only.where(~wk, 0), 365)}; weekends only: {per(long_only.where(wk, 0), 365)}")
blocks = {f"{y}-{y+1}": round(sh(long_only.loc[str(y):str(y + 1)], 365), 2) for y in range(2014, 2026, 2)}
print(f"- Sharpe by 2-year block: {blocks}")

print("\n## B) IBS x volatility target (swap-free)")
MK = {"SPY": 1.5, "QQQ": 1.5, "DIA": 2.0, "GLD": 1.0}
print("| market | IBS | vol target | IBS x vol target | buy&hold | IBS x VT next-open | worst drop IBS x VT | B&H worst drop |")
for t, b in MK.items():
    d = load(t); c = d.Close
    ibs = (c - d.Low) / (d.High - d.Low).replace(0, np.nan)
    pi = F.hold_until(ibs < 0.2, ibs > 0.8)
    vt = (0.15 / (c.pct_change().rolling(20).std() * np.sqrt(252))).clip(upper=1.0).fillna(0)
    def net(pos, nxt=False):
        r = (d.Open.shift(-1) / d.Open - 1) if nxt else c.pct_change()
        p = pos.shift().fillna(0); turn = pos.diff().abs().fillna(0).shift().fillna(0)
        return (p * r - turn * b / 2 / 1e4).fillna(0).loc["2014":]
    dd = lambda x: ((1 + x).cumprod() / (1 + x).cumprod().cummax() - 1).min()
    combo = net(pi * vt)
    print(f"| {t} | {sh(net(pi),252):.2f} | {sh(net(vt),252):.2f} | {sh(combo,252):.2f} ({per(combo,252)}) | {sh(net(pd.Series(1.0,index=c.index)),252):.2f} | {sh(net(pi*vt,True),252):.2f} | {dd(combo):.0%} | {dd(net(pd.Series(1.0,index=c.index))):.0%} |")

print("\n## C) Halloween (long Nov-Apr only)")
for t, b in {"SPY": 1.5, "QQQ": 1.5, "DIA": 2.0, "IWM": 3.0, "GLD": 1.0, "BTC-USD": 10}.items():
    d = load(t); c = d.Close; ann = 365 if t == "BTC-USD" else 252
    pos = pd.Series(np.isin(c.index.month, [11, 12, 1, 2, 3, 4]).astype(float), index=c.index)
    r = c.pct_change(); n = (pos.shift().fillna(0) * r - pos.diff().abs().fillna(0).shift().fillna(0) * b / 2e4).fillna(0)
    print(f"- {t}: Sharpe {per(n, ann)}; post-2014 {sh(n.loc['2014':], ann):.2f} vs hold {sh(r.loc['2014':], ann):.2f}")

print("\n## D) BTC best weekday (picked on 2014-2019)")
d = load("BTC-USD"); oc = d.Close / d.Open - 1 - 10 / 1e4
m = oc.loc["2014":"2019"].groupby(oc.loc["2014":"2019"].index.dayofweek).mean()
best = int(m.idxmax()); x = oc.where(oc.index.dayofweek == best, 0)
print(f"- weekday {best} (0=Mon) means 2014-19 bp: {(m*1e4).round(0).to_dict()}; 2020-23 Sharpe {sh(x.loc['2020':'2023'],365):.2f}, 2024-now {sh(x.loc['2024':],365):.2f}")
