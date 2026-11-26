"""Can anything help the crypto TREND day trade? (pre-registered 2026-11-26, before any run; the user asked
"can something help this strategy").
Base (from day_ticket_costs.py): BTC-USD, each UTC day: long if yesterday's close > 50-day average, else short;
entry at the open, stop 0.5 x ATR14, out at the close. Costs from costs.py (Exness Standard swap-free: spread only,
+ stop slippage on stop exits).
Variants (each changes ONE thing; 9 tried, all reported):
  V1 long only (no shorts)                 V2 shorts only when also below the 200-day average
  V3 vol sizing: size = min(1, 2% / ATR%)  V4 skip Saturdays and Sundays
  V5 BTC + ETH 50/50 (diversify)           V6 stop 0.75 ATR      V7 stop 0.35 ATR
  V8 trend average 20 days                 V9 trend average 100 days   (V6-V9 are robustness / neighbour checks)
Periods: EARLY 2014-2021, LATE 2022+ (the weak recent years).
"HELPS" (fixed): better return / worst-drop ratio (MAR) than the base in BOTH periods, and Sharpe not lower in
LATE. Reported but not "helps": anything that only wins in one period. With 9 variants, one may help by luck.
Research, not financial advice.   python3 oil-brain/live/btc_trend_improve.py
"""
import os, sys
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); OB = os.path.dirname(HERE)
sys.path.insert(0, HERE); sys.path.insert(0, OB)
from day_ticket_backrun import full_bars, atr
import costs


def daily(sym, look=50, k=0.5, mode="both", size=False, weekend=True):
    d = full_bars(sym); d = d[(d.High > d.Low) & (d.Open > 0)]; a = atr(d); c = d.Close
    sma, s200 = c.rolling(look).mean(), c.rolling(200).mean()
    sig = np.where(c > sma, 1.0, -1.0)
    if mode == "long": sig = np.where(sig > 0, 1.0, 0.0)
    if mode == "short200": sig = np.where((sig < 0) & (c > s200), 0.0, sig)
    f = pd.DataFrame({"O": d.Open.shift(-1), "H": d.High.shift(-1), "L": d.Low.shift(-1), "C": d.Close.shift(-1),
                      "a": a, "s": sig, "ok": s200.notna()}, index=d.index)
    f = f[(f.index >= "2014-01-01") & f[["O", "H", "L", "C", "a"]].notna().all(axis=1) & f.ok]
    s = f.s.values; st = f.O - s * k * f.a
    hit = np.where(s > 0, f.L <= st, np.where(s < 0, f.H >= st, False))
    x = np.where(hit, st, f.C); g = s * (x / f.O - 1)
    cost = np.where(s != 0, costs.round_trip(sym, False) + np.where(hit, costs.STOP_SLIPPAGE_BP / 1e4, 0), 0)
    w = np.minimum(1.0, 0.02 / (f.a / f.O)).values if size else np.ones(len(f))
    r = pd.Series(w * (g - cost), index=f.index + pd.Timedelta(days=1))   # P&L lands on the trade day
    if not weekend: r[r.index.day_of_week >= 5] = 0.0
    return r.dropna()


def stats(r):
    e = (1 + r).cumprod(); dd = (e / e.cummax() - 1).min(); yrs = len(r) / 365
    cagr = e.iloc[-1] ** (1 / yrs) - 1
    return dict(day_pct=r.mean() * 100, year_pct=cagr * 100, worst_drop=dd * 100, MAR=cagr / abs(dd),
                sharpe=r.mean() / r.std() * np.sqrt(365))


def main():
    V = {"BASE": lambda: daily("BTC-USD"), "V1 long only": lambda: daily("BTC-USD", mode="long"),
         "V2 short only <200d": lambda: daily("BTC-USD", mode="short200"),
         "V3 vol sizing": lambda: daily("BTC-USD", size=True), "V4 skip weekends": lambda: daily("BTC-USD", weekend=False),
         "V5 BTC+ETH 50/50": lambda: pd.concat([daily("BTC-USD"), daily("ETH-USD")], axis=1).dropna().mean(axis=1),
         "V6 stop 0.75": lambda: daily("BTC-USD", k=0.75), "V7 stop 0.35": lambda: daily("BTC-USD", k=0.35),
         "V8 trend 20d": lambda: daily("BTC-USD", look=20), "V9 trend 100d": lambda: daily("BTC-USD", look=100)}
    rows = []
    for name, f in V.items():
        r = f()
        for per, m in (("EARLY 2014-21", r.index < "2022-01-01"), ("LATE 2022+", r.index >= "2022-01-01")):
            rows.append(dict(variant=name, period=per, **stats(r[m])))
    df = pd.DataFrame(rows); base = df[df.variant == "BASE"].set_index("period")
    helps = []
    for name in V:
        if name == "BASE": continue
        q = df[df.variant == name].set_index("period")
        ok = all(q.MAR[p] > base.MAR[p] for p in base.index) and q.sharpe["LATE 2022+"] >= base.sharpe["LATE 2022+"]
        helps.append((name, ok))
    df.to_csv(os.path.join(HERE, "btc_trend_improve_results.csv"), index=False)
    pd.set_option("display.width", 200)
    print(df.round(2).to_string(index=False))
    print("\nHELPS (better MAR in both periods, Sharpe not lower in LATE):", [n for n, ok in helps if ok] or "none")


if __name__ == "__main__":
    main()
