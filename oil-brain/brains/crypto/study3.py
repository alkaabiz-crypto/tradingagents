"""Study 3: day-of-week and Nasdaq lead-lag (pre-registered 2026-11-24, before running).

Mechanisms:
  - Day-of-week: Caporale & Plastun (2019, Finance Research Letters) report abnormally high BTC
    returns on Mondays; weekend thin liquidity (no US institutional desks) argued to shift returns
    into Monday. Yahoo daily bars are UTC days, so "Monday" = Monday 00:00-24:00 UTC.
  - Crypto vs Nasdaq: since ~2020 BTC co-moves with tech stocks; if equity news diffuses slowly into
    crypto, last week's QQQ return should predict BTC's next day (lead-lag). Liu & Tsyvinski 2021
    found little exposure to stock factors in their sample, so prior is weak.
Time-of-day: Yahoo hourly history is only 730 days -> not testable in-sample; not run.

Rules (2 of 15, total so far 9 incl. R5 diagnostic slot):
  R8 btc_monday: long BTC only for the Monday UTC bar (position = 1 at Sunday close), else flat.
  R9 btc_qqq_lead: long BTC when QQQ's trailing 5-trading-day return (last QQQ close, 16:00 ET,
     which is before the BTC bar's 00:00 UTC close of the same date) > 0, else flat.
Expectation: both fail. R8 exposure is 1/7, so it cannot beat buy-and-hold Sharpe unless the
Monday mean is huge.
"""
from common import *

btc = ret("BTC-USD"); cb = px("BTC-USD")
# position at close of date t earns bar t+1. Monday bar follows Sunday close (dayofweek 6).
p8 = pd.Series((cb.index.dayofweek == 6).astype(float), index=cb.index)
dow = btc.groupby(btc.index.dayofweek).agg(["mean", "std", "count"])
dow["t"] = dow["mean"] / dow["std"] * np.sqrt(dow["count"])
print("BTC mean return by UTC weekday (0=Mon), full sample:\n", (dow * [1e4, 1e4, 1, 1]).round(2).to_string())
for a, b_ in [("2014", "2018"), ("2019", "2021"), ("2022", "2026")]:
    x = btc.loc[a:b_]; print(a, b_, (x.groupby(x.index.dayofweek).mean() * 1e4).round(1).to_dict())
q = shared_close("QQQ")
q5 = q.pct_change(5)
p9 = (q5 > 0).astype(float).reindex(cb.index, method="ffill").fillna(0)
E, C = [], []
for name, pos in [("R8 btc_monday", p8), ("R9 btc_qqq_lead", p9)]:
    e, c = both(name, pos, btc); E.append(e); C.append(c)
show(E, C)
pd.DataFrame(E).merge(pd.DataFrame(C), on="rule").to_csv(os.path.join(HERE, "study3_results.csv"), index=False)
