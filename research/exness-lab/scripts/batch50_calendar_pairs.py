"""Batch 50 (pre-registered 2026-11-28 before running): known anomalies not yet tested in the lab.
 E1 pre-holiday: long at the close of the last session before a scheduled NYSE holiday, out next close (US500, USTEC, US30).
    Holidays = a skipped weekday in SPY's calendar; unscheduled closures (9/11, Reagan, Ford, Sandy, Bush, Carter) removed.
 E2 Turnaround Tuesday: Monday close below Friday close -> long Monday close to Tuesday close (US500, USTEC, US30).
 E3 gold/silver ratio pair: z60 of log(GLD/SLV) > 2 -> long silver/short gold, < -2 the reverse, out at |z| < 0.5; $3,640 a leg.
 E4 ETH ID/NR4 straddle (from Batch 47) also on ETH at 2x cost and with 1-day delay as a check (not a new test).
Same PASS bar."""
import numpy as np, pandas as pd
from brainlab import *
s = D("SPY"); idx = s.index
nxt = pd.Series(idx[1:].append(pd.DatetimeIndex([idx[-1] + pd.Timedelta(days=1)])), index=idx)
gap_bd = np.busday_count(idx.values.astype("datetime64[D]"), nxt.values.astype("datetime64[D]"))
unsched = pd.to_datetime(["2001-09-10", "2004-06-10", "2006-12-29", "2012-10-26", "2018-12-04", "2025-01-08"])
pre_h = pd.Series((gap_bd > 1), index=idx) & ~idx.isin(unsched)
rows = []; tests = []
for mk, t, exp, bp in (("US500", "SPY", 1000, 1.6), ("USTEC", "QQQ", 1330, 1.4), ("US30", "DIA", 500, 1.3)):
    d = D(t); ph = pre_h.reindex(d.index).fillna(False).astype(float).values
    tests.append(("E1 pre-holiday", mk, exp, ph, lambda x, d=d, bp=bp: pos_ret(d, hold(x, 1), bp)))
    c = d.Close; mon_dn = ((d.index.dayofweek == 0) & (c < c.shift())).astype(float)
    tests.append(("E2 turnaround Tuesday", mk, exp, np.asarray(mon_dn), lambda x, d=d, bp=bp: pos_ret(d, hold(x, 1), bp)))
g, sv = D("GLD"), D("SLV"); j = g.index.intersection(sv.index); g, sv = g.loc[j], sv.loc[j]
lr = np.log(g.Close / sv.Close); z = (lr - lr.rolling(60).mean()) / lr.rolling(60).std()
def state(el, xl, es, xs):
    p, out = 0, []
    for a, b, c_, d_ in zip(el, xl, es, xs):
        if p == 0: p = 1 if a else (-1 if c_ else 0)
        elif p == 1 and b: p = 0
        elif p == -1 and d_: p = 0
        out.append(p)
    return np.array(out, float)
e3 = state((z > 2).values, (z.abs() < 0.5).values, (z < -2).values, (z.abs() < 0.5).values)
spread = (sv.Close.pct_change() - g.Close.pct_change()).fillna(0)
pair = lambda x: pd.Series(x, index=j).shift().fillna(0) * spread - pd.Series(x, index=j).diff().abs().fillna(0) * 9.5 / 2e4
tests.append(("E3 gold/silver pair", "XAG/XAU", 3640, e3, pair))
for nm, mk, exp, sig, b in tests:
    r = b(sig); st = stats(r, exp); rows.append(dict(rule=nm, market=mk, **st, _b=(b, sig)))
R = pd.DataFrame(rows); R["p"] = 1.0
cand = R.pre_sh_ok & (R.t_post14 >= 2)
for i in R.index[cand]:
    b, x = R.at[i, "_b"]; R.at[i, "p"] = shift_p(x, b, n=300)
R["fdr"] = bh(R.p.values); R["PASS"] = cand & R.recent_ok & R.fdr
R.drop(columns="_b").to_csv("batch50_results.csv", index=False)
pd.set_option("display.width", 250); print(R.drop(columns="_b").to_string(index=False))
e = D("ETH-USD"); P = CB.detect_patterns(e); ok = (P.inside_bar & P.nr4).shift().fillna(False).astype(bool)
for lab, okk, bp in (("base", ok, 5), ("2x cost", ok, 10), ("1-day delay", ok.shift().fillna(False).astype(bool), 5)):
    r = straddle(e, e.High.shift(), e.Low.shift(), okk, bp) if lab != "1-day delay" else straddle(e, e.High.shift(2), e.Low.shift(2), okk, bp)
    st = stats(r, 165); print("ETH ID/NR4", lab, {k: st[k] for k in ("2014-19", "2020-23", "2024-now", "usd_pre_yr", "usd_24_yr", "drop14", "trades_yr")})
