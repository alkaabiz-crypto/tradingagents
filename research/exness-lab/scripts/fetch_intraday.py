"""Download Yahoo chart intraday bars (1h 730d, 5m 60d) incl. pre/post market to CSV (NY time)."""
import json, sys, time, urllib.request, pandas as pd
out = sys.argv[1]
def get(sym, iv, rng):
    u = f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?interval={iv}&range={rng}&includePrePost=true"
    r = json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=60))["chart"]["result"][0]
    q = r["indicators"]["quote"][0]
    d = pd.DataFrame({k.capitalize(): q[k] for k in ("open", "high", "low", "close", "volume")},
                     index=pd.to_datetime(r["timestamp"], unit="s", utc=True).tz_convert("America/New_York"))
    return d.dropna(subset=["Open"])
for s in ["NQ=F", "ES=F", "GC=F", "QQQ", "SPY", "GLD", "BTC-USD"]:
    for iv, rng in (("1h", "730d"), ("5m", "60d")):
        try:
            d = get(s, iv, rng); d.to_csv(f"{out}/{s.replace('=','_')}_{iv}.csv"); print(s, iv, len(d), d.index[0], d.index[-1])
        except Exception as e: print(s, iv, "ERR", e)
        time.sleep(0.5)
