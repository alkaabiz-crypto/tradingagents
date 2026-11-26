"""Day ticket v2: every version of the ticket rule (pre-registered 2026-11-26, before any run; the user asked "try all
versions and v2" after the v1 rule — stop 0.5 ATR, target 1 ATR — lost ~0.1R a trade in all 17 markets).

Trade: signal at day i's close, entry at day i+1's OPEN, out at that day's close at the latest (a day trade, as live).
Exits (ATR14 known at day i):  stop  k in {0.5, 1, 1.5, 2, none} x ATR below/above the entry
                               target m in {0.5, 1, 1.5, 2, none} x ATR
  Both touched on the same bar = STOP (A7). Costs 5 bp a side; 2x-cost check at 10 bp a side.
Directions (8): ALWAYS LONG, ALWAYS SHORT, COIN FLIP (seed 61), YESTERDAY (same side as day i's move),
  FADE (opposite of day i's move), TREND (long above the 50-day average, short below),
  IBS (long if day i IBS < 0.2, short if > 0.8, else no trade), TREND-DIP (long only: above the 50-day average AND IBS < 0.2).
Systems: 5 stops x 5 targets x 8 directions = 200 versions, each pooled over the 17 ticket markets (daily mean over the
  markets that traded, so one day counts once). Periods: IS 2006-2013, OOS 2014-2019, HOLDOUT 2020+.
PASS (fixed): average trade > 0 bp net in OOS AND HOLDOUT, > 0 at 2x costs post-2014, post-2014 t >= the Sidak 1% bar
  for 200 systems, placebo p <= 0.01 (500 runs, seed 62: same days, same exits, RANDOM direction — this tests direction
  skill; ALWAYS LONG/SHORT are judged against it too, so a pass there would only be drift), and >= 70% of its grid
  neighbours (stop/target one step away, same direction) clear the OOS/HOLDOUT/2x checks.
Also (part "ai"): the AI back-run + live tickets re-scored under all 25 exits, vs always-long and coin flip on the same days.
    python3 oil-brain/live/day_ticket_v2.py         # the 200-version study
    python3 oil-brain/live/day_ticket_v2.py ai      # AI tickets under every exit
Research, not financial advice.
"""
import os, sys, math
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from day_ticket_backrun import full_bars, atr, ALL17

COST = 5e-4
KS = [0.5, 1.0, 1.5, 2.0, None]; MS = [0.5, 1.0, 1.5, 2.0, None]
DIRS = ["ALWAYS LONG", "ALWAYS SHORT", "COIN FLIP", "YESTERDAY", "FADE", "TREND", "IBS", "TREND-DIP"]


def gross(O, H, L, C, a, s, k, m):
    """Gross % of one day trade per row; s = +1 long, -1 short (arrays)."""
    x = C.copy()
    if m is not None:
        tg = O + s * m * a; hit = np.where(s > 0, H >= tg, L <= tg); x = np.where(hit, tg, x)
    if k is not None:
        st = O - s * k * a; hit = np.where(s > 0, L <= st, H >= st); x = np.where(hit, st, x)
    return s * (x / O - 1)


def panel():
    rng = np.random.default_rng(61); out = []
    for sym in ALL17:
        d = full_bars(sym); a = atr(d); c = d.Close
        ibs = (c - d.Low) / (d.High - d.Low); up = np.sign(c.diff()); tr = np.where(c > c.rolling(50).mean(), 1, -1)
        f = pd.DataFrame({"O": d.Open.shift(-1), "H": d.High.shift(-1), "L": d.Low.shift(-1), "C": d.Close.shift(-1),
                          "a": a, "ibs": ibs, "up": up, "tr": tr, "sma_ok": c.rolling(50).mean().notna()}, index=d.index)
        f = f[(f.index >= "2006-01-01") & f.notna().all(axis=1) & f.sma_ok & (f.up != 0)]
        n = len(f); S = {"ALWAYS LONG": np.ones(n), "ALWAYS SHORT": -np.ones(n),
                         "COIN FLIP": np.where(rng.random(n) < .5, 1., -1.), "YESTERDAY": f.up.values,
                         "FADE": -f.up.values, "TREND": f.tr.values.astype(float),
                         "IBS": np.where(f.ibs < .2, 1., np.where(f.ibs > .8, -1., 0.)),
                         "TREND-DIP": np.where((f.tr > 0) & (f.ibs < .2), 1., 0.)}
        for k_, v in S.items(): f["s_" + k_] = v
        f["sym"] = sym; out.append(f)
    return pd.concat(out)


def sidak_t(mm, alpha=0.01):
    p = 1 - (1 - alpha) ** (1 / mm); lo, hi = 0.0, 10.0
    for _ in range(60):
        mid = (lo + hi) / 2; lo, hi = (mid, hi) if math.erfc(mid / math.sqrt(2)) > p else (lo, mid)
    return hi


def daily(idx, r):
    return pd.Series(r, index=idx).groupby(level=0).mean()


def tstat(x):
    return x.mean() / (x.std(ddof=1) / np.sqrt(len(x))) if len(x) > 2 else np.nan


