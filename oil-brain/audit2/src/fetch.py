import sys, yfinance as yf
out = sys.argv[1]
for t in ["GLD", "IAU", "GC=F", "SLV"]:
    for adj in (False, True):
        df = yf.download(t, start="2004-01-01", auto_adjust=adj, actions=True, progress=False)
        if hasattr(df.columns, "levels"):
            df.columns = [c[0] for c in df.columns]
        name = t.replace("=", "_") + ("_adj" if adj else "_raw")
        df.to_csv(f"{out}/{name}.csv")
        print(name, len(df), df.index[0], df.index[-1])
