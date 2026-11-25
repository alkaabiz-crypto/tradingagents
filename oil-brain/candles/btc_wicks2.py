"""BTC wicks, round 2 (pre-registered 2026-11-25 after the John Wick research, before running; counts on top of
round 1's 180 systems -> 180 + 48 = 228 for the luck bar, ~t 3.5).
Rules (long; short = mirror), from the research notes (candles/REF_johnwick_btc.md):
  L1 LIQUIDATION WICK: lower wick >= 2 x ATR(14) AND the largest lower wick of the last 50 candles
  L2 L1 + uptrend (close > 200-candle average)
  P1 PLAIN PIN BAR benchmark: lower wick >= 2/3 of the range and close in the top third
  C1 CONFIRMED SWEEP: round-1 W2 (John Wick + sweep) but enter only if the NEXT candle trades above the signal
     candle's high (entry at that high, or the open if it gaps above)
Entry: L1, L2, P1 at the NEXT OPEN (more realistic than round 1's close); C1 as above.
Exits: H1, H3, H5 candles to the close; SR = stop at the wick tip - 0.1 x ATR, target 2R, max 10 candles.
Timeframes D1, H4, H1 (as round 1). Costs 10 bp a side; stress 2x. Same gates as round 1 with the luck bar t >= 3.5.
Research, not financial advice.
"""
import os, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import btc_wicks as W

RULES = ["L1", "L2", "P1", "C1"]; EXITS = ["H1", "H3", "H5", "SR"]
DESC = {"L1": "liquidation wick", "L2": "liquidation wick + trend", "P1": "plain pin bar", "C1": "confirmed sweep"}


def sig(b, side):
    O, H, L, C = b.Open, b.High, b.Low, b.Close
    rng = H - L; tr = pd.concat([rng, (H - C.shift()).abs(), (L - C.shift()).abs()], axis=1).max(axis=1); atr = tr.rolling(14).mean()
    wick = (np.minimum(O, C) - L) if side == 1 else (H - np.maximum(O, C))
    closeloc = (C - L) / rng if side == 1 else (H - C) / rng
    prior = L.shift(1).rolling(20).min() if side == 1 else H.shift(1).rolling(20).max()
    sweep = (L < prior) if side == 1 else (H > prior)
    trend = (C > C.rolling(200).mean()) if side == 1 else (C < C.rolling(200).mean())
    liq = (wick >= 2 * atr) & (wick >= wick.rolling(50).max())
    jw = (wick >= 0.6 * rng) & (rng >= 1.5 * atr) & sweep
    S = {"L1": liq, "L2": liq & trend, "P1": (wick >= 2 / 3 * rng) & (closeloc >= 2 / 3), "C1": jw}
    return {k: v.fillna(False).values for k, v in S.items()}, atr.values


def run(b, flags, atr, side, ex, rule, start, end):
    O, C, H, L = b.Open.values, b.Close.values, b.High.values, b.Low.values; idx = b.index; n = len(C)
    s = (idx >= pd.Timestamp(start)) & (idx < pd.Timestamp(end)); out = []; k = 0
    while k < n - 2:
        if s[k] and flags[k] and not np.isnan(atr[k]):
            i = k + 1  # entry candle
            if rule == "C1":
                trig = H[k] if side == 1 else L[k]
                if (side == 1 and H[i] < trig) or (side == -1 and L[i] > trig):
                    k += 1; continue
                e = max(trig, O[i]) if side == 1 else min(trig, O[i])
            else:
                e = O[i]
            tip = L[k] if side == 1 else H[k]
            if ex == "SR":
                stop = tip - side * 0.1 * atr[k]; risk = abs(e - stop)
                if risk <= 0 or (side == 1 and stop >= e) or (side == -1 and stop <= e):
                    k += 1; continue
                tgt = e + side * 2 * risk; j = None
                for jj in range(i, min(i + 10, n)):
                    if (side == 1 and L[jj] <= stop) or (side == -1 and H[jj] >= stop): j, px = jj, stop; break
                    if (side == 1 and H[jj] >= tgt) or (side == -1 and L[jj] <= tgt): j, px = jj, tgt; break
                if j is None: j = min(i + 9, n - 1); px = C[j]
            else:
                j = min(i + int(ex[1:]) - 1, n - 1); px = C[j]
            out.append((idx[k], side * (px / e - 1))); k = max(j, k + 1)
        else:
            k += 1
    return pd.DataFrame(out, columns=["date", "g"])


def main():
    TF = {"D1": (W.daily(), [("A", "2018-01-01", "2022-01-01"), ("B", "2022-01-01", "2030-01-01")], "2018-01-01")}
    for tf, r in [("H4", "4h"), ("H1", "1h")]:
        h = W.hourly(r); mid = h.index[0] + pd.Timedelta(days=365)
        TF[tf] = (h, [("A", str(h.index[0]), str(mid)), ("B", str(mid), "2030-01-01")], str(h.index[0]))
    rows = []
    for tf, (b, pers, tf0) in TF.items():
        for side in (1, -1):
            S, atr = sig(b, side)
            for rl in RULES:
                for ex in EXITS:
                    r = dict(tf=tf, name=DESC[rl], side="long" if side == 1 else "short", exit=ex)
                    for nm, a, z in pers:
                        t = run(b, S[rl], atr, side, ex, rl, a, z); m, tt = W.st(t); r[f"{nm}_n"], r[f"{nm}_bp"] = len(t), m
                    t = run(b, S[rl], atr, side, ex, rl, tf0, "2030-01-01"); m, tt = W.st(t); m2, _ = W.st(t, 2)
                    r.update(test_n=len(t), test_win=float(((t.g - 2 * W.COST) > 0).mean()) if len(t) else np.nan,
                             test_bp=m, test_bp_2x=m2, test_t=tt)
                    rows.append(r)
    df = pd.DataFrame(rows)
    df["first_gates"] = (df.A_bp > 0) & (df.B_bp > 0) & (df.test_bp_2x > 0) & (df.test_t >= 2)
    df["PASS"] = df.first_gates & (df.test_t >= 3.5)
    df.to_csv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "btc_wicks2_results.csv"), index=False)
    pd.set_option("display.width", 250); pd.set_option("display.max_rows", 100)
    print(f"Systems: {len(df)}; first gates: {int(df.first_gates.sum())}; PASS: {int(df.PASS.sum())}")
    print(df.sort_values("test_t", ascending=False).head(15).round(2).to_string(index=False))


if __name__ == "__main__":
    main()
