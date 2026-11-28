"""Paper ledger for the Batch 43 hourly passes (frozen 2026-11-28). Fresh Yahoo hourly bars each run; the daily trend is the prior UTC
day's close vs its 50-day average, built from the same hourly bars. Prints JSON of trades entered on/after START (closed and open).
 H1 Gold hourly EMA(20)/EMA(50) trend, long only in a daily uptrend, 1 oz (XAUUSD 0.01 lot); exit on the opposite cross.
 H2 BTC hourly EMA(20)/EMA(50) trend, both ways with the daily trend, 0.01 lot; exit on the opposite cross. (Replaced the BTC hourly
    Bollinger rule on 2026-11-28: it lost money on 2017-2023 Bitstamp data, Batch 44.)
 H3 ETH London-open breakout: 07:00 UTC hourly bar range, stop order in the daily-trend direction, stop at the other side, out 23:00 UTC; 0.1 ETH."""
import json, sys, urllib.request, numpy as np, pandas as pd
START = pd.Timestamp(sys.argv[1] if len(sys.argv) > 1 else "2026-11-28", tz="UTC")
def hourly(s):
    u = f"https://query1.finance.yahoo.com/v8/finance/chart/{s}?interval=60m&range=730d"
    r = json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=60))["chart"]["result"][0]; q = r["indicators"]["quote"][0]
    h = pd.DataFrame({k: q[k] for k in ("open", "high", "low", "close")}, index=pd.to_datetime(r["timestamp"], unit="s", utc=True)).dropna()
    return h[h.index < pd.Timestamp.now(tz="UTC").floor("h")]  # drop the still-forming bar
def trend_of(h):
    dc = h.close.groupby(h.index.normalize()).last(); up = (dc > dc.rolling(50).mean()).astype(int) * 2 - 1; up[dc.rolling(50).mean().isna()] = 0
    return up.shift().reindex(h.index.normalize()).fillna(0).values
out = []
def add(name, t_in, side, ent, t_out, ex, pnl, status): out.append(dict(strategy=name, entry_time=str(t_in), side="long" if side == 1 else "short", entry=round(ent, 2),
                                                                        exit_time=str(t_out) if t_out is not None else "", exit=round(ex, 2) if ex is not None else None, pnl=round(pnl, 2) if pnl is not None else None, status=status))
# H1 gold
h = hourly("GC=F"); tr = trend_of(h); c, o = h.close.values, h.open.values; e20, e50 = h.close.ewm(span=20, adjust=False).mean().values, h.close.ewm(span=50, adjust=False).mean().values
i = 60
while i < len(c) - 1:
    if e20[i] > e50[i] and e20[i-1] <= e50[i-1] and tr[i] == 1:
        j = i + 1; ent = o[j]
        while j < len(c) and not e20[j] < e50[j]: j += 1
        if h.index[i + 1] >= START:
            if j < len(c): add("Gold hourly trend", h.index[i + 1], 1, ent, h.index[j], c[j], (c[j] - ent) - ent * 2.5e-4, "closed")
            else: add("Gold hourly trend", h.index[i + 1], 1, ent, None, None, None, f"open, last {c[-1]:.2f}")
        i = j + 1
    else: i += 1
# H2 BTC hourly trend
h = hourly("BTC-USD"); tr = trend_of(h); c, o = h.close.values, h.open.values; e20, e50 = h.close.ewm(span=20, adjust=False).mean().values, h.close.ewm(span=50, adjust=False).mean().values
i = 60
while i < len(c) - 1:
    side = 1 if (e20[i] > e50[i] and e20[i-1] <= e50[i-1] and tr[i] == 1) else (-1 if (e20[i] < e50[i] and e20[i-1] >= e50[i-1] and tr[i] == -1) else 0)
    if not side: i += 1; continue
    j = i + 1; ent = o[j]
    while j < len(c) and not ((side == 1 and e20[j] < e50[j]) or (side == -1 and e20[j] > e50[j])): j += 1
    if h.index[i + 1] >= START:
        if j < len(c): add("BTC hourly trend", h.index[i + 1], side, ent, h.index[j], c[j], side * (c[j] - ent) * 0.01 - ent * 0.01 * 2.1e-4, "closed")
        else: add("BTC hourly trend", h.index[i + 1], side, ent, None, None, None, f"open, last {c[-1]:.2f}")
    i = j + 1
# H3 ETH
h = hourly("ETH-USD"); tr = pd.Series(trend_of(h), index=h.index); df = h.assign(tr=tr)
for d_, g in df.groupby(df.index.normalize()):
    g = g[(g.index.hour >= 7) & (g.index.hour <= 23)]
    if len(g) < 2 or g.index[0].hour != 7 or g.index[0] < START: continue
    side = int(g.tr.iloc[0]);
    if side == 0: continue
    H, Lw = g.high.iloc[0], g.low.iloc[0]; ent = None; ex = None; t_in = None
    for t, b in g.iloc[1:].iterrows():
        if ent is None:
            if side == 1 and b.high >= H: ent, stop, t_in = max(H, b.open), Lw, t
            elif side == -1 and b.low <= Lw: ent, stop, t_in = min(Lw, b.open), H, t
            else: continue
        if (side == 1 and b.low <= stop) or (side == -1 and b.high >= stop): ex, t_out = stop, t; break
    if ent is None: continue
    complete = g.index[-1].hour == 23
    if ex is None and complete: ex, t_out = g.close.iloc[-1], g.index[-1]
    if ex is not None: add("ETH London breakout", t_in, side, ent, t_out, ex, side * (ex - ent) * 0.1 - ent * 0.1 * 6e-4, "closed")
    else: add("ETH London breakout", t_in, side, ent, None, None, None, f"open, stop {stop:.2f}")
print(json.dumps(out))
