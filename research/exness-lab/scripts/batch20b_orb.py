"""Batch 20b, pre-registered after Batch 20 found the first-hour ORB (B) positive every year on USTEC and US500.
Neighbours: TP in {1R, 1.5R, 2R, none (exit 16:00)} x stop in {other side, range middle}; long-only and short-only splits;
second data source = CME futures NQ=F / ES=F hourly (2024-07 ->), session bars 09:00/10:00 differ, so the first hour is
09:30-10:30 for ETFs and 10:00-11:00 for futures (bars on the hour). Same costs and worst-case bar rules as Batch 20.
"""
import numpy as np, pandas as pd
def load(f, m):
    d = pd.read_csv(f"intraday/{f}_1h.csv", index_col=0); d.index = pd.to_datetime(d.index, utc=True).tz_convert("America/New_York")
    return d[["Open", "High", "Low", "Close"]] * m
def orb(d, lots, c1, start, end, tpm, mid, sides):
    hh = d.index.strftime("%H:%M"); cash = d[(hh >= start) & (hh < end)]; rows = []
    for day, b in cash.groupby(cash.index.date):
        if len(b) < 3: continue
        H, L, C, O = b.High.values, b.Low.values, b.Close.values, b.Open.values; rh, rl = H[0], L[0]
        r = 0.0
        for i in range(1, len(H)):
            up, dn = H[i] >= rh, L[i] <= rl
            side = 1 if up and "L" in sides else (-1 if dn and "S" in sides else 0)
            if up and dn: side = -1 if "S" in sides and "L" not in sides else (1 if "L" in sides else 0)
            if side == 0: continue
            lvl = rh if side > 0 else rl; fill = (max(lvl, O[i]) if side > 0 else min(lvl, O[i])) * (1 + side * 1e-4)
            stop = ((rh + rl) / 2) if mid else (rl if side > 0 else rh); risk = abs(fill - stop)
            tp = fill + side * tpm * risk if tpm else None; r = None
            for j in range(i, len(H)):
                if (L[j] <= stop) if side > 0 else (H[j] >= stop): r = side * (stop - fill); break
                if j > i and tp is not None and ((H[j] >= tp) if side > 0 else (L[j] <= tp)): r = side * (tp - fill); break
            if r is None: r = side * (C[-1] - fill)
            r -= 2 * c1; break
        rows.append((pd.Timestamp(day), r * lots))
    return pd.Series(dict(rows))
def st(s):
    n = (s != 0).sum(); e = s.cumsum()
    return f"{n} | {(s>0).sum()/max(n,1):.0%} | {s.loc['2024'].sum():+.0f} | {s.loc['2025'].sum():+.0f} | {s.loc['2026'].sum():+.0f} | {(e-e.cummax()).min():.0f}"
print("| market | source | stop | TP | sides | trades | win | 2024 | 2025 | 2026 | worst drop |")
for mk, f, m, lots, c1, start, end in (("USTEC", "QQQ", 41, 0.05, 1.12, "09:30", "16:00"), ("USTEC", "NQ_F", 1, 0.05, 1.12, "10:00", "16:00"),
                                       ("US500", "SPY", 10, 0.14, 0.4, "09:30", "16:00"), ("US500", "ES_F", 1, 0.14, 0.4, "10:00", "16:00")):
    d = load(f, m)
    for mid in (False, True):
        for tpm in (1, 1.5, 2, None):
            print(f"| {mk} | {f} | {'mid' if mid else 'other side'} | {tpm or 'close'} | both | {st(orb(d, lots, c1, start, end, tpm, mid, 'LS'))} |")
    for sd in ("L", "S"):
        print(f"| {mk} | {f} | other side | 1.5 | {sd} only | {st(orb(d, lots, c1, start, end, 1.5, False, sd))} |")
