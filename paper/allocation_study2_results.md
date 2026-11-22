# Study batch 8: macro signals and adding BTC

Run 2026-11-22 19:30 UTC. Same pass rules.

| Test | Per year | Worst drop | Sharpe | Benchmark Sharpe | 1st half Sharpe (vs bench) | 2nd half Sharpe (vs bench) | Per year at stress cost | Luck check | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| 58. Yield-curve filter: SPY, IEF when inverted (vs SPY) (since 2002-07-30) | +8.8% | -57% | 0.56 | 0.64 | 0.45 vs 0.53 | 0.69 vs 0.77 | +8.3% | 31% | fail |
| 59. Credit risk-on filter: SPY, IEF when credit weakens (vs SPY) (since 2007-04-11) | +7.7% | -37% | 0.67 | 0.60 | 0.72 vs 0.43 | 0.62 vs 0.79 | +1.8% | 93% | fail |
| 60. Gold only while TIP is above its 50-day average (vs GLD) (since 2004-11-18) | +6.7% | -36% | 0.52 | 0.58 | 0.40 vs 0.49 | 0.67 vs 0.71 | +3.8% | 84% | fail |
| 61. Sharpe momentum rotation SPY/TLT/GLD (vs 60/40) (since 2004-11-18) | +10.3% | -34% | 0.66 | 0.77 | 0.78 vs 0.77 | 0.54 vs 0.77 | +8.9% | 84% | fail |
| Reference: risk parity #12 over the same years (since 2014-09-17) | +7.5% | -22% | 0.82 | 0.77 | 1.12 vs 1.13 | 0.61 vs 0.47 | +7.3% | 75% | fail |
| 62. Risk parity SPY/TLT/GLD/BTC (vs 60/40) (since 2014-09-17) | +11.6% | -27% | 1.09 | 0.77 | 1.46 vs 1.13 | 0.80 vs 0.47 | +11.4% | 74% | fail |
| 63. Minimum variance SPY/TLT/GLD/BTC, BTC max 10% (vs 60/40) (since 2014-09-17) | +8.7% | -22% | 0.94 | 0.77 | 1.23 vs 1.13 | 0.73 vs 0.47 | +8.3% | 89% | fail |
| 64. Equal thirds + 5% BTC, fixed (vs 60/40) (since 2014-09-17) | +10.7% | -26% | 1.03 | 0.77 | 1.48 vs 1.13 | 0.69 vs 0.47 | +10.7% | n/a | **PASS** |
| Reference: equal thirds without BTC, same years (since 2014-09-17) | +7.9% | -23% | 0.82 | 0.77 | 1.20 vs 1.13 | 0.56 vs 0.47 | +7.9% | n/a | **PASS** |
