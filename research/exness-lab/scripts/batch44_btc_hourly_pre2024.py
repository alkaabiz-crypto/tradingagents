"""Batch 44 (2026-11-28): the Batch 43 hourly BTC rules, unchanged, on Bitstamp 1-minute data rebuilt to hourly bars
(github.com/ff137/bitstamp-btcusd-minute-data, 2016-06 to 2024-11). $ = % move x today's 0.01-lot exposure ($600), Exness costs.
ETH and gold hourly history before 2024 could not be reached from this machine (Binance, Kraken, Bitstamp API, Dukascopy, HistData blocked)."""
import numpy as np, pandas as pd
src = open("lab/batch43b_neighbours.py").read().split("def show")[0]
src = src.replace('"ETH": ("ETH-USD_60m", "ETH-USD", 0.1, 5.0)}', '"ETH": ("ETH-USD_60m", "ETH-USD", 0.1, 5.0), "BTCH": ("BTC-USD_hist_60m", "BTC-USD", 0.01, 1.1)}')
src = src.replace("T.append(side * (ex - ent) * units - ent * units * (bp + 1) / 1e4)\n        return", "T.append((d_, side * (ex - ent) * (600 / ent) - 600 * (bp + 1) / 1e4))\n        return")
src = src.replace("T.append(side * (ex - ent) * units - ent * units * (bp + 1) / 1e4); i = j + 1", "T.append((h.index[i], side * (ex - ent) * (600 / ent) - 600 * (bp + 1) / 1e4)); i = j + 1")
src = src.replace("return np.array(T)", "return pd.Series([p for _, p in T], index=pd.to_datetime([t for t, _ in T], utc=True))")
exec(src)
for rule, mode, lab, p in (("R2", "B", "BTC hourly Bollinger (paper rule)", {}), ("R4", "L", "BTC London breakout, long only", {}), ("R4", "B", "BTC London breakout, both ways", {}),
                           ("R1", "L", "BTC hourly RSI(2) dip-buy", {}), ("R3", "B", "BTC hourly EMA trend", {})):
    T = run("BTCH", rule, mode, **p); T = T.loc["2017":"2023"]; e = T.cumsum(); y = T.groupby(T.index.year).sum()
    print(f"{lab}: years {dict((k, int(v)) for k, v in y.items())}  total {T.sum():+.0f}  worst drop {(e - e.cummax()).min():.0f}  trades/wk {len(T) / (7 * 52.18):.1f}")
