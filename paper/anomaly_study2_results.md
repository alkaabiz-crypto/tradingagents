# Academic anomaly study, batch 2

Run 2026-11-22 18:53 UTC. Same pass rules as batch 1.

| Test | Per year | Worst drop | Sharpe | Benchmark Sharpe | 1st half Sharpe (vs bench) | 2nd half Sharpe (vs bench) | Per year at stress cost | Luck check | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| 9. Volatility-managed S&P 500 (Stocks (SPY since 2000)) | +7.8% | -40% | 0.60 | 0.49 | 0.36 vs 0.23 | 0.85 vs 0.82 | +7.6% | 98% | **PASS** |
| 10. VIX term-structure filter (SPY) (Stocks (VIX3M data since 2006-07-17)) | +8.6% | -41% | 0.67 | 0.63 | 0.47 vs 0.46 | 0.87 vs 0.82 | +6.2% | 93% | fail |
| 11. Sector momentum, top 3 of 9 (vs SPY) (Sectors (2000-01-03 on)) | +9.2% | -46% | 0.57 | 0.49 | 0.38 vs 0.23 | 0.80 vs 0.82 | +8.4% | 81% | fail |
| 12. Multi-asset 12-month trend, 8 ETFs (vs hold all 8) (Multi-asset (2006-02-06 on)) | +4.4% | -14% | 0.61 | 0.59 | 0.62 vs 0.49 | 0.60 vs 0.73 | +4.2% | 71% | fail |
| 13. Our BTC trend rule on ETH (out of sample) (Crypto (ETH since 2017-11-10)) | +33.5% | -55% | 0.95 | 0.65 | 1.06 vs 0.94 | 0.83 vs 0.27 | +30.7% | 97% | **PASS** |
| 14. Our trend rule on gold (GLD) (Gold (GLD since 2004-11-18)) | +5.7% | -37% | 0.48 | 0.58 | 0.25 vs 0.49 | 0.71 vs 0.71 | +4.5% | 67% | fail |
