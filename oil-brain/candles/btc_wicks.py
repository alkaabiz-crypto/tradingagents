"""BTC wick strategies, incl. the "John Wick" candle (pre-registered 2026-11-25, before any run; the user asked for
a BTCUSD strategy built from the candle brain, starting with the "John Wick" candle).

Definitions (long side; the SHORT side is the exact mirror with the upper wick and highs):
  W1 JOHN WICK: lower wick >= 60% of the candle's range AND range >= 1.5 x ATR(14) (an unusually big wick)
  W2 JOHN WICK + SWEEP: W1 and the low takes out the lowest low of the prior 20 candles (a liquidity grab)
  W3 SWING FAILURE (SFP): low below the prior 20-candle low AND close back above that low (any wick size)
  W4 TURTLE SOUP (Raschke): low below the prior 20-candle low, where that old low was set >= 4 candles ago,
     and close back above the old low
  W5 JOHN WICK WITH THE TREND: W1 and close above the 200-candle average (short: below)
  W6 CONTROL: a long lower wick (>= 60% of range) on a SMALL candle (range < 1.0 x ATR) — tests whether size matters
Entry: at the close of the signal candle (BTC trades 24/7). One position at a time per system.
Exits: H1/H3/H5/H10 = hold 1/3/5/10 candles to the close;
       SR = stop just beyond the wick (low - 0.1 x ATR), target 2R, max 10 candles (if a candle touches both: stop).
Timeframes: D1 = UTC daily candles 2014-09 -> now (IS to 2017, OOS 2018-2021, HOLDOUT 2022+);
            H4 and H1 = from Yahoo 1h bars, 2024-11 -> now (YEAR1 = first 12 months, YEAR2 = the rest).
Systems: 6 rules x 2 sides x 5 exits x 3 timeframes = 180.
Costs: 10 bp a side (Exness-like BTCUSD spread); stress 2x. (Overnight swaps not included; see the notes.)
PASS (fixed): average trade > 0 in OOS and HOLDOUT (D1) / in YEAR1 and YEAR2 (H4, H1); > 0 at 2x cost over the
  test span (D1: 2018+; H: all); t >= 2 over that span; random-entry placebo (same count, same exit, 500 runs,
  seed 21) p <= 0.01; and t above the family-wise luck bar for 180 systems (~3.4). Neighbour check before any sleeve.
Research, not financial advice.
"""
import os
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); OB = os.path.dirname(HERE)
SCR = "/tmp/claude-0/-home-user-tradingagents/862edda5-54ef-5bf8-971e-481bdcdf4dee/scratchpad/btc_1h.csv"
COST = 1e-3
RULES = ["W1", "W2", "W3", "W4", "W5", "W6"]
EXITS = ["H1", "H3", "H5", "H10", "SR"]
DESC = {"W1": "John Wick", "W2": "John Wick + sweep", "W3": "swing failure", "W4": "turtle soup",
        "W5": "John Wick + trend", "W6": "small-candle wick (control)"}


def daily():
    d = pd.read_csv(os.path.join(OB, "data/BTC-USD.csv"), index_col=0, parse_dates=True)
    d.index = pd.to_datetime(d.index).tz_localize(None).normalize()
    d = d[~d.index.duplicated()][["Open", "High", "Low", "Close"]].dropna()
    return d[d.index < pd.Timestamp.utcnow().tz_localize(None).normalize()]  # finished UTC days only


def hourly(rule="1h"):
    if not os.path.exists(SCR):
        import yfinance as yf
        yf.Ticker("BTC-USD").history(period="730d", interval="1h").to_csv(SCR)
    h = pd.read_csv(SCR, index_col=0)
    h.index = pd.to_datetime(h.index, utc=True).tz_localize(None)
    h = h[["Open", "High", "Low", "Close"]].dropna(); h = h[~h.index.duplicated()].iloc[:-1]  # drop the unfinished bar
    if rule == "1h":
        return h
    return h.resample(rule).agg({"Open": "first", "High": "max", "Low": "min", "Close": "last"}).dropna().iloc[:-1]


def signals(b, side):
    O, H, L, C = b.Open, b.High, b.Low, b.Close
    rng = H - L; lo = np.minimum(O, C) - L; up = H - np.maximum(O, C)
    tr = pd.concat([rng, (H - C.shift()).abs(), (L - C.shift()).abs()], axis=1).max(axis=1); atr = tr.rolling(14).mean()
    sma = C.rolling(200).mean()
    if side == 1:
        wick, prior = lo, L.shift(1).rolling(20).min()
        sweep = L < prior; back = C > prior
        age = L.shift(1).rolling(20).apply(lambda x: 19 - int(np.argmin(x)), raw=True)  # candles since the old low
        trend = C > sma
    else:
        wick, prior = up, H.shift(1).rolling(20).max()
        sweep = H > prior; back = C < prior
        age = H.shift(1).rolling(20).apply(lambda x: 19 - int(np.argmax(x)), raw=True)
        trend = C < sma
    big = (wick >= 0.6 * rng) & (rng >= 1.5 * atr)
    S = {"W1": big, "W2": big & sweep, "W3": sweep & back, "W4": sweep & back & (age >= 3),
         "W5": big & trend, "W6": (wick >= 0.6 * rng) & (rng < atr)}
    return {k: v.fillna(False).values for k, v in S.items()}, atr.values


