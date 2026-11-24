"""Shared helpers for the crypto brain (no tuning here).

Two evaluations are reported for every rule:
1. engine.evaluate unchanged (official, comparable with other brains). Its splits are fixed:
   IS <=2013 (EMPTY for crypto: BTC data starts 2014-09-17), OOS 2014-2019, HOLDOUT 2020+.
   Its Sharpe uses sqrt(252) on 7-day data, so every Sharpe (rule AND benchmark) is understated
   by sqrt(365/252)=1.20; trades_per_year is overstated by 365/252; cagr_post is wrong
   (uses 252 periods/year on 365-day data). Ranking vs benchmark is unaffected.
2. crypto splits (pre-registered for this brain): IS 2014-09..2018, OOS 2019-2021, HOLDOUT 2022+,
   Sharpe annualized with sqrt(365), same 6 gates, post = 2019+.
"""
import os, sys
import numpy as np
import pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, ROOT)
import engine  # noqa: E402

LAST = "2026-11-23"  # drop today's partial bar


def px(sym, col="Close"):
    d = pd.read_csv(os.path.join(HERE, "data", sym + ".csv"), index_col=0, parse_dates=True)
    return d[col].loc[:LAST]


def ret(sym):
    return px(sym).pct_change().dropna()


def shared_close(sym):
    return engine.load(sym).loc[:LAST]


def s365(r):
    r = r.dropna()
    return float(r.mean() / r.std() * np.sqrt(365)) if len(r) > 20 and r.std() > 0 else np.nan


def maxdd(r):
    eq = (1 + r.fillna(0)).cumprod()
    return float((eq / eq.cummax() - 1).min())


def crypto_eval(name, pos, rt, cost_bps=10, bench=None, n_placebo=500, seed=7):
    rt = rt.dropna()
    pos = pos.reindex(rt.index).ffill().fillna(0)
    r = engine.pnl(pos, rt, cost_bps)
    r2 = engine.pnl(pos, rt, 2 * cost_bps)
    b = (bench if bench is not None else rt).reindex(rt.index).fillna(0)
    IS, OOS, HO = r.loc[:"2018-12-31"], r.loc["2019":"2021"], r.loc["2022":]
    post, bpost = r.loc["2019":], b.loc["2019":]
    m = rt.index >= "2019-01-01"
    real = s365(post)
    rng = np.random.default_rng(seed)
    p = pos.values; n = len(p); beats = 0
    for _ in range(n_placebo):
        k = int(rng.integers(n // 10, n - n // 10))
        sp = pd.Series(np.roll(p, k), index=rt.index)
        if s365(engine.pnl(sp, rt, cost_bps)[m]) < real:
            beats += 1
    pp = 1 - beats / n_placebo
    t = float(post.mean() / post.std() * np.sqrt(len(post)))
    yrs = len(post) / 365
    out = dict(rule=name, cIS=s365(IS), cOOS=s365(OOS), cHO=s365(HO), cpost=real,
               cbench=s365(bpost), ct=t, cplac=pp,
               cagr=float((1 + post).prod() ** (1 / yrs) - 1),
               bcagr=float((1 + bpost).prod() ** (1 / yrs) - 1),
               dd=maxdd(post), bdd=maxdd(bpost), x2=float(r2.loc["2019":].sum()),
               expo=float(pos.loc["2019":].abs().mean()))
    g = [out["cOOS"] > 0.3, out["cHO"] > 0.3, real > out["cbench"], t >= 2, pp <= 0.05, out["x2"] > 0]
    out["cverdict"] = "PASS" if all(g) else f"FAIL ({6 - sum(g)} of 6)"
    return out


def both(name, pos, rt, cost_bps=10, bench=None):
    e = engine.evaluate(name, pos, rt, cost_bps=cost_bps, bench=bench)
    c = crypto_eval(name, pos, rt, cost_bps=cost_bps, bench=bench)
    e["winner"] = e["verdict"] == "PASS" and e["t_post"] >= 3.0
    s = engine.evaluate(name, pos, rt, cost_bps=25, bench=bench, n_placebo=1)
    e["post_25bp"] = s["post"]
    return e, c


def show(rows_e, rows_c):
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
    print("ENGINE (sqrt252, OOS 2014-19, HO 2020+, 10bp):")
    print(pd.DataFrame(rows_e).set_index("rule")[["IS", "OOS", "HOLDOUT", "post", "bench_post", "t_post",
          "placebo_p", "trades_per_year", "exposure", "post_25bp", "verdict", "winner"]].round(2).to_string())
    print("\nCRYPTO SPLITS (sqrt365, IS 2014-18, OOS 2019-21, HO 2022+, post 2019+):")
    print(pd.DataFrame(rows_c).set_index("rule").round(2).to_string())
