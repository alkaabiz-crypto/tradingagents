"""Batch 52 (pre-registered 2026-11-28): (a) JP225 NR4 straddle on CME Nikkei futures bars (NKD=F, ~23h session, closer to
the Exness CFD) as a robustness check; (b) overnight drift (close -> next open, with and without the 200-day filter) on
DE30, JP225, STOXX50, FR40, HK50 (only US was tested before); (c) gold turn of month only above the 200-day (generic
trend filter, to cut the -$520 drop); (d) correlation of JP225 NR4 and ETH ID/NR4 with Plan A legs and the pool."""
import numpy as np, pandas as pd
from pool import *
out = []
d = D("NKD=F"); d = d[d.High > d.Low]; rg = d.High - d.Low
for n in (4, 5, 7):
    ok = (rg <= rg.rolling(n).min()).shift().fillna(False).astype(bool)
    st = stats(straddle(d, d.High.shift(), d.Low.shift(), ok, 3), 1000); out.append(("NKD=F NR%d" % n, st))
for mk, t, bp in (("DE30", "^GDAXI", 2), ("JP225", "^N225", 3), ("STOXX50", "^STOXX50E", 4), ("FR40", "^FCHI", 3), ("HK50", "^HSI", 5)):
    x = D(t); on = (x.Open.shift(-1) / x.Close - 1 - bp / 1e4).shift().fillna(0)
    out.append((f"{mk} overnight", stats(on, 1000)))
    f2 = (x.Close > x.Close.rolling(200).mean()).shift().fillna(False)
    out.append((f"{mk} overnight >200d", stats(on.where(f2, 0), 1000)))
g = D("GLD"); m = pd.Series(g.index.to_period("M"), index=g.index); tdom = m.groupby(m).cumcount() + 1; last = m != m.shift(-1)
tom = (last | (tdom <= 3)).shift(-1).fillna(False)
up = g.Close > g.Close.rolling(200).mean()
out.append(("Gold TOM", stats(pos_ret(g, tom.astype(float).values, 1.5), 3640)))
out.append(("Gold TOM >200d", stats(pos_ret(g, (tom & up).astype(float).values, 1.5), 3640)))
for k, st in out: print(f"{k:22s}", {a: st[a] for a in ("2007-13", "2014-19", "2020-23", "2024-now", "t_post14", "usd_pre_yr", "usd_24_yr", "drop14", "trades_yr")})
n = D("^N225"); n = n[n.High > n.Low]; rg = n.High - n.Low; ok = (rg <= rg.rolling(4).min()).shift().fillna(False).astype(bool)
jp = straddle(n, n.High.shift(), n.Low.shift(), ok, 3) * 1000
A = planA(); P = pool(); P["JP225 NR4"] = jp
df = pd.DataFrame({**A, **P}).loc["2018":].fillna(0)
print(df.corr()[["JP225 NR4", "ETH ID/NR4"]].round(2).to_string())
