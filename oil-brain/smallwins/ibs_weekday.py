"""IBS by weekday (pre-registered 2026-11-25, before running). Literature (Pagonidis, via CXO/Quantpedia): the IBS
effect is strongest from Monday into Tuesday. ONE hypothesis: QQQ IBS-dip trades entered on a MONDAY close beat the
trades entered on other days, in BOTH 2000-2013 and 2014-2026, and Monday-only trades have t >= 2 in both.
Same rule as ibs_live.py, 5 bp a side. If it holds, it is a hint for sizing, not a new sleeve (neighbour check first).
Research, not financial advice.
"""
import os, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import smallwins as W

b = W.load("QQQ"); i = W.indicators(b); c = b.Close.values; ibs = i.ibs.values; ok = i.sma200.notna().values; n = len(c)
out = []; k = 0
while k < n - 1:
    if ok[k] and ibs[k] < 0.2:
        j = next((j for j in range(k + 1, min(k + 6, n)) if ibs[j] > 0.5), min(k + 5, n - 1))
        out.append(dict(date=b.index[k], wd=b.index[k].weekday(), r=c[j] / c[k] - 1 - 2 * W.COST)); k = j
    else:
        k += 1
t = pd.DataFrame(out); names = ["Mon", "Tue", "Wed", "Thu", "Fri"]
for lab, m in [("2000-2013", t.date < "2014-01-01"), ("2014-2026", t.date >= "2014-01-01")]:
    x = t[m]; g = x.groupby("wd").r.agg(["count", "mean", "std"])
    g["bp"] = g["mean"] * 1e4; g["t"] = g["mean"] / (g["std"] / np.sqrt(g["count"])); g.index = [names[w] for w in g.index]
    print(lab); print(g[["count", "bp", "t"]].round(2).to_string())
    mon = x[x.wd == 0].r; oth = x[x.wd != 0].r
    print(f"  Monday {mon.mean()*1e4:.1f} bp vs others {oth.mean()*1e4:.1f} bp\n")
