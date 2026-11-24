"""Study 1 - plain insider purchases and clusters in today's 500 largest US Section-16 issuers.

PRE-REGISTRATION (written before any return was computed, 2026-11-24)
Data: SEC DERA Insider Transactions Data Sets 2006q1-2026q3, Form 4 (no amendments),
non-derivative, code P with acquired flag A, reporting owner an officer and/or director
(pure 10% owners and 'Other' excluded). One event per filing. Signal date = FILING_DATE; entry at
the close of the next trading day (lib.Book.entry_idx). Universe: first 500 issuers (by SEC's
current size ordering) with Form 4 P/S rows and Yahoo prices -> SURVIVORSHIP BIAS (today's large
caps). Benchmark = same-universe equal-weight minus SPY, which absorbs that bias.
Splits: IS 2006-01..2013-12 (data begin 2006; engine IS_END unchanged), OOS 2014-2019,
HOLDOUT 2020-now. Book: equal weight across names with an active event, short SPY 1:1,
10 bp per side on all legs. Gates: lib docstring (event-date-shift placebo, 2x costs).

Rules (3 of 15 budget):
  I1  any purchase filing with value >= $10k, hold 21 trading days   (Lakonishok & Lee 2001;
      Jeng, Metrick & Zeckhauser 2003: most abnormal return in the first month)
  I2  same events, hold 63 trading days                               (LL01 use 6-12 months)
  I3  cluster: a purchase filing (>= $10k) on a day when >= 2 distinct insiders of the same firm
      have filed purchases within the trailing 30 calendar days; hold 63 days
Expectation: weak, because LL01/JMZ find the purchase effect mostly in small firms; large caps
are the hard case. Diagnostic (not a rule): mean event excess return vs SPY over +1..+21 and
+1..+63 days, by split.
"""
import json
import numpy as np
import pandas as pd
import lib


def events_any(p, minv=10_000):
    return p[p.value >= minv]


def events_cluster(p, k=2, days=30, minv=10_000):
    p = p[p.value >= minv].sort_values("fdate")
    keep = []
    for cik, g in p.groupby("cik"):
        d, o = g.fdate.values, g.owner.values
        for i in range(len(g)):
            m = (d >= d[i] - np.timedelta64(days, "D")) & (d <= d[i])
            if len(set(o[m])) >= k:
                keep.append(g.index[i])
    return p.loc[keep]


def car(bk, ev_i, ev_j, h):
    R = np.nan_to_num(bk.R) - bk.spy[:, None]
    T = len(R)
    out = []
    for i, j in zip(ev_i, ev_j):
        if i + h < T:
            out.append(np.prod(1 + R[i + 1:i + h + 1, j]) - 1)
        else:
            out.append(np.nan)
    return np.array(out)


if __name__ == "__main__":
    uni = lib.load_universe()
    bk = lib.Book(uni, lib.load_prices())
    p = lib.filings("P")
    p = p[p.cik.isin(bk.col)]
    rows = []
    specs = [("I1 any buy >=10k, hold 21", events_any(p), 21),
             ("I2 any buy >=10k, hold 63", events_any(p), 63),
             ("I3 cluster >=2 insiders/30d, hold 63", events_cluster(p), 63)]
    for name, ev, h in specs:
        ei = bk.entry_idx(ev.fdate.values)
        ej = ev.cik.map(bk.col).values
        d = bk.dates[np.clip(ei, 0, len(bk.dates) - 1)]
        for hh in (21, 63):
            c = car(bk, ei, ej, hh)
            for lab, m in [("IS", d <= "2013-12-31"), ("OOS", (d > "2013-12-31") & (d <= "2019-12-31")),
                           ("HO", d > "2019-12-31")]:
                x = c[m]; x = x[~np.isnan(x)]
                print(f"  diag {name[:2]} CAR+{hh} {lab}: n={len(x)} mean={x.mean():.4f} t={x.mean()/x.std()*np.sqrt(len(x)):.2f}")
        out, r = lib.evaluate(name, bk, ei, ej, h)
        rows.append(out)
        print(lib.show([out]), flush=True)
    print(lib.show(rows))
    pd.DataFrame(rows).to_csv(lib.os.path.join(lib.HERE, "study1_results.csv"), index=False)
