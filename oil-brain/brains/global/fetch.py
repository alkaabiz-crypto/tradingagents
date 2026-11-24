"""Download country ETFs (and benchmarks) from Yahoo into brains/global/data/ (auto-adjusted OHLCV)."""
import os, yfinance as yf
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
SYMS = ["EWJ","EWG","EWU","EWQ","EWC","EWA","EWZ","EWW","EWH","EWS","EWT","EWY","FXI","INDA","EZA",
        "EWP","EWI","EWL","EWN","EWD","NORW","EWK","EWO","EWM","EFA","ACWX","EEM","SPY","USO"]
for s in SYMS:
    for k in range(3):
        try:
            df = yf.Ticker(s).history(period="max", auto_adjust=True)
            if len(df):
                df.index = df.index.tz_localize(None)
                df[["Open","High","Low","Close","Volume"]].to_csv(os.path.join(D, s+".csv"))
                print(s, len(df), df.index[0].date(), df.index[-1].date()); break
        except Exception as e:
            print(s, "retry", e)
