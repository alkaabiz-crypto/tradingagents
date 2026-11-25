"""Candle study (pre-registered 2026-11-25, before any run). The user asked for the largest possible test of what
candles and wicks mean and whether they tell when price will rise or fall.

Markets (daily bars): USO, BNO, XLE, XOP (oil); SPY, QQQ, IWM, DIA (US stocks); GLD, SLV, TLT; BTC-USD.
Candle parts: body = |C - O|, range = H - L, upper wick = H - max(O, C), lower wick = min(O, C) - L.
Prior trend (for reversal patterns) = close below / above the close 5 days earlier ("down" / "up").
Patterns (standard Nison / Bulkowski-style numeric definitions; direction = the move they are said to predict):
  bullish (long):  HAMMER (down, lower wick >= 2 x body, upper wick <= 0.1 x range, body >= 0.05 x range)
                   INV_HAMMER (down, upper wick >= 2 x body, lower wick <= 0.1 x range)
                   DRAGONFLY_DOJI (body <= 0.1 x range, lower wick >= 0.7 x range)
                   BULL_MARUBOZU (C > O, body >= 0.9 x range)          BULL_ENGULF (down, red then green body engulfing it)
                   BULL_HARAMI (down, big red then small green inside it) PIERCING (down, red, then opens below its low,
                   closes above its midpoint but below its open)          MORNING_STAR (down, big red, small body, big green
                   closing above the first body's midpoint)               THREE_SOLDIERS (3 green, each closing higher,
                   each opening inside the prior body)                    TWEEZER_BOTTOM (down, two lows within 0.05 x ATR,
                   red then green)                                        LONG_LOWER_WICK (lower wick >= 0.6 x range)
                   OUTSIDE_UP (high > prior high, low < prior low, C > O)
  bearish (short): HANGING_MAN, SHOOTING_STAR, GRAVESTONE_DOJI, BEAR_MARUBOZU, BEAR_ENGULF, BEAR_HARAMI, DARK_CLOUD,
                   EVENING_STAR, THREE_CROWS, TWEEZER_TOP, LONG_UPPER_WICK, OUTSIDE_DOWN (mirror definitions, "up" trend)
  neutral: DOJI (body <= 0.1 x range) and INSIDE_BAR (high < prior high, low > prior low) are scored LONG for the record.
Trade: pattern known at the close of day t; enter at the OPEN of t+1 (realistic); exit at the close of t+h,
  h in {1, 3, 5, 10} days. Costs 5 bp a side (10 bp BTC). Overlapping signals are all counted (event study).
Systems: 26 patterns x 4 holds x 12 markets = 1,248.
Score per system, by entry date: IS up to 2013, OOS 2014-2019, HOLDOUT 2020+ (BTC: IS up to 2017, OOS 2018-2021,
  HOLDOUT 2022+); average net return, t-stat (Newey-West-free but events are non-overlapping only when h = 1),
  hit rate; EXCESS over the market's average h-day return (open t+1 -> close t+h) in the same period and direction.
PASS (fixed): excess > 0 in OOS AND HOLDOUT, post-2014 net average > 0 at 2x cost, post-2014 t >= 2 on the
  EXCESS series, and a random-day placebo (same count, same hold, same direction; 500 runs, seed 7) p <= 0.01.
  With 1,248 systems ~12 pass p <= 0.01 by luck, so a PASS is only a candidate; the luck bar is also reported as
  the 99th percentile of the best placebo t across all systems' first placebo draw.
Also a WICK MAP: for each market, next-day open->close return by deciles of lower-wick share, upper-wick share and
  close location (IBS), post-2014. Research, not financial advice.
"""
import os, sys
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); OB = os.path.dirname(HERE)
MARKETS = ["USO", "BNO", "XLE", "XOP", "SPY", "QQQ", "IWM", "DIA", "GLD", "SLV", "TLT", "BTC-USD"]
HOLDS = [1, 3, 5, 10]
BULL = ["HAMMER", "INV_HAMMER", "DRAGONFLY_DOJI", "BULL_MARUBOZU", "BULL_ENGULF", "BULL_HARAMI", "PIERCING",
        "MORNING_STAR", "THREE_SOLDIERS", "TWEEZER_BOTTOM", "LONG_LOWER_WICK", "OUTSIDE_UP"]
