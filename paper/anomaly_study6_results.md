# Academic anomaly study, batch 6

Run 2026-11-22 19:19 UTC. Same pass rules as batch 1.

| Test | Per year | Worst drop | Sharpe | Benchmark Sharpe | 1st half Sharpe (vs bench) | 2nd half Sharpe (vs bench) | Per year at stress cost | Luck check | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| 40. Vol-managed long bonds (TLT) (TLT since 2002-07-30) | +2.9% | -45% | 0.28 | 0.31 | 0.51 vs 0.57 | 0.08 vs 0.07 | +2.8% | 13% | fail |
| 41. Vol-managed emerging markets (EEM) (EEM since 2003-04-14) | +7.0% | -32% | 0.49 | 0.45 | 0.66 vs 0.55 | 0.30 vs 0.32 | +6.7% | 86% | fail |
| 42. Vol-managed real estate (VNQ) (VNQ since 2004-09-29) | +7.4% | -32% | 0.54 | 0.39 | 0.77 vs 0.43 | 0.30 vs 0.36 | +7.2% | 96% | fail |
| 43. Weekly trend rule on the US dollar (UUP) (UUP since 2007-03-01) | +1.1% | -16% | 0.21 | 0.27 | 0.03 vs 0.12 | 0.45 vs 0.48 | -0.1% | 77% | fail |
| 44. Weekly trend rule on commodities (DBC) (DBC since 2006-02-06) | +4.5% | -34% | 0.41 | 0.20 | 0.23 vs -0.09 | 0.59 vs 0.54 | +3.3% | 95% | fail |
| 45. BTC only while SPY is above its 200-day average (BTC since 2014-09-17) | +56.5% | -70% | 1.05 | 0.94 | 1.27 vs 1.10 | 0.79 vs 0.76 | +54.0% | 93% | fail |
| 46. Country momentum, top 3 of 10 (vs hold all 10) (countries since 2000-07-14) | +5.8% | -66% | 0.36 | 0.43 | 0.46 vs 0.45 | 0.24 vs 0.41 | +5.0% | 44% | fail |
| 47. Multi-asset trend with vol scaling (vs hold all 8) (multi-asset since 2006-02-06) | +3.1% | -11% | 0.68 | 0.59 | 0.82 vs 0.49 | 0.57 vs 0.73 | +2.9% | 86% | fail |
| 48. Risk parity + 200-day filter per fund (vs 60/40) (since 2004-11-18) | +6.9% | -11% | 0.94 | 0.77 | 1.07 vs 0.77 | 0.81 vs 0.77 | +6.5% | 94% | fail |
