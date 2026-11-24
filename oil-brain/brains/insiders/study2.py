"""Study 2 - who buys and how much: opportunistic insiders, big purchases, top executives,
a survivorship-neutral hedge, and a sales negative control.

PRE-REGISTRATION (written 2026-11-24 after study1, before running this file)
What study1 taught (all splits seen for I1-I3, so nothing below is tuned on them except the
hold length, which is chosen from IS only): IS Sharpe favours 63-day holds (I2 1.13 vs I1 0.65),
so every rule here holds 63 trading days. Same data, universe, entry lag, costs, gates as study1.
The same-universe passive basket minus SPY has post-2014 Sharpe 1.00 (survivorship), and placebo
books average 0.37, so a SPY-hedged book of today's large caps carries a big drift unrelated to
insider timing.

Rules (5 more; 8 of 15 used):
  I4  opportunistic buys (Cohen, Malloy & Pomorski 2012): owner-firm pair with >= 1 P/S trade in
      each of the 3 preceding calendar years; "routine" if it traded in the same calendar month
      in all 3 of those years; I4 = purchases (>= $10k) by non-routine (opportunistic) owners.
      Events exist from 2009.
  I5  large purchases: filing value >= $100k (Seyhun 1986 / LL01: bigger trades carry more info).
  I6  top-executive purchases: title contains CEO / Chief Executive / CFO / Chief Financial /
      President / Chairman (hierarchy hypothesis, Seyhun 1986; Wang, Shin & Francis 2012).
  I7  I2's events (all buys >= $10k) but hedged with the equal-weight universe instead of SPY.
      This removes the survivorship drift; its passive benchmark is exactly zero, so gate 2
      becomes post Sharpe > 0 (deviation stated here before running).
  I8  NEGATIVE CONTROL: long stocks after a sales cluster (>= 3 distinct officer/director sellers
      within 30 calendar days, any size), SPY-hedged. Literature: sales carry little or negative
      information; expected to look like placebo. Counted as a rule.
"""
import numpy as np
import pandas as pd
import lib
from study1 import events_cluster

TOP = r"CEO|Chief Executive|CFO|Chief Financial|President|Chairman|Chair\b"


def opportunistic(p_all, buys):
    """p_all: all P and S filings (officer/director). Return the subset of buys whose owner is
    classifiable and not routine."""
    a = p_all.assign(y=p_all.tdate.dt.year, m=p_all.tdate.dt.month).dropna(subset=["y"])
    ym = a.groupby(["owner", "cik"]).apply(lambda g: set(zip(g.y.astype(int), g.m.astype(int))))
    keep = []
    for idx, r in buys.iterrows():
        s = ym.get((r.owner, r.cik))
        if s is None or pd.isna(r.tdate):
            continue
        y0 = r.tdate.year
        years = {y for y, _ in s}
        if not all((y0 - k) in years for k in (1, 2, 3)):
            continue  # not classifiable
        routine = any(all((y0 - k, mm) in s for k in (1, 2, 3)) for mm in range(1, 13))
        if not routine:
            keep.append(idx)
    return buys.loc[keep]


if __name__ == "__main__":
    uni = lib.load_universe()
    bk = lib.Book(uni, lib.load_prices())
    p = lib.filings("P"); p = p[p.cik.isin(bk.col)]
    s = lib.filings("S"); s = s[s.cik.isin(bk.col)]
    buys = p[p.value >= 10_000]
    opp = opportunistic(pd.concat([p, s]), buys)
    big = p[p.value >= 100_000]
    top = buys[buys.title.fillna("").str.contains(TOP, case=False, regex=True)]
    sclu = events_cluster(s, k=3, days=30, minv=0)
    print("event counts:", dict(opp=len(opp), big=len(big), top=len(top), sales_cluster=len(sclu)))
    specs = [("I4 opportunistic buys, hold 63", opp, "spy"),
             ("I5 buys >= $100k, hold 63", big, "spy"),
             ("I6 CEO/CFO/Pres/Chair buys, hold 63", top, "spy"),
             ("I7 any buy, EW-universe hedge, hold 63", buys, "ew"),
             ("I8 CONTROL sales cluster >=3, hold 63", sclu, "spy")]
    rows = []
    for name, ev, hedge in specs:
        bk.hedge = hedge
        ei = bk.entry_idx(ev.fdate.values); ej = ev.cik.map(bk.col).values
        out, r = lib.evaluate(name, bk, ei, ej, 63)
        rows.append(out)
        print(lib.show([out]), flush=True)
    print(lib.show(rows))
    pd.DataFrame(rows).to_csv(lib.os.path.join(lib.HERE, "study2_results.csv"), index=False)
