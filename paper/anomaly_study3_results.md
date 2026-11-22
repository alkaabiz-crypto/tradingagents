# Academic anomaly study, batch 3

Run 2026-11-22 19:07 UTC. Same pass rules as batch 1.

| Test | Per year | Worst drop | Sharpe | Benchmark Sharpe | 1st half Sharpe (vs bench) | 2nd half Sharpe (vs bench) | Per year at stress cost | Luck check | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| 15. Trend rule on 10 other coins (vs hold all 10) (crypto since 2017-11-10) | +20.8% | -39% | 0.83 | 0.97 | 1.00 vs 1.33 | 0.63 vs 0.45 | +18.3% | 62% | fail |
| 16. Vol-managed Nasdaq 100 (QQQ) (QQQ since 2000-01-03) | +9.6% | -43% | 0.66 | 0.42 | 0.36 vs 0.11 | 0.96 vs 0.90 | +9.4% | 97% | **PASS** |
| 17. Vol-managed ex-US stocks (EFA) (EFA since 2001-08-27) | +6.2% | -39% | 0.47 | 0.39 | 0.57 vs 0.37 | 0.37 vs 0.42 | +6.0% | 96% | fail |
| 18. Vol-managed BTC (50% target) (BTC since 2017-11-10) | +19.2% | -73% | 0.60 | 0.70 | 0.58 vs 0.83 | 0.63 vs 0.56 | +18.7% | 25% | fail |
| 19. Weekly trend rule on Nasdaq 100 (QQQ) (QQQ since 2000-01-03) | +3.7% | -44% | 0.33 | 0.42 | 0.02 vs 0.11 | 0.65 vs 0.90 | +2.6% | 53% | fail |
| 20. Pre-holiday effect (SPY) (SPY since 2000-01-03) | -0.0% | -12% | 0.01 | 0.49 | -0.05 vs 0.23 | 0.09 vs 0.82 | -2.7% | 80% | fail |
| 21. ETH/BTC rotation with trend filter (vs 50/50) (crypto since 2017-11-10) | +19.2% | -90% | 0.60 | 0.72 | 0.66 vs 0.95 | 0.54 vs 0.41 | +12.0% | 67% | fail |
| 22. BTC weekend only (Fri-Sun) (BTC since 2017-11-10) | -3.7% | -53% | -0.02 | 0.70 | 0.09 vs 0.83 | -0.22 vs 0.56 | -29.6% | 29% | fail |
| 23. Weekly trend rule on long bonds (TLT) (TLT since 2002-07-30) | +2.3% | -26% | 0.27 | 0.31 | 0.40 vs 0.57 | 0.14 vs 0.07 | +1.1% | 76% | fail |
