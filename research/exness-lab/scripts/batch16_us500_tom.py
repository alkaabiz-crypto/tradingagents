"""Batch 16, pre-registered 2026-11-26 before running. 1.4 bp USTEC / 1.6 bp US500 round trip, swap-free.
A) US500 overnight hold above 200-day at 0.14 lot (US500 ~ SPY x 10) vs USTEC at 0.05, Sharpe by period, $ 2025-now.
B) Turn of month on the USTEC overnight hold: only nights from the last trading day to day 3 vs all other nights.
2 new trials.
"""
import numpy as np, pandas as pd
def sh(x): return x.mean() / x.std() * np.sqrt(252) if x.std() > 0 else np.nan
def st(x): e = x.cumsum(); return f"{x.sum():+.0f} / {(e - e.cummax()).min():.0f}"
def on(t, mult, lots, bp):
    q = pd.read_csv(f"data/{t}.csv", parse_dates=["Date"], index_col="Date").dropna(); c, o = q.Close * mult, q.Open * mult
    m = (q.Close > q.Close.rolling(200).mean()).shift().fillna(False)
    return (lots * ((o - c.shift()) - bp / 1e4 * c.shift())).where(m, 0).fillna(0), q
P = {"USTEC 0.05": on("QQQ", 41, 0.05, 1.4)[0], "US500 0.14": on("SPY", 10, 0.14, 1.6)[0]}
x, q = on("QQQ", 41, 0.05, 1.4); mm = pd.Series(q.index.to_period("M"), index=q.index)
tdom = mm.groupby(mm).cumcount() + 1; last = mm != mm.shift(-1)
tom = (last.shift().fillna(False) | (tdom <= 3))  # night ending at this open starts on last day .. day 3
P["USTEC turn-of-month nights"] = x.where(tom, 0); P["USTEC other nights"] = x.where(~tom, 0)
print("| plan | 2000-13 | 2014-19 | 2020-23 | 2024-now | $ 2024-now / drop | $ 2025-now / drop |")
for nm, s in P.items():
    print(f"| {nm} | " + " | ".join(f"{sh(s.loc[a:b]):.2f}" for a, b in (("2000","2013"),("2014","2019"),("2020","2023"),("2024","2026"))) + f" | {st(s.loc['2024':])} | {st(s.loc['2025':])} |")
