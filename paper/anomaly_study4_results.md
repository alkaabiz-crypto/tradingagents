# Academic anomaly study, batch 4

Run 2026-11-22 18:58 UTC. Same pass rules as batch 1.

| Test | Per year | Worst drop | Sharpe | Benchmark Sharpe | 1st half Sharpe (vs bench) | 2nd half Sharpe (vs bench) | Per year at stress cost | Luck check | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| 24. 200-day average filter (SPY) (SPY since 2000-01-03) | +6.7% | -22% | 0.65 | 0.49 | 0.38 vs 0.23 | 0.88 vs 0.82 | +5.7% | 96% | **PASS** |
| 25. Vol-managed SPY + 200-day filter (SPY since 2000-01-03) | +6.6% | -20% | 0.67 | 0.49 | 0.42 vs 0.23 | 0.89 vs 0.82 | +5.7% | 96% | **PASS** |
| 26. Vol-managed QQQ + 200-day filter (QQQ since 2000-01-03) | +7.5% | -20% | 0.64 | 0.42 | 0.31 vs 0.11 | 0.92 vs 0.90 | +6.6% | 96% | **PASS** |
| 27. Vol-managed small caps (IWM) (IWM since 2000-05-26) | +5.9% | -36% | 0.44 | 0.45 | 0.49 vs 0.42 | 0.38 vs 0.49 | +5.6% | 59% | fail |
| 28. Vol-managed gold (GLD) (GLD since 2004-11-18) | +9.1% | -43% | 0.66 | 0.58 | 0.54 vs 0.49 | 0.79 vs 0.71 | +8.9% | 98% | **PASS** |
| 29. Weekly reversal: buy after a -2% week (SPY) (SPY since 2000-01-03) | +3.3% | -40% | 0.34 | 0.49 | 0.04 vs 0.23 | 0.74 vs 0.82 | +1.5% | 91% | fail |
| 30. BTC + ETH weekly trend, 50/50 (vs 50/50 hold) (crypto since 2017-11-10) | +29.9% | -51% | 0.96 | 0.72 | 1.07 vs 0.95 | 0.84 vs 0.41 | +26.9% | 94% | fail |