def run(b, flags, atr, side, ex, start, end):
    C, H, L = b.Close.values, b.High.values, b.Low.values; idx = b.index; n = len(C)
    s = (idx >= pd.Timestamp(start)) & (idx < pd.Timestamp(end)); out = []; k = 0
    while k < n - 1:
        if s[k] and flags[k] and not np.isnan(atr[k]):
            e = C[k]
            if ex == "SR":
                stop = (L[k] - 0.1 * atr[k]) if side == 1 else (H[k] + 0.1 * atr[k]); risk = abs(e - stop)
                tgt = e + side * 2 * risk; j, px = None, None
                for jj in range(k + 1, min(k + 11, n)):
                    if (side == 1 and L[jj] <= stop) or (side == -1 and H[jj] >= stop):
                        j, px = jj, stop; break
                    if (side == 1 and H[jj] >= tgt) or (side == -1 and L[jj] <= tgt):
                        j, px = jj, tgt; break
                if j is None:
                    j = min(k + 10, n - 1); px = C[j]
            else:
                j = min(k + int(ex[1:]), n - 1); px = C[j]
            if j == k:
                break
            out.append((idx[k], side * (px / e - 1))); k = j
        else:
            k += 1
    return pd.DataFrame(out, columns=["date", "g"])


def st(t, mult=1.0):
    if len(t) < 3:
        return np.nan, np.nan
    r = t.g - 2 * COST * mult
    return r.mean() * 1e4, r.mean() / (r.std(ddof=1) / np.sqrt(len(r)))


def main():
    TF = {"D1": (daily(), [("IS", "2014-01-01", "2018-01-01"), ("A", "2018-01-01", "2022-01-01"), ("B", "2022-01-01", "2030-01-01")], "2018-01-01")}
    for tf, rule in [("H4", "4h"), ("H1", "1h")]:
        h = hourly(rule); mid = h.index[0] + pd.Timedelta(days=365)
        TF[tf] = (h, [("IS", "2000-01-01", "2000-01-02"), ("A", str(h.index[0]), str(mid)), ("B", str(mid), "2030-01-01")], str(h.index[0]))
    rows = []
    for tf, (b, pers, test_from) in TF.items():
        for side in (1, -1):
            S, atr = signals(b, side)
            for rl in RULES:
                for ex in EXITS:
                    r = dict(tf=tf, rule=rl, name=DESC[rl], side="long" if side == 1 else "short", exit=ex)
                    for nm, a, z in pers:
                        t = run(b, S[rl], atr, side, ex, a, z); m, tt = st(t)
                        r[f"{nm}_n"], r[f"{nm}_bp"], r[f"{nm}_t"] = len(t), m, tt
                    t = run(b, S[rl], atr, side, ex, test_from, "2030-01-01"); m, tt = st(t); m2, _ = st(t, 2)
                    r.update(test_n=len(t), test_bp=m, test_t=tt, test_bp_2x=m2,
                             test_win=float(((t.g - 2 * COST) > 0).mean()) if len(t) else np.nan)
                    rows.append(r)
    df = pd.DataFrame(rows)
    cand = df[(df.A_bp > 0) & (df.B_bp > 0) & (df.test_bp_2x > 0) & (df.test_t >= 2)].copy()
    rng = np.random.default_rng(21); ps = []
    for _, r in cand.iterrows():
        b, pers, test_from = TF[r.tf]; side = 1 if r.side == "long" else -1; _, atr = signals(b, side)
        pos = np.where(b.index >= pd.Timestamp(test_from))[0][:-12]; sims = []
        for _ in range(500):
            m = np.zeros(len(b), bool); m[rng.choice(pos, size=min(int(r.test_n), len(pos)), replace=False)] = True
            t = run(b, m, atr, side, r.exit, test_from, "2030-01-01"); sims.append(st(t)[0])
        ps.append(round(float(np.nanmean(np.array(sims) >= r.test_bp)), 3))
    cand["placebo_p"] = ps
    df = df.merge(cand[["tf", "rule", "side", "exit", "placebo_p"]], how="left", on=["tf", "rule", "side", "exit"])
    df["PASS"] = (df.placebo_p <= 0.01) & (df.test_t >= 3.4)
    df.to_csv(os.path.join(HERE, "btc_wicks_results.csv"), index=False)
    pd.set_option("display.width", 260); pd.set_option("display.max_rows", 300)
    cols = ["tf", "name", "side", "exit", "IS_bp", "A_n", "A_bp", "B_n", "B_bp", "test_n", "test_win", "test_bp", "test_bp_2x", "test_t", "placebo_p", "PASS"]
    print(f"Systems: {len(df)}; passed first gates: {len(cand)}; placebo p <= 0.01: {int((df.placebo_p <= 0.01).sum())}; PASS: {int(df.PASS.sum())}")
    print("\nCandidates:"); print(df[df.placebo_p.notna()].sort_values("test_t", ascending=False)[cols].round(2).to_string(index=False))
    print("\nJohn Wick (W1) and the control (W6), every timeframe/side/exit:")
    print(df[df.rule.isin(["W1", "W2", "W6"])][cols].round(2).to_string(index=False))


if __name__ == "__main__":
    main()
