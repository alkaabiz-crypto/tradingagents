import yfinance as yf, pandas as pd
for s in ["BTC-USD","ETH-USD","USO","HYG","LQD","IEF","TLT","SHY"]:
    df = yf.download(s, start="2000-01-01", auto_adjust=False, progress=False, actions=True)
    if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
    df.to_csv(f"data/{s}.csv"); print(s, df.shape, df.index[0], df.index[-1])
