"""Batch 20, pre-registered 2026-11-26 before running. Day trades with SL/TP on HOURLY bars (Yahoo, 2024-01 -> 2026-11-25).
USTEC = QQQ x 41, US500 = SPY x 10 (cash session 09:30-16:00 NY, hourly bars 09:30..15:30); gold = GLD x 10.9 (~XAUUSD).
Daily range / ATR(14) / 20-day EMA from the cash-session bars. Lots: USTEC 0.05 ($0.05/pt), US500 0.14, XAU 0.01 ($1/$1).
Costs per side: USTEC 1.12 pt (3.5 pt if filled in the 09:30 bar's first touch at the open), US500 0.4 (1.5), XAU $0.20;
stop entries +1 bp slippage. Within an hourly bar: if SL and TP both touched -> SL; on the entry bar only the SL counts.
Rules: A1 Williams long (open + 0.5 x prior range), no stop, out 16:00; A2 = A1 + SL 0.5 ATR, TP 1x; A3 SL 0.5 ATR, TP 2x;
B first-hour ORB (09:30-10:30 range) either side, SL other side, TP 1.5R; C trend-day (open vs 20-day EMA, stop entry at
open +/- 0.25 ATR, SL 0.5 ATR, TP 1x). 5 rules x 3 markets = 15 trials. D (descriptive): USTEC overnight above 200-day
(200-day from the daily CSV) exits at the 08:00 open, 09:00 open (pre-market), 09:30 open and 10:30 open.
"""
import numpy as np, pandas as pd
MK = {"USTEC": ("QQQ", 41, 0.05, 1.12, 3.5), "US500": ("SPY", 10, 0.14, 0.4, 1.5), "XAUUSD": ("GLD", 10.9, 1.0, 0.20, 0.30)}
def load(f, m):
    d = pd.read_csv(f"intraday/{f}_1h.csv", index_col=0); d.index = pd.to_datetime(d.index, utc=True).tz_convert("America/New_York")
    return d[["Open", "High", "Low", "Close"]] * m
res = []; trades_all = {}
for mk, (f, m, lots, c1, c0) in MK.items():
    d = load(f, m); hh = d.index.strftime("%H:%M"); cash = d[(hh >= "09:30") & (hh <= "15:30")]
    days = cash.groupby(cash.index.date)
    D = days.agg(Open=("Open", "first"), High=("High", "max"), Low=("Low", "min"), Close=("Close", "last"))
    tr = pd.concat([D.High - D.Low, (D.High - D.Close.shift()).abs(), (D.Low - D.Close.shift()).abs()], axis=1).max(axis=1)
    D["ATR"] = tr.ewm(alpha=1/14, adjust=False).mean().shift(); D["R"] = (D.High - D.Low).shift(); D["EMA"] = D.Close.ewm(span=20, adjust=False).mean().shift()
    out = {k: [] for k in ("A1", "A2", "A3", "B", "C")}
    for day, bars in days:
        x = D.loc[day]
        if not np.isfinite(x.ATR): continue
        o = bars.Open.iloc[0]; H, L, C, T = bars.High.values, bars.Low.values, bars.Close.values, bars.index.strftime("%H:%M")
        def run(side, lvl, sl_d, tp_d, start=0):
            for i in range(start, len(H)):
                hit = (H[i] >= lvl) if side > 0 else (L[i] <= lvl)
                if not hit: continue
                fill = (max(lvl, bars.Open.iloc[i]) if side > 0 else min(lvl, bars.Open.iloc[i]))
                fill *= (1 + side * 1e-4); cost = (c0 if (i == 0 and fill == o * (1 + side * 1e-4)) else c1) + c1
                sl = fill - side * sl_d if sl_d else None; tp = fill + side * tp_d if tp_d else None
                for j in range(i, len(H)):
                    if sl is not None and ((L[j] <= sl) if side > 0 else (H[j] >= sl)): return side * (sl - fill) - cost
                    if j > i and tp is not None and ((H[j] >= tp) if side > 0 else (L[j] <= tp)): return side * (tp - fill) - cost
                return side * (C[-1] - fill) - cost
            return 0.0
        trig = o + 0.5 * x.R; a = x.ATR
        out["A1"].append((day, run(1, trig, None, None))); out["A2"].append((day, run(1, trig, 0.5 * a, 0.5 * a))); out["A3"].append((day, run(1, trig, 0.5 * a, 1.0 * a)))
        if len(H) > 1:
            rh, rl = H[0], L[0]; risk = rh - rl
            lng, sht = run(1, rh, risk, 1.5 * risk, 1), run(-1, rl, risk, 1.5 * risk, 1)
            out["B"].append((day, lng if lng != 0 else sht))
        if o > x.EMA: out["C"].append((day, run(1, o + 0.25 * a, 0.5 * a, 0.5 * a)))
        else: out["C"].append((day, run(-1, o - 0.25 * a, 0.5 * a, 0.5 * a)))
    for k, v in out.items():
        s = pd.Series([p for _, p in v], index=pd.to_datetime([q for q, _ in v])) * lots
        e = s.cumsum(); n = (s != 0).sum()
        res.append(dict(market=mk, rule=k, trades=n, win=(s > 0).sum() / max(n, 1), y2024=s.loc["2024"].sum(), y2025=s.loc["2025"].sum(),
                        y2026=s.loc["2026"].sum(), per_trade=s.sum() / max(n, 1), worst_drop=(e - e.cummax()).min()))
print(pd.DataFrame(res).round(2).to_string(index=False))
# D overnight exit timing on USTEC
d = load("QQQ", 41); dl = pd.read_csv("data/QQQ.csv", parse_dates=["Date"], index_col="Date").Close
above = (dl > dl.rolling(200).mean()); hh = d.index.strftime("%H:%M"); dates = sorted(set(d.index.date))
cl = d[hh == "15:30"].Close; cl.index = cl.index.date
print("\nD) USTEC overnight hold (0.05 lot, above 200-day), exit-time comparison, 2024-now; cost 1.12 pt buy + exit-time spread")
for ex, sp in (("08:00", 2.0), ("09:00", 1.5), ("09:30", 3.5), ("10:30", 1.12)):
    op = d[hh == ex].Open; op.index = op.index.date; pnl = []
    for i in range(1, len(dates)):
        p, t = dates[i - 1], dates[i]
        if p in cl.index and t in op.index and pd.Timestamp(p) in above.index and above.loc[pd.Timestamp(p)]:
            pnl.append(0.05 * (op.loc[t] - cl.loc[p] - 1.12 - sp))
    s = pd.Series(pnl); e = s.cumsum()
    print(f"- exit {ex} NY (assumed spread {sp} pt): nights {len(s)}, total ${s.sum():.0f}, avg ${s.mean():.2f}/night, worst drop ${(e-e.cummax()).min():.0f}")
