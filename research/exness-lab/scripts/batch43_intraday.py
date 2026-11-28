"""Batch 43, pre-registered 2026-11-28 (Hazza: why not hourly / 15-minute?). Yahoo hourly bars (indices and gold from 2024, crypto from
Nov 2024); 15-minute bars only go back 60 days, too short to test. Pick half = first half of each market's data, check half = second.
Rules on hourly bars, with the daily trend filter (prior daily close vs its 50-day average); mode L = long only in a daily uptrend,
mode B = long in an uptrend and short in a downtrend. Entries at the next bar's open; stops checked on bar high/low (worst case).
 R1 RSI(2) < 10 (> 90 for shorts): exit when RSI(2) crosses 50, after 10 bars, or at a 2 x ATR(14) stop.
 R2 Bollinger(20,2) close outside the band: exit at the middle band, after 20 bars, or at a 2 x ATR stop.
 R3 EMA(20)/EMA(50) cross in the trend direction: exit on the opposite cross.
 R4 Session-open breakout: range of the first hour (indices: first cash-session bar; gold: 13:00 UTC bar; crypto: 07:00 UTC London bar),
    stop order beyond it in the trend direction, stop at the other side, out at the last bar of the session/day.
Costs per round trip: spread + 1 bp slippage (USTEC 1.4 bp, 3 bp for R4 at the open; US500 1.6; gold 1.5; BTC 1.1; ETH 5).
Sizes: USTEC 0.05 lot (2.05 $/QQQ $), US500 0.14 (1.4 $/SPY $), gold 1 oz, BTC 0.01, ETH 0.1.
PASS: positive in both halves, Sharpe > 0.3 in both, still positive at 2x cost."""
import numpy as np, pandas as pd
def daily(t): d = pd.read_csv(f"data/{t}.csv", parse_dates=["Date"], index_col="Date")["Close"].dropna(); return (d > d.rolling(50).mean())
MK = {"USTEC": ("QQQ_60m", "QQQ", 2.05, 1.4, 3.0), "US500": ("SPY_60m", "SPY", 1.4, 1.6, 2.5), "Gold": ("GC_F_60m", "GLD", 1.0, 1.5, 1.5),
      "BTC": ("BTC-USD_60m", "BTC-USD", 0.01, 1.1, 1.1), "ETH": ("ETH-USD_60m", "ETH-USD", 0.1, 5.0, 5.0)}
def rsi(c, n):
    d = c.diff(); u = d.clip(lower=0).ewm(alpha=1/n, adjust=False).mean(); v = (-d.clip(upper=0)).ewm(alpha=1/n, adjust=False).mean(); return 100 - 100 / (1 + u / v)
