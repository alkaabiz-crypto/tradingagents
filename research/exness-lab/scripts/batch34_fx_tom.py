"""Batch 34, pre-registered 2026-11-27 before running. Close-only rules (Yahoo FX closes are usable, ranges are not).
 F1 FX RSI(2) reversal L/S: RSI(2) < 10 -> long 2 days, > 90 -> short 2 days, entered at the close.
 F2 FX 3 down closes -> long 2 days; 3 up closes -> short 2 days.
 F3 FX 5-day z-score < -2 -> long 3 days, > 2 -> short 3 days.
 T1 Turn of month (Lakonishok & Smidt 1988; Ariel 1987): hold from the close of the last trading day before month end
    through the 3rd trading day of the new month (4 sessions). QQQ, DIA, IWM, GLD, BTC, ETH.
PASS as before: Sharpe > 0.3 in 2014-19, 2020-23, 2024-now; t >= 2; positive at 2x cost; next-open entry Sharpe > 0
(FX next-open = next close, i.e. one day delay).
"""
import numpy as np, pandas as pd
def sh(x, ann): x = x.dropna(); return x.mean() / x.std() * np.sqrt(ann) if len(x) > 30 and x.std() > 0 else np.nan
def L(t): return pd.read_csv(f"data/{t}.csv", parse_dates=["Date"], index_col="Date").dropna().loc[:"2026-11-24"]
def rsi(c, n):
    d = c.diff(); u = d.clip(lower=0).ewm(alpha=1/n, adjust=False).mean(); v = (-d.clip(upper=0)).ewm(alpha=1/n, adjust=False).mean(); return 100 - 100 / (1 + u / v)
def hold(sig, n):  # sig[t] in {-1,0,1} at close t -> position over t+1..t+n (newest signal wins)
    p = pd.Series(0.0, index=sig.index); s = sig.values; out = np.zeros(len(s)); left = 0; cur = 0
    for i in range(len(s)):
        out[i] = cur if left > 0 else 0; left -= 1 if left > 0 else 0
        if s[i] != 0: cur, left = s[i], n
    return pd.Series(out, index=sig.index)
rows = []
def add(nm, t, r, pos, bp, ann, delay_pos=None):
    def net(p, m=1): return p * r - p.diff().abs().fillna(0) * bp * m / 2e4
    x, x2 = net(pos), net(pos, 2); xn = net(delay_pos) if delay_pos is not None else x
    st = "2018" if t == "ETH-USD" else "2014"
    p = [sh(x.loc[st:"2019"], ann), sh(x.loc["2020":"2023"], ann), sh(x.loc["2024":], ann)]; post = x.loc["2014":]; tt = sh(post, ann) * np.sqrt(len(post) / ann)
    rows.append(dict(rule=nm, market=t, s14=p[0], s20=p[1], s24=p[2], t=tt, nextopen=sh(xn.loc["2014":], ann), expo=pos.abs().loc["2014":].mean(),
                     PASS=all(z > 0.3 for z in p) and tt >= 2 and x2.loc["2014":].sum() > 0 and sh(xn.loc["2014":], ann) > 0))
for t, bp in (("EURUSD", 1.5), ("GBPUSD", 2.0), ("USDJPY", 1.5), ("AUDUSD", 2.0)):
    c = L(t).Close; r = c.pct_change().fillna(0); r2 = rsi(c, 2)
    for nm, sig, n in (("F1 RSI(2) reversal L/S", np.where(r2 < 10, 1, np.where(r2 > 90, -1, 0)), 2),
                       ("F2 3 closes reversal L/S", np.where((r < 0) & (r.shift() < 0) & (r.shift(2) < 0), 1, np.where((r > 0) & (r.shift() > 0) & (r.shift(2) > 0), -1, 0)), 2),
                       ("F3 5-day z reversal L/S", (lambda z: np.where(z < -2, 1, np.where(z > 2, -1, 0)))((c / c.shift(5) - 1) / (r.rolling(60).std() * np.sqrt(5))), 3)):
        sg = pd.Series(sig, index=c.index).fillna(0); pos = hold(sg, n); add(nm, t, r, pos, bp, 260, hold(sg.shift().fillna(0), n))
for t, bp in (("QQQ", 1.4), ("DIA", 1.3), ("IWM", 3.0), ("GLD", 1.5), ("BTC-USD", 3.0), ("ETH-USD", 5.0)):
    d = L(t); c, o = d.Close, d.Open; r = c.pct_change().fillna(0); ann = 365 if "-USD" in t else 252
    m = pd.Series(c.index.to_period("M"), index=c.index); k = m.groupby(m).cumcount() + 1  # trading day of month
    last = m != m.shift(-1); pos = ((k <= 3) | last.shift().fillna(False) & False).astype(float)
    pos = (k <= 3).astype(float)  # held over days 1..3 of the month = from the close of the last day of prior month
    alt = pos.copy(); first = (k == 1); rn = r.copy(); rn[first] = (c / o - 1)[first]  # next-open: enter at the open of day 1
    def addn():
        bpx = bp
        x = pos * r - pos.diff().abs().fillna(0) * bpx / 2e4; xn = pos * rn - pos.diff().abs().fillna(0) * bpx / 2e4; x2 = pos * r - pos.diff().abs().fillna(0) * bpx / 1e4
        st = "2018" if t == "ETH-USD" else "2014"
        p = [sh(x.loc[st:"2019"], ann), sh(x.loc["2020":"2023"], ann), sh(x.loc["2024":], ann)]; post = x.loc["2014":]; tt = sh(post, ann) * np.sqrt(len(post) / ann)
        rows.append(dict(rule="T1 turn of month", market=t, s14=p[0], s20=p[1], s24=p[2], t=tt, nextopen=sh(xn.loc["2014":], ann), expo=pos.loc["2014":].mean(),
                         PASS=all(z > 0.3 for z in p) and tt >= 2 and x2.loc["2014":].sum() > 0 and sh(xn.loc["2014":], ann) > 0))
    addn()
df = pd.DataFrame(rows); df.to_csv("lab/batch34_results.csv", index=False); print("passes:", int(df.PASS.sum()), "of", len(df)); print(df.round(2).to_string(index=False))
