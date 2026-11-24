"""Study 1 (earnings brain): post-earnings-announcement drift (PEAD). PRE-REGISTERED 2026-11-24,
written before any return of these rules was computed.

Literature: Bernard & Thomas (1989): prices drift for ~60 trading days in the direction of the
earnings surprise. Chordia, Subrahmanyam & Tong (2014) and Martineau (2022, "Rest in peace
post-earnings announcement drift") find the drift has largely disappeared, especially in large,
liquid stocks, after ~2006. Brandt et al. (2008) show the announcement-RETURN surprise (not just
SUE) also predicts drift. Prior: FAIL in large caps post-2014.

Data: 92 large US stocks (fetch.py; today's survivors -> survivorship bias; L/S + SPY hedge
reduces but does not remove it). Events: SEC 8-K Item 2.02 dates 2004-10..2026-11.
Splits: the engine's own (IS ..2013, OOS 2014-2019, HOLDOUT 2020-). Evaluation starts 2005-06-01.

Surprise: CAR = sum over days 0 and +1 of (stock return - SPY return). Known at close of day +1.
Classification: CAR above the 80th percentile of all universe events' CARs in the previous 365
calendar days (needs >= 100 prior events) -> long; below the 20th percentile -> short.
Portfolio: each position SPY-hedged, equal weighted across all active positions, enter at close
of day +1, 10 bp per side per unit of weight change (stocks and SPY).

Rules (2, no parameters chosen on data; horizons from the papers):
  P1 PEAD-60: hold 60 trading days (Bernard & Thomas horizon).
  P2 PEAD-20: hold 20 trading days (if any drift survives, it is faster now; Martineau 2022).
Gates: engine.evaluate on the net daily series with pos=1, cost 0, bench = SPY buy and hold
(gate 2: post-2014 Sharpe must beat SPY's). Engine's circular-shift placebo is degenerate for a
constant position, so gate 4 uses an EVENT-DATE placebo instead: every event's day 0 is moved by
a random +-10..50 trading days, the same classification and portfolio are rebuilt; 200 placebos;
p = share of placebo post-2014 Sharpes >= the real one. Gate 5 = 2x-cost series post-2014 sum > 0.
Winner bar: all 6 gates and post-2014 t >= 3.
"""
import numpy as np
import pandas as pd
from common import prices, events, build, evaluate, engine

START = "2005-06-01"
HOLDS = {"P1 PEAD-60": 60, "P2 PEAD-20": 20}


def classify(ev, ret):
    R = ret.drop(columns="SPY")
    spy = ret["SPY"].values
    T = len(ret)
    cols = {c: k for k, c in enumerate(R.columns)}
    Rv = R.values
    car = np.full(len(ev), np.nan)
    for j, (tk, i0) in enumerate(zip(ev.ticker.values, ev.i0.values)):
        if 0 <= i0 and i0 + 1 < T:
            x = Rv[i0:i0 + 2, cols[tk]] - spy[i0:i0 + 2]
            car[j] = x.sum()
    ev = ev.assign(car=car).dropna(subset=["car"]).sort_values("i0").reset_index(drop=True)
    days = ret.index
    d0 = days[ev.i0.values].values
    lo = np.searchsorted(d0, d0 - np.timedelta64(365, "D"))
    hi = np.searchsorted(d0, d0)  # strictly earlier days only (same-day events excluded)
    sign = np.zeros(len(ev))
    c = ev.car.values
    for j in range(len(ev)):
        if hi[j] - lo[j] >= 100:
            p20, p80 = np.percentile(c[lo[j]:hi[j]], [20, 80])
            sign[j] = 1 if c[j] > p80 else (-1 if c[j] < p20 else 0)
    ev["sign"] = sign
    return ev


def trades(ev, hold):
    t = ev[ev.sign != 0]
    return pd.DataFrame({"ticker": t.ticker, "i_in": t.i0 + 1, "i_out": t.i0 + 1 + hold,
                         "sign": t.sign})


def main(n_placebo=200):
    cl, ret = prices()
    ev = events(ret.index)
    cev = classify(ev, ret)
    print("events", len(ev), "classified long/short", (cev.sign == 1).sum(), (cev.sign == -1).sum())
    rng = np.random.default_rng(11)
    plac = {k: [] for k in HOLDS}
    for _ in range(n_placebo):
        k = rng.integers(10, 51, len(ev)) * rng.choice([-1, 1], len(ev))
        pe = ev.assign(i0=ev.i0.values + k)
        pe = pe[(pe.i0 >= 0) & (pe.i0 < len(ret) - 2)]
        pc = classify(pe, ret)
        for name, h in HOLDS.items():
            n, _, _ = build(trades(pc, h), ret)
            plac[name].append(engine.sharpe(n.loc["2014-01-01":]))
    rows = []
    for name, h in HOLDS.items():
        net, net2, nact = build(trades(cev, h), ret)
        o = evaluate(name, net, net2, ret["SPY"], START, plac[name])
        o["avg_names"] = float(nact.loc[START:].mean())
        o["placebo_median_post"] = float(np.median(plac[name]))
        rows.append(o)
        net.to_csv(f"study1_{name.split()[0]}_net.csv")
    df = pd.DataFrame(rows)
    df.to_csv("study1_results.csv", index=False)
    print(engine.table(rows))
    print(df[["rule", "ann_ret_post", "avg_names", "placebo_median_post", "x2cost_post",
              "gates_passed"]].round(3).to_string())


if __name__ == "__main__":
    main()