rows = []; TR = {}
for mk, (f, dt, units, bp, bp_open) in MK.items():
    h = pd.read_csv(f"intraday2/{f}.csv", index_col=0, parse_dates=True); h.index = pd.to_datetime(h.index, utc=True)
    up = daily(dt); up.index = pd.to_datetime(up.index).tz_localize("UTC")
    day = h.index.normalize(); trend = up.reindex(up.index.union(day.unique())).ffill().shift().reindex(day).values  # prior day's daily state
    trend = np.where(pd.isna(trend), 0, np.where(trend.astype(bool) if trend.dtype != object else trend == True, 1, -1))
    o, hi, lo, c = (h[k].values for k in ("open", "high", "low", "close")); N = len(c)
    tr = pd.concat([h.high - h.low, (h.high - h.close.shift()).abs(), (h.low - h.close.shift()).abs()], axis=1).max(axis=1); atr = tr.ewm(alpha=1/14, adjust=False).mean().values
    r2 = rsi(h.close, 2).values; mid = h.close.rolling(20).mean().values; sd = h.close.rolling(20).std().values
    e20, e50 = h.close.ewm(span=20, adjust=False).mean().values, h.close.ewm(span=50, adjust=False).mean().values
    for rule in ("R1", "R2", "R3", "R4"):
        for mode in ("L", "B"):
            trades = []; i = 60
            if rule == "R4":
                dfd = pd.DataFrame({"o": o, "h": hi, "l": lo, "c": c, "tr": trend}, index=h.index); dfd["d"] = dfd.index.normalize()
                for dd_, g in dfd.groupby("d"):
                    if mk in ("BTC", "ETH"): g = g[g.index.hour >= 7]
                    elif mk == "Gold": g = g[(g.index.hour >= 13) & (g.index.hour < 21)]
                    if len(g) < 3: continue
                    t0 = g.tr.iloc[0]; H, Lw = g.h.iloc[0], g.l.iloc[0]; side = 1 if t0 == 1 else (-1 if (t0 == -1 and mode == "B") else 0)
                    if side == 0: continue
                    rest = g.iloc[1:]; ent = None
                    for k in range(len(rest)):
                        b = rest.iloc[k]
                        if ent is None:
                            if side == 1 and b.h >= H: ent = max(H, b.o); stop = Lw
                            elif side == -1 and b.l <= Lw: ent = min(Lw, b.o); stop = H
                            else: continue
                        if (side == 1 and b.l <= stop) or (side == -1 and b.h >= stop): ex = stop; break
                    else:
                        ex = rest.c.iloc[-1] if ent is not None else None
                    if ent is None: continue
                    trades.append((dd_, side * (ex - ent) * units - ent * units * (bp_open + 1) / 1e4))
            else:
                while i < N - 1:
                    t0 = trend[i]; side = 0
                    if rule == "R1":
                        if r2[i] < 10 and t0 == 1: side = 1
                        elif r2[i] > 90 and t0 == -1 and mode == "B": side = -1
                    elif rule == "R2":
                        if c[i] < mid[i] - 2 * sd[i] and t0 == 1: side = 1
                        elif c[i] > mid[i] + 2 * sd[i] and t0 == -1 and mode == "B": side = -1
                    else:
                        if e20[i] > e50[i] and e20[i - 1] <= e50[i - 1] and t0 == 1: side = 1
                        elif e20[i] < e50[i] and e20[i - 1] >= e50[i - 1] and t0 == -1 and mode == "B": side = -1
                    if side == 0: i += 1; continue
                    j = i + 1; ent = o[j]; stop = ent - side * 2 * atr[i]; ex = None
                    while j < N:
                        if rule != "R3" and ((side == 1 and lo[j] <= stop) or (side == -1 and hi[j] >= stop)): ex = stop; break
                        done = (rule == "R1" and ((side == 1 and r2[j] > 50) or (side == -1 and r2[j] < 50) or j - i >= 10)) or \
                               (rule == "R2" and ((side == 1 and c[j] >= mid[j]) or (side == -1 and c[j] <= mid[j]) or j - i >= 20)) or \
                               (rule == "R3" and ((side == 1 and e20[j] < e50[j]) or (side == -1 and e20[j] > e50[j])))
                        if done: ex = c[j]; break
                        j += 1
                    if ex is None: break
                    trades.append((h.index[i], side * (ex - ent) * units - ent * units * (bp + 1) / 1e4)); i = j + 1
            if not trades: continue
            T = pd.Series([p for _, p in trades], index=pd.to_datetime([t for t, _ in trades], utc=True)); TR[(mk, rule, mode)] = T
            mid_t = h.index[0] + (h.index[-1] - h.index[0]) / 2; a, b2 = T[T.index < mid_t], T[T.index >= mid_t]
            cost = pd.Series([0.0] * len(T), index=T.index)
            weeks = (h.index[-1] - h.index[0]).days / 7; e = T.cumsum(); px = c.mean() * units * (bp + 1) / 1e4
            def s_(x): return x.mean() / x.std() * np.sqrt(len(x)) if len(x) > 5 and x.std() > 0 else np.nan
            rows.append(dict(market=mk, rule=rule, mode=mode, trades_wk=len(T) / weeks, pick_half=a.sum(), check_half=b2.sum(), t_pick=s_(a), t_check=s_(b2),
                             at_2x_cost=(T - px).sum(), drop=(e - e.cummax()).min(), per_year=T.sum() / ((h.index[-1] - h.index[0]).days / 365.25), avg_trade=T.mean()))
df = pd.DataFrame(rows); df["PASS"] = (df.pick_half > 0) & (df.check_half > 0) & (df.t_pick > 0.3) & (df.t_check > 0.3) & (df.at_2x_cost > 0)
pd.set_option("display.width", 250); print(df.round(2).to_string(index=False)); df.to_csv("lab/batch43_results.csv", index=False)
import pickle; pickle.dump(TR, open("lab/batch43_trades.pkl", "wb"))
