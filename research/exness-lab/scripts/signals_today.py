"""Daily signal sheet for a 10,000 AED (~$2,720) account at Exness minimum lots. Writes
/mnt/project-files/tradingagents-lab/signals/today.json. Run twice a day:
  crypto run  ~00:50 UTC (04:50 UAE): after the 00:00 UTC daily close; crypto stop orders for the new UTC day.
  US run      ~20:40 UTC winter / 19:40 UTC summer (about 15 min before the NY close): index signals that fill at the close,
              computed on the live price as the stand-in for today's close.
Each run keeps the other half from the previous file. Rules are the lab's frozen rules (Plan A first, then candidates).
Backtests are not guarantees: every signal can lose; "AED at risk" is the stop distance, or a 2-ATR guide where the rule has no stop."""
import json, os, sys, time, urllib.request, numpy as np, pandas as pd
from zoneinfo import ZoneInfo
AED = 3.6725; OUT = "/mnt/project-files/tradingagents-lab/signals/today.json"
MODE = sys.argv[1] if len(sys.argv) > 1 else "crypto"
NOW = pd.Timestamp(os.environ["SIG_NOW"], tz="UTC") if os.environ.get("SIG_NOW") else pd.Timestamp.now(tz="UTC"); UAE = ZoneInfo("Asia/Dubai"); NY = ZoneInfo("America/New_York")
def uae(ts): return pd.Timestamp(ts).tz_convert(UAE).strftime("%a %d %b %H:%M UAE")
def get(s, iv="1d", days=400):
    u = f"https://query1.finance.yahoo.com/v8/finance/chart/{s}?interval={iv}&period1={int(time.time()) - days * 86400}&period2={int(time.time())}"
    for k in range(4):
        try: r = json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=60))["chart"]["result"][0]; break
        except Exception: time.sleep(5 * (k + 1))
    q = r["indicators"]["quote"][0]
    return pd.DataFrame({k: q[k] for k in ("open", "high", "low", "close")}, index=pd.to_datetime(r["timestamp"], unit="s", utc=True)).dropna()
def cdaily(s):
    h = get(s, "60m", 200); g = h.groupby(h.index.normalize()).agg(open=("open", "first"), high=("high", "max"), low=("low", "min"), close=("close", "last"), n=("close", "size"))
    today = NOW.normalize(); g = g[(g.index < today) & (g.n >= 20)].drop(columns="n"); ft = h[h.index >= today]
    return g, (ft.open.iloc[0] if len(ft) else g.close.iloc[-1])
def money(usd): return dict(usd=round(float(usd), 2), aed=round(float(usd) * AED))
prev = json.load(open(OUT)) if os.path.exists(OUT) else {}
sig = []
if MODE == "crypto":
    exp_at = NOW.normalize() + pd.Timedelta(days=1)
    def straddle(tag, market, U, D, qty, unit, plan, note):
        sig.append(dict(group=plan, strategy=tag, market=market, action="place BOTH: buy-stop and sell-stop (one-cancels-other)",
                        buy_stop=round(U, 5), sell_stop=round(D, 5), stop_if_long=round(D, 5), stop_if_short=round(U, 5),
                        exit="close at the daily close 00:00 UTC (04:00 UAE) if not stopped", lot=f"{qty} {unit}", at_risk=money((U - D) * qty if unit != "USD" else 0),
                        place=uae(NOW), expires=uae(exp_at), note=note))
    btc, bo = cdaily("BTC-USD"); eth, eo = cdaily("ETH-USD")
    rg = btc.high - btc.low; last = btc.iloc[-1]
    if rg.iloc[-1] <= rg.iloc[-4:].min(): straddle("BTC NR4", "BTCUSD", last.high, last.low, 0.01, "lot (0.01 BTC)", "Plan A", "yesterday was the narrowest range of 4 days")
    straddle("BTC Williams", "BTCUSD", bo + 0.5 * rg.iloc[-1], bo - 0.5 * rg.iloc[-1], 0.01, "lot (0.01 BTC)", "Plan A", "levels = today's 00:00 UTC open +/- half of yesterday's range")
    e = eth.close; s50 = e.rolling(50).mean().iloc[-1]; atr = (eth.high - eth.low).rolling(14).mean().iloc[-1]
    sig.append(dict(group="Plan A", strategy="ETH above 50-day", market="ETHUSD", action=("HOLD/BUY long" if e.iloc[-1] > s50 else "FLAT (close any long)"),
                    entry="market now" if e.iloc[-1] > s50 else None, exit_rule=f"close the long after a daily close below the 50-day average (now {s50:.2f})",
                    stop=None, lot="0.1 ETH", at_risk=money(2 * atr * 0.1) if e.iloc[-1] > s50 else money(0), risk_basis="2 x daily ATR guide (rule has no fixed stop)",
                    place=uae(NOW), expires=uae(exp_at)))
    def setup(d, kind):
        h, l = d.high, d.low; r = h - l; ins = (h < h.shift()) & (l > l.shift()); n4 = r <= r.rolling(4).min(); n7 = r <= r.rolling(7).min()
        return bool({"NR4": n4, "NR7": n7, "inside bar": ins, "ID/NR4": ins & n4}[kind].iloc[-1])
    if setup(eth, "ID/NR4"): straddle("ETH ID/NR4", "ETHUSD", eth.high.iloc[-1], eth.low.iloc[-1], 0.2, "ETH", "Candidate", "inside day that is also NR4")
    for coin, kind in (("ADA", "NR4"), ("XRP", "NR7"), ("XLM", "NR7"), ("DOGE", "inside bar"), ("XRP", "Williams")):
        d, o = cdaily(f"{coin}-USD"); q = round(500 / d.close.iloc[-1], 0); l_ = d.iloc[-1]
        if kind == "Williams": straddle(f"{coin} Williams", f"{coin}USD", o + 0.5 * (l_.high - l_.low), o - 0.5 * (l_.high - l_.low), q, coin, "Candidate", "$500 notional; Exness lot and spread not verified")
        elif setup(d, kind): straddle(f"{coin} {kind}", f"{coin}USD", l_.high, l_.low, q, coin, "Candidate", "$500 notional; Exness lot and spread not verified")
    keep = [s for s in prev.get("signals", []) if s.get("session") == "US close"]
    for s in sig: s["session"] = "crypto day"
    sig = sig + keep
