"""Batch 22, pre-registered 2026-11-26 before running (Hazza's request). Supertrend + VWAP on BTC and oil, hourly bars.
Data: Yahoo hourly CL=F (2024-07 ->; Exness USOIL 0.01 lot = 10 bbl = $10 per $1) and BTC-USD (2024-11 ->; 0.01 lot).
Supertrend(10, 3) on hourly bars (ATR Wilder 10). VWAP resets each day (oil: NY date, flat by 16:00 NY;
BTC: UTC date, flat at 23:00 UTC bar close). BTC Yahoo volume is missing on ~half the bars: missing volume is filled
with that day's median volume (approximate VWAP).
Signals act at the NEXT bar's open (no look-ahead). Costs per side: oil $0.03/bbl, BTC $3.20 (+1 bp slippage each fill);
sensitivity oil $0.05.
 S1 Supertrend flip in the VWAP direction: ST turns up while close > VWAP -> long; ST turns down while close < VWAP -> short.
    Stop = the Supertrend line (trailing, checked each bar); exit at opposite flip or end of day.
 S2 = S1 with a target at 2x the initial risk.
 S3 = Supertrend flips alone (no VWAP filter), same exits.  (comparison)
 S4 Pullback: ST up and close crosses back above VWAP -> long (mirror short); stop = ST line; exit end of day.
 S5 = S4 with a target at 1.5x initial risk.
5 rules x 2 markets = 10 trials. Lead = positive in each half (oil 2024-07..2025-08 vs 2025-09..; BTC 2024-11..2025-11 vs after).
"""
import numpy as np, pandas as pd, sys
OILC = float(sys.argv[1]) if len(sys.argv) > 1 else 0.03
def load(f):
    d = pd.read_csv(f"intraday/{f}_1h.csv", index_col=0); d.index = pd.to_datetime(d.index, utc=True); return d
def supertrend(d, n=10, k=3):
    h, l, c = d.High, d.Low, d.Close
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1); atr = tr.ewm(alpha=1/n, adjust=False).mean()
    mid = (h + l) / 2; ub, lb = (mid + k * atr).values, (mid - k * atr).values; C = c.values
    fu, fl, st, dirn = ub.copy(), lb.copy(), np.zeros(len(C)), np.ones(len(C))
    for i in range(1, len(C)):
        fu[i] = ub[i] if (ub[i] < fu[i-1] or C[i-1] > fu[i-1]) else fu[i-1]
        fl[i] = lb[i] if (lb[i] > fl[i-1] or C[i-1] < fl[i-1]) else fl[i-1]
        dirn[i] = 1 if C[i] > fu[i-1] else (-1 if C[i] < fl[i-1] else dirn[i-1])
        st[i] = fl[i] if dirn[i] > 0 else fu[i]
    return pd.Series(st, index=d.index), pd.Series(dirn, index=d.index)
def run(mk):
    if mk == "OIL":
        d = load("CL_F").tz_convert("America/New_York"); day = pd.Series(d.index.date, index=d.index)
        # trading day ends 17:00 NY; bars from 18:00 belong to the next day; flat by the 16:00 bar
        day = pd.Series((d.index + pd.Timedelta(hours=6)).date, index=d.index); last_ok = d.index.strftime("%H:%M") <= "15:00"
        last_ok = pd.Series(last_ok | (d.index.hour >= 18), index=d.index); mult, cost = 10.0, OILC
    else:
        d = load("BTC-USD"); day = pd.Series(d.index.date, index=d.index); last_ok = pd.Series(d.index.hour < 23, index=d.index); mult, cost = 0.01, 3.20
    v = d.Volume.where(d.Volume > 0); v = v.fillna(v.groupby(day).transform("median")).fillna(1.0)
    tp_ = (d.High + d.Low + d.Close) / 3; vwap = (tp_ * v).groupby(day).cumsum() / v.groupby(day).cumsum()
    st, dr = supertrend(d)
    O, H, L, C, ST, DR, VW, DY, OK = d.Open.values, d.High.values, d.Low.values, d.Close.values, st.values, dr.values, vwap.values, day.values, last_ok.values
    res = {k: [] for k in ("S1", "S2", "S3", "S4", "S5")}
    for rule in res:
        pos = 0; entry = stop = target = None; eday = None
        for i in range(11, len(C) - 1):
            # manage open position on bar i
            if pos != 0:
                ex = None
                if (pos > 0 and L[i] <= stop) or (pos < 0 and H[i] >= stop): ex = stop if ((pos > 0 and O[i] > stop) or (pos < 0 and O[i] < stop)) else O[i]
                elif target is not None and ((pos > 0 and H[i] >= target) or (pos < 0 and L[i] <= target)): ex = target
                elif DY[i] != eday or not OK[i]: ex = C[i] if OK[i] is False and DY[i] == eday else O[i]
                elif DR[i] != pos and rule in ("S1", "S2", "S3"): ex = C[i]
                if ex is not None:
                    res[rule].append((pd.Timestamp(d.index[i]), mult * (pos * (ex - entry) - 2 * cost - 1e-4 * entry))); pos = 0
                else:
                    stop = max(stop, ST[i]) if pos > 0 else min(stop, ST[i])  # trail on the line
            if pos != 0 or not OK[i]: continue
            flip_up, flip_dn = DR[i] > 0 and DR[i-1] < 0, DR[i] < 0 and DR[i-1] > 0
            sig = 0
            if rule in ("S1", "S2"): sig = 1 if flip_up and C[i] > VW[i] else (-1 if flip_dn and C[i] < VW[i] else 0)
            elif rule == "S3": sig = 1 if flip_up else (-1 if flip_dn else 0)
            else:
                same_day = DY[i] == DY[i-1]
                if same_day and DR[i] > 0 and C[i] > VW[i] and C[i-1] <= VW[i-1]: sig = 1
                elif same_day and DR[i] < 0 and C[i] < VW[i] and C[i-1] >= VW[i-1]: sig = -1
            if sig and DY[i+1] == DY[i] and OK[i+1]:
                pos = sig; entry = O[i+1]; stop = ST[i]; eday = DY[i]; risk = abs(entry - stop)
                if (pos > 0 and stop >= entry) or (pos < 0 and stop <= entry): pos = 0; continue
                target = entry + pos * (2.0 if rule == "S2" else 1.5) * risk if rule in ("S2", "S5") else None
    return res
mid = {"OIL": "2025-09-01", "BTC": "2025-11-26"}
rows = []
for mk in ("OIL", "BTC"):
    for k, v in run(mk).items():
        s = pd.Series([p for _, p in v], index=[t for t, _ in v]).sort_index(); e = s.cumsum()
        a, b = s[s.index < pd.Timestamp(mid[mk], tz="UTC")].sum(), s[s.index >= pd.Timestamp(mid[mk], tz="UTC")].sum()
        rows.append(dict(market=mk, rule=k, trades=len(s), win=(s > 0).mean(), first_half=a, second_half=b, total=s.sum(), per_trade=s.mean(),
                         worst_drop=(e - e.cummax()).min(), worst_trade=s.min(), lead=a > 0 and b > 0))
print(pd.DataFrame(rows).round(2).to_string(index=False))
