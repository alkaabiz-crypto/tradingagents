"""Batch 45b: BTC NR4 and Williams with a tighter stop, simulated on hourly paths (daily bars cannot judge stops inside the day).
Hourly bars: Bitstamp 2016-06..2024-11 (github ff137) + Yahoo from 2024-11-29. Levels from the UTC daily bars built from the same hourly
data. First bar that touches a level decides the side; a bar touching both levels, or the entry bar touching the stop, counts as the
worse case. Stop = entry -/+ f x (buy level - sell level), f = 1 (the normal rule, as a check), 0.5, 0.33. Out at the last hour.
$ = % x $600 (0.01 BTC today), cost 1.1 bp + 2 bp slippage per trade."""
import numpy as np, pandas as pd
a = pd.read_csv("intraday2/BTC-USD_hist_60m.csv", index_col=0, parse_dates=True); b = pd.read_csv("intraday2/BTC-USD_60m.csv", index_col=0, parse_dates=True)
a.index = pd.to_datetime(a.index, utc=True); b.index = pd.to_datetime(b.index, utc=True); h = pd.concat([a[a.index < b.index[0]], b]).sort_index()
h = h[h.index < pd.Timestamp("2026-11-28", tz="UTC")]
d = h.groupby(h.index.normalize()).agg(open=("open", "first"), high=("high", "max"), low=("low", "min"), close=("close", "last"), n=("close", "size")); d = d[d.n >= 20]
rg = d.high - d.low; days = {k: g for k, g in h.groupby(h.index.normalize())}
def sim(kind, f):
    out = {}
    nr = (rg <= rg.rolling(4).min())
    for i in range(5, len(d)):
        day = d.index[i]; prev = d.iloc[i - 1]
        if kind == "nr4":
            if not nr.iloc[i - 1]: continue
            U, D = prev.high, prev.low
        else: U, D = d.open.iloc[i] + 0.5 * rg.iloc[i - 1], d.open.iloc[i] - 0.5 * rg.iloc[i - 1]
        W = U - D; g = days.get(day)
        if g is None: continue
        side = 0; pnl = None
        for _, bar in g.iterrows():
            if side == 0:
                hu, hd = bar.high >= U, bar.low <= D
                if hu and hd: pnl = -(min(f, 1) * W) / U * 2 if f < 1 else -W / U; break   # both in one hour: worst case
                if hu: side, ent = 1, max(U, bar.open); stop = ent - f * W
                elif hd: side, ent = -1, min(D, bar.open); stop = ent + f * W
                else: continue
                if (side == 1 and bar.low <= stop) or (side == -1 and bar.high >= stop): pnl = -f * W / ent; break
            else:
                if (side == 1 and bar.low <= stop) or (side == -1 and bar.high >= stop): pnl = -f * W / ent; break
                if f >= 1 and ((side == 1 and bar.low <= D) or (side == -1 and bar.high >= U)): pnl = -W / ent; break
        if side == 0 and pnl is None: continue
        if pnl is None: pnl = side * (g.close.iloc[-1] - ent) / ent
        out[day] = pnl * 600 - 600 * 3.1e-4
    return pd.Series(out)
for f in (1.0, 0.5, 0.33):
    t = sim("nr4", f) .add(sim("w", f), fill_value=0)
    def st(u, a_, z):
        u = u.loc[a_:z]; e = u.cumsum(); m = u.groupby(u.index.to_period("M")).sum(); yrs = len(m) / 12
        return u.sum() / yrs, (e - e.cummax()).min(), (m < 0).sum(), len(m)
    p, q = st(t, "2017", "2023"), st(t, "2024", "2026")
    print(f"stop f={f}: BTC legs 2017-23 ${p[0]:+.0f}/yr drop {p[1]:.0f} losing months {p[2]}/{p[3]} | 2024+ ${q[0]:+.0f}/yr drop {q[1]:.0f} losing months {q[2]}/{q[3]}")
    print("   years:", ", ".join(f"{y} {v:+.0f}" for y, v in t.loc["2017":].groupby(t.loc["2017":].index.year).sum().items()))
