"""Study 13 (pre-registered 2026-11-24 ~16:00 UTC, before running): turning-point brain.
WARNING, stated before running: the pattern (rallies start when funds have given up; crashes from crowded
longs in backwardation) was found in history.py on the SAME 2008-2026 data, so this backtest is biased in
its favour. Only its forward results (brain_forward-style, from 2026-11-25) can count as evidence.
Inputs lagged to publication (CFTC Friday; prices at the close). USO, 5 bp per turnover. Daily decisions.
 T1 long when funds' net-long 3-year percentile < 25%, else flat.
 T2 long when percentile < 25% AND USO closes above its 20-day average (the turn has started);
    stay long until the percentile rises above 50% or USO closes below its 20-day average.
 T3 short when percentile > 70% AND backwardation (USO-USL 63d > 0) AND USO closes below its 20-day
    average; cover when the percentile falls below 50% or USO closes above its 20-day average.
 T4 T2 + T3 together (long bottoms, short tops).
Gates: engine.py unchanged; plus the tournament bar t > 4.19 for a winner.
"""
import numpy as np, pandas as pd
import brain_v2 as B
from engine import evaluate, table
f = B.features(); uso = f.uso; r = uso.pct_change()
pct = f.mm_pct3y; ma20 = uso.rolling(20).mean(); above = uso > ma20
def stateful(enter, exit_):
    pos = np.zeros(len(f)); on = False
    for i, (e, x) in enumerate(zip(enter.fillna(False).values, exit_.fillna(False).values)):
        if not on and e: on = True
        elif on and x: on = False
        pos[i] = 1.0 if on else 0.0
    return pd.Series(pos, index=f.index)
t1 = (pct < 0.25).astype(float)
t2 = stateful((pct < 0.25) & above, (pct > 0.5) | ~above)
t3 = -stateful((pct > 0.7) & (f.curve63 > 0) & ~above, (pct < 0.5) | above)
rows = [evaluate("T1 long when funds gave up (<25%)", t1, r, start="2008-06-01"),
        evaluate("T2 long: funds gave up + price turns up", t2, r, start="2008-06-01"),
        evaluate("T3 short: crowded + backwardation + price turns down", t3, r, start="2008-06-01"),
        evaluate("T4 T2 + T3", t2 + t3, r, start="2008-06-01")]
print(table(rows))
for name, p in [("T2", t2), ("T4", t2 + t3)]:
    x = (p.shift(1) * r - p.diff().abs().shift(1).fillna(0) * 5e-4).loc["2008-06":]
    trades = int((p.diff().abs() > 0).sum() / 2)
    ent = p.diff().fillna(0); starts = p.index[(ent != 0) & (p != 0)]
    tr = []
    for s in starts:
        seg = p.loc[s:]; end = seg.index[(seg != p.loc[s])]
        e = end[0] if len(end) else p.index[-1]
        tr.append(p.loc[s] * (uso.loc[e] / uso.loc[s] - 1))
    tr = pd.Series(tr)
    print(f"\n{name}: {trades} trades, win rate {(tr>0).mean():.0%}, avg trade {tr.mean():+.1%}, "
          f"time in market {(p!=0).mean():.0%}")
    print(f"{name} by year %:", (x.groupby(x.index.year).sum() * 100).round(1).to_dict())
print("\nToday: funds percentile %.0f%%, USO %.2f vs 20d avg %.2f -> T2 %s, T3 %s" %
      (pct.iloc[-1]*100, uso.iloc[-1], ma20.iloc[-1], "LONG" if t2.iloc[-1] else "flat", "SHORT" if t3.iloc[-1] else "flat"))
