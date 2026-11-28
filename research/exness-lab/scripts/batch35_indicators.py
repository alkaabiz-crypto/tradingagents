"""Batch 35, pre-registered 2026-11-27 before running. Broad indicator and candle sweep, textbook settings only, no tuning.
Signals are computed at the close of day t; the position earns day t+1 (close-to-close). Costs as before.
Oscillators (enter / exit):
 O1 RSI(14)<30 / >50   O2 RSI(14)>50 trend   O3 Stoch(14,3) %K crosses above %D below 20 / %K>80   O4 CCI(20)<-100 / >0
 O5 CCI(20)>100 / <0 (trend)   O6 MFI(14)<20 / >50   O7 %R(14)<-80 / >-20   O8 Ultimate osc(7,14,28)<30 / >50
 O9 ROC(12)>0 state   O10 StochRSI(14)<0.2 / >0.8
Trend (long while true): T1 MACD(12,26,9)>signal  T2 MACD hist turns >0 below zero / hist<0  T3 EMA9>EMA21  T4 close>SMA50
 T5 ADX(14)>25 and +DI>-DI  T6 Parabolic SAR(0.02,0.2) below price  T7 Ichimoku close above cloud and tenkan>kijun
 T8 Aroon(25) up>70 and down<30  T9 Supertrend(10,3) up  T10 TRIX(15)>signal(9)  T11 Hull MA(20) rising
Volatility: V1 close<lower Bollinger(20,2) / >mid   V2 close>upper Bollinger / <mid   V3 close>Keltner(20, 2 ATR) upper / <mid
 V4 Donchian 20-day high / 10-day low exit   V5 Bollinger squeeze (bandwidth at 120-day low) -> next close direction, hold 5 L/S
Volume: W1 OBV>EMA20(OBV)  W2 CMF(20)>0.05  W3 volume>2x 20d avg on a down day -> long 3 days  W4 close>20-day VWAP
Candles (pattern direction, hold 3 days): K1 bullish engulfing after 3 down closes  K2 hammer at a 10-day low  K3 morning star
 K4 three white soldiers  K5 piercing line  K6 doji after 3 down closes  K7 bearish engulfing after 3 up closes (short)
 K8 shooting star at a 10-day high (short)  K9 three black crows (short)
Markets: SPY QQQ DIA IWM GLD SLV USO BTC ETH; FX majors only for close-based rules (O1 O2 O9 O10 T1-T4 T10 T11 V1 V2).
Volume rules skip FX/GLD-less-volume issues: ETF volume is used as is. No volume for FX.
PASS: Sharpe > 0.3 in 2014-19, 2020-23 and 2024-now; t >= 2; positive at 2x cost; 1-day-delay Sharpe > 0; AND survives a
random-timing baseline: 500 circular shifts of the position series (same exposure and trade lengths, random timing);
z-score vs that null, one-sided p, Benjamini-Hochberg FDR q < 0.10 across ALL tests in this batch.
"""
import numpy as np, pandas as pd
from math import erf, sqrt
class norm:
    @staticmethod
    def cdf(z): return 0.5 * (1 + erf(z / sqrt(2)))
MK = {"SPY": 1.6, "QQQ": 1.4, "DIA": 1.3, "IWM": 3.0, "GLD": 1.5, "SLV": 4.4, "USO": 4.0, "BTC-USD": 3.0, "ETH-USD": 5.0,
      "EURUSD": 1.5, "GBPUSD": 2.0, "USDJPY": 1.5, "AUDUSD": 2.0}
FX = {"EURUSD", "GBPUSD", "USDJPY", "AUDUSD"}; CLOSE_ONLY = {"O1", "O2", "O9", "O10", "T1", "T2", "T3", "T4", "T10", "T11", "V1", "V2"}
def L(t): return pd.read_csv(f"data/{t}.csv", parse_dates=["Date"], index_col="Date").dropna().loc[:"2026-11-24"]
def sh(x, ann): x = x[~np.isnan(x)]; return x.mean() / x.std() * np.sqrt(ann) if len(x) > 30 and x.std() > 0 else np.nan
def state(ent, ex, side=1):
    out = np.zeros(len(ent)); pos = 0
    for i, (e, x) in enumerate(zip(np.asarray(ent, bool), np.asarray(ex, bool))):
        if pos == 0 and e: pos = side
        elif pos != 0 and x: pos = 0
        out[i] = pos
    return out
def hold(sig, n):
    s = np.nan_to_num(np.asarray(sig, float)); out = np.zeros(len(s)); left = 0; cur = 0
    for i in range(len(s)):
        if s[i] != 0: cur, left = s[i], n
        out[i] = cur if left > 0 else 0   # out[i] = position after close i
        left -= 1 if left > 0 else 0
    return out
