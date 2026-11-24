"""Study 9 (pre-registered 2026-11-24 12:15 UTC, before running): month-end pension rebalancing.
Source: Harvey, Mazzoleni & Melone (2025), "The Unintended Consequences of Rebalancing": balanced
funds sell the asset class that outperformed over the month near month-end, so stocks that beat bonds
month-to-date tend to underperform bonds in the last days of the month (and vice versa).
Rules (no tuning; the paper's mechanism, the audit's month-end window of 3 trading days):
 R1 at the close 4 trading days before month-end, s = sign(SPY - IEF return from the previous month-end
    close to that day). Hold -s on the spread (IEF minus SPY) for the last 3 trading days; else flat.
    Traded as a spread: 2 legs x 5 bp per side.
 R2 same, but only when |SPY - IEF month-to-date| > 2% (large imbalances, the paper's strongest bucket).
Gates: engine.py unchanged (IS to 2013, OOS 2014-19, HOLDOUT 2020+, placebo, 2x cost, t>=2); because the
tournament tried ~2,930 rules, a winner also needs post-2014 t above the luck bar 4.19.
"""
import numpy as np, pandas as pd
from engine import load, evaluate, table
spy = load("SPY"); ief = pd.read_csv("brains/macro/data/IEF.csv", index_col=0, parse_dates=True)["Close"]
ief.index = pd.to_datetime(ief.index).tz_localize(None).normalize()
df = pd.concat([spy.rename("spy"), ief.rename("ief")], axis=1).dropna()
r = df.pct_change(); spread = r.ief - r.spy
m = pd.Series(df.index.to_period("M"), index=df.index)
left = pd.Series(1, index=df.index).groupby(m).transform("sum") - pd.Series(1, index=df.index).groupby(m).cumsum()
prev_me = df.groupby(m).tail(1).reindex(df.index).ffill().shift(1)  # last close of the previous month
mtd = (df.spy / prev_me.spy - 1) - (df.ief / prev_me.ief - 1)
sig_day = left == 3                       # close 4 trading days before month-end... 3 days remain after it
s = np.sign(mtd).where(sig_day)
big = mtd.abs().where(sig_day) > 0.02
def hold(sig):
    pos = sig.copy()
    pos = pos.where(sig_day).ffill().where(left >= 1, 0)  # carry through the last 3 days, flat on the final close
    return pos.where(left <= 3, 0).fillna(0)
rows = [evaluate("R1 rebalancing: -sign(MTD SPY-IEF) on IEF-SPY, last 3 days", hold(s), spread, cost_bps=10, start="2003-01-01"),
        evaluate("R2 same, only |MTD gap| > 2%", hold(s.where(big, 0)), spread, cost_bps=10, start="2003-01-01")]
print(table(rows))
