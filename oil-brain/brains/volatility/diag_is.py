"""IS-only diagnostic (2006-07..2013), not a rule: SPY forward returns by VIX term-structure state.
Used to choose ONE final pre-registered rule (study 3). Post-2013 data is not looked at here."""
import numpy as np, pandas as pd
from common import load, vload
vix, v3m = load("^VIX"), vload("VIX3M"); spy = load("SPY")
R = (vix / v3m).dropna().loc[:"2013-12-31"]
f = {h: (spy.shift(-h) / spy - 1).reindex(R.index) for h in (5, 21, 63)}
back = R > 1
exit_ = (R < 1) & (R.shift(1) >= 1)       # day backwardation resolves
ex_win = exit_.astype(float).replace(0, np.nan).ffill(limit=62).fillna(0) > 0
for lab, m in [("contango", ~back), ("backwardation", back), ("63d after exit", ex_win), ("other contango", ~back & ~ex_win)]:
    print(f"{lab:16s} days {int(m.sum()):5d} " + " ".join(f"fwd{h}d {f[h][m].mean()*100:6.2f}%" for h in f),
          " daily ann. Sharpe next day:", round(float(spy.pct_change().shift(-1).reindex(R.index)[m].mean()/spy.pct_change().shift(-1).reindex(R.index)[m].std()*np.sqrt(252)),2))
print("exits in IS:", int(exit_.sum()))
