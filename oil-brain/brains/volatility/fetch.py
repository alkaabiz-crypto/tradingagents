"""Fetch extra Yahoo vol indices for the volatility brain into brains/volatility/data/."""
import os, yfinance as yf
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
for s in ["^VIX3M", "^VIX9D", "^VVIX", "^VIX6M"]:
    for k in range(3):
        try:
            df = yf.Ticker(s).history(period="max", auto_adjust=True)
            if len(df):
                df.index = df.index.tz_localize(None)
                df[["Open","High","Low","Close"]].to_csv(os.path.join(D, s.replace("^","") + ".csv"))
                print(s, len(df), df.index[0].date(), df.index[-1].date()); break
        except Exception as e:
            print(s, "retry", e)
