"""Study 3 - isolate insider TIMING from the stock-selection drag with a matched control pool.

PRE-REGISTRATION (written 2026-11-24 after study2, before running this file)
CONTAMINATION WARNING: this idea came from looking at post-2014 numbers of I7 (EW-hedged book
Sharpe -0.17 while its placebo books averaged -0.58, p=0.014): stocks where insiders buy
underperform the large-cap universe at ALL times, but less so in the 63 days after a purchase.
So this study is informed by OOS/HOLDOUT. Even a full pass can only be a "candidate" for
forward testing, never a winner, and must be discounted. No parameter is tuned: hold 63 (from
IS in study1), pool window 756 trading days (~3 years, fixed a priori), same events as I2/I5.

Design: long names with an active purchase event (equal weight); short, with equal gross, the
equal-weight "control pool" = universe names that had a purchase event (same filter) within the
trailing 756 trading days but have no active event now (fallback: whole universe when the pool
is empty). 10 bp per side on every leg incl. pool rebalancing. Passive benchmark = 0, so gate 2
is post Sharpe > 0. Placebo shifts the events and rebuilds both the long side and the pool.

Rules (2 more; 10 of 15 used):
  I9   all buys >= $10k (I2 events), pool-hedged, hold 63
  I10  buys >= $100k (I5 events), pool-hedged, hold 63
"""
import pandas as pd
import lib

if __name__ == "__main__":
    uni = lib.load_universe()
    bk = lib.Book(uni, lib.load_prices())
    bk.hedge = "pool"
    p = lib.filings("P"); p = p[p.cik.isin(bk.col)]
    rows = []
    for name, ev in [("I9 any buy, control-pool hedge, hold 63", p[p.value >= 10_000]),
                     ("I10 buys>=100k, control-pool hedge, hold 63", p[p.value >= 100_000])]:
        ei = bk.entry_idx(ev.fdate.values); ej = ev.cik.map(bk.col).values
        out, r = lib.evaluate(name, bk, ei, ej, 63)
        rows.append(out)
        print(lib.show([out]), flush=True)
        yr = r.groupby(r.index.year).apply(lambda x: x.mean() / x.std() * 252 ** .5 if x.std() > 0 else 0)
        print("  yearly Sharpe:", yr.round(2).to_dict())
    print(lib.show(rows))
    pd.DataFrame(rows).to_csv(lib.os.path.join(lib.HERE, "study3_results.csv"), index=False)
