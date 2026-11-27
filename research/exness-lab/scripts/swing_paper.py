"""Paper ledger for the Batch 30-35 passes (frozen 2026-11-27). Rules exactly as backtested, entered at the close.
Index rules use ETF proxies (USTEC = QQQ x 41, US500 = SPY x 10, US30 = DIA x 100) and enter at the US close (~15:55 NY);
crypto rules use UTC daily bars rebuilt from hourly. Lots: USTEC 0.05, US500 0.14, US30 0.1 (unverified), BTC 0.01, ETH 0.1 (unverified).
Cost per round trip: USTEC 1.4 bp, US500 1.6 bp, US30 1.3 bp, BTC $6.40, ETH 5 bp, charged when a position opens.
Prints JSON: rows (one per strategy per day it holds a position or signals) from START, plus each strategy's action at the last close."""
import json, sys, os, urllib.request, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from yahoo_daily import crypto_daily
START = sys.argv[1] if len(sys.argv) > 1 else "2026-11-27"
def get(s, rng="2y"):
    u = f"https://query1.finance.yahoo.com/v8/finance/chart/{s}?interval=1d&range={rng}"
    r = json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=60))["chart"]["result"][0]; q = r["indicators"]["quote"][0]
    d = pd.DataFrame({k: q[k] for k in ("open", "high", "low", "close")}, index=pd.to_datetime(r["timestamp"], unit="s", utc=True).date).dropna()
    return d[~d.index.duplicated(keep="last")]
def rsi(c, n):
    d = c.diff(); u = d.clip(lower=0).ewm(alpha=1/n, adjust=False).mean(); v = (-d.clip(upper=0)).ewm(alpha=1/n, adjust=False).mean(); return 100 - 100 / (1 + u / v)
def hold(sig, n):
    s = np.asarray(sig, bool); out = np.zeros(len(s)); left = 0
    for i in range(len(s)):
        if s[i]: left = n
        out[i] = 1 if left > 0 else 0; left -= 1 if left > 0 else 0
    return out
def r3(c):
    r2 = rsi(c, 2); ent = (r2 < r2.shift()) & (r2.shift() < r2.shift(2)) & (r2.shift(2) < r2.shift(3)) & (r2.shift(2) < 60) & (r2 < 10) & (c > c.rolling(200).mean())
    pos, out = 0, []
    for e, x in zip(ent.values, (r2 > 70).values):
        if pos == 0 and e: pos = 1
        elif pos == 1 and x: pos = 0
        out.append(pos)
    return np.array(out, float)
idx = {"QQQ": get("QQQ"), "SPY": get("SPY"), "DIA": get("DIA")}
MULT = {"QQQ": 41 * 0.05, "SPY": 10 * 0.14, "DIA": 100 * 0.1}; BP = {"QQQ": 1.4, "SPY": 1.6, "DIA": 1.3}; NM = {"QQQ": "USTEC", "SPY": "US500", "DIA": "US30"}
def ibs(d): return ((d.close - d.low) / (d.high - d.low)).values < 0.2
def wr(d): return (-100 * (d.high.rolling(10).max() - d.close) / (d.high.rolling(10).max() - d.low.rolling(10).min())).values < -90
S = [("IBS USTEC", "QQQ", hold(ibs(idx["QQQ"]), 2)), ("IBS US30", "DIA", hold(ibs(idx["DIA"]), 2)), ("IBS US500", "SPY", hold(ibs(idx["SPY"]), 2)),
     ("%R USTEC", "QQQ", hold(wr(idx["QQQ"]), 2)), ("%R US500", "SPY", hold(wr(idx["SPY"]), 2)), ("Connors R3 US500", "SPY", r3(idx["SPY"].close)),
     ("10-day low US500", "SPY", hold((idx["SPY"].close <= idx["SPY"].close.rolling(10).min()).values, 3))]
rows, act = [], {}
def ledger(name, d, pos, usd_per_pt, cost_fn, disp):
    c = d.close; p = pd.Series(pos, index=d.index)  # p[t] = position after close t
    held = p.shift().fillna(0); opened = (p.diff() > 0)
    for i, day in enumerate(d.index):
        if str(day) < START: continue
        pnl = held.iloc[i] * (c.iloc[i] - c.iloc[i - 1]) * usd_per_pt - (cost_fn(c.iloc[i]) if opened.iloc[i] else 0)
        note = ("buy at close" if opened.iloc[i] else ("sell at close" if p.iloc[i] < held.iloc[i] else ("hold" if p.iloc[i] else "")))
        if held.iloc[i] or p.iloc[i]: rows.append(dict(strategy=name, day=str(day), held=bool(held.iloc[i]), close=round(c.iloc[i] * disp, 2), action=note, pnl=round(pnl, 2)))
    act[name] = dict(last_close_day=str(d.index[-1]), in_position=bool(p.iloc[-1]), action=("buy at close" if opened.iloc[-1] else ("sell at close" if p.iloc[-1] < held.iloc[-1] else ("hold" if p.iloc[-1] else "flat"))))
for name, t, pos in S:
    ledger(name, idx[t], pos, MULT[t], lambda px, t=t: BP[t] / 1e4 * px * MULT[t], {"QQQ": 41, "SPY": 10, "DIA": 100}[t])
today = pd.Timestamp.now("UTC").date()
for name, sym, q, rule in (("BTC TRIX trend", "BTC-USD", 0.01, "trix"), ("ETH above 50-day", "ETH-USD", 0.1, "sma")):
    d = crypto_daily(sym, "2y"); d = d[d.index < today]; c = d.close
    if rule == "trix":
        e = c.ewm(span=15, adjust=False).mean().ewm(span=15, adjust=False).mean().ewm(span=15, adjust=False).mean(); tr = e.pct_change(); pos = (tr > tr.ewm(span=9, adjust=False).mean()).astype(float).values
    else: pos = (c > c.rolling(50).mean()).astype(float).values
    ledger(name, d, pos, q, (lambda px: 6.4) if sym == "BTC-USD" else (lambda px: 5e-4 * px * 0.1), 1)
print(json.dumps(dict(rows=rows, actions=act)))
