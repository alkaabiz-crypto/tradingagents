"""Batch 53 (pre-registered 2026-11-28 before running): the crypto rules that work on BTC/ETH, on other coins Exness lists
(LTC, XRP, BCH, ADA, DOGE, LINK, XLM; SOL/DOT lack pre-2020 data and are skipped). Exposure $500 each (min lots unverified),
cost 20 bp round trip (+2 bp slippage on stop entries), 2x cost check. Rules: NR4, ID/NR4, inside bar, NR7 straddles;
Williams 0.5x-range breakout; close > SMA50 long-only; TRIX(15) > signal long-only. Same PASS bar (2,000 shifts, BH)."""
import numpy as np, pandas as pd
from pool import *
rows = []; ser = {}
for coin in ("LTC", "XRP", "BCH", "ADA", "DOGE", "LINK", "XLM"):
    d = D(f"{coin}-USD"); d = d[d.High > d.Low]; P = CB.detect_patterns(d); rg = d.High - d.Low
    U, Dn = d.High.shift(), d.Low.shift(); sh = lambda m: m.shift().fillna(False).astype(bool)
    for nm, ok in (("NR4", sh(P.nr4)), ("ID/NR4", sh(P.inside_bar & P.nr4)), ("inside bar", sh(P.inside_bar)), ("NR7", sh(P.nr7))):
        b = lambda x, d=d, U=U, Dn=Dn, c=20: straddle(d, U, Dn, pd.Series(np.asarray(x, bool), index=d.index), c)
        rows.append((coin, nm, b, ok.values, straddle(d, U, Dn, ok, 40)))
    WU, WD = d.Open + 0.5 * rg.shift(), d.Open - 0.5 * rg.shift()
    allok = np.ones(len(d), bool)
    rows.append((coin, "Williams", lambda x, d=d, WU=WU, WD=WD: straddle(d, WU, WD, pd.Series(np.asarray(x, bool), index=d.index), 20), allok, straddle(d, WU, WD, pd.Series(True, index=d.index), 40)))
    c = d.Close; s50 = (c > c.rolling(50).mean()).astype(float).values
    e = c.ewm(span=15, adjust=False).mean().ewm(span=15, adjust=False).mean().ewm(span=15, adjust=False).mean(); tr = e.pct_change()
    tx = (tr > tr.ewm(span=9, adjust=False).mean()).astype(float).values
    for nm, s in (("above SMA50", s50), ("TRIX", tx)):
        rows.append((coin, nm, lambda x, d=d: pos_ret(d, x, 20), s, pos_ret(d, s, 40)))
out = []
for coin, nm, b, x, r2 in rows:
    r = b(x); st = stats(r, 500); st2 = stats(r2, 500)
    p = shift_p(x, b, n=2000) if (st["pre_sh_ok"] and st["t_post14"] >= 2 and nm != "Williams") else 1.0
    out.append(dict(coin=coin, rule=nm, **{k: st[k] for k in ("2014-19", "2020-23", "2024-now", "pre_sh_ok", "recent_ok", "t_post14", "usd_pre_yr", "usd_24_yr", "drop14", "trades_yr")}, usd_2x=st2["usd_pre_yr"], p=p))
    ser[f"{coin} {nm}"] = r * 500
R = pd.DataFrame(out); R["fdr"] = bh(R.p.values); R["PASS"] = R.pre_sh_ok & R.recent_ok & (R.t_post14 >= 2) & R.fdr & (R.usd_2x > 0)
R.to_csv("batch53_results.csv", index=False); pd.to_pickle(ser, "batch53_series.pkl")
pd.set_option("display.width", 250); print(R.to_string(index=False))