def rsi(c, n):
    d = c.diff(); u = d.clip(lower=0).ewm(alpha=1/n, adjust=False).mean(); v = (-d.clip(upper=0)).ewm(alpha=1/n, adjust=False).mean(); return 100 - 100 / (1 + u / v)
def atr(h, l, c, n): tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1); return tr.ewm(alpha=1/n, adjust=False).mean()
def wma(x, n): w = np.arange(1, n + 1); return x.rolling(n).apply(lambda a: (a * w).sum() / w.sum(), raw=True)
def psar(h, l, af0=0.02, mx=0.2):
    h, l = h.values, l.values; n = len(h); up = np.zeros(n, bool); sar = np.zeros(n); bull = True; af = af0; ep = h[0]; sar[0] = l[0]
    for i in range(1, n):
        s = sar[i-1] + af * (ep - sar[i-1])
        if bull:
            s = min(s, l[i-1], l[i-2] if i > 1 else l[i-1])
            if l[i] < s: bull, s, ep, af = False, ep, l[i], af0
            elif h[i] > ep: ep, af = h[i], min(af + af0, mx)
        else:
            s = max(s, h[i-1], h[i-2] if i > 1 else h[i-1])
            if h[i] > s: bull, s, ep, af = True, ep, h[i], af0
            elif l[i] < ep: ep, af = l[i], min(af + af0, mx)
        sar[i] = s; up[i] = bull
    return up
def supertrend(h, l, c, n=10, m=3):
    a = atr(h, l, c, n).values; hl2 = ((h + l) / 2).values; cc = c.values; N = len(cc)
    ub = hl2 + m * a; lb = hl2 - m * a; fu, fl = ub.copy(), lb.copy(); up = np.zeros(N, bool); trend = True
    for i in range(1, N):
        fu[i] = ub[i] if (ub[i] < fu[i-1] or cc[i-1] > fu[i-1]) else fu[i-1]
        fl[i] = lb[i] if (lb[i] > fl[i-1] or cc[i-1] < fl[i-1]) else fl[i-1]
        if trend and cc[i] < fl[i]: trend = False
        elif not trend and cc[i] > fu[i]: trend = True
        up[i] = trend
    return up
