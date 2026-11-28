"""Batch 17, pre-registered 2026-11-26 before running. Sizing only, no new rule: on $1,000, hold BOTH overnight legs
(USTEC 0.05 + US500 0.14, ~$2,300 exposure = 2.3x) vs each alone. Costs 1.4 / 1.6 bp. Report $ and worst drop
2000-13, 2020-23, 2024-now, 2025-now and the worst night, plus the correlation of nightly P&L.
"""
import numpy as np, pandas as pd
def on(t, mult, lots, bp):
    q = pd.read_csv(f"data/{t}.csv", parse_dates=["Date"], index_col="Date").dropna(); c, o = q.Close * mult, q.Open * mult
    m = (q.Close > q.Close.rolling(200).mean()).shift().fillna(False)
    return (lots * ((o - c.shift()) - bp / 1e4 * c.shift())).where(m, 0).fillna(0)
A, B = on("QQQ", 41, 0.05, 1.4), on("SPY", 10, 0.14, 1.6); j = pd.concat([A, B], axis=1, sort=True).fillna(0); j.columns = ["T", "S"]
P = {"USTEC 0.05": j["T"], "US500 0.14": j["S"], "both": j.sum(axis=1)}
def st(x): e = x.cumsum(); return f"{x.sum():+.0f} / {(e - e.cummax()).min():.0f}"
print("| plan | 2000-13 (at today's lot $) | 2020-23 | 2024-now | 2025-now | worst night 2020-now |")
for nm, x in P.items():
    print(f"| {nm} | {st(x.loc['2000':'2013'])} | {st(x.loc['2020':'2023'])} | {st(x.loc['2024':])} | {st(x.loc['2025':])} | {x.loc['2020':].min():.0f} |")
k = j.loc["2020":]; k = k[(k != 0).all(axis=1)]; print("correlation:", round(k.corr().iloc[0, 1], 2))