BEAR = ["HANGING_MAN", "SHOOTING_STAR", "GRAVESTONE_DOJI", "BEAR_MARUBOZU", "BEAR_ENGULF", "BEAR_HARAMI", "DARK_CLOUD",
        "EVENING_STAR", "THREE_CROWS", "TWEEZER_TOP", "LONG_UPPER_WICK", "OUTSIDE_DOWN"]
NEUTRAL = ["DOJI", "INSIDE_BAR"]


def load(sym):
    p = os.path.join(OB, "data", f"{sym}.csv")
    df = pd.read_csv(p, index_col=0, parse_dates=True)
    df.index = pd.to_datetime(df.index).tz_localize(None).normalize()
    df = df[~df.index.duplicated()][["Open", "High", "Low", "Close"]].dropna()
    return df[(df.High >= df[["Open", "Close"]].max(axis=1)) & (df.Low <= df[["Open", "Close"]].min(axis=1)) & (df.High > df.Low)]


def patterns(b):
    O, H, L, C = b.Open, b.High, b.Low, b.Close
    rng = H - L; body = (C - O).abs(); up = H - np.maximum(O, C); lo = np.minimum(O, C) - L
    green, red = C > O, C < O
    down, upt = C.shift(1) < C.shift(6), C.shift(1) > C.shift(6)  # trend BEFORE the pattern bar
    tr = pd.concat([rng, (H - C.shift()).abs(), (L - C.shift()).abs()], axis=1).max(axis=1); atr = tr.rolling(14).mean()
    O1, H1, L1, C1 = O.shift(1), H.shift(1), L.shift(1), C.shift(1); body1 = body.shift(1); rng1 = rng.shift(1)
    O2, C2, body2, rng2 = O.shift(2), C.shift(2), body.shift(2), rng.shift(2)
    big1 = body1 >= 0.6 * rng1; big2 = body2 >= 0.6 * rng2
    P = {}
    P["HAMMER"] = down & (lo >= 2 * body) & (up <= 0.1 * rng) & (body >= 0.05 * rng)
    P["HANGING_MAN"] = upt & (lo >= 2 * body) & (up <= 0.1 * rng) & (body >= 0.05 * rng)
    P["INV_HAMMER"] = down & (up >= 2 * body) & (lo <= 0.1 * rng) & (body >= 0.05 * rng)
    P["SHOOTING_STAR"] = upt & (up >= 2 * body) & (lo <= 0.1 * rng) & (body >= 0.05 * rng)
    P["DOJI"] = body <= 0.1 * rng
    P["DRAGONFLY_DOJI"] = (body <= 0.1 * rng) & (lo >= 0.7 * rng)
    P["GRAVESTONE_DOJI"] = (body <= 0.1 * rng) & (up >= 0.7 * rng)
    P["BULL_MARUBOZU"] = green & (body >= 0.9 * rng)
    P["BEAR_MARUBOZU"] = red & (body >= 0.9 * rng)
    P["BULL_ENGULF"] = down & (C1 < O1) & green & (O <= C1) & (C >= O1) & (body > body1)
    P["BEAR_ENGULF"] = upt & (C1 > O1) & red & (O >= C1) & (C <= O1) & (body > body1)
    P["BULL_HARAMI"] = down & (C1 < O1) & big1 & green & (O > C1) & (C < O1) & (body < 0.5 * body1)
    P["BEAR_HARAMI"] = upt & (C1 > O1) & big1 & red & (O < C1) & (C > O1) & (body < 0.5 * body1)
    P["PIERCING"] = down & (C1 < O1) & big1 & green & (O < L1) & (C > (O1 + C1) / 2) & (C < O1)
    P["DARK_CLOUD"] = upt & (C1 > O1) & big1 & red & (O > H1) & (C < (O1 + C1) / 2) & (C > O1)
    small1 = body1 <= 0.3 * rng1
    P["MORNING_STAR"] = (C2 < O2) & big2 & small1 & green & (body >= 0.6 * rng) & (C > (O2 + C2) / 2) & (C.shift(2) < C.shift(7))
    P["EVENING_STAR"] = (C2 > O2) & big2 & small1 & red & (body >= 0.6 * rng) & (C < (O2 + C2) / 2) & (C.shift(2) > C.shift(7))
    g1, g2 = C1 > O1, C2 > O2; r1, r2 = C1 < O1, C2 < O2
    P["THREE_SOLDIERS"] = green & g1 & g2 & (C > C1) & (C1 > C2) & (O > O1) & (O < C1) & (O1 > O2) & (O1 < C2)
    P["THREE_CROWS"] = red & r1 & r2 & (C < C1) & (C1 < C2) & (O < O1) & (O > C1) & (O1 < O2) & (O1 > C2)
    P["TWEEZER_BOTTOM"] = down & r1 & green & ((L - L1).abs() <= 0.05 * atr)
    P["TWEEZER_TOP"] = upt & g1 & red & ((H - H1).abs() <= 0.05 * atr)
    P["LONG_LOWER_WICK"] = lo >= 0.6 * rng
    P["LONG_UPPER_WICK"] = up >= 0.6 * rng
    P["INSIDE_BAR"] = (H < H1) & (L > L1)
    P["OUTSIDE_UP"] = (H > H1) & (L < L1) & green
    P["OUTSIDE_DOWN"] = (H > H1) & (L < L1) & red
    feats = pd.DataFrame({"lower_share": lo / rng, "upper_share": up / rng, "ibs": (C - L) / rng}, index=b.index)
    return {k: v.fillna(False).astype(bool) for k, v in P.items()}, feats


