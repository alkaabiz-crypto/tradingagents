"""Study 2b (macro brain), written 2026-11-24 after study 2. NOT a new rule.

Measurement fix for M11: the engine's placebo cannot shift a constant position, so M11's
placebo p = 1.00 is meaningless. Here the engine's own placebo method (500 circular shifts of
the switch path, same seed and shift range, 5 bp, post-2014 Sharpe) is applied to the SPY/IEF
switch path itself. Also: yearly returns of M11 and M5/M10 (credit -> USO), to see whether the
credit edge is a crisis effect like oil momentum (BRAIN.md study 3). No parameter is changed.
"""
import numpy as np, pandas as pd
from common import engine, px, ret, monthly

START = "2007-06-01"
spy, ief, uso = ret("SPY"), ret("IEF"), ret("USO")
idx = spy.loc[START:].dropna().index
spy, ief, uso = spy.reindex(idx), ief.reindex(idx).fillna(0), uso.reindex(idx).fillna(0)
credit = np.log(px("HYG") / px("LQD")).reindex(idx).ffill()
onm = monthly((credit.diff(21) > 0).astype(float), idx).fillna(0)

def sw(on):
    turn = on.diff().abs().fillna(0) * 2
    return on.shift(1).fillna(0) * spy + (1 - on.shift(1).fillna(0)) * ief - turn.shift(1).fillna(0) * 5e-4

r = sw(onm); post = idx >= "2014-01-01"
real = engine.sharpe(r[post])
rng = np.random.default_rng(7); n = len(onm); beats = 0
for _ in range(500):
    k = int(rng.integers(n // 10, n - n // 10))
    if engine.sharpe(sw(pd.Series(np.roll(onm.values, k), index=idx))[post]) < real:
        beats += 1
print(f"M11 post Sharpe {real:.2f}, t {engine.tstat(r[post]):.2f}, proper placebo p {1-beats/500:.3f}")
print(f"M11 time in SPY {onm.mean():.2f}; static mix with same weight post Sharpe "
      f"{engine.sharpe((onm.mean()*spy + (1-onm.mean())*ief)[post]):.2f}")
crisis = ((idx >= "2020-01-15") & (idx <= "2020-06-30")) | ((idx >= "2022-01-01") & (idx <= "2022-12-31"))
print("M11 post Sharpe excluding 2020H1 and 2022:", round(engine.sharpe(r[post & ~crisis]), 2),
      "SPY same window:", round(engine.sharpe(spy[post & ~crisis]), 2))
uso_l = engine.pnl(onm, uso, 5)
yr = pd.DataFrame({"M11 switch": r, "SPY": spy, "M5 credit->USO L/F": uso_l, "USO": uso})
print((yr.groupby(idx.year).apply(lambda d: (1 + d).prod() - 1) * 100).round(1).to_string())
