"""All 61 TA-Lib candlestick patterns (pre-registered 2026-11-25, before any run; the user asked to widen the
candle brain to the famous patterns). TA-Lib 0.8.3 is the standard open-source pattern library (its definitions
follow Nison / Morris / Bulkowski and its own "candle settings": body/shadow sizes relative to the last 10 candles).

Signal: TA-Lib returns +100/+200 (bullish) or -100/-200 (bearish) on the pattern's last candle. Bullish -> LONG,
bearish -> SHORT. Each pattern's bullish and bearish signals are separate systems.
Markets (daily): USO, BNO, XLE, XOP, SPY, QQQ, IWM, DIA, GLD, SLV, TLT, BTC-USD. Entry at the NEXT OPEN, exit at the
close h days later, h in {1, 3, 5, 10}. Costs 5 bp a side (BTC 10 bp). Periods as candle_study.py.
Score = EXCESS over the market's own average h-day return in the same direction and period (so a long-only pattern
in a rising market is not credited for the drift).
Systems = 61 patterns x 2 directions x 12 markets x 4 holds (only those with >= 20 post-2014 events are judged).
PASS (fixed): excess > 0 in OOS and HOLDOUT; post-2014 net > 0 at 2x cost; post-2014 t >= the family-wise luck bar
(Sidak at 1% for the number of judged systems); random-day placebo (500 runs, seed 31) p <= 0.01. Then a market
check: a pattern is called RELIABLE only if its post-2014 excess is positive in >= 9 of the 12 markets at the same
hold (consistency across markets, even if each one alone is not significant).
Also reported for every pattern: total events, markets right (of 12), median excess, and the verdict.
Research, not financial advice.
"""
import os, sys, math
import numpy as np, pandas as pd, talib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import candle_study as CS

HERE = os.path.dirname(os.path.abspath(__file__))
PATTERNS = sorted(f for f in talib.get_functions() if f.startswith("CDL"))
HOLDS = [1, 3, 5, 10]


def sidak_t(m, alpha=0.01):
    p = 1 - (1 - alpha) ** (1 / max(m, 1)); lo, hi = 0.0, 10.0  # two-sided normal quantile by bisection
    for _ in range(60):
        mid = (lo + hi) / 2
        if math.erfc(mid / math.sqrt(2)) > p: lo = mid
        else: hi = mid
    return hi


def main():
    rows = []; data = {}
    for sym in CS.MARKETS:
        b = CS.load(sym); data[sym] = b; cost = 1e-3 if sym == "BTC-USD" else 5e-4; a, z = CS.periods(sym)
        o, h, l, c = (b[x].values.astype(float) for x in ("Open", "High", "Low", "Close"))
        sig = {p: pd.Series(getattr(talib, p)(o, h, l, c), index=b.index) for p in PATTERNS}
        for hold in HOLDS:
            r = CS.fwd(b, hold); base = r.dropna()
            pers = {"IS": base.index < a, "OOS": (base.index >= a) & (base.index < z), "HOLDOUT": base.index >= z, "POST": base.index >= a}
            for p in PATTERNS:
                for side, mask in ((1, sig[p] > 0), (-1, sig[p] < 0)):
                    ev = r[mask].dropna() * side
                    row = dict(sym=sym, pattern=p, side="bull" if side > 0 else "bear", hold=hold)
                    for per, pm in pers.items():
                        bm = base[pm].mean() * side; e = ev[ev.index.isin(base.index[pm])]; x = e - bm
                        row[f"{per}_n"] = len(e)
                        row[f"{per}_ex_bp"] = x.mean() * 1e4 if len(e) else np.nan
                        if per == "POST":
                            row["POST_t"] = x.mean() / (x.std(ddof=1) / np.sqrt(len(x))) if len(x) > 2 and x.std() > 0 else np.nan
                            row["POST_net_bp_2x"] = (e.mean() - 4 * cost) * 1e4 if len(e) else np.nan
                            row["POST_hit"] = float((e - 2 * cost > 0).mean()) if len(e) else np.nan
                    rows.append(row)
    df = pd.DataFrame(rows)
    judged = df[df.POST_n >= 20]; bar = sidak_t(len(judged))
    cand = judged[(judged.OOS_ex_bp > 0) & (judged.HOLDOUT_ex_bp > 0) & (judged.POST_net_bp_2x > 0) & (judged.POST_t >= bar)].copy()
    ps = []
    for _, r in cand.iterrows():
        b = data[r.sym]; a, _ = CS.periods(r.sym); side = 1 if r.side == "bull" else -1
        post = CS.fwd(b, r.hold).dropna(); post = post[post.index >= a]
        sims = np.array([(post.sample(n=int(r.POST_n), random_state=31 + i) * side - side * post.mean()).mean() for i in range(500)])
        ps.append(float((sims >= r.POST_ex_bp / 1e4).mean()))
    cand["placebo_p"] = ps
    df = df.merge(cand[["sym", "pattern", "side", "hold", "placebo_p"]], how="left", on=["sym", "pattern", "side", "hold"])
    df["PASS"] = df.placebo_p <= 0.01
    df.to_csv(os.path.join(HERE, "talib_results.csv"), index=False)
    # Consistency across markets, per pattern/direction/hold
    g = df[df.POST_n >= 5].groupby(["pattern", "side", "hold"]).agg(
        markets=("sym", "size"), right=("POST_ex_bp", lambda x: int((x > 0).sum())), median_ex_bp=("POST_ex_bp", "median"),
        events=("POST_n", "sum"), passes=("PASS", "sum")).reset_index()
    g["RELIABLE"] = (g.markets >= 10) & (g.right >= 9)
    g["WRONG_WAY"] = (g.markets >= 10) & (g.right <= 3)
    g.to_csv(os.path.join(HERE, "talib_by_pattern.csv"), index=False)
    pd.set_option("display.width", 250); pd.set_option("display.max_rows", 400)
    print(f"Patterns: {len(PATTERNS)}; systems: {len(df)}; judged (>= 20 events): {len(judged)}; luck bar t >= {bar:.2f}")
    print(f"Passed first gates: {len(cand)}; PASS (placebo too): {int(df.PASS.sum())}")
    if len(cand):
        print(df[df.placebo_p.notna()].sort_values("POST_t", ascending=False)[["sym", "pattern", "side", "hold", "POST_n", "POST_hit", "OOS_ex_bp", "HOLDOUT_ex_bp", "POST_net_bp_2x", "POST_t", "placebo_p"]].round(2).to_string(index=False))
    h1 = g[g.hold == 1].sort_values("median_ex_bp", ascending=False)
    print("\nPer pattern, 1-day hold (markets with >= 5 events):")
    print(h1.round(1).to_string(index=False))
    print("\nRELIABLE (right in >= 9 of >= 10 markets), any hold:"); print(g[g.RELIABLE].round(1).to_string(index=False))
    print("\nWRONG WAY (right in <= 3 of >= 10 markets), any hold:"); print(g[g.WRONG_WAY].round(1).to_string(index=False))


if __name__ == "__main__":
    main()
