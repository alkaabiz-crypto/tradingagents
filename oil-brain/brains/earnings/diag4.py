"""Diagnostic for study 4 (not a rule): in-season vs out-of-season SPY mean, Welch t."""
import numpy as np, pandas as pd
from common import prices, events
from study2 import predicted
cl, ret = prices(); days = ret.index
pe = predicted(events(days), days)
c = pd.Series(np.bincount(pe.iP.values, minlength=len(days))[:len(days)], index=days).astype(float)
fwd = sum(c.shift(-k) for k in range(1, 6)).fillna(0)
p = (fwd >= 9).astype(float).shift(1)
s = ret["SPY"]
for a, b in (("2005-06", "2013"), ("2014", "2026")):
    x, q = s.loc[a:b], p.loc[a:b]
    i, o = x[q == 1], x[q == 0]
    t = (i.mean() - o.mean()) / np.sqrt(i.var() / len(i) + o.var() / len(o))
    print(a, b, "in %.1f bp (n %d, vol %.2f%%) out %.1f bp (n %d, vol %.2f%%) Welch t %.2f" % (
        i.mean()*1e4, len(i), i.std()*100, o.mean()*1e4, len(o), o.std()*100, t))
