"""Day ticket v3: the same 200 rule versions on markets that MOVE A LOT (pre-registered 2026-11-26, before any run;
the user asked for "other markets that move a lot" after v2 showed 0 of 200 versions beat costs on the 17 ticket
markets, whose open-to-close move is too small for the ~10 bp round trip).
Groups (cost a side):  CRYPTO BTC-USD ETH-USD SOL-USD (10 bp; daily bar = UTC day)
                       LEVERAGED TQQQ SOXL UPRO TNA (5 bp)
                       HIGH-VOL STOCKS TSLA AMD COIN MSTR PLTR SMCI (5 bp)
                       FUTURES CL=F NG=F SI=F (2 bp)
Rule and the 200 versions exactly as day_ticket_v2.py (entry next open, stop/target in ATR, out at the close,
both touched = stop, 8 directions). Systems: 200 x 4 groups = 800; Sidak 1% bar for 800.
Periods: many of these markets are young, so per group the post-2014 data (crypto: all data) is split in half by
date: OOS = first half, HOLDOUT = second half. PASS as v2: > 0 in both halves, > 0 at 2x costs, t >= the bar,
random-direction placebo p <= 0.01 (500 runs, seed 72), >= 70% of grid neighbours OK.
Warning written before the run: these markets were picked because they moved a lot (and many rose a lot) — hindsight
bias; ALWAYS LONG results there are mostly that drift. Research, not financial advice.
    python3 oil-brain/live/day_ticket_v3.py
"""
import os, sys
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from day_ticket_backrun import full_bars, atr
from day_ticket_v2 import gross, sidak_t, daily, tstat, KS, MS, DIRS

GROUPS = {"CRYPTO": (["BTC-USD", "ETH-USD", "SOL-USD"], 1e-3), "LEVERAGED": (["TQQQ", "SOXL", "UPRO", "TNA"], 5e-4),
          "HIGH-VOL STOCKS": (["TSLA", "AMD", "COIN", "MSTR", "PLTR", "SMCI"], 5e-4),
          "FUTURES": (["CL=F", "NG=F", "SI=F"], 2e-4)}


def panel(syms, rng):
    out = []
    for sym in syms:
        d = full_bars(sym); d = d[(d.High > d.Low) & (d.Open > 0)]; a = atr(d); c = d.Close
        ibs = (c - d.Low) / (d.High - d.Low); up = np.sign(c.diff()); tr = np.where(c > c.rolling(50).mean(), 1, -1)
        f = pd.DataFrame({"O": d.Open.shift(-1), "H": d.High.shift(-1), "L": d.Low.shift(-1), "C": d.Close.shift(-1),
                          "a": a, "ibs": ibs, "up": up, "tr": tr, "ok": c.rolling(50).mean().notna()}, index=d.index)
        f = f[(f.index >= "2014-01-01") & f.notna().all(axis=1) & f.ok & (f.up != 0)]
        n = len(f); S = {"ALWAYS LONG": np.ones(n), "ALWAYS SHORT": -np.ones(n),
                         "COIN FLIP": np.where(rng.random(n) < .5, 1., -1.), "YESTERDAY": f.up.values, "FADE": -f.up.values,
                         "TREND": f.tr.values.astype(float), "IBS": np.where(f.ibs < .2, 1., np.where(f.ibs > .8, -1., 0.)),
                         "TREND-DIP": np.where((f.tr > 0) & (f.ibs < .2), 1., 0.)}
        for k_, v in S.items(): f["s_" + k_] = v
        f["sym"] = sym; out.append(f)
    return pd.concat(out)


def main():
    bar = sidak_t(800); rng = np.random.default_rng(71); prng = np.random.default_rng(72); rows = []
    for gname, (syms, cost) in GROUPS.items():
        P = panel(syms, rng); O, H, L, C, a = (P[c].values for c in "OHLCa"); idx = P.index
        mid = idx.sort_values()[len(idx) // 2]
        rng_pct = float(np.median((P.H - P.L) / P.O)) * 1e4
        for k in KS:
            for m in MS:
                gl, gs = gross(O, H, L, C, a, np.ones(len(P)), k, m), gross(O, H, L, C, a, -np.ones(len(P)), k, m)
                for dname in DIRS:
                    s = P["s_" + dname].values; on = s != 0; g = np.where(s > 0, gl, gs)[on]; ix = idx[on]
                    net, net2 = daily(ix, g - 2 * cost), daily(ix, g - 4 * cost)
                    row = dict(group=gname, direction=dname, stop=k or "none", target=m or "none", trades=int(on.sum()),
                               day_range_bp=rng_pct, OOS_bp=net[net.index < mid].mean() * 1e4,
                               HO_bp=net[net.index >= mid].mean() * 1e4, bp=net.mean() * 1e4, bp_2x=net2.mean() * 1e4,
                               t=tstat(net), win=float((g - 2 * cost > 0).mean()), placebo_p=np.nan)
                    row["basic"] = row["OOS_bp"] > 0 and row["HO_bp"] > 0 and row["bp_2x"] > 0
                    if row["basic"] and row["t"] >= bar:
                        GL, GS = gl[on], gs[on]; sims = [daily(ix, np.where(prng.random(len(GL)) < .5, GL, GS) - 2 * cost).mean() for _ in range(500)]
                        row["placebo_p"] = float((np.array(sims) >= net.mean()).mean())
                    rows.append(row)
    df = pd.DataFrame(rows)
    ki = lambda v: KS.index(None if v == "none" else v); mi = lambda v: MS.index(None if v == "none" else v)
    df["neighbours_ok"] = [df[(df.group == r.group) & (df.direction == r.direction) &
                              ((df.stop.map(ki) - ki(r.stop)).abs() + (df.target.map(mi) - mi(r.target)).abs() == 1)].basic.mean()
                           for _, r in df.iterrows()]
    df["PASS"] = (df.placebo_p <= 0.01) & (df.neighbours_ok >= 0.7)
    df.to_csv(os.path.join(HERE, "day_ticket_v3_results.csv"), index=False)
    pd.set_option("display.width", 230)
    print(f"Versions: {len(df)} | luck bar t >= {bar:.2f} | clear both halves + 2x cost: {int(df.basic.sum())} | "
          f"reach the bar: {int(df.placebo_p.notna().sum())} | PASS: {int(df.PASS.sum())}")
    cols = ["group", "direction", "stop", "target", "trades", "day_range_bp", "OOS_bp", "HO_bp", "bp", "bp_2x", "t", "win", "placebo_p", "neighbours_ok", "PASS"]
    print("\nBest 3 versions per group:"); print(df.sort_values("t", ascending=False).groupby("group").head(3)[cols].round(2).to_string(index=False))
    print("\nVersions clearing both halves + 2x cost, by group and direction:")
    print(df[df.basic].groupby(["group", "direction"]).size().to_string() if df.basic.any() else "none")


if __name__ == "__main__":
    main()
