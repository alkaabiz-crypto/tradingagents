"""Brains paper ledger (frozen 2026-11-28): the new Batch 47-54 candidates not already on paper.
 Candle-brain crypto breakouts (stop orders at the levels, exit at the 00:00 UTC daily close, the other level is the stop,
 both levels hit = full-range loss): ETH ID/NR4 (0.5 ETH), ADA NR4, XRP NR7, XLM NR7, DOGE inside bar, XRP Williams
 (each $500 notional, coin quantity fixed at the setup day's close; Exness alt lots and spreads still to be verified,
 cost 20 bp round trip + 2 bp slippage; ETH 5 bp). Turnaround Tuesday USTEC 0.05 lot (Monday close below Friday close ->
 buy Monday's close, sell Tuesday's close; QQQ x 41 proxy, 1.12 pt spread). Each strategy stops at -$300.
Writes /mnt/project-files/tradingagents-lab/brains_paper/ledger.json."""
import json, os, sys, time, urllib.request, numpy as np, pandas as pd
START = pd.Timestamp(sys.argv[1] if len(sys.argv) > 1 else "2026-11-29", tz="UTC"); STOP = -300
OUTD = "/mnt/project-files/tradingagents-lab/brains_paper"
def get(s, iv="1d", p1=None):
    p1 = p1 or int(time.time()) - 400 * 86400
    u = f"https://query1.finance.yahoo.com/v8/finance/chart/{s}?interval={iv}&period1={p1}&period2={int(time.time())}"
    for k in range(4):
        try: r = json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=60))["chart"]["result"][0]; break
        except Exception: time.sleep(5 * (k + 1))
    q = r["indicators"]["quote"][0]
    return pd.DataFrame({k: q[k] for k in ("open", "high", "low", "close")}, index=pd.to_datetime(r["timestamp"], unit="s", utc=True)).dropna()
def cdaily(s):
    h = get(s, "60m", int(time.time()) - 200 * 86400)
    g = h.groupby(h.index.normalize()).agg(open=("open", "first"), high=("high", "max"), low=("low", "min"), close=("close", "last"), n=("close", "size"))
    today = pd.Timestamp.now(tz="UTC").normalize(); g = g[(g.index < today) & (g.n >= 20)].drop(columns="n")
    ft = h[h.index >= today]; return g, (ft.open.iloc[0] if len(ft) else np.nan)
def setups(d, kind):
    h, l = d.high, d.low; rg = h - l; inside = (h < h.shift()) & (l > l.shift()); nr4 = rg <= rg.rolling(4).min(); nr7 = rg <= rg.rolling(7).min()
    return {"NR4": nr4, "NR7": nr7, "inside bar": inside, "ID/NR4": inside & nr4}[kind]
def brk(d, kind, qty_fn, bp):
    o, h, l, c = d.open, d.high, d.low, d.close; rg = h - l
    if kind == "Williams": U, D = o + 0.5 * rg.shift(), o - 0.5 * rg.shift(); ok = pd.Series(True, index=d.index)
    else: U, D = h.shift(), l.shift(); ok = setups(d, kind).shift().fillna(False).astype(bool)
    q = qty_fn(c.shift()); up, dn = (h >= U) & ok, (l <= D) & ok; eL, eS = np.maximum(U, o), np.minimum(D, o)
    pnl = np.where(up & dn, -(U - D) * q, np.where(up, (c - eL) * q, np.where(dn, (eS - c) * q, 0.0)))
    return pd.Series(pnl, index=d.index).fillna(0) - (up | dn) * ((bp + 2) / 1e4) * c.shift() * q
RULES = [("ETH ID/NR4 (0.5 ETH)", "ETH-USD", "ID/NR4", lambda p: 0.5, 5), ("ADA NR4 ($500)", "ADA-USD", "NR4", lambda p: 500 / p, 20),
         ("XRP NR7 ($500)", "XRP-USD", "NR7", lambda p: 500 / p, 20), ("XLM NR7 ($500)", "XLM-USD", "NR7", lambda p: 500 / p, 20),
         ("DOGE inside bar ($500)", "DOGE-USD", "inside bar", lambda p: 500 / p, 20), ("XRP Williams ($500)", "XRP-USD", "Williams", lambda p: 500 / p, 20)]
legs, orders, cache = {}, {}, {}
for nm, sym, kind, qf, bp in RULES:
    if sym not in cache: cache[sym] = cdaily(sym)
    d, o_today = cache[sym]; legs[nm] = brk(d, kind, qf, bp)
    last = d.iloc[-1]; q = qf(last.close)
    if kind == "Williams":
        rg = last.high - last.low
        orders[nm] = (dict(buy_stop=round(o_today + 0.5 * rg, 5), sell_stop=round(o_today - 0.5 * rg, 5), qty=round(q, 2)) if not np.isnan(o_today) else "after 00:00 UTC open")
    else:
        orders[nm] = dict(buy_stop=round(last.high, 5), sell_stop=round(last.low, 5), qty=round(q, 2)) if bool(setups(d, kind).iloc[-1]) else "no setup"
qqq = get("QQQ"); qqq.index = qqq.index.normalize(); qqq = qqq[~qqq.index.duplicated(keep="last")]
c = qqq.close; mon = (qqq.index.dayofweek == 0) & (c < c.shift()); p = pd.Series(mon.astype(float), index=c.index).shift().fillna(0)
legs["Turnaround Tuesday USTEC (0.05)"] = p * c.diff().fillna(0) * 41 * 0.05 - p * 1.12 * 0.05
orders["Turnaround Tuesday USTEC (0.05)"] = ("buy 0.05 lot at Monday's close" if pd.Timestamp.now(tz="UTC").dayofweek == 0 else "only on a down Monday")
P = pd.DataFrame(legs).sort_index().fillna(0); P = P[P.index >= START]
eqs = P.cumsum(); status = {k: ("STOP" if len(eqs) and (eqs[k] - eqs[k].cummax()).min() <= STOP else "trading allowed") for k in P.columns}
tot = P.sum(axis=1); eq = tot.cumsum()
rows = [dict(day=str(d.date()), **{k: round(v, 2) for k, v in r.items()}, total=round(float(tot[d]), 2), running=round(float(eq[d]), 2)) for d, r in P.iterrows()]
summary = dict(name="Brains paper (candle-brain crypto + Turnaround Tuesday)", start=str(START.date()), updated_utc=pd.Timestamp.now(tz="UTC").strftime("%Y-%m-%d %H:%M"),
               total_usd=round(float(eq.iloc[-1]) if len(eq) else 0.0, 2), per_strategy={k: round(float(P[k].sum()), 2) for k in P.columns}, status=status, orders=orders)
os.makedirs(OUTD, exist_ok=True); json.dump(dict(summary=summary, rows=rows), open(f"{OUTD}/ledger.json", "w"), indent=1)
print(json.dumps(dict(summary=summary, rows=rows[-5:]), indent=1))