else:
    ny_close = NOW.tz_convert(NY).normalize() + pd.Timedelta(hours=16); place_by = (ny_close - pd.Timedelta(minutes=5)).tz_convert("UTC")
    def live(sym):
        d = get(sym, "1d", 420); d.index = d.index.tz_convert(NY).normalize(); d = d[~d.index.duplicated(keep="last")]; return d
    spy, qqq = live("SPY"), live("QQQ"); todayNY = NOW.tz_convert(NY).normalize()
    if spy.index[-1] != todayNY: sig.append(dict(group="info", session="US close", strategy="US market", action="closed today, no index signals"))
    else:
        c = spy.close; atr = (spy.high - spy.low).rolling(14).mean().iloc[-1] * 10
        if c.iloc[-1] <= c.iloc[-10:].min():
            sig.append(dict(group="Plan A", strategy="US500 10-day low", market="US500", action="BUY at the close", entry=f"market at ~{c.iloc[-1]*10:.1f} (US500)", stop=None,
                            exit_rule="sell at the close 3 trading days later (a new 10-day low restarts the 3 days)", lot="0.14 lot", at_risk=money(2 * atr * 0.14), risk_basis="2 x daily ATR guide (rule has no fixed stop)"))
        d = c.diff(); up = d.clip(lower=0).ewm(alpha=0.5, adjust=False).mean(); dn = (-d.clip(upper=0)).ewm(alpha=0.5, adjust=False).mean(); r2 = 100 - 100 / (1 + up / dn)
        ent = r2.iloc[-1] < r2.iloc[-2] < r2.iloc[-3] < r2.iloc[-4] and r2.iloc[-3] < 60 and r2.iloc[-1] < 10 and c.iloc[-1] > c.iloc[-200:].mean()
        if ent: sig.append(dict(group="Candidate", strategy="Connors R3 US500", market="US500", action="BUY at the close", stop=None, exit_rule="sell at the first close with RSI(2) above 70",
                                lot="0.14 lot", at_risk=money(2 * atr * 0.14), risk_basis="2 x daily ATR guide"))
        q = qqq.close; qatr = (qqq.high - qqq.low).rolling(14).mean().iloc[-1] * 41
        if q.iloc[-1] > q.iloc[-200:].mean():
            sig.append(dict(group="Candidate", strategy="USTEC overnight", market="USTEC", action="BUY at 15:55 New York", stop=None, exit_rule="sell at the next US open (09:30 New York)",
                            lot="0.05 lot", at_risk=money(0.5 * qatr * 0.05), risk_basis="half a daily ATR guide (overnight only)"))
        if NOW.tz_convert(NY).dayofweek == 0 and q.iloc[-1] < q.iloc[-2]:
            sig.append(dict(group="Candidate", strategy="Turnaround Tuesday USTEC", market="USTEC", action="BUY at the close", stop=None, exit_rule="sell at Tuesday's close",
                            lot="0.05 lot", at_risk=money(qatr * 0.05), risk_basis="1 x daily ATR guide"))
        for s in sig: s.update(session="US close", place=f"by {uae(place_by)} (15:55 New York)", expires=uae(ny_close))
        if not sig: sig.append(dict(group="info", session="US close", strategy="US index rules", action="no index signal today"))
    keep = [s for s in prev.get("signals", []) if s.get("session") == "crypto day"]
    sig = keep + sig
sig.sort(key=lambda s: (s.get("group") != "Plan A", s.get("session", "")))
doc = dict(account="10,000 AED (~$2,720), Exness Standard swap-free, minimum lots", updated=uae(NOW), run=MODE,
           warning="Backtested rules, not guaranteed. Any signal can lose. Plan A first; candidates are paper-tested only.",
           signals=sig)
os.makedirs(os.path.dirname(OUT), exist_ok=True); json.dump(doc, open(OUT, "w"), indent=1); print(json.dumps(doc, indent=1))
