"""Study 4 - the short-horizon version (last rule this brain runs).

PRE-REGISTRATION (written 2026-11-24 after study3, before running this file)
Jeng, Metrick & Zeckhauser (2003) report that a large share of the purchase abnormal return
comes in the first days after the trade. Our entry is already 1 trading day after the FILING
date (often 2-4 days after the trade date), so much of that may be gone. Study1's CAR+21 was
negative in OOS (-0.18%), so the prior is weak; this run exists to answer the question plainly,
not because anything suggests it will work. Same events as I2 (all officer/director buys
>= $10k), SPY hedge, 10 bp per side, hold 5 trading days.

Rule (1 more; 11 of 15 used):
  I11  any buy >= $10k, SPY-hedged, hold 5
"""
import pandas as pd
import lib

if __name__ == "__main__":
    uni = lib.load_universe()
    bk = lib.Book(uni, lib.load_prices())
    p = lib.filings("P"); p = p[p.cik.isin(bk.col)]
    ev = p[p.value >= 10_000]
    ei = bk.entry_idx(ev.fdate.values); ej = ev.cik.map(bk.col).values
    out, r = lib.evaluate("I11 any buy >=10k, hold 5", bk, ei, ej, 5)
    print(lib.show([out]))
    pd.DataFrame([out]).to_csv(lib.os.path.join(lib.HERE, "study4_results.csv"), index=False)
