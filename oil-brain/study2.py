"""Study 2 (2026-11-24): robustness grid for the two near-misses of study 1 (H2 carry, H3b momentum).
Not a search: every neighbour is reported, a real effect must hold on most of them.
Note: chosen AFTER seeing study 1's post-2014 results, so a PASS here is only a candidate
for forward paper testing, never proof."""
import numpy as np, pandas as pd
from engine import load, evaluate, table
uso, usl = load("USO"), load("USL"); r = uso.pct_change()
vol = r.rolling(63).std()*np.sqrt(252)
rows=[]
for lb in [10, 21, 42, 63, 126]:
    sp = (uso.pct_change(lb)-usl.pct_change(lb)).dropna()
    rows.append(evaluate(f"carry L/S lookback {lb}d", np.sign(sp), r, start="2008-07-01", n_placebo=300))
me = uso.index.to_series().groupby(uso.index.to_period("M")).last()
for lb in [10, 21, 42, 63, 126]:
    s = np.sign(uso.pct_change(lb)).loc[me.values]; sc=(0.2/vol).clip(upper=1).loc[me.values]
    rows.append(evaluate(f"TSMOM {lb}d monthly rebal", (s*sc).reindex(uso.index).ffill(), r, start="2008-07-01", n_placebo=300))
for lb in [10, 21, 42]:
    s = np.sign(uso.pct_change(lb)); sc=(0.2/vol).clip(upper=1)
    rows.append(evaluate(f"TSMOM {lb}d weekly rebal", (s*sc).resample("W-FRI").last().reindex(uso.index).ffill(), r, start="2008-07-01", n_placebo=300))
# Combo from the literature (carry + trend, e.g. Koijen et al. 2018; Levine & Pedersen): average of the two 21d signals
sp = np.sign((uso.pct_change(21)-usl.pct_change(21)))
tm = (np.sign(uso.pct_change(21)).loc[me.values]*(0.2/vol).clip(upper=1).loc[me.values]).reindex(uso.index).ffill()
rows.append(evaluate("COMBO carry21 + TSMOM21 (avg)", (sp+tm)/2, r, start="2008-07-01", n_placebo=300))
print(table(rows))
