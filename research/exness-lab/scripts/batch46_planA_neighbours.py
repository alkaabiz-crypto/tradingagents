"""Batch 46, pre-registered 2026-11-28 (Hazza: is Plan A the best, or does adding / removing / swapping a part beat it?).
Start from Plan A = 10-day low US500 + BTC NR4 + BTC Williams + ETH above 50-day. Try every single change: remove one part, add one
strategy, swap one part for one strategy. Candidates: every strategy on paper (daily ones) plus BTC hourly trend (Bitstamp/Yahoo hourly).
ETH London breakout is left out: no ETH hourly data before 2024 to judge it on.
Score = profit per year / |worst drop| on 2014-10..2023 (pick period). Limits: worst drop 2014-23 <= $300 and <= $3,000 open at once.
A change only counts as better if its pick-period score beats Plan A by > 10% AND its 2024+ score is also higher.
$ = % x today's min-lot exposure, Exness costs."""
import io, contextlib, numpy as np, pandas as pd
with contextlib.redirect_stdout(io.StringIO()): exec(open("lab/batch38b_minlot.py").read().split("res = []")[0])
src = open("lab/batch44_btc_hourly_pre2024.py").read().split("for rule, mode")[0]
with contextlib.redirect_stdout(io.StringIO()): exec(src)
t_old = run("BTCH", "R3", "B"); 
MK["BTCN"] = ("BTC-USD_60m", "BTC-USD", 0.01, 1.1); t_new = run("BTCN", "R3", "B")
th = pd.concat([t_old[t_old.index < t_new.index[0]], t_new]); th.index = th.index.tz_convert(None).normalize(); th = th.groupby(th.index).sum()
U["BTC hourly trend"] = th.reindex(U.index).fillna(0); G["BTC hourly trend"] = (U["BTC hourly trend"] != 0) * 600
# approximate open-exposure for the hourly rule: in a trade ~ half the days
plan = ["10-day low US500", "BTC NR4", "BTC Williams (T1)", "ETH above 50-day"]
cands = [c for c in U.columns if c not in plan and not c.startswith("N1")]  # N1 is a near-copy of IBS USTEC
pre = (U.index >= "2014-10") & (U.index < "2024"); oos = U.index >= "2024"; yp, yo = (U.index[pre][-1] - U.index[pre][0]).days / 365.25, (U.index[-1] - pd.Timestamp("2024-01-01")).days / 365.25
def dd(x): e = np.cumsum(x); return (e - np.maximum.accumulate(e)).min()
def score(legs_):
    u = U[legs_].sum(axis=1).values; g = G[legs_].sum(axis=1).values
    a, b = u[pre], u[oos]; da, db = dd(a), dd(b)
    return dict(per_yr_pre=a.sum() / yp, dd_pre=da, sc_pre=a.sum() / yp / -da, per_yr_24=b.sum() / yo, dd_24=db, sc_24=b.sum() / yo / -db, max_open=g.max())
base = score(plan); rows = [dict(change="Plan A (no change)", **base)]
for p in plan: rows.append(dict(change=f"remove {p}", **score([x for x in plan if x != p])))
for c in cands: rows.append(dict(change=f"add {c}", **score(plan + [c])))
for p in plan:
    for c in cands: rows.append(dict(change=f"swap {p} -> {c}", **score([x for x in plan if x != p] + [c])))
df = pd.DataFrame(rows); n = len(df) - 1
df["ok_limits"] = (df.dd_pre >= -300) & (df.max_open <= 3000)
df["better"] = df.ok_limits & (df.sc_pre > 1.1 * base["sc_pre"]) & (df.sc_24 > base["sc_24"])
pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 70)
print("variants tested:", n, "| within limits:", int(df.ok_limits.sum()) - 1, "| better in both periods:", int(df.better.sum()))
print(df.round(2).iloc[[0]].to_string(index=False))
print(df[df.ok_limits].sort_values("sc_pre", ascending=False).head(15).round(2).to_string(index=False))
print("\nbetter in both periods:"); print(df[df.better].round(2).to_string(index=False))
# chance check: how often does a random reshuffle of 'pre' vs '2024' rankings give that many joint winners? use rank correlation
ok = df[df.ok_limits].iloc[1:]; print("rank correlation of pre vs 2024 scores among valid variants:", round(ok.sc_pre.rank().corr(ok.sc_24.rank()), 2))
df.to_csv("lab/batch46_results.csv", index=False)
