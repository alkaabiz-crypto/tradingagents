"""Check that PlanA_EA.mq5's day-by-day logic gives the same trades as the vectorized lab backtest (2024-01-01 .. 2026-11-27).
The mirror walks the bars one day at a time exactly as the EA does (levels from the previous D1 bar, OCO, worst case when
both levels trade, exit at the next daily close; ETH long while close > SMA50; US500 long while a 10-day-low signal
happened today or on one of the 2 previous trading days). Prices: Yahoo daily (BTC/ETH UTC days, SPY close as the
15:55 NY price). Compares trade dates, sides and P&L with the vectorized versions."""
import numpy as np, pandas as pd
from brainlab import D, hold
A, B = "2024-01-01", "2026-11-27"
btc, eth, spy = D("BTC-USD"), D("ETH-USD"), D("SPY")
# ---- vectorized (lab) ----
def vec_brk(d, kind):
    o, h, l, c = d.Open, d.High, d.Low, d.Close; rg = h - l
    if kind == "nr4": U, Dn = h.shift(), l.shift(); ok = (rg <= rg.rolling(4).min()).shift().fillna(False).astype(bool)
    else: U, Dn = o + 0.5 * rg.shift(), o - 0.5 * rg.shift(); ok = pd.Series(True, index=d.index)
    up, dn = (h >= U) & ok, (l <= Dn) & ok
    side = np.where(up & dn, 9, np.where(up, 1, np.where(dn, -1, 0)))
    eL, eS = np.maximum(U, o), np.minimum(Dn, o)
    pnl = np.where(up & dn, -(U - Dn), np.where(up, c - eL, np.where(dn, eS - c, 0.0)))
    return pd.DataFrame({"side": side, "pnl": pnl}, index=d.index).loc[A:B]
vec_eth = pd.Series((eth.Close > eth.Close.rolling(50).mean()).astype(int).values, index=eth.index).loc[A:B]
sig = (spy.Close <= spy.Close.rolling(10).min()).astype(float).values
vec_us = pd.Series(hold(sig, 3).astype(int), index=spy.index).loc[A:B]
# ---- EA mirror (one day at a time) ----
def ea_brk(d, kind):
    out = []; H, L, O, C = d.High.values, d.Low.values, d.Open.values, d.Close.values
    for i in range(4, len(d)):
        r1 = H[i - 1] - L[i - 1]
        if kind == "nr4":
            if any(H[i - k] - L[i - k] < r1 for k in (2, 3, 4)): out.append((d.index[i], 0, 0.0)); continue
            up, dn = H[i - 1], L[i - 1]
        else: up, dn = O[i] + 0.5 * r1, O[i] - 0.5 * r1
        if O[i] >= up: side, entry = 1, O[i]              # EA: market buy when price already above
        elif O[i] <= dn: side, entry = -1, O[i]
        else: side, entry = 0, None
        if side == 0:
            hu, hd = H[i] >= up, L[i] <= dn
            if hu and hd: out.append((d.index[i], 9, -(up - dn))); continue   # both traded: OCO, stopped at the other level
            if hu: side, entry = 1, up
            elif hd: side, entry = -1, dn
            else: out.append((d.index[i], 0, 0.0)); continue
        if side == 1: pnl = (dn - entry) if L[i] <= dn else C[i] - entry
        else: pnl = (entry - up) if H[i] >= up else entry - C[i]
        if (side == 1 and L[i] <= dn) or (side == -1 and H[i] >= up): side_out = 9
        else: side_out = side
        out.append((d.index[i], side_out, pnl))
    return pd.DataFrame(out, columns=["day", "side", "pnl"]).set_index("day").loc[A:B]
def ea_eth(d):
    c = d.Close.values; out = []
    for i in range(50, len(d)): out.append((d.index[i], int(c[i] > c[i - 49:i + 1].mean())))
    return pd.DataFrame(out, columns=["day", "pos"]).set_index("day").pos.loc[A:B]
def ea_us(d):
    px = d.Close.values; out = []
    s = [px[j] <= px[j - 9:j + 1].min() if j >= 9 else False for j in range(len(px))]
    for i in range(12, len(px)): out.append((d.index[i], int(s[i] or s[i - 1] or s[i - 2])))
    return pd.DataFrame(out, columns=["day", "pos"]).set_index("day").pos.loc[A:B]
for nm, v, e in (("BTC NR4", vec_brk(btc, "nr4"), ea_brk(btc, "nr4")), ("BTC Williams", vec_brk(btc, "w"), ea_brk(btc, "w"))):
    j = v.join(e, rsuffix="_ea", how="inner"); traded = (j.side != 0) | (j.side_ea != 0)
    same_side = ((j.side == j.side_ea) | ((j.side == 9) & (j.side_ea == 9))).loc[traded]
    print(f"{nm}: {int(traded.sum())} trade days; same outcome {int(same_side.sum())}; P&L per 1 BTC lab {j.pnl.sum():.0f} vs EA mirror {j.pnl_ea.sum():.0f}; max day diff {np.abs(j.pnl - j.pnl_ea).max():.2f}")
    diff = j[(np.abs(j.pnl - j.pnl_ea) > 1e-6)]
    if len(diff): print("   differing days:", len(diff), diff.head(5).to_dict("index"))
for nm, v, e in (("ETH above 50-day", vec_eth, ea_eth(eth)), ("US500 10-day low", vec_us, ea_us(spy))):
    j = pd.concat([v, e], axis=1, join="inner"); j.columns = ["lab", "ea"]
    print(f"{nm}: {len(j)} days, position identical on {int((j.lab == j.ea).sum())}; entries lab {int((j.lab.diff() == 1).sum())} vs EA {int((j.ea.diff() == 1).sum())}")
