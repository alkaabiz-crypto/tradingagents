"""Batch 18, pre-registered 2026-11-26 before running. Day trades with explicit stop-loss (SL) and take-profit (TP)
on daily bars, entered and closed the same day (swap irrelevant). When SL and TP both lie inside the day's range,
assume the SL was hit first (worst case). Stop entries pay 2 bp extra slippage. ATR = 14-day ATR known at the open.
Rules (each with SL in {0.5, 1.0} x ATR and TP in {1, 2} x SL -> 4 variants; 6 rules x 4 x 7 markets = 168 trials):
 R1 Williams breakout long: buy-stop at open + 0.5 x prior range.
 R2 Prior-day high breakout long / prior-day low breakout short (both, worse side if both touched -> skip day as loss-first).
 R3 Buy the dip ("buy low, sell high"): buy-limit at open - 0.5 x ATR.  Mirror: sell-limit at open + 0.5 x ATR (R4).
 R5 Gap fade with stops: open gaps > 0.5% vs prior close -> trade toward the prior close; TP fixed at the prior close
    (variants only change SL), SL as listed.
 R6 Trend day: if open > 20-day EMA, buy-stop at open + 0.25 x ATR; else sell-stop at open - 0.25 x ATR.
Exit at SL, TP or the close. Costs = round-trip bp per market. PASS bar: avg R>0 and Sharpe > 0.3 in 2014-19,
2020-23 and 2024-now, and post-2014 t >= 2. With 168 trials, ~8 false passes at t>=2 are expected; a pass needs
neighbours (>= 3 of its rule's 4 variants) to count as a lead.
"""
import numpy as np, pandas as pd
MK = {"SPY": 1.6, "QQQ": 1.4, "DIA": 1.3, "IWM": 3.0, "GLD": 1.5, "SLV": 4.4, "BTC-USD": 3.0}
def sh(x, ann): x = x.dropna(); return x.mean() / x.std() * np.sqrt(ann) if len(x) > 30 and x.std() > 0 else np.nan
def trade(side, entry, sl, tp, h, l, c, active):
    """side +1 long / -1 short, arrays; returns % return per day (0 when no trade)."""
    if side > 0:
        hit_sl, hit_tp = l <= sl, h >= tp
        exitp = np.where(hit_sl, sl, np.where(hit_tp, tp, c)); r = exitp / entry - 1
    else:
        hit_sl, hit_tp = h >= sl, l <= tp
        exitp = np.where(hit_sl, sl, np.where(hit_tp, tp, c)); r = entry / exitp - 1
    return np.where(active, r, 0.0)
rows = []
for t, bp in MK.items():
    d = pd.read_csv(f"data/{t}.csv", parse_dates=["Date"], index_col="Date").dropna(); ann = 365 if t == "BTC-USD" else 252
    o, h, l, c = d.Open.values, d.High.values, d.Low.values, d.Close.values; pc = d.Close.shift().values
    tr = pd.concat([d.High - d.Low, (d.High - d.Close.shift()).abs(), (d.Low - d.Close.shift()).abs()], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1 / 14, adjust=False).mean().shift().values; R = (d.High - d.Low).shift().values
    ph, pl = d.High.shift().values, d.Low.shift().values; ema = d.Close.ewm(span=20, adjust=False).mean().shift().values
    cost = bp / 1e4; slip = 2e-4
    for slm in (0.5, 1.0):
        for tpm in (1, 2):
            S = {}
            # R1
            trig = o + 0.5 * R; e = np.maximum(trig, o) * (1 + slip); act = h >= trig
            S["R1 Williams long"] = trade(1, e, e - slm * atr, e + tpm * slm * atr, h, l, c, act) - act * cost
            # R2 both sides
            eL = np.maximum(ph, o) * (1 + slip); aL = h > ph; eS = np.minimum(pl, o) * (1 - slip); aS = l < pl
            rL = trade(1, eL, eL - slm * atr, eL + tpm * slm * atr, h, l, c, aL); rS = trade(-1, eS, eS + slm * atr, eS - tpm * slm * atr, h, l, c, aS)
            both = aL & aS; S["R2 prior-day high/low breakout"] = np.where(both, -slm * atr / c, rL + rS) - (aL | aS) * cost
            # R3 / R4 limit entries
            e = o - 0.5 * atr; act = l <= e
            S["R3 buy the dip (limit)"] = trade(1, e, e - slm * atr, e + tpm * slm * atr, h, l, c, act) - act * cost
            e = o + 0.5 * atr; act = h >= e
            S["R4 sell the rip (limit)"] = trade(-1, e, e + slm * atr, e - tpm * slm * atr, h, l, c, act) - act * cost
            # R5 gap fade (TP = prior close)
            gap = o / pc - 1; up, dn = gap > 0.005, gap < -0.005
            rl = trade(1, o, o - slm * atr, pc, h, l, c, dn); rs = trade(-1, o, o + slm * atr, pc, h, l, c, up)
            S["R5 gap fade to prior close"] = rl + rs - (up | dn) * cost
            # R6 trend day
            lg = o > ema; eL = (o + 0.25 * atr) * (1 + slip); eS = (o - 0.25 * atr) * (1 - slip)
            aL = lg & (h >= o + 0.25 * atr); aS = ~lg & (l <= o - 0.25 * atr)
            S["R6 trend-day stop entry"] = trade(1, eL, eL - slm * atr, eL + tpm * slm * atr, h, l, c, aL) + trade(-1, eS, eS + slm * atr, eS - tpm * slm * atr, h, l, c, aS) - (aL | aS) * cost
            for nm, x in S.items():
                x = pd.Series(np.nan_to_num(x), index=d.index)
                p = [sh(x.loc[a:b], ann) for a, b in (("2014", "2019"), ("2020", "2023"), ("2024", "2026"))]
                post = x.loc["2014":]; tt = sh(post, ann) * np.sqrt(len(post) / ann)
                n = (post != 0).sum(); wr = (post > 0).sum() / max(n, 1)
                rows.append(dict(rule=nm, market=t, sl=slm, tp=tpm, s14=p[0], s20=p[1], s24=p[2], t=tt, trades_yr=n / (len(post) / ann), win=wr,
                                 pass_=all(v > 0.3 for v in p) and tt >= 2))
df = pd.DataFrame(rows); df.to_csv("lab/batch18_results.csv", index=False)
print("passes:", int(df.pass_.sum()), "of", len(df))
g = df.groupby(["rule", "market"]).agg(passes=("pass_", "sum"), med_s24=("s24", "median"), med_t=("t", "median"), win=("win", "median"), tr=("trades_yr", "median")).round(2)
print(g[g.passes >= 1].to_string()); print("\nmedian by rule:"); print(df.groupby("rule")[["s14", "s20", "s24", "t", "win"]].median().round(2).to_string())
