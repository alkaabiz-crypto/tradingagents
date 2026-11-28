"""Batch 51b: checks of the Batch 51 non-US index breakout leads on markets with clean Yahoo opens
(FTSE/AXJO opens are copies of the prior close and PL/PA bars are mostly flat, so those are discarded).
Random timing with 2,000 shifts (300 cannot resolve p below 0.0033); neighbours NR4..NR8; 2x cost; per-year $."""
import numpy as np, pandas as pd
from brainlab import *
M = {"JP225": ("^N225", 3), "STOXX50": ("^STOXX50E", 4), "DE30": ("^GDAXI", 2), "FR40": ("^FCHI", 3), "HK50": ("^HSI", 5)}
rows = []; ser = {}
for mk, (t, bp) in M.items():
    d = D(t); d = d[d.High > d.Low]; rg = d.High - d.Low; P = CB.detect_patterns(d)
    U, Dn = d.High.shift(), d.Low.shift()
    setups = {"inside bar": P.inside_bar, "ID/NR4": P.inside_bar & P.nr4, "doji": P.doji}
    for n in (4, 5, 6, 7, 8): setups[f"NR{n}"] = rg <= rg.rolling(n).min()
    for nm, m in setups.items():
        ok = m.shift().fillna(False).astype(bool)
        b = lambda x, d=d, U=U, Dn=Dn, bp=bp: straddle(d, U, Dn, pd.Series(np.asarray(x, bool), index=d.index), bp)
        r = b(ok.values); st = stats(r, 1000); st2 = stats(straddle(d, U, Dn, ok, 2 * bp), 1000)
        yr = (r.loc["2007":] * 1000).groupby(r.loc["2007":].index.year).sum()
        p = shift_p(ok.values, b, n=2000) if st["pre_sh_ok"] and st["t_post14"] >= 2 else 1.0
        rows.append(dict(market=mk, setup=nm, **{k: st[k] for k in ("2007-13", "2014-19", "2020-23", "2024-now", "t_post14", "usd_pre_yr", "usd_24_yr", "drop14", "trades_yr")},
                         usd_2x=st2["usd_pre_yr"], losing_yrs=f"{(yr < 0).sum()}/{len(yr)}", p=round(p, 4)))
        ser[f"{mk} {nm}"] = r * 1000
R = pd.DataFrame(rows); R.to_csv("batch51b_results.csv", index=False); pd.to_pickle(ser, "batch51b_series.pkl")
pd.set_option("display.width", 250); print(R.to_string(index=False))
