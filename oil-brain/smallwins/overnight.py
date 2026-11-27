"""OVERNIGHT hold: buy at the US close, sell at the next US open (pre-registered 2026-11-27, before any run).
Why: day ticket v2 showed open-to-close earns ~nothing; academic work finds most US stock-index returns arrive
OVERNIGHT (Kelly & Clark 2011; Cooper, Cliff & Gulen 2008; Lou, Polk & Skouras 2019 JFE "A tug of war: overnight
versus intraday expected returns"). The user's Exness account is SWAP-FREE (ACCOUNT.md), so an overnight CFD hold
pays no financing: a small, frequent trade (one every night) whose only cost is the spread. Oil first: USO, XLE, XOM,
CVX, plus SPY, QQQ, IWM, DIA, GLD, SLV (10 markets).
Variants (long only): V1 every night | V2 only above the 200-day average | V3 only after a weak close (IBS < 0.5,
  from the candle brain). 3 x 10 = 30 systems. Costs per trade: costs.round_trip (Exness Standard spread; stocks use
  the stock-CFD spread), no swap. Raw (unadjusted) prices: ex-dividend gaps count against the long (conservative).
Periods: IS < 2014, OOS 2014-2019, HOLDOUT 2020+.
PASS (fixed): net > 0 in OOS and HOLDOUT, > 0 at 2x cost post-2014, post-2014 t >= the Sidak 1% bar for 30;
  V2/V3 also need a random-night placebo (same number of nights, 1000 runs, seed 101) p <= 0.01 vs V1's nights;
  then a neighbour check (SMA 150/250, IBS 0.4/0.6) before any paper sleeve. V1 is judged against zero only, so a V1
  pass is the overnight drift itself (A5): still tradeable, but it is market exposure, not timing skill.
Research, not financial advice.      python3 oil-brain/smallwins/overnight.py
"""
import os, sys, math
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); OB = os.path.dirname(HERE)
sys.path.insert(0, OB); sys.path.insert(0, os.path.join(OB, "live"))
import costs
from day_ticket_backrun import full_bars

MARKETS = ["USO", "XLE", "XOM", "CVX", "SPY", "QQQ", "IWM", "DIA", "GLD", "SLV"]


def sidak_t(m, alpha=0.01):
    p = 1 - (1 - alpha) ** (1 / m); lo, hi = 0.0, 10.0
    for _ in range(60):
        mid = (lo + hi) / 2; lo, hi = (mid, hi) if math.erfc(mid / math.sqrt(2)) > p else (lo, mid)
    return hi


def tstat(x):
    return x.mean() / (x.std(ddof=1) / np.sqrt(len(x))) if len(x) > 2 else np.nan


def nights(sym):
    d = full_bars(sym); c = d.Close
    g = pd.Series(d.Open.shift(-1).values / c.values - 1, index=d.index)       # close(t) -> open(t+1)
    ibs = (c - d.Low) / (d.High - d.Low)
    f = pd.DataFrame({"g": g, "trend": c > c.rolling(200).mean(), "ok": c.rolling(250).mean().notna(),
                      "ibs": ibs, "t150": c > c.rolling(150).mean(), "t250": c > c.rolling(250).mean()}).dropna()
    return f[f.ok & (f.index >= "2000-01-01")]


def main():
    bar = sidak_t(30); rng = np.random.default_rng(101); rows = []
    for sym in MARKETS:
        f = nights(sym); cost = costs.round_trip(sym)
        masks = {"V1 every night": np.ones(len(f), bool), "V2 above 200d": f.trend.values, "V3 weak close": (f.ibs < .5).values,
                 "n V2 150d": f.t150.values, "n V2 250d": f.t250.values,
                 "n V3 IBS<0.4": (f.ibs < .4).values, "n V3 IBS<0.6": (f.ibs < .6).values}
        for name, m in masks.items():
            r = f.g[m] - cost; post = r[r.index >= "2014-01-01"]
            row = dict(sym=sym, variant=name, nights=len(post), cost_bp=cost * 1e4,
                       IS_bp=r[r.index < "2014-01-01"].mean() * 1e4,
                       OOS_bp=r[(r.index >= "2014-01-01") & (r.index < "2020-01-01")].mean() * 1e4,
                       HO_bp=r[r.index >= "2020-01-01"].mean() * 1e4, post_bp=post.mean() * 1e4,
                       post_bp_2x=(post.mean() - cost) * 1e4, t=tstat(post), win=float((post > 0).mean()), placebo_p=np.nan)
            row["basic"] = row["OOS_bp"] > 0 and row["HO_bp"] > 0 and row["post_bp_2x"] > 0
            if name.startswith(("V2", "V3")) and row["basic"] and row["t"] >= bar:
                allp = (f.g[f.index >= "2014-01-01"] - cost).values
                sims = [rng.choice(allp, size=len(post), replace=False).mean() for _ in range(1000)]
                row["placebo_p"] = float((np.array(sims) >= post.mean()).mean())
            rows.append(row)
    df = pd.DataFrame(rows)
    main_v = df[~df.variant.str.startswith("n ")].copy()
    main_v["PASS"] = main_v.basic & (main_v.t >= bar) & ((main_v.variant == "V1 every night") | (main_v.placebo_p <= 0.01))
    nb = df[df.variant.str.startswith("n ")]
    main_v["neighbours_ok"] = [nb[(nb.sym == r.sym) & nb.variant.str.contains(r.variant[:2])].basic.mean() if r.variant != "V1 every night" else np.nan
                               for _, r in main_v.iterrows()]
    df.to_csv(os.path.join(HERE, "overnight_results.csv"), index=False)
    pd.set_option("display.width", 220)
    print(f"30 systems, luck bar t >= {bar:.2f}. Post-2014, bp a night net of the Exness spread (no swap):")
    print(main_v.sort_values("t", ascending=False)[["sym", "variant", "nights", "cost_bp", "OOS_bp", "HO_bp", "post_bp",
          "post_bp_2x", "t", "win", "placebo_p", "neighbours_ok", "PASS"]].round(2).to_string(index=False))
    print("\nPASS:", main_v[main_v.PASS][["sym", "variant"]].values.tolist() or "none")


if __name__ == "__main__":
    main()
