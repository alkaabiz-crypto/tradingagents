"""Batch 43b: neighbour check for the Batch 43 passes. R1: RSI(2) entry 5/10/15 x exit 40/50/60. R2: band 1.5/2/2.5 x lookback 15/20/30.
R3: EMA pairs 10/30, 20/50, 30/100, 50/200. R4 (crypto): range bar 06/07/08 UTC x exit 20/23 UTC. Same costs/sizes as Batch 43.
Also: gold buy-and-hold 1 oz over the same span for comparison, and a random-entry baseline for gold R3 (same trade count and lengths)."""
import numpy as np, pandas as pd
def daily(t): d = pd.read_csv(f"data/{t}.csv", parse_dates=["Date"], index_col="Date")["Close"].dropna(); return (d > d.rolling(50).mean())
MK = {"US500": ("SPY_60m", "SPY", 1.4, 1.6), "Gold": ("GC_F_60m", "GLD", 1.0, 1.5), "BTC": ("BTC-USD_60m", "BTC-USD", 0.01, 1.1), "ETH": ("ETH-USD_60m", "ETH-USD", 0.1, 5.0)}
def rsi(c, n):
    d = c.diff(); u = d.clip(lower=0).ewm(alpha=1/n, adjust=False).mean(); v = (-d.clip(upper=0)).ewm(alpha=1/n, adjust=False).mean(); return 100 - 100 / (1 + u / v)
def load(mk):
    f, dt, units, bp = MK[mk]; h = pd.read_csv(f"intraday2/{f}.csv", index_col=0, parse_dates=True); h.index = pd.to_datetime(h.index, utc=True)
    up = daily(dt); up.index = pd.to_datetime(up.index).tz_localize("UTC"); day = h.index.normalize()
    tr_ = up.reindex(up.index.union(day.unique())).ffill().shift().reindex(day).values
    trend = np.array([0 if pd.isna(x) else (1 if x else -1) for x in tr_]); return h, trend, units, bp
def run(mk, rule, mode, **p):
    h, trend, units, bp = load(mk); o, hi, lo, c = (h[k].values for k in ("open", "high", "low", "close")); N = len(c)
    tr = pd.concat([h.high - h.low, (h.high - h.close.shift()).abs(), (h.low - h.close.shift()).abs()], axis=1).max(axis=1); atr = tr.ewm(alpha=1/14, adjust=False).mean().values
    r2 = rsi(h.close, 2).values; lb = p.get("lb", 20); k_ = p.get("k", 2); mid = h.close.rolling(lb).mean().values; sd = h.close.rolling(lb).std().values
    f_, s_ = p.get("ema", (20, 50)); ef, es = h.close.ewm(span=f_, adjust=False).mean().values, h.close.ewm(span=s_, adjust=False).mean().values
    ent_t, ex_t = p.get("ent", 10), p.get("ex", 50); T = []; i = 210
    if rule == "R4":
        df = pd.DataFrame({"o": o, "h": hi, "l": lo, "c": c, "tr": trend}, index=h.index); df["d"] = df.index.normalize()
        for d_, g in df.groupby("d"):
            g = g[(g.index.hour >= p.get("bar", 7)) & (g.index.hour <= p.get("end", 23))]
            if len(g) < 3: continue
            side = 1 if g.tr.iloc[0] == 1 else (-1 if g.tr.iloc[0] == -1 and mode == "B" else 0)
            if not side: continue
            H, Lw = g.h.iloc[0], g.l.iloc[0]; ent = None; ex = None
            for _, b in g.iloc[1:].iterrows():
                if ent is None:
                    if side == 1 and b.h >= H: ent, stop = max(H, b.o), Lw
                    elif side == -1 and b.l <= Lw: ent, stop = min(Lw, b.o), H
                    else: continue
                if (side == 1 and b.l <= stop) or (side == -1 and b.h >= stop): ex = stop; break
            if ent is None: continue
            if ex is None: ex = g.c.iloc[-1]
            T.append(side * (ex - ent) * units - ent * units * (bp + 1) / 1e4)
        return np.array(T)
    while i < N - 1:
        t0 = trend[i]; side = 0
        if rule == "R1": side = 1 if (r2[i] < ent_t and t0 == 1) else (-1 if (r2[i] > 100 - ent_t and t0 == -1 and mode == "B") else 0)
        elif rule == "R2": side = 1 if (c[i] < mid[i] - k_ * sd[i] and t0 == 1) else (-1 if (c[i] > mid[i] + k_ * sd[i] and t0 == -1 and mode == "B") else 0)
        else: side = 1 if (ef[i] > es[i] and ef[i-1] <= es[i-1] and t0 == 1) else (-1 if (ef[i] < es[i] and ef[i-1] >= es[i-1] and t0 == -1 and mode == "B") else 0)
        if not side: i += 1; continue
        j = i + 1; ent = o[j]; stop = ent - side * 2 * atr[i]; ex = None
        while j < N:
            if rule != "R3" and ((side == 1 and lo[j] <= stop) or (side == -1 and hi[j] >= stop)): ex = stop; break
            if (rule == "R1" and ((side == 1 and r2[j] > ex_t) or (side == -1 and r2[j] < 100 - ex_t) or j - i >= 10)) or \
               (rule == "R2" and ((side == 1 and c[j] >= mid[j]) or (side == -1 and c[j] <= mid[j]) or j - i >= 20)) or \
               (rule == "R3" and ((side == 1 and ef[j] < es[j]) or (side == -1 and ef[j] > es[j]))): ex = c[j]; break
            j += 1
        if ex is None: break
        T.append(side * (ex - ent) * units - ent * units * (bp + 1) / 1e4); i = j + 1
    return np.array(T)
