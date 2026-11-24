"""Study 3 (earnings brain): cheaper ways to hold the announcement premium.
PRE-REGISTERED 2026-11-24, after study 2 and before any study-3 return was computed.

What study 2 showed (stated honestly, OOS/HOLDOUT were already seen): A1 earns ~10%/yr GROSS
post-2014 but -7% net; the daily equal-weight re-normalisation churns every held name whenever
one enters or exits, and each 4-day event pays ~40 bp round trip (stock + hedge) against
~16 bp of gross premium. The two rules below change only the portfolio mechanics, using
mechanisms from the papers; no window or threshold was tuned on any period.

  A3 = A1 with fixed slots: each active position weight 1/10 (constant), EW-universe hedge;
     exposure varies with the number of names; no churn of other names. (Sharpe does not depend
     on the slot size apart from its effect on nothing, so 10 is not a tuned parameter.)
  E1 Frazzini & Lamont (2007) monthly announcer portfolio: at the last trading day of each month,
     long (equal weight) every stock whose predicted date P (day 0 + 364 calendar days of the
     event a year earlier) falls in the next calendar month; hedge with the EW universe; hold
     to the next month end. One rebalance a month.
Costs 10 bp per side; gates as study 2 (bench SPY buy-and-hold, event-date placebo: P moved by
random +-10..50 trading days, 200 placebos; gate 5 on the 2x-cost series).
Prior: A3 still fails net (gross per event < round-trip cost). E1: FL report ~0.5-1%/month for
announcers, diluted here (large caps, a third of the universe in every portfolio): maybe a
small positive net, unlikely to beat SPY's Sharpe.
"""
import numpy as np
import pandas as pd
from common import prices, events, build, evaluate, engine
from study2 import predicted, trades as win_trades

START = "2005-06-01"


def month_trades(pe, days):
    me = pd.Series(np.arange(len(days)), index=days).groupby(days.to_period("M")).last()
    mi = me.values  # index of last trading day of each month
    pm = days[np.minimum(pe.iP.values, len(days) - 1)].to_period("M")
    out = []
    per = list(me.index)
    pos = {p: k for k, p in enumerate(per)}
    for tk, m, ip in zip(pe.ticker.values, pm, pe.iP.values):
        if ip >= len(days):
            continue
        k = pos[m]
        if k >= 1:
            out.append((tk, mi[k - 1], mi[k], 1.0))
    t = pd.DataFrame(out, columns=["ticker", "i_in", "i_out", "sign"])
    return t.drop_duplicates(["ticker", "i_in"])


def run(pe, ret, days):
    res = {}
    t = win_trades(pe, -3, 1)
    res["A3 announce premium fixed slots"] = (t, dict(hedge="EW", slot=10))
    res["E1 FL monthly announcers vs EW"] = (month_trades(pe, days), dict(hedge="EW"))
    return res


def main(n_placebo=200):
    cl, ret = prices()
    days = ret.index
    ev = events(days)
    pe = predicted(ev, days)
    rng = np.random.default_rng(17)
    names = list(run(pe, ret, days))
    plac = {k: [] for k in names}
    for _ in range(n_placebo):
        k = rng.integers(10, 51, len(pe)) * rng.choice([-1, 1], len(pe))
        pp = pe.assign(iP=pe.iP.values + k)
        pp = pp[(pp.iP >= 0) & (pp.iP < len(days))]
        for name, (t, kw) in run(pp, ret, days).items():
            n, _, _ = build(t, ret, **kw)
            plac[name].append(engine.sharpe(n.loc["2014-01-01":]))
    rows = []
    for name, (t, kw) in run(pe, ret, days).items():
        net, net2, nact = build(t, ret, **kw)
        g, _, _ = build(t, ret, cost_bps=0, **kw)
        o = evaluate(name, net, net2, ret["SPY"], START, plac[name])
        o["avg_names"] = float(nact.loc[START:].mean())
        o["placebo_median_post"] = float(np.median(plac[name]))
        o["gross_IS_OOS_HO"] = [round(engine.sharpe(g.loc[START:"2013"]), 2),
                                round(engine.sharpe(g.loc["2014":"2019"]), 2),
                                round(engine.sharpe(g.loc["2020":]), 2)]
        o["gross_ann_post"] = float(g.loc["2014":].mean() * 252)
        rows.append(o)
        net.to_csv(f"study3_{name.split()[0]}_net.csv")
    df = pd.DataFrame(rows)
    df.to_csv("study3_results.csv", index=False)
    print(engine.table(rows))
    print(df[["rule", "ann_ret_post", "gross_ann_post", "gross_IS_OOS_HO", "avg_names",
              "placebo_median_post", "x2cost_post", "gates_passed"]].round(3).to_string())


if __name__ == "__main__":
    main()
