"""Batch 51 (pre-registered 2026-11-28 before running): the Batch 47 candle-brain rules (C1-C10, B1-B5, unchanged) plus two
classic dip rules (IBS < 0.2 hold 2d; 10-day low close hold 3d) on markets the lab never tested:
 FX on clean CME futures bars (6E, 6B, 6J, 6A, 6C; the Batch 47 FX passes were a Yahoo spot-bar artifact),
 non-US indices (DE30 ^GDAXI, UK100 ^FTSE, JP225 ^N225, HK50 ^HSI, AUS200 ^AXJO, STOXX50 ^STOXX50E, FR40 ^FCHI),
 platinum (PL=F), palladium (PA=F), natural gas (NG=F, intraday-only rules since the chain has roll gaps: B-rules only).
Exposure $1,000 for each new market (Exness min lots for these not yet verified), FX as before.
Costs bp round trip: DE30 2, UK100 2, JP225 3, HK50 5, AUS200 3, STOXX50 4, FR40 3, XPT 15, XPD 20, XNG 30, FX as before.
Same PASS bar (BH over all tests in this batch)."""
import numpy as np, pandas as pd
from brainlab import *
import batch47_candle_brain as B47  # reuse rule definitions (module guarded below)
NEW = {"EURUSD(fut)": ("6E=F", 1100, 2.0), "GBPUSD(fut)": ("6B=F", 1300, 3.0), "JPY(fut)": ("6J=F", 1000, 2.5), "AUDUSD(fut)": ("6A=F", 650, 3.0),
       "CAD(fut)": ("6C=F", 1000, 3.0), "DE30": ("^GDAXI", 1000, 2), "UK100": ("^FTSE", 1000, 2), "JP225": ("^N225", 1000, 3), "HK50": ("^HSI", 1000, 5),
       "AUS200": ("^AXJO", 1000, 3), "STOXX50": ("^STOXX50E", 1000, 4), "FR40": ("^FCHI", 1000, 3), "XPT": ("PL=F", 1000, 15), "XPD": ("PA=F", 1000, 20), "XNG": ("NG=F", 1000, 30)}
rows = []
for mk, (t, exp, bp) in NEW.items():
    d = D(t); d = d[(d.High > d.Low)]
    H = B47.rules(d) if mk != "XNG" else {}
    if mk != "XNG":
        ib = ((d.Close - d.Low) / (d.High - d.Low) < 0.2).astype(float); H["IBS dip"] = (ib, 2)
        H["10-day low"] = ((d.Close <= d.Close.rolling(10).min()).astype(float), 3)
    for nm, (sig, n) in H.items():
        s = sig.fillna(0).values; build = lambda x, d=d, n=n, c=bp: pos_ret(d, hold(x, n), c)
        r = build(s); st = stats(r, exp); st2 = stats(pos_ret(d, hold(s, n), 2 * bp), exp)
        rows.append(dict(rule=nm, market=mk, **st, usd_pre_2x=st2["usd_pre_yr"], _b=(build, s)))
    for nm, (U, Dn, ok, side) in B47.brk(d).items():
        build = lambda m, d=d, U=U, Dn=Dn, side=side, c=bp: straddle(d, U, Dn, pd.Series(np.asarray(m, bool), index=d.index), c, side=side)
        okv = ok.values; r = build(okv); st = stats(r, exp); st2 = stats(straddle(d, U, Dn, ok, 2 * bp, side=side), exp)
        rows.append(dict(rule=nm, market=mk, **st, usd_pre_2x=st2["usd_pre_yr"], _b=(build, okv)))
R = pd.DataFrame(rows); R["p"] = 1.0
cand = R.pre_sh_ok & (R.t_post14 >= 2)
for i in R.index[cand]:
    b, x = R.at[i, "_b"]; R.at[i, "p"] = shift_p(x, b, n=300)
R["fdr"] = bh(R.p.values); R["PASS"] = cand & R.recent_ok & R.fdr & (R.usd_pre_2x > 0)
pd.to_pickle({f"{a}|{b}": c for a, b, c in zip(R["rule"], R["market"], R["_b"])}, "batch51_builders.pkl") if False else None
R.drop(columns="_b").to_csv("batch51_results.csv", index=False)
pd.set_option("display.width", 250); pd.set_option("display.max_rows", 400)
print(R[cand].drop(columns="_b").sort_values("p").to_string(index=False)); print("tests", len(R), "pre", int(cand.sum()), "PASS", int(R.PASS.sum()))
