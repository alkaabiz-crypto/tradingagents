"""Combo lab (pre-registered 2026-11-24, before running): STRATEGY (daily regime) x INDICATOR (hourly entry)
x SKILLS (trade management as in trader-exit / trader-budget / trader-risk), on 6 markets.

Data: Yahoo 1-hour bars, regular session, 2023-12-28 .. 2026-11-24.
Honest test: SELECT on 2023-12-28 .. 2025-06-30 only (IS), JUDGE on 2025-07-01 .. now (OOS, unseen).

Strategy layer (direction allowed today, from the PREVIOUS day's close):
  R0 any direction     R1 50-day trend (above SMA50 -> longs only, below -> shorts only)
  R2 200-day trend     R3 oil brain v2 composite sign (USO and XLE only)
  R4 dollar: DXY 63-day change < 0 -> longs only, > 0 -> shorts only
Indicator layer (signal at an hourly close, entry at the next bar's open):
  E1 opening-range breakout: close beyond the 09:30 bar's high/low (once a day)
  E2 RSI(14) pullback: RSI crosses up through 30 (long) / down through 70 (short)
  E3 EMA 9/21 cross      E4 Donchian: close beyond the prior 20-bar high/low
  E5 VWAP reclaim: close crosses the session VWAP
Skills layer (trader-exit rules; trader-budget sizing = fixed dollar risk, so results are in R):
  X1 day trade: stop 1.0 x ATR(14 bars), target 2R, flat at the day's last bar (trader-exit default)
  X2 swing: stop 1.5 x ATR, target 3R, max hold 21 bars (~3 days)
  X3 trailing: initial stop 2 x ATR, trailing at 2 x ATR, max hold 35 bars (~5 days)
  trader-risk: one position at a time per system; stop must be on the right side; risk >= 0.05% of price.
Costs: 3 bp per side (ETF spread + slippage), stress 6 bp.
Per system: trades, win rate, average R, t-stat of R, profit factor, IS vs OOS.
Selection test: the 15 systems with the best IS t (min 30 IS trades) are judged on OOS. Expected by luck:
about half positive. A combo is worth a forward paper test only if it is positive OOS with OOS t >= 2,
and still positive at 6 bp.
"""
import os, itertools, json
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
OB = os.path.dirname(HERE)
IS_END = pd.Timestamp("2025-06-30 23:59", tz="America/New_York")
INSTR = ["USO", "XLE", "SPY", "QQQ", "GLD", "IWM"]


def daily(sym):
    for p in (os.path.join(OB, "data", f"{sym}.csv"), os.path.join(OB, "brains", "liquidity", "data", f"{sym}.csv")):
        if os.path.exists(p):
            s = pd.read_csv(p, index_col=0, parse_dates=True)["Close"]
            s.index = pd.to_datetime(s.index).tz_localize(None).normalize()
            return s[~s.index.duplicated()]
    raise FileNotFoundError(sym)


import sys; sys.path.insert(0, OB)
import brain_v2 as B
bv = B.votes(B.features()).composite
dxy = daily("DX-Y.NYB")


def regimes(sym):
    c = daily(sym)
    out = {"R0": pd.Series(0, index=c.index),
           "R1": np.sign(c - c.rolling(50).mean()),
           "R2": np.sign(c - c.rolling(200).mean()),
           "R4": -np.sign(dxy.reindex(c.index, method="ffill").pct_change(63))}
    if sym in ("USO", "XLE"):
        out["R3"] = np.sign(bv.reindex(c.index, method="ffill"))
    # value known at the close of day d applies to day d+1's bars
    return {k: v.shift(1) for k, v in out.items()}


def rsi(x, n=14):
    d = x.diff(); up = d.clip(lower=0).ewm(alpha=1 / n).mean(); dn = (-d.clip(upper=0)).ewm(alpha=1 / n).mean()
    return 100 - 100 / (1 + up / dn)


def entries(b):
    day = b.index.date
    first = b.groupby(day).transform("first")
    is_first = b.index.strftime("%H:%M") == "09:30"
    orh = b.High.where(is_first).groupby(day).transform("max"); orl = b.Low.where(is_first).groupby(day).transform("min")
    e1 = np.where(~is_first & (b.Close > orh), 1, np.where(~is_first & (b.Close < orl), -1, 0))
    e1 = pd.Series(e1, index=b.index)
    seen = e1.ne(0).groupby(day).cumsum()
    e1 = e1.where((seen == 1) & e1.ne(0), 0)  # first breakout of the day only
    r = rsi(b.Close)
    e2 = pd.Series(np.where((r.shift(1) < 30) & (r >= 30), 1, np.where((r.shift(1) > 70) & (r <= 70), -1, 0)), index=b.index)
    f9, f21 = b.Close.ewm(span=9).mean(), b.Close.ewm(span=21).mean()
    up = f9 > f21
    e3 = pd.Series(np.where(up & ~up.shift(1, fill_value=False), 1, np.where(~up & up.shift(1, fill_value=False), -1, 0)), index=b.index)
    hi, lo = b.High.rolling(20).max().shift(1), b.Low.rolling(20).min().shift(1)
    e4 = pd.Series(np.where(b.Close > hi, 1, np.where(b.Close < lo, -1, 0)), index=b.index)
    tp = (b.High + b.Low + b.Close) / 3
    vwap = (tp * b.Volume).groupby(day).cumsum() / b.Volume.groupby(day).cumsum()
    above = b.Close > vwap
    same_day = pd.Series(day, index=b.index) == pd.Series(day, index=b.index).shift(1)
    e5 = pd.Series(np.where(same_day & above & ~above.shift(1, fill_value=False), 1,
                            np.where(same_day & ~above & above.shift(1, fill_value=True), -1, 0)), index=b.index)
    return {"E1": e1, "E2": e2, "E3": e3, "E4": e4, "E5": e5}


