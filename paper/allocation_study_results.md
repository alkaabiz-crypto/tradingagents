# Risk-parity-like portfolio study

Run 2026-11-22 19:24 UTC, common history 2006-02-06 to 2026-11-20. Benchmark 60% SPY / 40% TLT. Fixed mixes have no timing, so they need only beat 60/40 in both halves; dynamic ones also need the luck check >= 95%.

| Test | Per year | Worst drop | Sharpe | Benchmark Sharpe | 1st half Sharpe (vs bench) | 2nd half Sharpe (vs bench) | Per year at stress cost | Luck check | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| 49. Permanent Portfolio | +6.9% | -19% | 0.91 | 0.76 | 0.99 vs 0.78 | 0.83 vs 0.75 | +6.8% | n/a | **PASS** |
| 50. All Weather (retail) | +6.5% | -23% | 0.80 | 0.76 | 0.98 vs 0.78 | 0.64 vs 0.75 | +6.5% | n/a | fail |
| 51. Golden Butterfly | +7.4% | -20% | 0.80 | 0.76 | 0.79 vs 0.78 | 0.82 vs 0.75 | +7.3% | n/a | **PASS** |
| 52. Equal thirds SPY/TLT/GLD | +8.4% | -23% | 0.86 | 0.76 | 0.92 vs 0.78 | 0.80 vs 0.75 | +8.4% | n/a | **PASS** |
| Reference: risk parity #12 (SPY/TLT/GLD) | +8.8% | -22% | 0.97 | 0.76 | 1.12 vs 0.78 | 0.84 vs 0.75 | +8.7% | 97% | **PASS** |
| 53. Risk parity, 5 assets | +7.1% | -25% | 0.73 | 0.76 | 0.62 vs 0.78 | 0.85 vs 0.75 | +6.9% | 94% | fail |
| 54. Minimum variance SPY/TLT/GLD | +9.7% | -22% | 1.09 | 0.76 | 1.28 vs 0.78 | 0.93 vs 0.75 | +9.4% | 98% | **PASS** |
| 55. Equal risk contribution SPY/TLT/GLD | +8.4% | -23% | 0.91 | 0.76 | 1.01 vs 0.78 | 0.82 vs 0.75 | +8.0% | 90% | fail |
| 56. Risk parity #12 + 8% volatility target | +7.6% | -17% | 0.96 | 0.76 | 1.12 vs 0.78 | 0.81 vs 0.75 | +7.4% | 95% | fail |
| 57. Vigilant Asset Allocation G4 | +7.8% | -21% | 0.64 | 0.76 | 0.71 vs 0.78 | 0.56 vs 0.75 | +5.5% | 97% | fail |
