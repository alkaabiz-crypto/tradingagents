"""Batch 37, pre-registered 2026-11-28 (Hazza: Supertrend on its own). Supertrend(ATR n, mult m) as the only rule:
long while up (long-only) or long up / short down (L/S), flip at the close. Grid n 7/10/14 x m 2/3.
Daily: USTEC(QQQ) US500(SPY) US30(DIA) gold(GLD) BTC ETH; periods 2014-19 (ETH 2018-19), 2020-23, 2024-now.
PASS as Batch 35: Sharpe > 0.3 all three periods, t >= 2, 2x cost positive, 1-day delay positive, and beats 500 random-timing
shifts with BH-FDR q < 0.10 across this batch. $ = % return x today's min-lot exposure.
Hourly (Yahoo, 2024+ only, so no pre-2024 check possible): QQQ SPY GLD BTC; first vs second half."""
import numpy as np, pandas as pd
from math import erf, sqrt
def L(t): return pd.read_csv(f"data/{t}.csv", parse_dates=["Date"], index_col="Date").dropna().loc[:"2026-11-24"]
def sh(x, ann): x = x[~np.isnan(x)]; return x.mean() / x.std() * np.sqrt(ann) if len(x) > 30 and x.std() > 0 else np.nan
def atr(h, l, c, n): tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1); return tr.ewm(alpha=1/n, adjust=False).mean()
def st(h, l, c, n, m):
    a = atr(h, l, c, n).values; hl2 = ((h + l) / 2).values; cc = c.values; N = len(cc)
    ub = hl2 + m * a; lb = hl2 - m * a; fu, fl = ub.copy(), lb.copy(); up = np.zeros(N, bool); tr = True
    for i in range(1, N):
        fu[i] = ub[i] if (ub[i] < fu[i-1] or cc[i-1] > fu[i-1]) else fu[i-1]
        fl[i] = lb[i] if (lb[i] > fl[i-1] or cc[i-1] < fl[i-1]) else fl[i-1]
        if tr and cc[i] < fl[i]: tr = False
        elif not tr and cc[i] > fu[i]: tr = True
        up[i] = tr
    return up
MK = {"QQQ": (1.4, 1330, "USTEC"), "SPY": (1.6, 1000, "US500"), "DIA": (1.3, 500, "US30"), "GLD": (1.5, 4140, "gold 1oz"), "BTC-USD": (1.1, 600, "BTC"), "ETH-USD": (5, 170, "ETH")}
rng = np.random.default_rng(37); rows = []
for t, (bp, exp, nm) in MK.items():
    d = L(t); c = d.Close; r = c.pct_change().fillna(0).values; ix = c.index; ann = 365 if "-USD" in t else 252; s0 = "2018" if t == "ETH-USD" else "2014"
    per = [(ix >= s0) & (ix < "2020"), (ix >= "2020") & (ix < "2024"), ix >= "2024"]; post = ix >= s0
    for n in (7, 10, 14):
        for m in (2, 3):
            up = st(d.High, d.Low, c, n, m)
            for side in ("long", "L/S"):
                pos = np.where(up, 1.0, 0.0 if side == "long" else -1.0)
                def net(p, k=1): p1 = np.r_[0, p[:-1]]; return p1 * r - np.abs(np.diff(np.r_[0, p1])) * bp * k / 2e4
                x = net(pos); s = [sh(x[q], ann) for q in per]; S0 = sh(x[post], ann); tt = S0 * np.sqrt(post.sum() / ann)
                pp = pos[post]; rp = r[post]; nul = []
                for k in rng.integers(60, len(pp) - 60, 500):
                    q = np.roll(pp, k); q1 = np.r_[0, q[:-1]]; z = q1 * rp - np.abs(np.diff(np.r_[0, q1])) * bp / 2e4; nul.append(z.mean() / z.std() * np.sqrt(ann))
                nul = np.array(nul); z = (S0 - nul.mean()) / nul.std(); usd = x * exp
                def dd(u): e = np.cumsum(u); return (e - np.maximum.accumulate(e)).min()
                rows.append(dict(market=nm, n=n, m=m, side=side, s14=s[0], s20=s[1], s24=s[2], t=tt, delay=sh(net(np.r_[0, pos[:-1]])[post], ann), x2=net(pos, 2)[post].sum() > 0,
                                 z=z, p=0.5 * (1 - erf(z / sqrt(2))), usd_pre=usd[post & (ix < "2024")].sum(), dd_pre=dd(usd[post & (ix < "2024")]), usd24=usd[per[2]].sum(), dd24=dd(usd[per[2]]),
                                 trades_yr=np.abs(np.diff(pp)).sum() / 2 / (post.sum() / ann)))
df = pd.DataFrame(rows); N = len(df); sp = np.sort(df.p.values); ok = sp <= 0.10 * np.arange(1, N + 1) / N; cut = sp[np.where(ok)[0].max()] if ok.any() else -1
df["bar"] = df[["s14", "s20", "s24"]].gt(0.3).all(axis=1) & (df.t >= 2) & df.x2 & (df.delay > 0); df["beats_random"] = df.p <= cut; df["PASS"] = df.bar & df.beats_random
df.to_csv("lab/batch37_results.csv", index=False)
print("daily tests", N, "bar", int(df.bar.sum()), "beats random", int(df.beats_random.sum()), "PASS", int(df.PASS.sum()))
print(df.round(2).sort_values(["market", "side", "n", "m"]).to_string(index=False))
print("\n== Hourly 2024+ (no pre-2024 data) ==")
for f, bp, exp, nm in (("QQQ_1h", 1.4, 1330, "USTEC"), ("SPY_1h", 1.6, 1000, "US500"), ("GLD_1h", 1.5, 4140, "gold"), ("BTC-USD_1h", 1.1, 600, "BTC")):
    h = pd.read_csv(f"intraday/{f}.csv"); h.columns = [x.lower() for x in h.columns]; tcol = h.columns[0]; h.index = pd.to_datetime(h[tcol], utc=True); h = h[["open", "high", "low", "close"]].dropna()
    r = h.close.pct_change().fillna(0).values; half = len(h) // 2
    for n in (7, 10, 14):
        for m in (2, 3):
            up = st(h.high, h.low, h.close, n, m)
            for side in ("long", "L/S"):
                pos = np.where(up, 1.0, 0.0 if side == "long" else -1.0); p1 = np.r_[0, pos[:-1]]; x = (p1 * r - np.abs(np.diff(np.r_[0, p1])) * bp / 2e4) * exp
                e = np.cumsum(x)
                print(f"{nm:6s} ST({n},{m}) {side:4s}: 1st half ${x[:half].sum():+6.0f}  2nd half ${x[half:].sum():+6.0f}  total ${x.sum():+6.0f}  drop ${(e - np.maximum.accumulate(e)).min():6.0f}  trades {int(np.abs(np.diff(pos)).sum() / 2)}  from {h.index[0].date()}")
