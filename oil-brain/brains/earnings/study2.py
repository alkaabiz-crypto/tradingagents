"""Study 2 (earnings brain): earnings-announcement premium and pre-announcement drift.
PRE-REGISTERED 2026-11-24, after study 1 (PEAD failed) and before any study-2 return was computed.

Literature: Beaver (1968), Frazzini & Lamont (2007, "The earnings announcement premium and
trading volume"): stocks earn more in months they are expected to announce; Barber, De George,
Lehavy & Trueman (2013): the premium is global and concentrated on the days around the
announcement (risk/attention). Frazzini & Lamont predict announcement timing from the date one
year earlier, which is what we do (the actual date is not known in advance in our data).

Predicted date P: trading day at/after (actual day 0 of an event + 364 calendar days), i.e. the
same weekday 52 weeks later. Known a year ahead, so no look-ahead.
Hedge: the equal-weighted universe of the same 92 stocks (survivor-matched; study 1 showed that
today's survivors beat SPY, so a SPY hedge would credit survivorship to the rule).
Rules (2, windows fixed from the papers, not from data):
  A1 announcement premium: long the stock from close of P-3 to close of P+1 (return days P-2..P+1,
     covers +-1-2 day timing error), EW-universe hedged, equal weight across active names.
  A2 pre-announcement run-up: long from close of P-11 to close of P-3 (return days P-10..P-3).
Costs 10 bp per side per unit weight change (stocks and hedge basket).
Gates: as study 1 (engine on net series, bench = SPY buy-and-hold, gate 4 = event-date placebo:
P moved by random +-10..50 trading days, 200 placebos; gate 5 on the 2x-cost series).
Diagnostic only (not a rule): share of predictions within +-1 / +-3 trading days of an actual
day 0, IS only; gross Sharpe.
Prior: gross premium ~5-10 bp/day for 4 days vs ~40 bp round trip costs -> likely FAIL net.
"""
import numpy as np
import pandas as pd
from common import prices, events, build, evaluate, engine

START = "2005-06-01"
WIN = {"A1 announce premium P-2..P+1": (-3, 1), "A2 pre-announce P-10..P-3": (-11, -3)}


def predicted(ev, days):
    p = days.searchsorted((ev.d0 + pd.Timedelta(days=364)).values)
    out = ev.assign(iP=p)
    return out[out.iP < len(days)]


def trades(pe, a, b):
    return pd.DataFrame({"ticker": pe.ticker, "i_in": pe.iP + a, "i_out": pe.iP + b, "sign": 1.0})


def main(n_placebo=200):
    cl, ret = prices()
    days = ret.index
    ev = events(days)
    pe = predicted(ev, days)
    # diagnostic: timing accuracy, IS only
    isp = pe[days[np.minimum(pe.iP, len(days) - 1)] <= pd.Timestamp("2013-12-31")]
    act = {t: np.sort(g.i0.values) for t, g in ev.groupby("ticker")}
    err = []
    for t, ip in zip(isp.ticker, isp.iP):
        a = act[t]
        err.append(np.min(np.abs(a - ip)))
    err = np.array(err)
    print("IS prediction error (trading days): <=1 %.2f, <=3 %.2f, n %d" %
          ((err <= 1).mean(), (err <= 3).mean(), len(err)))
    rng = np.random.default_rng(13)
    plac = {k: [] for k in WIN}
    for _ in range(n_placebo):
        k = rng.integers(10, 51, len(pe)) * rng.choice([-1, 1], len(pe))
        pp = pe.assign(iP=pe.iP.values + k)
        for name, (a, b) in WIN.items():
            n, _, _ = build(trades(pp, a, b), ret, hedge="EW")
            plac[name].append(engine.sharpe(n.loc["2014-01-01":]))
    rows = []
    for name, (a, b) in WIN.items():
        tr = trades(pe, a, b)
        net, net2, nact = build(tr, ret, hedge="EW")
        g, _, _ = build(tr, ret, cost_bps=0, hedge="EW")
        o = evaluate(name, net, net2, ret["SPY"], START, plac[name])
        o["avg_names"] = float(nact.loc[START:].mean())
        o["placebo_median_post"] = float(np.median(plac[name]))
        o["gross_IS_OOS_HO"] = [round(engine.sharpe(g.loc[START:"2013"]), 2),
                                round(engine.sharpe(g.loc["2014":"2019"]), 2),
                                round(engine.sharpe(g.loc["2020":]), 2)]
        o["gross_ann_post"] = float(g.loc["2014":].mean() * 252)
        rows.append(o)
        net.to_csv(f"study2_{name.split()[0]}_net.csv")
    df = pd.DataFrame(rows)
    df.to_csv("study2_results.csv", index=False)
    print(engine.table(rows))
    print(df[["rule", "ann_ret_post", "gross_ann_post", "gross_IS_OOS_HO", "avg_names",
              "placebo_median_post", "x2cost_post", "gates_passed"]].round(3).to_string())


if __name__ == "__main__":
    main()
