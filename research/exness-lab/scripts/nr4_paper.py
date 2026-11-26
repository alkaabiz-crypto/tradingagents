"""Daily paper ledger for the BTC NR4 breakout (rule frozen 2026-11-26, Batch 21b/24: no optimised change beat it).
Fetches Yahoo BTC-USD daily bars (UTC days, same as Exness server time GMT+0) and prints, for each day from START:
setup?, buy-stop, sell-stop, which side filled, entry, exit, P&L $ at 0.01 lot after $3.20/side spread + 2 bp slippage.
Both sides hit in one day -> counted as a stop-out on the first side (worst case): loss = range x 0.01 + costs."""
import json, sys, urllib.request, pandas as pd, numpy as np
START = sys.argv[1] if len(sys.argv) > 1 else "2026-11-27"
u = "https://query1.finance.yahoo.com/v8/finance/chart/BTC-USD?interval=1d&range=3mo"
r = json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=60))["chart"]["result"][0]
q = r["indicators"]["quote"][0]
d = pd.DataFrame({k: q[k] for k in ("open", "high", "low", "close")}, index=pd.to_datetime(r["timestamp"], unit="s", utc=True).date).dropna()
d = d[~d.index.duplicated(keep="last")]
today = pd.Timestamp.now("UTC").date()
d = d[d.index < today]  # completed UTC days only
rg = d.high - d.low; nr4 = rg <= rg.rolling(4).min()
days = list(d.index) + [today]; rows = []
for i in range(4, len(days)):
    day = days[i]
    if str(day) < START: continue
    y = d.iloc[i - 1]; setup = bool(nr4.iloc[i - 1]); bs, ss = float(y.high), float(y.low); done = day < today
    row = dict(day=str(day), setup=setup, buy_stop=round(bs, 2) if setup else None, sell_stop=round(ss, 2) if setup else None,
               filled="", entry=None, exit=None, pnl=None, status="closed" if done else "today")
    if not setup: row.update(filled="no setup", pnl=0.0 if done else None)
    elif done:
        t = d.iloc[i]; up, dn = t.high >= bs, t.low <= ss; c = 0.064
        if up and dn: row.update(filled="both (worst case)", entry=round(max(bs, t.open), 2), exit=round(ss, 2), pnl=round(-0.01 * (bs - ss) - c - 0.0002 * 0.01 * bs, 2))
        elif up: e = max(bs, t.open); row.update(filled="long", entry=round(e, 2), exit=round(t.close, 2), pnl=round(0.01 * (t.close - e) - c - 0.0002 * 0.01 * e, 2))
        elif dn: e = min(ss, t.open); row.update(filled="short", entry=round(e, 2), exit=round(t.close, 2), pnl=round(0.01 * (e - t.close) - c - 0.0002 * 0.01 * e, 2))
        else: row.update(filled="no fill", pnl=0.0)
    rows.append(row)
print(json.dumps(rows))
