"""Download free daily data from Yahoo for the oil brain. Saves CSVs in oil-brain/data/."""
import os, yfinance as yf
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
SYMS = ["CL=F","BZ=F","HO=F","RB=F","NG=F","USO","USL","BNO","XLE","XOP","SPY","QQQ","IWM","^OVX","^VIX","DX-Y.NYB","^TNX","GLD","TLT","UNG","UNL","UGA","SLV","CPER","DBA","CORN","WEAT","SOYB","DBC","DBB","PALL","PPLT"]
for s in SYMS:
    for k in range(3):
        try:
            df = yf.Ticker(s).history(period="max", auto_adjust=True)
            if len(df):
                df.index = df.index.tz_localize(None)
                df[["Open","High","Low","Close","Volume"]].to_csv(os.path.join(D, s.replace("^","").replace("=","_")+".csv"))
                print(s, len(df), df.index[0].date(), df.index[-1].date()); break
        except Exception as e:
            print(s, "retry", e)