def signals(d, fx):
    c = d.Close; o, h, l = d.Open, d.High, d.Low; v = d.Volume if "Volume" in d else None; S = {}
    r14 = rsi(c, 14); S["O1 RSI(14)<30"] = state(r14 < 30, r14 > 50); S["O2 RSI(14)>50 trend"] = (r14 > 50).astype(float).values
    S["O9 ROC(12)>0"] = (c / c.shift(12) > 1).astype(float).values
    srs = (r14 - r14.rolling(14).min()) / (r14.rolling(14).max() - r14.rolling(14).min()); S["O10 StochRSI<0.2"] = state(srs < 0.2, srs > 0.8)
    m = c.ewm(span=12, adjust=False).mean() - c.ewm(span=26, adjust=False).mean(); sg = m.ewm(span=9, adjust=False).mean(); hist = m - sg
    S["T1 MACD>signal"] = (m > sg).astype(float).values; S["T2 MACD hist turn below 0"] = state((hist > 0) & (hist.shift() <= 0) & (m < 0), hist < 0)
    S["T3 EMA9>EMA21"] = (c.ewm(span=9, adjust=False).mean() > c.ewm(span=21, adjust=False).mean()).astype(float).values
    S["T4 close>SMA50"] = (c > c.rolling(50).mean()).astype(float).values
    e1 = c.ewm(span=15, adjust=False).mean().ewm(span=15, adjust=False).mean().ewm(span=15, adjust=False).mean(); tr = e1.pct_change(); S["T10 TRIX>signal"] = (tr > tr.ewm(span=9, adjust=False).mean()).astype(float).values
    hma = wma(2 * wma(c, 10) - wma(c, 20), 4); S["T11 Hull MA rising"] = (hma > hma.shift()).astype(float).values
    mid = c.rolling(20).mean(); sd = c.rolling(20).std(); S["V1 below lower BB"] = state(c < mid - 2 * sd, c > mid); S["V2 above upper BB"] = state(c > mid + 2 * sd, c < mid)
    if fx: return S
    k = 100 * (c - l.rolling(14).min()) / (h.rolling(14).max() - l.rolling(14).min()); kk = k.rolling(3).mean(); dd = kk.rolling(3).mean()
    S["O3 Stoch cross <20"] = state((kk > dd) & (kk.shift() <= dd.shift()) & (kk < 20), kk > 80)
    tp = (h + l + c) / 3; cci = (tp - tp.rolling(20).mean()) / (0.015 * tp.rolling(20).apply(lambda a: np.abs(a - a.mean()).mean(), raw=True))
    S["O4 CCI<-100"] = state(cci < -100, cci > 0); S["O5 CCI>100 trend"] = state(cci > 100, cci < 0)
    wr = -100 * (h.rolling(14).max() - c) / (h.rolling(14).max() - l.rolling(14).min()); S["O7 %R(14)<-80"] = state(wr < -80, wr > -20)
    bp_ = c - pd.concat([l, c.shift()], axis=1).min(axis=1); trr = pd.concat([h, c.shift()], axis=1).max(axis=1) - pd.concat([l, c.shift()], axis=1).min(axis=1)
    uo = 100 * (4 * bp_.rolling(7).sum() / trr.rolling(7).sum() + 2 * bp_.rolling(14).sum() / trr.rolling(14).sum() + bp_.rolling(28).sum() / trr.rolling(28).sum()) / 7
    S["O8 Ultimate osc<30"] = state(uo < 30, uo > 50)
    a14 = atr(h, l, c, 14); upm = h.diff(); dnm = -l.diff(); pdm = np.where((upm > dnm) & (upm > 0), upm, 0); ndm = np.where((dnm > upm) & (dnm > 0), dnm, 0)
    pdi = 100 * pd.Series(pdm, index=c.index).ewm(alpha=1/14, adjust=False).mean() / a14; ndi = 100 * pd.Series(ndm, index=c.index).ewm(alpha=1/14, adjust=False).mean() / a14
    adx = (100 * (pdi - ndi).abs() / (pdi + ndi)).ewm(alpha=1/14, adjust=False).mean(); S["T5 ADX>25 +DI>-DI"] = ((adx > 25) & (pdi > ndi)).astype(float).values
    S["T6 Parabolic SAR"] = psar(h, l).astype(float)
    ten = (h.rolling(9).max() + l.rolling(9).min()) / 2; kij = (h.rolling(26).max() + l.rolling(26).min()) / 2
    sa = ((ten + kij) / 2).shift(26); sb = ((h.rolling(52).max() + l.rolling(52).min()) / 2).shift(26)
    S["T7 Ichimoku"] = ((c > np.maximum(sa, sb)) & (ten > kij)).astype(float).values
    au = 100 * h.rolling(26).apply(np.argmax, raw=True) / 25; ad = 100 * l.rolling(26).apply(np.argmin, raw=True) / 25
    S["T8 Aroon"] = ((au > 70) & (ad < 30)).astype(float).values; S["T9 Supertrend(10,3)"] = supertrend(h, l, c).astype(float)
    a20 = atr(h, l, c, 20); em = c.ewm(span=20, adjust=False).mean(); S["V3 Keltner breakout"] = state(c > em + 2 * a20, c < em)
    S["V4 Donchian 20/10"] = state(c > h.rolling(20).max().shift(), c < l.rolling(10).min().shift())
    bw = 4 * sd / mid; sq = (bw <= bw.rolling(120).min()).shift().fillna(False); S["V5 BB squeeze dir"] = hold(np.where(sq, np.sign(c.diff()), 0), 5)
    if v is not None and (v > 0).mean() > 0.9:
        if "Volume" in d:
            mf = tp * v; pos_mf = mf.where(tp > tp.shift(), 0).rolling(14).sum(); neg_mf = mf.where(tp < tp.shift(), 0).rolling(14).sum(); mfi = 100 - 100 / (1 + pos_mf / neg_mf)
            S["O6 MFI<20"] = state(mfi < 20, mfi > 50)
            obv = (np.sign(c.diff()).fillna(0) * v).cumsum(); S["W1 OBV>EMA20"] = (obv > obv.ewm(span=20, adjust=False).mean()).astype(float).values
            mfm = ((c - l) - (h - c)) / (h - l).replace(0, np.nan); cmf = (mfm * v).rolling(20).sum() / v.rolling(20).sum(); S["W2 CMF>0.05"] = (cmf > 0.05).astype(float).values
            S["W3 volume spike down day"] = hold(((v > 2 * v.rolling(20).mean().shift()) & (c < c.shift())).astype(float), 3)
            S["W4 close>20d VWAP"] = (c > (tp * v).rolling(20).sum() / v.rolling(20).sum()).astype(float).values
    body = (c - o).abs(); rng_ = (h - l).replace(0, np.nan); dn3 = (c < c.shift()) & (c.shift() < c.shift(2)) & (c.shift(2) < c.shift(3)); up3 = (c > c.shift()) & (c.shift() > c.shift(2)) & (c.shift(2) > c.shift(3))
    bull, bear = c > o, c < o
    S["K1 bullish engulfing"] = hold((bull & bear.shift() & (c >= o.shift()) & (o <= c.shift()) & dn3.shift()).astype(float), 3)
    lo_sh = np.minimum(o, c) - l; hi_sh = h - np.maximum(o, c)
    S["K2 hammer at 10d low"] = hold(((lo_sh > 2 * body) & (hi_sh < body) & (l <= l.rolling(10).min())).astype(float), 3)
    S["K3 morning star"] = hold((bear.shift(2) & (body.shift(2) > 0.6 * rng_.shift(2)) & (body.shift() < 0.3 * rng_.shift()) & bull & (c > (o.shift(2) + c.shift(2)) / 2)).astype(float), 3)
    S["K4 three white soldiers"] = hold((bull & bull.shift() & bull.shift(2) & up3 & (body > 0.5 * rng_) & (body.shift() > 0.5 * rng_.shift())).astype(float), 3)
    S["K5 piercing line"] = hold((bear.shift() & bull & (o < l.shift()) & (c > (o.shift() + c.shift()) / 2) & (c < o.shift())).astype(float), 3)
    S["K6 doji after decline"] = hold(((body < 0.1 * rng_) & dn3.shift()).astype(float), 3)
    S["K7 bearish engulfing (short)"] = hold(-(bear & bull.shift() & (o >= c.shift()) & (c <= o.shift()) & up3.shift()).astype(float), 3)
    S["K8 shooting star (short)"] = hold(-((hi_sh > 2 * body) & (lo_sh < body) & (h >= h.rolling(10).max())).astype(float), 3)
    S["K9 three black crows (short)"] = hold(-(bear & bear.shift() & bear.shift(2) & dn3 & (body > 0.5 * rng_)).astype(float), 3)
    return S