def fwd(b, h):
    """Return from the next open to the close h days later, aligned to the signal day."""
    return b.Close.shift(-h) / b.Open.shift(-1) - 1


def periods(sym):
    return ("2018-01-01", "2022-01-01") if sym == "BTC-USD" else ("2014-01-01", "2020-01-01")


def main():
    rows = []; rng = np.random.default_rng(7); placebo_best_t = []
    wick_rows = []
    for sym in MARKETS:
        b = load(sym); P, feats = patterns(b); cost = 1e-3 if sym == "BTC-USD" else 5e-4
        a, z = periods(sym)
        for h in HOLDS:
            r = fwd(b, h); base = r.dropna()
            for name, flag in P.items():
                side = -1 if name in BEAR else 1
                ev = r[flag].dropna() * side
                ex = ev - side * base.mean()  # simple excess vs the whole-sample drift (refined below per period)
                row = dict(sym=sym, pattern=name, side="short" if side < 0 else "long", hold=h)
                for per, mask in {"IS": ev.index < a, "OOS": (ev.index >= a) & (ev.index < z), "HOLDOUT": ev.index >= z,
                                  "POST": ev.index >= a}.items():
                    e = ev[mask]; bm = base[(base.index < a) if per == "IS" else (base.index >= a) & (base.index < z) if per == "OOS"
                                           else (base.index >= z) if per == "HOLDOUT" else (base.index >= a)]
                    x = e - side * bm.mean()
                    row[f"{per}_n"] = len(e)
                    row[f"{per}_net_bp"] = round((e.mean() - 2 * cost) * 1e4, 1) if len(e) else np.nan
                    row[f"{per}_excess_bp"] = round(x.mean() * 1e4, 1) if len(e) else np.nan
                    row[f"{per}_t"] = round(x.mean() / (x.std(ddof=1) / np.sqrt(len(x))), 2) if len(x) > 2 and x.std() > 0 else np.nan
                    if per == "POST":
                        row["POST_hit"] = round(float((e - 2 * cost > 0).mean()), 3) if len(e) else np.nan
                        row["POST_net_bp_2x"] = round((e.mean() - 4 * cost) * 1e4, 1) if len(e) else np.nan
                rows.append(row)
                # first placebo draw for the luck bar
                post = base[base.index >= a]
                if row["POST_n"] > 2:
                    s = post.sample(n=min(row["POST_n"], len(post)), random_state=int(rng.integers(1 << 31))) * side
                    xs = s - side * post.mean()
                    placebo_best_t.append(xs.mean() / (xs.std(ddof=1) / np.sqrt(len(xs))))
        post = b.index >= pd.Timestamp(a); nxt = fwd(b, 1)
        for f in ["lower_share", "upper_share", "ibs"]:
            d = pd.DataFrame({"f": feats[f], "r": nxt})[post].dropna()
            d["dec"] = pd.qcut(d.f.rank(method="first"), 5, labels=[1, 2, 3, 4, 5])
            g = d.groupby("dec", observed=True).r.mean() * 1e4
            wick_rows.append(dict(sym=sym, feature=f, **{f"Q{k}": round(v, 1) for k, v in g.items()}))
    df = pd.DataFrame(rows)
    luck99 = float(np.nanpercentile(np.abs(placebo_best_t), 99)) if placebo_best_t else np.nan
    cand = df[(df.OOS_excess_bp > 0) & (df.HOLDOUT_excess_bp > 0) & (df.POST_net_bp_2x > 0) & (df.POST_t >= 2)].copy()
    ps = []
    for _, r in cand.iterrows():
        b = load(r.sym); a, _ = periods(r.sym); side = -1 if r.side == "short" else 1
        post = fwd(b, r.hold).dropna(); post = post[post.index >= a]
        real = r.POST_excess_bp / 1e4
        sims = np.array([(post.sample(n=int(r.POST_n), replace=False, random_state=i) * side - side * post.mean()).mean()
                         for i in range(500)])
        ps.append(round(float((sims >= real).mean()), 3))
    cand["placebo_p"] = ps
    df = df.merge(cand[["sym", "pattern", "hold", "placebo_p"]], how="left", on=["sym", "pattern", "hold"])
    df["PASS"] = (df.placebo_p <= 0.01) & (df.POST_t >= luck99)
    df.to_csv(os.path.join(HERE, "candle_results.csv"), index=False)
    wk = pd.DataFrame(wick_rows); wk.to_csv(os.path.join(HERE, "wick_map.csv"), index=False)
    pd.set_option("display.width", 250); pd.set_option("display.max_rows", 400); pd.set_option("display.max_columns", 30)
    print(f"Systems: {len(df)}; luck bar (99th pct |t| of random-day placebos): {luck99:.2f}")
    print(f"Passed first gates: {len(cand)}; placebo p <= 0.01: {int((df.placebo_p <= 0.01).sum())}; "
          f"PASS (also above the luck bar): {int(df.PASS.sum())}")
    cols = ["sym", "pattern", "side", "hold", "POST_n", "POST_hit", "IS_excess_bp", "OOS_excess_bp", "HOLDOUT_excess_bp",
            "POST_net_bp", "POST_net_bp_2x", "POST_t", "placebo_p", "PASS"]
    print("\nCandidates (passed the first gates):")
    print(df[df.placebo_p.notna()].sort_values("POST_t", ascending=False)[cols].to_string(index=False))
    print("\nEach pattern across all markets (post-2014, hold 1 day): share of markets with positive excess, median excess bp")
    p1 = df[df.hold == 1].groupby("pattern").agg(markets_positive=("POST_excess_bp", lambda x: round((x > 0).mean(), 2)),
                                                 median_excess_bp=("POST_excess_bp", "median"), median_t=("POST_t", "median"),
                                                 events=("POST_n", "sum")).sort_values("median_t", ascending=False)
    print(p1.to_string())
    print("\nWICK MAP: next-day open->close return (bp) by quintile of the feature (Q1 = smallest), post-2014")
    print(wk.to_string(index=False))


if __name__ == "__main__":
    main()
