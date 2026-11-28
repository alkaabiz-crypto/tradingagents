"""Plan A paper ledger, 20,000 AED (~$5,450) size = 2 x minimum lots (frozen 2026-11-28, Hazza's go-ahead).
 US500 10-day low 0.28 lot | BTC NR4 0.02 lot | BTC Williams 0.02 lot | ETH above 50-day 0.2 ETH (ETH lot unverified).
Same rules and Exness costs as verify_planA.py (real lot dollars on fresh Yahoo prices; crypto days rebuilt from hourly bars).
P&L counts from START (positions already open at START are carried in). Kill limit: total <= -$680 (about -2,500 AED).
Writes /mnt/project-files/tradingagents-lab/planA_20k/ledger.json (summary + daily rows + today's orders) and prints it."""
import json, os, sys, time, urllib.request, numpy as np, pandas as pd
START = pd.Timestamp(sys.argv[1] if len(sys.argv) > 1 else "2026-11-28", tz="UTC"); K = 2; AED = 3.6725; KILL = -680
OUTD = "/mnt/project-files/tradingagents-lab/planA_20k"
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
    first_today = h[h.index >= today]; return g, (first_today.open.iloc[0] if len(first_today) else np.nan)
spy = get("SPY"); spy.index = spy.index.normalize(); spy = spy[~spy.index.duplicated(keep="last")]
spy = spy[spy.index < pd.Timestamp.now(tz="UTC").normalize() + pd.Timedelta(hours=21)]  # keep a completed US close only
btc, btc_open_today = cdaily("BTC-USD"); eth, _ = cdaily("ETH-USD")
legs = {}
c = spy.close; sig = (c <= c.rolling(10).min()).values; pos = np.zeros(len(c)); left = 0
for i in range(len(c)):
    pos[i] = 1 if left > 0 else 0; left -= 1 if left > 0 else 0
    if sig[i]: left = 3
p = pd.Series(pos, index=c.index).shift().fillna(0); legs["US500 10-day low"] = (p * c.diff().fillna(0) * 10 * 0.14 - (p.diff() > 0) * 0.40 * 0.14) * K
us_pos_now = int(pos[-1])
def brk(d, kind):
    o, h, l, cl = d.open, d.high, d.low, d.close; rg = h - l
    if kind == "nr4": U, D = h.shift(), l.shift(); ok = (rg <= rg.rolling(4).min()).shift().fillna(False)
    else: U, D = o + 0.5 * rg.shift(), o - 0.5 * rg.shift(); ok = pd.Series(True, index=d.index)
    up, dn = (h >= U) & ok, (l <= D) & ok; eL, eS = np.maximum(U, o), np.minimum(D, o); q = 0.01 * K
    pnl = np.where(up & dn, -(U - D) * q, np.where(up, (cl - eL) * q, np.where(dn, (eS - cl) * q, 0.0)))
    return pd.Series(pnl, index=d.index).fillna(0) - (up | dn) * (6.4 * q + 2e-4 * cl * q)
legs["BTC NR4"] = brk(btc, "nr4"); legs["BTC Williams"] = brk(btc, "w")
e = eth.close; st_ = (e > e.rolling(50).mean()).astype(float); pe = st_.shift().fillna(0)
legs["ETH above 50-day"] = (pe * e.diff().fillna(0) * 0.1 - (pe.diff().abs() > 0) * 5e-4 / 2 * e * 0.1) * K
P = pd.DataFrame(legs).sort_index().fillna(0); P = P[P.index >= START]; tot = P.sum(axis=1); eq = tot.cumsum()
rows = [dict(day=str(d.date()), **{k: round(v, 2) for k, v in r.items()}, total=round(float(tot[d]), 2), running=round(float(eq[d]), 2)) for d, r in P.iterrows()]
mo = tot.groupby(tot.index.strftime("%Y-%m")).sum()
# today's orders
rg = btc.high - btc.low; nr4_today = bool(rg.iloc[-1] <= rg.iloc[-4:].min())
orders = dict(utc_day=str(pd.Timestamp.now(tz="UTC").date()),
              btc_nr4=(dict(buy_stop=round(btc.high.iloc[-1], 2), sell_stop=round(btc.low.iloc[-1], 2), lots=0.02) if nr4_today else "no setup"),
              btc_williams=(dict(buy_stop=round(btc_open_today + 0.5 * rg.iloc[-1], 2), sell_stop=round(btc_open_today - 0.5 * rg.iloc[-1], 2), lots=0.02) if not np.isnan(btc_open_today) else "after 00:00 UTC open"),
              eth=("long 0.2 ETH" if st_.iloc[-1] else "flat (below 50-day)"), us500=("long 0.28 lot" if us_pos_now else "flat"))
total = float(eq.iloc[-1]) if len(eq) else 0.0; dd = float((eq - eq.cummax()).min()) if len(eq) else 0.0
summary = dict(name="Plan A (20k AED)", start=str(START.date()), updated_utc=pd.Timestamp.now(tz="UTC").strftime("%Y-%m-%d %H:%M"), total_usd=round(total, 2), total_aed=round(total * AED),
               worst_drop_usd=round(dd, 2), losing_months=int((mo < 0).sum()), months=int(len(mo)), days=len(rows), kill_usd=KILL, status="STOP" if total <= KILL else "trading allowed", orders=orders)
os.makedirs(OUTD, exist_ok=True); json.dump(dict(summary=summary, rows=rows), open(f"{OUTD}/ledger.json", "w"), indent=1)
print(json.dumps(dict(summary=summary, rows=rows)))
