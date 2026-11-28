"""Robustness of the famous2 PASS candidates. Pre-registered 2026-11-26 after famous2 and before this run.
1) Fill one bar later: positions decided at close t earn open(t+1) -> open(t+2) (no close fill needed).
2) Neighbour grids around the published parameters; a candidate needs >= 70% of neighbours with post-2014 Sharpe
   above buy-and-hold (swap-free costs).
3) Block bootstrap (20-day blocks, 1000 draws, seed 7) of post-2014 Sharpe(strategy) - Sharpe(buy and hold).
4) BTC at 10 bp round trip (Exness BTC spread unverified) and 2 bp extra slippage on breakout stop entries.
"""
import sys, numpy as np, pandas as pd
sys.path.insert(0, sys.argv[2]); import famous2_lib as F
D = sys.argv[1]
rng = np.random.default_rng(7)


def load(t): return pd.read_csv(f"{D}/{t}.csv", parse_dates=["Date"], index_col="Date").dropna()


def net_pos(d, pos, bp, next_open=False):
    if next_open:
        r = (d.Open.shift(-1) / d.Open - 1)  # open t -> open t+1
        p = pos.shift(1).fillna(0)          # decided at close t-1, entered open t
    else:
        r = d.Close.pct_change(); p = pos.shift().fillna(0)
    turn = pos.diff().abs().fillna(0).shift(1 if not next_open else 1).fillna(0)
    return (p * r - turn * bp / 2 / 1e4).fillna(0)


def sh(x, ann): return x.mean() / x.std() * np.sqrt(ann) if x.std() > 0 else np.nan


def boot_diff(a, b, ann, n=1000, blk=20):
    a, b = a.values, b.values; L = len(a); out = []
    for _ in range(n):
        idx = np.concatenate([np.arange(s, s + blk) % L for s in rng.integers(0, L, L // blk + 1)])[:L]
        out.append(sh(pd.Series(a[idx]), ann) - sh(pd.Series(b[idx]), ann))
    out = np.array(out); return np.mean(out <= 0)


def ibs_pos(d, e, x):
    ibs = (d.Close - d.Low) / (d.High - d.Low).replace(0, np.nan)
    return F.hold_until(ibs < e, ibs > x)


def vt_pos(d, tgt, win):
    vol = d.Close.pct_change().rolling(win).std() * np.sqrt(252)
    return (tgt / vol).clip(upper=1.0).fillna(0)


MK = {"SPY": 1.5, "QQQ": 1.5, "DIA": 2.0, "IWM": 3.0, "GLD": 1.0, "SLV": 6.0, "BTC-USD": 3.0}
print("## IBS")
print("| market | close fill Sharpe | next-open fill Sharpe | buy&hold Sharpe | neighbours beating B&H | bootstrap p (close fill) | RECENT Sharpe next-open |")
for t, bp in MK.items():
    d = load(t); ann = 365 if t == "BTC-USD" else 252
    bh = net_pos(d, pd.Series(1.0, index=d.index), bp).loc["2014":]
    base = net_pos(d, ibs_pos(d, 0.2, 0.8), bp).loc["2014":]
    nxt = net_pos(d, ibs_pos(d, 0.2, 0.8), bp, True)
    nb = [sh(net_pos(d, ibs_pos(d, e, x), bp).loc["2014":], ann) > sh(bh, ann) for e in (0.1, 0.15, 0.2, 0.25, 0.3) for x in (0.7, 0.8, 0.9)]
    print(f"| {t} | {sh(base, ann):.2f} | {sh(nxt.loc['2014':], ann):.2f} | {sh(bh, ann):.2f} | {np.mean(nb):.0%} | {boot_diff(base, bh, ann):.3f} | {sh(nxt.loc['2024':], ann):.2f} |")
print("## Vol-targeted hold")
print("| market | Sharpe | B&H | neighbours beating B&H | bootstrap p | worst drop | B&H worst drop |")
for t, bp in MK.items():
    d = load(t); ann = 365 if t == "BTC-USD" else 252
    bh = net_pos(d, pd.Series(1.0, index=d.index), bp).loc["2014":]
    base = net_pos(d, vt_pos(d, 0.15, 20), bp).loc["2014":]
    nb = [sh(net_pos(d, vt_pos(d, g, w), bp).loc["2014":], ann) > sh(bh, ann) for g in (0.10, 0.15, 0.20) for w in (20, 60)]
    dd = lambda x: ((1 + x).cumprod() / (1 + x).cumprod().cummax() - 1).min()
    print(f"| {t} | {sh(base, ann):.2f} | {sh(bh, ann):.2f} | {np.mean(nb):.0%} | {boot_diff(base, bh, ann):.3f} | {dd(base):.0%} | {dd(bh):.0%} |")
print("## BTC trend/breakout at 10 bp round trip (+2 bp breakout slippage)")
d = load("BTC-USD"); ann = 365; bp = 10
bh = net_pos(d, pd.Series(1.0, index=d.index), bp).loc["2014":]
P = F.strategies(d)
for nm in ("MACD 12/26/9 above signal, long only", "12-month time-series momentum, monthly, long/flat", "Faber 10-month average, monthly"):
    x = net_pos(d, P[nm][1], bp).loc["2014":]; y = net_pos(d, P[nm][1], bp, True)
    print(f"- {nm}: Sharpe {sh(x, ann):.2f} (next-open {sh(y.loc['2014':], ann):.2f}) vs B&H {sh(bh, ann):.2f}; RECENT {sh(x.loc['2024':], ann):.2f}; bootstrap p {boot_diff(x, bh, ann):.3f}")
c, h, l, o = d.Close, d.High, d.Low, d.Open
for k in (0.3, 0.4, 0.5, 0.6, 0.7, 0.8):
    trig = o + k * (h - l).shift(); hit = h >= trig
    g = pd.Series(np.where(hit, c / np.maximum(trig, o) * (1 - 2e-4) - 1, 0.0), index=c.index).fillna(0) - hit * bp / 1e4
    print(f"- Williams k={k}: Sharpe post-2014 {sh(g.loc['2014':], ann):.2f}, 2014-19 {sh(g.loc['2014':'2019'], ann):.2f}, 2020-23 {sh(g.loc['2020':'2023'], ann):.2f}, RECENT {sh(g.loc['2024':], ann):.2f}, trades/yr {hit.loc['2014':].mean()*365:.0f}")
