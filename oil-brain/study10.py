"""Study 10 (pre-registered 2026-11-24 14:15 UTC, before running): EIA natural gas storage report
(Thursday 10:30 ET) on UNG, hourly Yahoo bars (~730 days; too short for IS/OOS/HOLDOUT, so the gate is
t >= 2 at 2 bp AND still positive at 5 bp AND Thursdays clearly better than the other weekdays).
Literature: Gay, Simkins & Turac (2009) and Linn & Zhu (2004): gas prices react within minutes to
storage surprises, with volatility persisting for hours; whether the move continues is untested here.
 G1 continuation: sign of the Thursday 10:30-11:30 bar, hold 11:30 -> 16:00.
 G2 fade: the opposite of G1.
 G3 last-half-hour momentum (Wen et al. style): sign of the 10:30-11:30 bar -> hold 15:30 -> 16:00.
Controls: the same rules on Monday-Wednesday and Friday.
OPEC production-cut drift (queue item): not tested; only ~6-8 surprise cut announcements since 2014,
too few events for t >= 2 under any rule. Logged as untestable with free data.
"""
import numpy as np, pandas as pd, yfinance as yf
b = yf.Ticker("UNG").history(period="730d", interval="1h"); b.index = b.index.tz_convert("America/New_York")
b = b[(b.index.strftime("%H:%M") >= "09:30") & (b.index.strftime("%H:%M") <= "15:30")]
rec = []
for d, g in b.groupby(b.index.date):
    g = g.sort_index(); hh = list(g.index.strftime("%H:%M"))
    if not all(h in hh for h in ("10:30", "11:30", "15:30")): continue
    i = hh.index
    r1 = g.Close.iloc[i("10:30")] / g.Open.iloc[i("10:30")] - 1
    rest = g.Close.iloc[-1] / g.Close.iloc[i("10:30")] - 1
    last = g.Close.iloc[i("15:30")] / g.Open.iloc[i("15:30")] - 1
    rec.append(dict(wd=pd.Timestamp(d).day_of_week, r1=r1, rest=rest, last=last))
x = pd.DataFrame(rec)
print(f"UNG hourly, {len(x)} days")
for nm, col, sgn in [("G1 continuation to close", "rest", 1), ("G2 fade to close", "rest", -1), ("G3 last half hour", "last", 1)]:
    for wd, lab in [(3, "Thu (report)"), (None, "other days")]:
        m = (x.wd == 3) if wd == 3 else (x.wd != 3)
        for c in (2, 5):
            y = sgn * np.sign(x.r1[m]) * x[col][m] - c / 1e4
            print(f"{nm:26} {lab:13} {c}bp n {len(y):4} mean {y.mean()*1e4:7.2f} bp t {y.mean()/y.std()*np.sqrt(len(y)):5.2f} win {100*(y>0).mean():3.0f}%")
