"""Yahoo adjusted closes for the candidate list (today's ~800 largest SEC filers) + SPY.
Output: data/prices.csv.gz (wide, adjusted close, 2005-06 .. now)."""
import os
import pandas as pd
import yfinance as yf

HERE = os.path.dirname(os.path.abspath(__file__))
c = pd.read_csv(os.path.join(HERE, "data", "candidates.csv"))
tk = [t.replace(".", "-") for t in c.ticker] + ["SPY"]
frames = []
for i in range(0, len(tk), 100):
    d = yf.download(tk[i:i + 100], start="2005-06-01", auto_adjust=True, progress=False, threads=True)
    frames.append(d["Close"])
px = pd.concat(frames, axis=1)
px = px.loc[:, ~px.columns.duplicated()]
px.to_csv(os.path.join(HERE, "data", "prices.csv.gz"), compression="gzip")
print(px.shape, px.notna().sum().describe())
