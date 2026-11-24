"""Extra Yahoo data for the macro brain (saved in brains/macro/data)."""
import os, yfinance as yf
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
for s in ["^IRX", "^FVX", "HYG", "LQD", "IEF", "SHY", "UUP", "JNK"]:
    for k in range(3):
        try:
            df = yf.Ticker(s).history(period="max", auto_adjust=True)
            if len(df):
                df.index = df.index.tz_localize(None)
                df[["Open","High","Low","Close","Volume"]].to_csv(os.path.join(D, s.replace("^","")+".csv"))
                print(s, len(df), df.index[0].date(), df.index[-1].date()); break
        except Exception as e:
            print(s, "retry", e)
