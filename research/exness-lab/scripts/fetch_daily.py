import json, sys, time, urllib.request, urllib.parse, pandas as pd
def get(t):
    u = f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(t)}?period1=0&period2={int(time.time())}&interval=1d&events=div%2Csplit"
    r = json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=60))["chart"]["result"][0]
    q = r["indicators"]["quote"][0]; adj = r["indicators"].get("adjclose", [{}])[0].get("adjclose")
    d = pd.DataFrame({"Open": q["open"], "High": q["high"], "Low": q["low"], "Close": q["close"], "Volume": q["volume"]}, index=pd.to_datetime(r["timestamp"], unit="s").normalize())
    if adj is not None:  # adjust OHLC for dividends/splits
        f = pd.Series(adj, index=d.index) / d.Close
        for k in ("Open", "High", "Low", "Close"): d[k] = d[k] * f
    d.index.name = "Date"; d = d[~d.index.duplicated(keep="last")]
    d.to_csv(f"data/{t}.csv"); return len(d), d.index[0].date(), d.index[-1].date()
for t in sys.argv[1:]:
    try: print(t, *get(t))
    except Exception as e: print(t, "ERR", e)
