"""Study 1: crypto time-series momentum (pre-registered 2026-11-24, before running).

Mechanism: Liu & Tsyvinski (2021, RFS) find past 1-4 week BTC returns predict the next 1-4 weeks
(investor attention / slow diffusion); Liu, Tsyvinski & Wu (2022, JF) find a crypto momentum factor.
Parameters come from the papers (1-week and 4-week lookbacks), not tuned.

Splits (stated): engine.evaluate as-is (OOS 2014-2019, HOLDOUT 2020+, IS empty) AND this brain's
crypto splits IS 2014-09..2018, OOS 2019-2021, HOLDOUT 2022+. Cost 10 bp/side, stress 25 bp.
Positions at close t (Yahoo daily bar closes 00:00 UTC), earn close t -> t+1. 7-day data.

Rules (4 of 15):
  R1 btc_tsmom28: long BTC if 28-day trailing return > 0 else flat.
  R2 btc_tsmom7 : long BTC if 7-day trailing return > 0 else flat.
  R3 eth_tsmom28: long ETH if 28-day trailing return > 0 else flat (bench ETH buy-and-hold).
  R4 btc_tsmom28_ls: +1 if 28d return > 0 else -1 (long/short BTC).
Expectation: long/flat rules cut drawdown a lot but probably do not beat BTC buy-and-hold Sharpe
after 2018 (buy-and-hold Sharpe ~1). Long/short likely fails: shorting a strongly up-drifting asset.
"""
from common import *

btc, eth = ret("BTC-USD"), ret("ETH-USD")
cb, ce = px("BTC-USD"), px("ETH-USD")
E, C = [], []
for name, pos, r in [
    ("R1 btc_tsmom28", (cb.pct_change(28) > 0).astype(float), btc),
    ("R2 btc_tsmom7", (cb.pct_change(7) > 0).astype(float), btc),
    ("R3 eth_tsmom28", (ce.pct_change(28) > 0).astype(float), eth),
    ("R4 btc_tsmom28_ls", np.sign(cb.pct_change(28)).fillna(0), btc),
]:
    e, c = both(name, pos, r)
    E.append(e); C.append(c)
show(E, C)
pd.DataFrame(E).merge(pd.DataFrame(C), on="rule").to_csv(os.path.join(HERE, "study1_results.csv"), index=False)
