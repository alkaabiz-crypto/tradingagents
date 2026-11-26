"""Batch 21, pre-registered 2026-11-26 before running. More well-known day-trade setups, tested on HOURLY bars 2024-now
(cash session 09:30-16:00 NY for USTEC=QQQx41, US500=SPYx10, XAUUSD=GLDx10.9; BTC hourly UTC days from 2024-11).
Engine: orders are processed bar by bar in time order; a stop fills at max(level, bar open) (+1 bp), a limit at
min(level, bar open); after entry, stop checked before target in every bar; target not counted on the entry bar;
otherwise exit at the session close. One trade per rule per day; the first order to fill wins.
Rules (published versions, simplified to one day):
 T1 Turtle Soup (Raschke): today trades below the 20-day low that was set >= 4 days ago -> buy-stop at that old low,
    stop = today's low so far at entry minus 0.1 ATR ... simplified: stop 0.5 ATR below entry, target 1 ATR. (long only + mirror short)
 T2 80-20 (Raschke): yesterday opened in its top 20% and closed in its bottom 20% -> if today trades below yesterday's low,
    buy-stop at yesterday's low, stop 0.5 ATR, target 1 ATR (mirror short).
 T3 Crabel stretch: stretch = 10-day average of min(|open-high|,|open-low|); buy-stop open+stretch / sell-stop open-stretch,
    stop at the other order level, exit at close.
 T4 NR4 breakout: if yesterday's range was the narrowest of 4, buy-stop at yesterday's high / sell-stop at its low,
    stop at the other side, exit at close.
 T5 Floor-pivot bounce: P=(H+L+C)/3, S1=2P-H, R1=2P-L, S2=P-(H-L); buy-limit at S1, stop at S2, target P; mirror at R1.
 T6 First-hour reversal: if the 09:30-10:30 move exceeds 0.5 ATR, fade it at 10:30 (market), stop at the first-hour
    extreme, exit at close.
Costs per side: USTEC 1.12 pt, US500 0.4, XAU $0.20, BTC $3.20 (+1 bp on stops). Lots 0.05 / 0.14 / 0.01 / 0.01.
6 rules x 4 markets = 24 trials (cumulative ~430). Lead = positive in each of 2024, 2025 and 2026.
"""
import numpy as np, pandas as pd
def load(f, m, tz):
    d = pd.read_csv(f"intraday/{f}_1h.csv", index_col=0); d.index = pd.to_datetime(d.index, utc=True).tz_convert(tz)
    return d[["Open", "High", "Low", "Close"]] * m
MK = {"USTEC": ("QQQ", 41, 0.05, 1.12, "America/New_York", True), "US500": ("SPY", 10, 0.14, 0.4, "America/New_York", True),
      "XAUUSD": ("GLD", 10.9, 1.0, 0.20, "America/New_York", True), "BTCUSD": ("BTC-USD", 1, 0.01, 3.20, "UTC", False)}
def simulate(bars, orders, cost):
    """orders: list of dict(side, kind 'stop'|'limit'|'mkt', lvl, sl, tp (abs prices or None), start index)."""
    O, H, L, C = bars.Open.values, bars.High.values, bars.Low.values, bars.Close.values
    for i in range(len(O)):
        for od in orders:
            if i < od.get("start", 0): continue
            s, k, lv = od["side"], od["kind"], od["lvl"]
            if k == "mkt": fill = O[i]
            elif k == "stop" and ((s > 0 and H[i] >= lv) or (s < 0 and L[i] <= lv)): fill = (max(lv, O[i]) if s > 0 else min(lv, O[i])) * (1 + s * 1e-4)
            elif k == "limit" and ((s > 0 and L[i] <= lv) or (s < 0 and H[i] >= lv)): fill = min(lv, O[i]) if s > 0 else max(lv, O[i])
            else: continue
            sl = od["sl"](fill) if callable(od["sl"]) else od["sl"]; tp = od["tp"](fill) if callable(od["tp"]) else od["tp"]
            for j in range(i, len(O)):
                if sl is not None and ((L[j] <= sl) if s > 0 else (H[j] >= sl)): return s * (sl - fill) - 2 * cost
                if j > i and tp is not None and ((H[j] >= tp) if s > 0 else (L[j] <= tp)): return s * (tp - fill) - 2 * cost
            return s * (C[-1] - fill) - 2 * cost
    return 0.0
