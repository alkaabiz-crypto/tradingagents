"""Independent re-check of Plan A (2026-11-28), written from scratch, fresh Yahoo prices, REAL lot dollars (price x lot, not scaled).
 10-day low US500: SPY close <= lowest close of 10 days -> long 3 sessions, close to close; US500 = SPY x 10, 0.14 lot ($0.14/pt); spread 0.40 pt per trade.
 BTC NR4: day range smallest of last 4 -> next UTC day buy-stop at its high, sell-stop at its low, other side = stop, out at the close;
          both touched = full-range loss. 0.01 lot, spread $6.40/coin -> $0.064 per trade, + 2 bp slippage.
 BTC Williams: buy-stop open + 0.5 x prior range, sell-stop open - 0.5 x prior range, same handling.
 ETH above 50-day: long 0.1 ETH while the daily close is above its 50-day average; 5 bp round trip.
Crypto daily bars rebuilt from Yahoo hourly where available (from Nov 2024); Yahoo daily before that."""
import json, urllib.request, time, numpy as np, pandas as pd
def get(s, iv="1d", p1=1609459200):
    u = f"https://query1.finance.yahoo.com/v8/finance/chart/{s}?interval={iv}&period1={p1}&period2={int(time.time())}"
    for k in range(4):
        try:
            r = json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=60))["chart"]["result"][0]; break
        except Exception as e: time.sleep(5 * (k + 1))
    q = r["indicators"]["quote"][0]
    d = pd.DataFrame({k: q[k] for k in ("open", "high", "low", "close")}, index=pd.to_datetime(r["timestamp"], unit="s", utc=True)).dropna()
    return d
def cdaily(s):
    d = get(s); d.index = d.index.normalize(); d = d[~d.index.duplicated(keep="last")]
    h = get(s, "60m", int(time.time()) - 729 * 86400); g = h.groupby(h.index.normalize()).agg(open=("open", "first"), high=("high", "max"), low=("low", "min"), close=("close", "last"), n=("close", "size"))
    g = g[g.n >= 20].drop(columns="n"); d = pd.concat([d[d.index < g.index[0]], g]); today = pd.Timestamp.now(tz="UTC").normalize(); return d[d.index < today]
spy = get("SPY"); spy.index = spy.index.normalize(); spy = spy[spy.index < pd.Timestamp.now(tz="UTC").normalize()]
btc, eth = cdaily("BTC-USD"), cdaily("ETH-USD")
legs = {}
c = spy.close; sig = (c <= c.rolling(10).min()).values; pos = np.zeros(len(c)); left = 0
for i in range(len(c)):
    pos[i] = 1 if left > 0 else 0; left -= 1 if left > 0 else 0
    if sig[i]: left = 3
p = pd.Series(pos, index=c.index).shift().fillna(0); legs["10-day low US500"] = p * c.diff().fillna(0) * 10 * 0.14 - (p.diff() > 0) * 0.40 * 0.14
def brk(d, kind):
    o, h, l, cl = d.open, d.high, d.low, d.close; rg = h - l
    if kind == "nr4": U, D = h.shift(), l.shift(); ok = (rg <= rg.rolling(4).min()).shift().fillna(False)
    else: U, D = o + 0.5 * rg.shift(), o - 0.5 * rg.shift(); ok = pd.Series(True, index=d.index)
    up, dn = (h >= U) & ok, (l <= D) & ok; eL, eS = np.maximum(U, o), np.minimum(D, o); q = 0.01
    pnl = np.where(up & dn, -(U - D) * q, np.where(up, (cl - eL) * q, np.where(dn, (eS - cl) * q, 0.0)))
    cost = (up | dn) * (6.4 * q + 2e-4 * cl * q); side = np.where(up & dn, 9, np.where(up, 1, np.where(dn, -1, 0)))
    return pd.Series(pnl, index=d.index).fillna(0) - cost, pd.Series(side, index=d.index)
legs["BTC NR4"], s_nr4 = brk(btc, "nr4"); legs["BTC Williams"], s_w = brk(btc, "w")
e = eth.close; pe = (e > e.rolling(50).mean()).astype(float).shift().fillna(0); legs["ETH above 50-day"] = pe * e.diff().fillna(0) * 0.1 - (pe.diff().abs() > 0) * 5e-4 / 2 * e * 0.1
P = pd.DataFrame({k: v for k, v in legs.items()}).loc["2024":].fillna(0); tot = P.sum(axis=1)
print("data ends:", spy.index[-1].date(), btc.index[-1].date(), eth.index[-1].date())
for y, g in P.groupby(P.index.year):
    t = g.sum(axis=1); e_ = t.cumsum(); print(f"{y}: total ${t.sum():+.0f} ({t.sum() / 30:+.1f}% of $3,000)  legs " + ", ".join(f"{k} {v:+.0f}" for k, v in g.sum().items()) + f"  worst drop in year {(e_ - e_.cummax()).min():.0f}")
yrs = (P.index[-1] - pd.Timestamp("2024-01-01", tz="UTC")).days / 365.25; eq = tot.cumsum()
print(f"since 2024: ${tot.sum():+.0f} over {yrs:.2f} years = ${tot.sum() / yrs:+.0f}/yr = {tot.sum() / yrs / 30:.1f}%/yr; worst drop ${(eq - eq.cummax()).min():.0f}; losing months {(tot.groupby(tot.index.to_period('M')).sum() < 0).sum()} of {tot.index.to_period('M').nunique()}")
a, b = s_nr4.loc["2024":], s_w.loc["2024":]; both = (a != 0) & (b != 0)
print(f"BTC overlap: NR4 trades {int((a != 0).sum())}, Williams trades {int((b != 0).sum())}, both on the same day {int(both.sum())}; same direction on those days {int((both & (a == b)).sum())}")
print("corr of daily $ NR4 vs Williams:", round(legs["BTC NR4"].loc["2024":].corr(legs["BTC Williams"].loc["2024":]), 2), "| max BTC lots open at once: 0.02")