def main():
    P = panel(); bar = sidak_t(200); rng = np.random.default_rng(62); rows = []
    O, H, L, C, a = (P[c].values for c in "OHLCa"); idx = P.index
    for k in KS:
        for m in MS:
            gl, gs = gross(O, H, L, C, a, np.ones(len(P)), k, m), gross(O, H, L, C, a, -np.ones(len(P)), k, m)
            for dname in DIRS:
                s = P["s_" + dname].values; on = s != 0
                g = np.where(s > 0, gl, gs)[on]; ix = idx[on]
                net, net2 = daily(ix, g - 2 * COST), daily(ix, g - 4 * COST)
                post = net[net.index >= "2014-01-01"]
                row = dict(direction=dname, stop=k or "none", target=m or "none", trades=int(on.sum()),
                           IS_bp=net[net.index < "2014-01-01"].mean() * 1e4,
                           OOS_bp=net[(net.index >= "2014-01-01") & (net.index < "2020-01-01")].mean() * 1e4,
                           HO_bp=net[net.index >= "2020-01-01"].mean() * 1e4, post_bp=post.mean() * 1e4,
                           post_bp_2x=net2[net2.index >= "2014-01-01"].mean() * 1e4, post_t=tstat(post),
                           win=float((g - 2 * COST > 0).mean()), placebo_p=np.nan)
                row["basic"] = row["OOS_bp"] > 0 and row["HO_bp"] > 0 and row["post_bp_2x"] > 0
                if row["basic"] and row["post_t"] >= bar:
                    pm = idx[on] >= pd.Timestamp("2014-01-01"); GL, GS = gl[on][pm], gs[on][pm]; ixp = ix[pm]; sims = []
                    for _ in range(500):
                        rs = np.where(rng.random(len(GL)) < .5, GL, GS) - 2 * COST
                        sims.append(daily(ixp, rs).mean())
                    row["placebo_p"] = float((np.array(sims) >= post.mean()).mean())
                rows.append(row)
    df = pd.DataFrame(rows)
    key = lambda v: KS.index(None if v == "none" else v)
    nb = []
    for _, r in df.iterrows():
        i, j = key(r.stop), MS.index(None if r.target == "none" else r.target)
        sub = df[(df.direction == r.direction) & df.apply(lambda q: abs(key(q.stop) - i) + abs(MS.index(None if q.target == "none" else q.target) - j) == 1, axis=1)]
        nb.append(sub.basic.mean())
    df["neighbours_ok"] = nb
    df["PASS"] = (df.placebo_p <= 0.01) & (df.neighbours_ok >= 0.7)
    df.to_csv(os.path.join(HERE, "day_ticket_v2_results.csv"), index=False)
    pd.set_option("display.width", 220)
    print(f"Versions: {len(df)} | luck bar t >= {bar:.2f} | clear OOS+HOLDOUT+2x: {int(df.basic.sum())} | "
          f"reach the bar: {int(df.placebo_p.notna().sum())} | PASS: {int(df.PASS.sum())}")
    print("\nBest version per direction (post-2014, bp per trade net):")
    best = df.sort_values("post_t", ascending=False).groupby("direction").head(1)
    print(best[["direction", "stop", "target", "trades", "OOS_bp", "HO_bp", "post_bp", "post_bp_2x", "post_t", "win", "placebo_p", "neighbours_ok", "PASS"]].round(2).to_string(index=False))
    print("\nv1 (stop 0.5, target 1):"); print(df[(df.stop == 0.5) & (df.target == 1.0)][["direction", "post_bp", "post_t", "win"]].round(2).to_string(index=False))


def ai():
    L = pd.concat([pd.read_csv(os.path.join(HERE, f)).assign(src=f.split(".")[0]) for f in ("day_tickets_backrun.csv", "day_tickets.csv")
                   if os.path.exists(os.path.join(HERE, f))], ignore_index=True)
    L = L[L.side.isin(["LONG", "SHORT"])]; cache = {}; B = []
    for _, r in L.iterrows():
        if r.ticker not in cache: cache[r.ticker] = full_bars(r.ticker)
        nx = cache[r.ticker][cache[r.ticker].index > pd.Timestamp(str(r.made)[:10])]
        if nx.empty: continue
        b = nx.iloc[0]; B.append((b.Open, b.High, b.Low, b.Close, float(r.atr), 1. if r.side == "LONG" else -1.))
    if not B: print("No scored AI tickets yet."); return
    O, H, L_, C, a, s = map(np.array, zip(*B)); rng = np.random.default_rng(63); rows = []
    for k in KS:
        for m in MS:
            gl, gs = gross(O, H, L_, C, a, np.ones(len(O)), k, m), gross(O, H, L_, C, a, -np.ones(len(O)), k, m)
            g = np.where(s > 0, gl, gs) - 2 * COST
            fl = np.array([np.where(rng.random(len(O)) < .5, gl, gs).mean() - 2 * COST for _ in range(2000)])
            rows.append(dict(stop=k or "none", target=m or "none", AI_bp=g.mean() * 1e4, AI_t=tstat(pd.Series(g)),
                             long_bp=(gl.mean() - 2 * COST) * 1e4, coin_bp=fl.mean() * 1e4, p_vs_coin=(fl >= g.mean()).mean()))
    df = pd.DataFrame(rows); pd.set_option("display.width", 200)
    print(f"AI tickets scored: {len(O)} ({int((s > 0).sum())} long, {int((s < 0).sum())} short); 25 exits tried, so a p < 0.002 is needed to beat luck")
    print(df.round(2).to_string(index=False))


if __name__ == "__main__":
    (ai if len(sys.argv) > 1 and sys.argv[1] == "ai" else main)()
