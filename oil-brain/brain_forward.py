"""Forward score of oil brain v2 (registered 2026-11-24, before any forward data).
After each US close: logs the composite and the next-day USO return it earns, then scores
B3 (position = composite, rebalanced each Wednesday close) from 2026-11-25 on. 5 bp per turnover.
Pass bar (fixed): at least 13 weeks forward, net > 0 and beating buy-and-hold USO over the same days.
python3 oil-brain/brain_forward.py
"""
import os, numpy as np, pandas as pd
import brain_v2 as B
START = "2026-11-25"
HERE = os.path.dirname(os.path.abspath(__file__))
f = B.features(); v = B.votes(f)
r = f.uso.pct_change()
pos = v.composite.where(f.index.day_of_week == 2).ffill().fillna(0)
turn = pos.diff().abs().fillna(0)
pl = (pos.shift(1) * r - turn.shift(1) * 5e-4)
log = pd.DataFrame({"composite": v.composite.round(3), "position": pos.round(3), "uso_ret": r.round(5), "brain_pl": pl.round(5)})
fw = log[log.index >= START]
fw.to_csv(os.path.join(HERE, "brain_forward.csv"))
net = (1 + fw.brain_pl.fillna(0)).prod() - 1 if len(fw) else 0.0
bh = (1 + fw.uso_ret.fillna(0)).prod() - 1 if len(fw) else 0.0
print(f"Brain forward since {START}: {len(fw)} days, brain {net:+.2%} vs USO {bh:+.2%}. "
      f"Today composite {v.composite.iloc[-1]:+.2f}, held position {pos.iloc[-1]:+.2f}.")
