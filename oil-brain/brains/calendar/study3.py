"""Study 3 (calendar brain): follow-ups on the two study-2 near misses. PRE-REGISTERED 2026-11-24
after seeing study 2 (so these are chosen with knowledge of C6/C7 OOS/HOLDOUT results; windows
and signals are copied unchanged, nothing is re-tuned). Last 2 rules of the 15-rule budget.

  C10 Quarter-end rebalancing SPY-TLT: C6 exactly, but only in March, June, September, December
      (the topic's end-of-quarter effect; quarterly rebalancers should make it stronger per
      dollar, but 4 events a year means less power). Cost 10 bp per unit of spread.
  C11 IEF last 3 days: C7 exactly, on the 7-10y Treasury ETF (data/IEF.csv, Yahoo, saved in
      this folder). An out-of-instrument replication: if the month-end index-extension story
      is real it should appear in intermediate Treasuries too. No window change.
Pass bar as RULES.md. Expect both to fail t >= 3; the question is whether the sign holds.
"""
import os
import numpy as np
import pandas as pd
from common import engine, month_day_ranks, pos_from_earn_days

rows = []
spy, tlt = engine.load("SPY"), engine.load("TLT")
px = pd.concat([spy, tlt], axis=1, keys=["S", "B"]).dropna()
rr = px.pct_change().dropna()
spread = rr.S - rr.B
first, last = month_day_ranks(rr.index)
anchor = px.groupby([px.index.year, px.index.month]).tail(1)
anchor.index = anchor.index + pd.offsets.MonthBegin(1)
anc = anchor.reindex(rr.index, method="ffill")
mtd_rel = (px.S.reindex(rr.index) / anc.S - 1) - (px.B.reindex(rr.index) / anc.B - 1)
pos = pd.Series(0.0, index=rr.index)
for d in rr.index[(last == -6) & (rr.index.month % 3 == 0)]:
    m = (rr.index.year == d.year) & (rr.index.month == d.month) & (last.values >= -6) & (last.values <= -2)
    pos[m] = -np.sign(mtd_rel[d])
rows.append(engine.evaluate("C10 quarter-end rebalancing SPY-TLT", pos, spread, 10))

ief = pd.read_csv(os.path.join(os.path.dirname(__file__), "data", "IEF.csv"),
                  index_col=0, parse_dates=True).Close.pct_change().dropna()
first, last = month_day_ranks(ief.index)
rows.append(engine.evaluate("C11 IEF last 3 days", pos_from_earn_days(last >= -3), ief, 5))
print(engine.table(rows))
pd.DataFrame(rows).to_csv("study3_results.csv", index=False)

# Descriptive only (no new rules): yearly P&L of C6/C7-style month-end TLT days, gross
t = engine.load("TLT").pct_change().dropna()
f, l = month_day_ranks(t.index)
me = t[l >= -3]
print("\nTLT last-3-day mean bp by period: IS %.1f OOS %.1f HO %.1f; other days %.1f" % (
    me[:"2013"].mean() * 1e4, me["2014":"2019"].mean() * 1e4, me["2020":].mean() * 1e4,
    t[l < -3].mean() * 1e4))
print("by year (sum %):", (me.groupby(me.index.year).sum() * 100).round(1).to_dict())