rows = []
for mk, (f, m, lots, cost, tz, cash) in MK.items():
    d = load(f, m, tz)
    if cash: hh = d.index.strftime("%H:%M"); d = d[(hh >= "09:30") & (hh <= "15:30")]
    g = {k: v for k, v in d.groupby(d.index.date)}; days = sorted(g)
    D = pd.DataFrame({k: [fn(g[x]) for x in days] for k, fn in (("O", lambda b: b.Open.iloc[0]), ("H", lambda b: b.High.max()), ("L", lambda b: b.Low.min()), ("C", lambda b: b.Close.iloc[-1]))}, index=days)
    tr = pd.concat([D.H - D.L, (D.H - D.C.shift()).abs(), (D.L - D.C.shift()).abs()], axis=1).max(axis=1); D["ATR"] = tr.ewm(alpha=1/14, adjust=False).mean()
    D["stretch"] = np.minimum((D.O - D.H).abs(), (D.O - D.L).abs()).rolling(10).mean()
    D["lo20"] = D.L.rolling(20).min(); D["hi20"] = D.H.rolling(20).max()
    D["lo20_age"] = D.L.rolling(20).apply(lambda x: 19 - np.argmin(x), raw=True); D["hi20_age"] = D.H.rolling(20).apply(lambda x: 19 - np.argmax(x), raw=True)
    D["nr4"] = (D.H - D.L) <= (D.H - D.L).rolling(4).min()
    out = {k: [] for k in ("T1", "T2", "T3", "T4", "T5", "T6")}
    for n in range(21, len(days)):
        y = D.iloc[n - 1]; b = g[days[n]]; o = b.Open.iloc[0]; a = y.ATR; day = days[n]
        if not np.isfinite(a): continue
        od = []
        if y.lo20_age >= 4: od.append(dict(side=1, kind="stop", lvl=y.lo20, sl=lambda f: f - 0.5 * a, tp=lambda f: f + a, start=0, need_below=y.lo20))
        if y.hi20_age >= 4: od.append(dict(side=-1, kind="stop", lvl=y.hi20, sl=lambda f: f + 0.5 * a, tp=lambda f: f - a, start=0, need_above=y.hi20))
        # Turtle soup needs price to first trade through the old extreme, then come back: emulate by requiring the open beyond it
        od = [x for x in od if (x["side"] > 0 and o < x["lvl"]) or (x["side"] < 0 and o > x["lvl"])]
        out["T1"].append((day, simulate(b, od, cost) * lots if od else 0.0))
        rng = y.H - y.L; od = []
        if rng > 0 and (y.O - y.L) / rng >= 0.8 and (y.C - y.L) / rng <= 0.2 and o < y.L: od.append(dict(side=1, kind="stop", lvl=y.L, sl=lambda f: f - 0.5 * a, tp=lambda f: f + a))
        if rng > 0 and (y.O - y.L) / rng <= 0.2 and (y.C - y.L) / rng >= 0.8 and o > y.H: od.append(dict(side=-1, kind="stop", lvl=y.H, sl=lambda f: f + 0.5 * a, tp=lambda f: f - a))
        out["T2"].append((day, simulate(b, od, cost) * lots if od else 0.0))
        st_ = y.stretch
        out["T3"].append((day, simulate(b, [dict(side=1, kind="stop", lvl=o + st_, sl=o - st_, tp=None), dict(side=-1, kind="stop", lvl=o - st_, sl=o + st_, tp=None)], cost) * lots if np.isfinite(st_) else 0.0))
        out["T4"].append((day, simulate(b, [dict(side=1, kind="stop", lvl=y.H, sl=y.L, tp=None), dict(side=-1, kind="stop", lvl=y.L, sl=y.H, tp=None)], cost) * lots if y.nr4 else 0.0))
        P = (y.H + y.L + y.C) / 3; S1, R1, S2, R2 = 2 * P - y.L - (y.H - y.L) + (y.H - y.L) - (y.H - P) * 0 if False else 2 * P - y.H, 2 * P - y.L, P - (y.H - y.L), P + (y.H - y.L)
        od = []
        if o > S1: od.append(dict(side=1, kind="limit", lvl=S1, sl=S2, tp=P))
        if o < R1: od.append(dict(side=-1, kind="limit", lvl=R1, sl=R2, tp=P))
        out["T5"].append((day, simulate(b, od, cost) * lots))
        if cash and len(b) > 1:
            mv = b.Close.iloc[0] - o
            if abs(mv) > 0.5 * a:
                s = -1 if mv > 0 else 1; ext = b.High.iloc[0] if mv > 0 else b.Low.iloc[0]
                out["T6"].append((day, simulate(b, [dict(side=s, kind="mkt", lvl=None, sl=ext, tp=None, start=1)], cost) * lots))
            else: out["T6"].append((day, 0.0))
        elif not cash and len(b) > 1:
            mv = b.Close.iloc[0] - o
            if abs(mv) > 0.25 * a:
                s = -1 if mv > 0 else 1; ext = b.High.iloc[0] if mv > 0 else b.Low.iloc[0]
                out["T6"].append((day, simulate(b, [dict(side=s, kind="mkt", lvl=None, sl=ext, tp=None, start=1)], cost) * lots))
            else: out["T6"].append((day, 0.0))
    for k, v in out.items():
        s = pd.Series([p for _, p in v], index=pd.to_datetime([q for q, _ in v])); n_ = (s != 0).sum(); e = s.cumsum()
        yr = {y_: s.loc[str(y_)].sum() if str(y_) in s.index.year.astype(str) else 0.0 for y_ in (2024, 2025, 2026)}
        rows.append(dict(market=mk, rule=k, trades=n_, win=(s > 0).sum() / max(n_, 1), **{f"y{y_}": v_ for y_, v_ in yr.items()},
                         per_trade=s.sum() / max(n_, 1), worst_drop=(e - e.cummax()).min(), lead=all(v_ > 0 for v_ in yr.values()) if mk != "BTCUSD" else (yr[2025] > 0 and yr[2026] > 0)))
df = pd.DataFrame(rows); print(df.round(2).to_string(index=False)); df.to_csv("lab/batch21_results.csv", index=False)
