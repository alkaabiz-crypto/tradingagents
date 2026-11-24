"""Study 2 (calendar brain): classic calendar effects, daily close-to-close. PRE-REGISTERED
2026-11-24 before running. All windows are taken from the papers; nothing is chosen on data.
Position is set at the close of day t for day t+1 (the exchange calendar is known in advance).
Costs 5 bp per unit of turnover (RULES.md). Benchmark: buy-and-hold of the traded instrument.

  C1 TOM SPY: long trading days -1..+3 around month end (Lakonishok & Smidt 1988;
     McConnell & Xu 2008 "Equity returns at the turn of the month"), flat otherwise.
  C2 TOM IWM: same (small caps, where the effect was historically larger).
  C3 Pre-holiday SPY (Ariel 1990): long only the last trading day before each exchange holiday
     (holidays = weekdays without trading, excluding unscheduled closures 9/11/2001 and
     Hurricane Sandy 2012).
  C4 Thanksgiving SPY: long Wednesday before Thanksgiving and the Friday after (position from
     Tuesday close to Friday close).
  C5 Option-expiration week SPY (Stivers & Sun 2013, high returns in opex week): long from the
     close before the first trading day of the week containing the monthly expiry (3rd Friday,
     or the Thursday before when that Friday is a holiday) through the expiry-day close.
  C6 Month-end rebalancing SPY-TLT (Harvey, Mazzoleni & Melone 2025, "The unintended
     consequences of rebalancing"): at the close of trading day -6, signal = SPY minus TLT
     return month-to-date; hold -sign(signal) of the spread (long SPY / short TLT, or the
     reverse) over days -5..-1. Traded return = SPY ret - TLT ret, cost 10 bp per unit
     (5 bp per leg). Benchmark: buy-and-hold of the spread.
  C7 TLT month-end (Treasury index-extension buying, e.g. Hartley & Schwarz): long TLT on
     the last 3 trading days of the month (-3..-1). Window not verified against the paper.
  C8 TOM XLE: C1 applied to energy equities.
  C9 TOM USO: C1 applied to the oil ETF (no strong prior; USO rolls ~2 weeks before expiry,
     not at month-end).
FOMC pre-announcement drift (Lucca & Moench 2015) is SKIPPED: federalreserve.gov is blocked
from this sandbox and the 1994-2026 scheduled dates cannot be listed from memory without error.
Prior: TOM is the best documented; pre-holiday and opex have been reported to decay. Expect
most to fail gate 2 (beat buy-and-hold Sharpe) because they are flat most of the time.
"""
import numpy as np
import pandas as pd
from common import engine, daily_ret, month_day_ranks, pos_from_earn_days, holidays

rows = []


def tom(sym):
    r = daily_ret(sym)
    first, last = month_day_ranks(r.index)
    earn = (last == -1) | (first <= 3)
    return pos_from_earn_days(earn), r


for name, sym in [("C1 TOM SPY", "SPY"), ("C2 TOM IWM", "IWM")]:
    p, r = tom(sym)
    rows.append(engine.evaluate(name, p, r, 5))

# C3 pre-holiday
r = daily_ret("SPY")
spy_idx = engine.load("SPY").index
H = holidays(spy_idx)
nxt_trade = pd.Series(spy_idx[1:].append(pd.DatetimeIndex([spy_idx[-1] + pd.Timedelta(days=3)])),
                      index=spy_idx)
pre = pd.Series(False, index=spy_idx)
for d in spy_idx:
    gap_days = pd.bdate_range(d + pd.Timedelta(days=1), nxt_trade[d] - pd.Timedelta(days=1))
    if len(gap_days.intersection(H)) > 0:
        pre[d] = True
pre = pre.reindex(r.index).fillna(False)
rows.append(engine.evaluate("C3 pre-holiday SPY", pos_from_earn_days(pre), r, 5))
print("pre-holiday days per year ~", round(pre.sum() / (len(pre) / 252), 1))

# C4 Thanksgiving: 4th Thursday of November
earn = pd.Series(False, index=r.index)
for y in sorted(set(r.index.year)):
    nov = pd.date_range(f"{y}-11-01", f"{y}-11-30")
    th = nov[nov.dayofweek == 3][3]
    for d in (th - pd.Timedelta(days=1), th + pd.Timedelta(days=1)):
        if d in earn.index:
            earn[d] = True
rows.append(engine.evaluate("C4 Thanksgiving SPY", pos_from_earn_days(earn), r, 5))

# C5 opex week
earn = pd.Series(False, index=r.index)
idx = r.index
for (y, m), g in pd.Series(idx, index=idx).groupby([idx.year, idx.month]):
    days = pd.date_range(f"{y}-{m:02d}-01", periods=31)
    days = days[days.month == m]
    fri3 = days[days.dayofweek == 4][2]
    exp = fri3 if fri3 in idx else fri3 - pd.Timedelta(days=1)
    mon = fri3 - pd.Timedelta(days=4)
    earn[(idx >= mon) & (idx <= exp)] = True
rows.append(engine.evaluate("C5 opex week SPY", pos_from_earn_days(earn), r, 5))

# C6 rebalancing spread
spy, tlt = engine.load("SPY"), engine.load("TLT")
px = pd.concat([spy, tlt], axis=1, keys=["S", "B"]).dropna()
rr = px.pct_change().dropna()
spread = rr.S - rr.B
first, last = month_day_ranks(rr.index)
prev_m_close = px.groupby([px.index.year, px.index.month]).tail(1)


anchor = prev_m_close.copy()
anchor.index = anchor.index + pd.offsets.MonthBegin(1)  # anchor for next month
anc = anchor.reindex(rr.index, method="ffill")
mtd_rel = (px.S.reindex(rr.index) / anc.S - 1) - (px.B.reindex(rr.index) / anc.B - 1)
pos = pd.Series(0.0, index=rr.index)
sig_days = rr.index[last == -6]
for d in sig_days:
    s = -np.sign(mtd_rel[d])
    m = (rr.index.year == d.year) & (rr.index.month == d.month) & (last.values >= -6) & (last.values <= -2)
    pos[m] = s
rows.append(engine.evaluate("C6 month-end rebalancing SPY-TLT", pos, spread, 10))

# C7 TLT month-end
rt = daily_ret("TLT")
first, last = month_day_ranks(rt.index)
rows.append(engine.evaluate("C7 TLT last 3 days", pos_from_earn_days(last >= -3), rt, 5))

for name, sym in [("C8 TOM XLE", "XLE"), ("C9 TOM USO", "USO")]:
    p, r2 = tom(sym)
    rows.append(engine.evaluate(name, p, r2, 5))

print(engine.table(rows))
pd.DataFrame(rows).to_csv("study2_results.csv", index=False)
