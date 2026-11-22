# Connors RSI(2) basket study

Run 2026-11-22 20:14 UTC. Same pass rules (luck >= 95%, Sharpe above holding the same funds in both halves, positive after costs).

| Test | Per year | Worst drop | Sharpe | Benchmark Sharpe | 1st half Sharpe (vs bench) | 2nd half Sharpe (vs bench) | Per year at stress cost | Luck check | Verdict | Avg % invested |
|---|---|---|---|---|---|---|---|---|---|---|
| 1. Stock basket (6) (since 2003-04-14) | +1.7% | -11% | 0.47 | 0.62 | 0.41 vs 0.60 | 0.54 vs 0.65 | +0.5% | 97% | fail | 6% |
| 2. Mixed basket (8, incl. oil stocks XLE) (since 2004-11-18) | +1.5% | -8% | 0.51 | 0.65 | 0.47 vs 0.57 | 0.57 vs 0.76 | +0.4% | 97% | fail | 5% |
| 3. Oil basket (XLE, USO, BNO) (since 2010-06-02) | +0.1% | -17% | 0.05 | 0.29 | -0.10 vs 0.06 | 0.16 vs 0.46 | -0.7% | 52% | fail | 4% |
| 4. Sector basket (9 SPDR sectors) (since 2000-01-03) | +1.2% | -10% | 0.40 | 0.57 | 0.49 vs 0.38 | 0.32 vs 0.80 | +0.1% | 95% | fail | 5% |