def show(lab, T, yrs): print(f"  {lab:28s} trades {len(T):4d}  $/yr {T.sum()/yrs:+7.0f}  1st half {T[:len(T)//2].sum():+7.0f}  2nd half {T[len(T)//2:].sum():+7.0f}")
for mk, rule, mode, grid in (("BTC", "R1", "L", [dict(ent=e, ex=x) for e in (5, 10, 15) for x in (40, 50, 60)]),
                             ("BTC", "R2", "B", [dict(k=k, lb=l) for k in (1.5, 2, 2.5) for l in (15, 20, 30)]),
                             ("BTC", "R4", "L", [dict(bar=b, end=e) for b in (6, 7, 8) for e in (20, 23)]),
                             ("ETH", "R4", "B", [dict(bar=b, end=e) for b in (6, 7, 8) for e in (20, 23)]),
                             ("ETH", "R3", "B", [dict(ema=e) for e in ((10, 30), (20, 50), (30, 100), (50, 200))]),
                             ("Gold", "R2", "L", [dict(k=k, lb=l) for k in (1.5, 2, 2.5) for l in (15, 20, 30)]),
                             ("Gold", "R3", "L", [dict(ema=e) for e in ((10, 30), (20, 50), (30, 100), (50, 200))]),
                             ("US500", "R2", "B", [dict(k=k, lb=l) for k in (1.5, 2, 2.5) for l in (15, 20, 30)])):
    h, *_ = load(mk); yrs = (h.index[-1] - h.index[0]).days / 365.25; print(f"== {mk} {rule} {mode} ==")
    pos = 0
    for g in grid:
        T = run(mk, rule, mode, **g); show(str(g), T, yrs); pos += T.sum() > 0 and T[:len(T)//2].sum() > 0 and T[len(T)//2:].sum() > 0
    print(f"  neighbours positive in both halves: {pos}/{len(grid)}")
h, *_ = load("Gold"); g = h.close; print("gold 1 oz buy and hold over the span: $", round(g.iloc[-1] - g.iloc[0]), "per year", round((g.iloc[-1] - g.iloc[0]) / ((h.index[-1] - h.index[0]).days / 365.25)), "drop", round(((g - g.iloc[0]) - (g - g.iloc[0]).cummax()).min()))