def run(b, sig, reg, exit_kind, atr, cost_bp):
    O, H, L, C = b.Open.values, b.High.values, b.Low.values, b.Close.values
    d = b.index.date; last_bar = pd.Series(d, index=b.index) != pd.Series(d, index=b.index).shift(-1)
    last_bar = last_bar.values; s = sig.values; g = reg.values; A = atr.values
    n = len(b); i = 0; trades = []
    k_stop, k_tgt, max_hold, trail = {"X1": (1.0, 2.0, 99, False), "X2": (1.5, 3.0, 21, False), "X3": (2.0, None, 35, True)}[exit_kind]
    while i < n - 1:
        side = s[i]
        if side == 0 or np.isnan(A[i]) or (g[i] != 0 and not np.isnan(g[i]) and np.sign(g[i]) != side) or np.isnan(g[i]):
            i += 1; continue
        if exit_kind == "X1" and last_bar[i]:
            i += 1; continue
        e = O[i + 1]; risk = k_stop * A[i]
        if risk < 0.0005 * e: i += 1; continue
        stop = e - side * risk; tgt = e + side * k_tgt * risk if k_tgt else None
        j = i + 1; out = None
        while j < n:
            if side > 0 and L[j] <= stop: out = min(stop, O[j]) if j > i + 1 else stop; break
            if side < 0 and H[j] >= stop: out = max(stop, O[j]) if j > i + 1 else stop; break
            if tgt is not None and ((side > 0 and H[j] >= tgt) or (side < 0 and L[j] <= tgt)): out = tgt; break
            if trail:
                stop = max(stop, C[j] - risk) if side > 0 else min(stop, C[j] + risk)
            if (exit_kind == "X1" and last_bar[j]) or (j - i >= max_hold):
                out = C[j]; break
            j += 1
        if out is None: break
        R = (side * (out - e) - 2 * cost_bp / 1e4 * e) / risk
        trades.append((b.index[i + 1], R))
        i = j + 1
    return pd.DataFrame(trades, columns=["t", "R"])


def stats(t):
    if len(t) < 2: return dict(n=len(t), win=np.nan, avgR=np.nan, tR=np.nan, pf=np.nan)
    R = t.R; pf = R[R > 0].sum() / max(1e-9, -R[R < 0].sum())
    return dict(n=len(t), win=round((R > 0).mean(), 2), avgR=round(R.mean(), 3),
                tR=round(R.mean() / R.std() * np.sqrt(len(R)), 2), pf=round(pf, 2))


rows = []
for sym in INSTR:
    b = pd.read_csv(os.path.join(HERE, "data", f"{sym}_1h.csv"), index_col=0)
    b.index = pd.to_datetime(b.index, utc=True).tz_convert("America/New_York")
    b = b[~b.index.duplicated()].dropna()
    tr = pd.concat([b.High - b.Low, (b.High - b.Close.shift()).abs(), (b.Low - b.Close.shift()).abs()], axis=1).max(axis=1)
    atr = tr.rolling(14).mean()
    regs = regimes(sym); ents = entries(b)
    bday = pd.DatetimeIndex(b.index.tz_localize(None).normalize())
    for (rk, rg), (ek, sg), xk in itertools.product(regs.items(), ents.items(), ["X1", "X2", "X3"]):
        rr = pd.Series(rg.reindex(bday).values, index=b.index)
        if rk == "R0": rr = rr.fillna(0)
        t3 = run(b, sg, rr, xk, atr, 3); t6 = run(b, sg, rr, xk, atr, 6)
        is_, oos = t3[t3.t <= IS_END], t3[t3.t > IS_END]
        si, so, s6 = stats(is_), stats(oos), stats(t6[t6.t > IS_END])
        rows.append(dict(system=f"{sym} {rk} {ek} {xk}", sym=sym, regime=rk, entry=ek, exit=xk,
                         **{f"is_{k}": v for k, v in si.items()}, **{f"oos_{k}": v for k, v in so.items()},
                         oos6_avgR=s6["avgR"]))
df = pd.DataFrame(rows)
df.to_csv(os.path.join(HERE, "combo_results.csv"), index=False)
pick = df[df.is_n >= 30].sort_values("is_tR", ascending=False).head(15)
pd.set_option("display.width", 250)
print(f"{len(df)} systems tested. Top 15 chosen on IS (Dec 2023 - Jun 2025), judged on OOS (Jul 2025 - Nov 2026):")
print(pick[["system", "is_n", "is_win", "is_avgR", "is_tR", "oos_n", "oos_win", "oos_avgR", "oos_tR", "oos6_avgR"]].to_string(index=False))
pos = (pick.oos_avgR > 0).mean()
print(f"\nOf the 15 IS winners, {pos:.0%} are positive OOS (luck alone: ~50%). "
      f"Mean OOS avg R {pick.oos_avgR.mean():+.3f}.")
ok = df[(df.is_n >= 30)]
print("Correlation of IS t with OOS t across all systems: %.2f" % ok[["is_tR", "oos_tR"]].corr().iloc[0, 1])
surv = pick[(pick.oos_tR >= 2) & (pick.oos6_avgR > 0)]
print("Survivors (OOS t >= 2 and positive at 6 bp):", surv.system.tolist() or "none")
for k in ["regime", "entry", "exit", "sym"]:
    g = ok.groupby(k)[["is_avgR", "oos_avgR"]].mean().round(3)
    print(f"\nAverage R by {k}:\n{g.to_string()}")
json.dump(dict(systems=len(df), survivors=surv.system.tolist()), open(os.path.join(HERE, "combo_summary.json"), "w"))
