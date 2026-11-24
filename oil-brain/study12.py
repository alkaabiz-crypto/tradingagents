"""Study 12 (pre-registered 2026-11-24 15:50 UTC, before running): backtest oil brain v2 (brain_v2.py) on USO.
Decision once a week, at the Wednesday close (after the EIA report), held until the next Wednesday.
Every input is lagged to its public release date (see brain_v2.py). 5 bp per unit of turnover.
Rules:
 B1 brain long/short: position = sign(composite) when |composite| >= 0.25, else flat.
 B2 brain long/flat: long when composite >= 0.25, else flat.
 B3 brain scaled: position = composite (a -1..+1 conviction size).
 New single components (not tested before): C1 stocks, C2 draws, C3 cushing, C4 crowding (each its vote, weekly).
Gates: engine.py unchanged. The brain was designed from the literature, not tuned; but trend and curve were
seen in earlier studies, so the brain is judged at the tournament bar too (t > 4.19) and needs an audit.
"""
import numpy as np, pandas as pd
import brain_v2 as B
from engine import evaluate, table
f = B.features(); v = B.votes(f)
r = f.uso.pct_change()
wed = f.index.day_of_week == 2
def weekly(x):
    return x.where(wed).ffill().fillna(0)
c = v.composite
rows = [evaluate("B1 brain long/short |c|>=0.25", weekly(np.sign(c).where(c.abs() >= 0.25, 0)), r, start="2008-06-01"),
        evaluate("B2 brain long/flat c>=0.25", weekly((c >= 0.25).astype(float)), r, start="2008-06-01"),
        evaluate("B3 brain scaled (composite)", weekly(c), r, start="2008-06-01")]
for k, col in [("C1", "stocks"), ("C2", "draws"), ("C3", "cushing"), ("C4", "crowding")]:
    rows.append(evaluate(f"{k} {col} vote alone", weekly(v[col]), r, start="2008-06-01"))
print(table(rows))
pos = weekly(np.sign(c).where(c.abs() >= 0.25, 0))
x = (pos.shift(1) * r).loc["2014":]
print("\nB1 by year %:", (x.groupby(x.index.year).sum() * 100).round(1).to_dict())
print("B1 time long/short/flat %:", round((pos > 0).mean()*100), round((pos < 0).mean()*100), round((pos == 0).mean()*100))
