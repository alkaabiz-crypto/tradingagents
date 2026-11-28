"""Batch 30, pre-registered 2026-11-27 before running. Buy-low swing rules (hold 2-5 days) and documented short-term
anomalies (Connors & Alvarez; Jegadeesh 1990 / Lehmann 1990 short-term reversal; Bollinger; Larry Williams %R;
VIX-spike premium). Long only, entered at the close of the signal day (index/gold CFDs trade through the US close),
exits at the close; the next-open fill is reported as robustness. Swap-free: holding costs nothing.
Markets: US500(SPY) USTEC(QQQ) US30(DIA) US2000(IWM) XAU(GLD) XAG(SLV) OIL(USO) BTC ETH. RT cost bp: 1.6 1.4 1.3 3 1.5 4.4 4 3 5.
Rules:
 S1 RSI(2) < 5 above 200-day, exit after 3 days          S2 close = 10-day low above 200-day, hold 3 days
 S3 two-day drop > 2 x daily vol, hold 2 days            S4 close below lower Bollinger(20,2), hold 3 days
 S5 three down closes in a row, hold 3 days              S6 Williams %R(10) < -90 above 200-day, hold 2 days
 S7 1-day return z-score < -2 (vs 60-day vol), hold 3 days (short-term reversal)
 S8 5-day return in the bottom 10% of the past year, hold 5 days
 S9 5-day return < -3% while above 200-day, hold 3 days  S10 gap down > 1% at the open, buy the close, hold 2 days
 S11 IBS < 0.2, hold 2 days                              S12 VIX close > 1.2 x its 10-day average, buy, hold 5 days
12 rules x 9 markets = 108 trials (cumulative ~760; ~5 false t>=2 passes expected).
PASS: Sharpe > 0.3 in 2014-19, 2020-23 and 2024-now (ETH from 2018), post-2014 t >= 2, positive at 2x cost,
AND positive post-2014 with the next-open fill. Sharpe is on all days (flat days count as 0).
"""
import numpy as np, pandas as pd
MK = {"SPY": 1.6, "QQQ": 1.4, "DIA": 1.3, "IWM": 3.0, "GLD": 1.5, "SLV": 4.4, "USO": 4.0, "BTC-USD": 3.0, "ETH-USD": 5.0}
vix = pd.read_csv("data/VIX.csv", parse_dates=["Date"], index_col="Date").Close
def sh(x, ann): x = x.dropna(); return x.mean() / x.std() * np.sqrt(ann) if len(x) > 30 and x.std() > 0 else np.nan
def hold_n(sig, n):
    """Position 1 for the n days after each signal close (re-signals extend the hold)."""
    s = sig.astype(int).values; pos = np.zeros(len(s)); left = 0
    for i in range(len(s)):
        if s[i]: left = n
        pos[i] = 1.0 if left > 0 else 0.0
        if left > 0 and not s[i]: left -= 1
        elif s[i]: left = n
    # pos[i]=1 means held from close i to close i+1 while counting down
    out = np.zeros(len(s)); left = 0
    for i in range(len(s)):
        if left > 0: out[i] = 1.0; left -= 1
        if s[i]: left = n
    return pd.Series(out, index=sig.index)  # out[i]=1: holding over day i (close i-1 -> close i)
def rsi(c, n):
    d = c.diff(); u = d.clip(lower=0).ewm(alpha=1/n, adjust=False).mean(); v = (-d.clip(upper=0)).ewm(alpha=1/n, adjust=False).mean(); return 100 - 100 / (1 + u / v)
rows = []
for t, bp in MK.items():
    d = pd.read_csv(f"data/{t}.csv", parse_dates=["Date"], index_col="Date").dropna().loc[:"2026-11-24"]; ann = 365 if "-USD" in t else 252
    o, h, l, c = d.Open, d.High, d.Low, d.Close; r = c.pct_change().fillna(0); ro = (o.shift(-1) / o - 1).fillna(0)
    s200 = c > c.rolling(200).mean(); vol = r.rolling(60).std()
    S = {"S1 RSI(2)<5, 3 days": ((rsi(c, 2) < 5) & s200, 3), "S2 10-day low, 3 days": ((c <= c.rolling(10).min()) & s200, 3),
         "S3 2-day drop > 2 vol, 2 days": (c.pct_change(2) < -2 * vol, 2), "S4 below lower Bollinger, 3 days": (c < c.rolling(20).mean() - 2 * c.rolling(20).std(), 3),
         "S5 3 down closes, 3 days": ((r < 0) & (r.shift() < 0) & (r.shift(2) < 0), 3)}
    wr = -100 * (h.rolling(10).max() - c) / (h.rolling(10).max() - l.rolling(10).min())
    S["S6 %R(10)<-90, 2 days"] = ((wr < -90) & s200, 2); S["S7 1-day z < -2, 3 days"] = (r / vol.shift() < -2, 3)
    r5 = c.pct_change(5); S["S8 worst-decile week, 5 days"] = (r5 < r5.rolling(252).quantile(0.1).shift(), 5)
    S["S9 -3% week above 200-day, 3 days"] = ((r5 < -0.03) & s200, 3); S["S10 gap down >1%, 2 days"] = (o / c.shift() - 1 < -0.01, 2)
    ibs = (c - l) / (h - l).replace(0, np.nan); S["S11 IBS<0.2, 2 days"] = (ibs < 0.2, 2)
    v = vix.reindex(c.index).ffill(); S["S12 VIX spike, 5 days"] = (v > 1.2 * v.rolling(10).mean(), 5)
    for nm, (sig, n) in S.items():
        sig = sig.fillna(False); pos = hold_n(sig, n); turn = pos.diff().abs().fillna(0)
        x = pos * r - turn * bp / 2e4; x2 = pos * r - turn * bp / 1e4
        posO = pos.shift().fillna(0)  # enter at next open: hold open(t)->open(t+1) one day later
        xo = (posO.shift(-1).fillna(0) * 0 + 0)  # placeholder
        # next-open version: signal at close t -> buy open t+1, sell open after n days
        po = hold_n(sig.shift().fillna(False), n); xo = po * (o / o.shift() - 1).fillna(0) - po.diff().abs().fillna(0) * bp / 2e4
        st = "2018" if t == "ETH-USD" else "2014"
        p = [sh(x.loc[st:"2019"], ann), sh(x.loc["2020":"2023"], ann), sh(x.loc["2024":], ann)]; post = x.loc["2014":]; tt = sh(post, ann) * np.sqrt(len(post) / ann)
        rows.append(dict(rule=nm, market=t, s14=p[0], s20=p[1], s24=p[2], t=tt, exposure=pos.loc["2014":].mean(), nextopen=sh(xo.loc["2014":], ann),
                         pct24=x.loc["2024":].sum(), PASS=all(z > 0.3 for z in p) and tt >= 2 and x2.loc["2014":].sum() > 0 and xo.loc["2014":].sum() > 0))
df = pd.DataFrame(rows); df.to_csv("lab/batch30_results.csv", index=False)
print("passes:", int(df.PASS.sum()), "of", len(df)); print(df[df.PASS].round(2).to_string(index=False))
print(df.pivot(index="rule", columns="market", values="s24").round(2).to_string())
