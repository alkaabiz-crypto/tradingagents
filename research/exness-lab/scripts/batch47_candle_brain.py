"""Batch 47 (pre-registered 2026-11-28 before running): candle brain = pattern + context, 14 Exness markets.
Earlier candle tests (Batch 35) used bare textbook patterns on indices/crypto and failed. Here every pattern must sit
in a stated context (trend vs 200-day, location at an N-day low/high, range vs ATR) and markets add gold, silver,
WTI, Brent and five FX pairs. Settings fixed in advance, nothing tuned.
Close-hold (signal at close t, filled at that close, held N days):
 C1 hammer at 20-day low in uptrend -> long 2d        C2 key reversal up at 10-day low -> long 3d
 C3 bull engulfing at 10-day low in uptrend -> long 3d C4 shooting star at 20-day high in downtrend -> short 2d
 C5 key reversal down at 10-day high in downtrend -> short 3d
 C6 outside-up bar (close top 30%) with range >= 1.5 ATR -> long 1d
 C7 wide-range bar (>= 2 ATR) close near high -> long 2d, close near low -> short 2d (continuation)
 C8 three white soldiers in uptrend -> long 3d, three black crows in downtrend -> short 3d
 C9 doji at 20-day high after 3 up closes -> short 2d   C10 close near low (IBS<=0.1) with range >= 1 ATR in uptrend -> long 2d
Day trades (stop orders next day, exit at the close, opposite level = stop, both hit = full-range loss, +2 bp slippage):
 B1 inside bar straddle   B2 inside bar + NR4 straddle   B3 NR7 straddle   B4 inside bar, only in 50-day trend direction
 B5 doji straddle
PASS: Sharpe > 0.3 in 2014-19 and 2020-23 (pick), Sharpe > 0.3 in 2024-now (confirm), t >= 2 post-2014, then beats
300 circular shifts of its own signal on 2007-23 (p) with BH FDR q < 0.10 over all 210 tests, positive at 2x cost."""
import numpy as np, pandas as pd
from brainlab import *
def rules(d):
    P = CB.detect_patterns(d); F = CB.candle_features(d); c = d.Close
    up = F.trend_200 > 0; dn = F.trend_200 < 0
    up3 = (c > c.shift()) & (c.shift() > c.shift(2)) & (c.shift(2) > c.shift(3))
    H = {}
    H["C1"] = (P.hammer & F.at_20d_low & up).astype(float), 2
    H["C2"] = (P.key_reversal_up & F.at_10d_low).astype(float), 3
    H["C3"] = (P.bull_engulfing & F.at_10d_low & up).astype(float), 3
    H["C4"] = -(P.shooting_star & F.at_20d_high & dn).astype(float), 2
    H["C5"] = -(P.key_reversal_down & F.at_10d_high & dn).astype(float), 3
    H["C6"] = (P.outside_up & (F.range_atr >= 1.5)).astype(float), 1
    H["C7"] = ((P.wide_range & P.close_near_high).astype(float) - (P.wide_range & P.close_near_low).astype(float)), 2
    H["C8"] = ((P.three_white_soldiers & up).astype(float) - (P.three_black_crows & dn).astype(float)), 3
    H["C9"] = -(P.doji & F.at_20d_high & up3).astype(float), 2
    H["C10"] = (P.close_near_low & (F.range_atr >= 1.0) & up).astype(float), 2
    return H
def brk(d):
    P = CB.detect_patterns(d); c = d.Close; tr50 = np.sign(c - c.rolling(50).mean()).shift().fillna(0)
    U, Dn = d.High.shift(), d.Low.shift(); sh = lambda m: m.shift().fillna(False).astype(bool)
    return {"B1": (U, Dn, sh(P.inside_bar), 0), "B2": (U, Dn, sh(P.inside_bar & P.nr4), 0), "B3": (U, Dn, sh(P.nr7), 0),
            "B4": (U, Dn, sh(P.inside_bar), tr50.values), "B5": (U, Dn, sh(P.doji), 0)}
if __name__ == '__main__':
    rows = []
    for mk, (hp, bp_t, exp, bp) in MK.items():
        d = D(hp)
        for nm, (sig, n) in rules(d).items():
            s = sig.fillna(0).values
            build = lambda x, d=d, n=n, c=bp: pos_ret(d, hold(x, n), c)
            r = build(s); st = stats(r, exp); st2 = stats(pos_ret(d, hold(s, n), 2 * bp), exp)
            rows.append(dict(rule=nm, market=mk, **st, usd_pre_2x=st2["usd_pre_yr"], _b=(build, s)))
        db = D(bp_t)
        for nm, (U, Dn, ok, side) in brk(db).items():
            build = lambda m, db=db, U=U, Dn=Dn, side=side, c=bp: straddle(db, U, Dn, pd.Series(np.asarray(m, bool), index=db.index), c, side=side)
            okv = ok.values; r = build(okv); st = stats(r, exp)
            st2 = stats(straddle(db, U, Dn, ok, 2 * bp, side=side), exp)
            rows.append(dict(rule=nm, market=mk, **st, usd_pre_2x=st2["usd_pre_yr"], _b=(build, okv)))
    R = pd.DataFrame(rows); R["p"] = 1.0
    cand = R.pre_sh_ok & (R.t_post14 >= 2)
    for i in R.index[cand]:
        b, x = R.at[i, "_b"]; R.at[i, "p"] = shift_p(x, b, n=300)
    R["fdr"] = bh(R.p.values); R["PASS"] = cand & R.recent_ok & R.fdr & (R.usd_pre_2x > 0)
    R = R.drop(columns="_b"); R.to_csv("batch47_results.csv", index=False)
    pd.set_option("display.width", 250); pd.set_option("display.max_rows", 300)
    print(R[cand].sort_values("p").to_string(index=False))
    print("tests", len(R), "pre-pass", int(cand.sum()), "PASS", int(R.PASS.sum()))
