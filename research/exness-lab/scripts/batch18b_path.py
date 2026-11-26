"""Batch 18b, pre-registered 2026-11-26 after Batch 18 showed a path bias: daily bars don't say whether the high or the
low came first, so Batch 18 gave limit entries free TPs and stop entries false SLs. Same 6 rules x 4 SL/TP variants x 7
markets, re-run with the standard OHLC path rule (up day O->L->H->C, down day O->H->L->C). Same PASS bar."""
import sys, numpy as np, pandas as pd
sys.path.insert(0, "lab"); from path_sim import walk
MK = {"SPY": 1.6, "QQQ": 1.4, "DIA": 1.3, "IWM": 3.0, "GLD": 1.5, "SLV": 4.4, "BTC-USD": 3.0}
def sh(x, ann): x = x.dropna(); return x.mean() / x.std() * np.sqrt(ann) if len(x) > 30 and x.std() > 0 else np.nan
rows = []
for t, bp in MK.items():
    d = pd.read_csv(f"data/{t}.csv", parse_dates=["Date"], index_col="Date").dropna().loc["2013-06":]; ann = 365 if t == "BTC-USD" else 252
    o, h, l, c = (d[k].values for k in ("Open", "High", "Low", "Close")); pc = d.Close.shift().values
    tr = pd.concat([d.High - d.Low, (d.High - d.Close.shift()).abs(), (d.Low - d.Close.shift()).abs()], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1/14, adjust=False).mean().shift().values; R = (d.High - d.Low).shift().values
    ph, pl = d.High.shift().values, d.Low.shift().values; ema = d.Close.ewm(span=20, adjust=False).mean().shift().values
    cost = bp / 1e4; slip = 2e-4; nan = np.full(len(o), np.nan)
    for slm in (0.5, 1.0):
        for tpm in (1, 2):
            SL, TP = slm * atr, tpm * slm * atr; S = {}
            def go(side, kind, lvl, sl=SL, tp=TP, sp=slip):
                r = walk(o, h, l, c, side, kind, lvl, sl, tp, sp); return r - (r != 0) * cost
            S["R1 Williams long"] = go(1, "stop", o + 0.5 * R)
            a, b = go(1, "stop", ph), go(-1, "stop", pl); S["R2 prior-day high/low breakout"] = np.where((a != 0) & (b != 0), np.minimum(a, b), a + b)
            S["R3 buy the dip (limit)"] = go(1, "limit", o - 0.5 * atr, sp=0)
            S["R4 sell the rip (limit)"] = go(-1, "limit", o + 0.5 * atr, sp=0)
            gap = o / pc - 1
            S["R5 gap fade to prior close"] = go(1, "open", np.where(gap < -0.005, o, nan), tp=np.abs(pc - o), sp=0) + go(-1, "open", np.where(gap > 0.005, o, nan), tp=np.abs(pc - o), sp=0)
            S["R6 trend-day stop entry"] = go(1, "stop", np.where(o > ema, o + 0.25 * atr, nan)) + go(-1, "stop", np.where(o <= ema, o - 0.25 * atr, nan))
            for nm, x in S.items():
                x = pd.Series(np.nan_to_num(x), index=d.index)
                p = [sh(x.loc[a_:b_], ann) for a_, b_ in (("2014", "2019"), ("2020", "2023"), ("2024", "2026"))]
                post = x.loc["2014":]; tt = sh(post, ann) * np.sqrt(len(post) / ann); n = (post != 0).sum()
                rows.append(dict(rule=nm, market=t, sl=slm, tp=tpm, s14=p[0], s20=p[1], s24=p[2], t=tt, win=(post > 0).sum() / max(n, 1),
                                 pass_=all(v > 0.3 for v in p) and tt >= 2))
df = pd.DataFrame(rows); df.to_csv("lab/batch18b_results.csv", index=False)
print("passes:", int(df.pass_.sum()), "of", len(df)); print(df[df.pass_].round(2).to_string(index=False))
print("\nmedian by rule:"); print(df.groupby("rule")[["s14", "s20", "s24", "t", "win"]].median().round(2).to_string())