rng = np.random.default_rng(35); rows = []
for t, bp in MK.items():
    d = L(t); fx = t in FX; ann = 365 if "-USD" in t else (260 if fx else 252); c = d.Close
    r = c.pct_change().fillna(0).values; ix = c.index; post = ix >= pd.Timestamp("2018" if t == "ETH-USD" else "2014")
    per = [(ix >= pd.Timestamp("2018" if t == "ETH-USD" else "2014")) & (ix < pd.Timestamp("2020")), (ix >= pd.Timestamp("2020")) & (ix < pd.Timestamp("2024")), ix >= pd.Timestamp("2024")]
    rp = r[post]
    for nm, pos in signals(d, fx).items():
        pos = np.nan_to_num(np.asarray(pos, float))
        def net(p, m=1): p1 = np.r_[0, p[:-1]]; return p1 * r - np.abs(np.diff(np.r_[0, p1])) * bp * m / 2e4
        x = net(pos); x2 = net(pos, 2); xd = net(np.r_[0, pos[:-1]])
        s = [sh(x[q], ann) for q in per]; S0 = sh(x[post], ann); tt = S0 * np.sqrt(post.sum() / ann)
        pp = pos[post]
        if np.abs(pp).sum() == 0: continue
        shifts = rng.integers(60, len(pp) - 60, 500)
        null = []
        for k in shifts:
            q = np.roll(pp, k); q1 = np.r_[0, q[:-1]]; z = q1 * rp - np.abs(np.diff(np.r_[0, q1])) * bp / 2e4; null.append(z.mean() / z.std() * np.sqrt(ann) if z.std() > 0 else 0)
        null = np.array(null); zsc = (S0 - null.mean()) / null.std()
        rows.append(dict(rule=nm, market=t, s14=s[0], s20=s[1], s24=s[2], t=tt, delay=sh(xd[post], ann), cost2x=x2[post].sum() > 0, expo=np.abs(pp).mean(),
                         null_mean=null.mean(), z=zsc, p=1 - norm.cdf(zsc), pct24=x[per[2]].sum()))
df = pd.DataFrame(rows); n = len(df)
o = df.p.rank(method="first").astype(int); df["bh_crit"] = 0.10 * o / n
sp = df.sort_values("p"); ok = sp.p.values <= sp.bh_crit.values; kmax = np.max(np.where(ok)[0]) + 1 if ok.any() else 0
df["fdr_ok"] = df.p <= (sp.p.values[kmax - 1] if kmax else -1)
df["bar"] = (df[["s14", "s20", "s24"]].gt(0.3).all(axis=1)) & (df.t >= 2) & df.cost2x & (df.delay > 0)
df["PASS"] = df.bar & df.fdr_ok
df.to_csv("lab/batch35_results.csv", index=False)
print("tests", n, "| period bar", int(df.bar.sum()), "| FDR ok", int(df.fdr_ok.sum()), "| PASS", int(df.PASS.sum()))
print("expected chance passes of the period bar (null, p<0.05 approx):", round(n * 0.05, 1))
print(df[df.bar | df.fdr_ok].sort_values("p").round(3).to_string(index=False))
print("\nby rule, markets passing the period bar:"); print(df.groupby("rule").bar.sum().sort_values(ascending=False).head(15).to_string())
