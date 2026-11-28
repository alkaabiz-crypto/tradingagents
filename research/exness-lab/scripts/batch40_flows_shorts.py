"""Batch 40, pre-registered 2026-11-28. More ideas that do not lean on crypto.
 R1/R2 Month-end rebalancing flows (Harvey, Mazzoleni & Melone 2021): at the close 5 trading days before month end, if US500 (USTEC)
       beat TLT month-to-date by > 3%, short it for the last 5 days; if it trailed by > 3%, go long for them.
 S1/S2 IBS > 0.8 short for 1 day, only when below the 200-day (US500 / USTEC).
 S3/S4 Bear-rally fade: below the 200-day, after 3 up closes, short for 2 days (US500 / USTEC).
Bar and $ as Batch 39 (US500 $1,000, USTEC $1,330), periods 2010-19, 2020-23, 2024-now; random-timing BH q < 0.10 across these 6."""
import io, contextlib, numpy as np, pandas as pd
src = open("lab/batch39_uncorr.py").read(); head = src.split("UNDER = {}")[0]
with contextlib.redirect_stdout(io.StringIO()): exec(head)
UNDER = {}; tlt = L("TLT").Close
for t, exp, bp, tag in (("SPY", 1000, 1.6, "US500"), ("QQQ", 1330, 1.4, "USTEC")):
    d = D[t]; c = d.Close; r = c.pct_change().fillna(0); ix = c.index; tl = tlt.reindex(ix).ffill()
    m = pd.Series(ix.to_period("M"), index=ix); kb = m.groupby(m).cumcount(ascending=False)  # 0 = last day
    first_close = c.groupby(m).transform(lambda s: s.iloc[0]); prev_close = c.shift().groupby(m).transform("first")
    mtd = c / prev_close - 1; mtd_b = tl / tl.shift().groupby(m).transform("first") - 1; diff = (mtd - mtd_b)
    sig = pd.Series(np.where(kb == 5, np.where(diff > 0.03, -1, np.where(diff < -0.03, 1, 0)), np.nan), index=ix)
    pos = sig.groupby(m).ffill().where(kb < 5, np.nan).fillna(0)  # held over the last 5 days
    pos = pos.where(kb < 5, 0); p = pos  # position over day i decided at close of kb==5 day
    nm = f"R{1 if t == 'SPY' else 2} {tag} month-end rebalancing"; UNDER[nm] = r.values
    evaluate(nm, p * r, p, "2010", 252, exp, (p.diff().abs() > 0) * bp / 2e4)
    below = c < c.rolling(200).mean(); ibs_ = (c - d.Low) / (d.High - d.Low)
    p = (-((ibs_ > 0.8) & below).astype(float)).shift().fillna(0); nm = f"S{1 if t == 'SPY' else 2} {tag} IBS>0.8 short below 200-day"; UNDER[nm] = r.values
    evaluate(nm, p * r, p, "2010", 252, exp, (p.diff().abs() > 0) * bp / 2e4)
    up3 = (r > 0) & (r.shift() > 0) & (r.shift(2) > 0); s = (up3 & below).values; out = np.zeros(len(s)); left = 0
    for i in range(len(s)):
        out[i] = -1 if left > 0 else 0; left -= 1 if left > 0 else 0
        if s[i]: left = 2
    p = pd.Series(out, index=ix); nm = f"S{3 if t == 'SPY' else 4} {tag} bear-rally fade"; UNDER[nm] = r.values
    evaluate(nm, p * r, p, "2010", 252, exp, (p.diff().abs() > 0) * bp / 2e4)
df = pd.DataFrame(rows); n = len(df); sp = np.sort(df.p.values); ok = sp <= 0.10 * np.arange(1, n + 1) / n; cut = sp[np.where(ok)[0].max()] if ok.any() else -1
df["PASS"] = df[["s_a", "s20", "s24"]].gt(0.3).all(axis=1) & (df.t >= 2) & df.x2 & (df.p <= cut)
pd.set_option("display.width", 250); print(df.round(2).to_string(index=False)); df.to_csv("lab/batch40_results.csv", index=False)
