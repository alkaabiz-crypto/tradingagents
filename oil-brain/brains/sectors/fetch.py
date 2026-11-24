"""Download sector ETFs from Yahoo into brains/sectors/data/."""
import os, yfinance as yf
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
SYMS = ["XLB","XLE","XLF","XLI","XLK","XLP","XLU","XLV","XLY","XLRE","XLC","SPY","XOP","OIH","JETS","IYT","USO"]
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
