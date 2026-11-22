# Academic anomaly study, batch 5

Run 2026-11-22 19:02 UTC. Same pass rules as batch 1.

| Test | Per year | Worst drop | Sharpe | Benchmark Sharpe | 1st half Sharpe (vs bench) | 2nd half Sharpe (vs bench) | Per year at stress cost | Luck check | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| 31. Vol-managed + 200-day, gold (GLD) (GLD since 2004-11-18) | +7.5% | -32% | 0.65 | 0.58 | 0.61 vs 0.49 | 0.69 vs 0.71 | +6.2% | 93% | fail |
| 32. Vol-managed + 200-day, ex-US stocks (EFA) (EFA since 2001-08-27) | +5.1% | -24% | 0.50 | 0.39 | 0.68 vs 0.37 | 0.30 vs 0.42 | +4.0% | 94% | fail |
| 33. Vol-managed + 200-day, small caps (IWM) (IWM since 2000-05-26) | +3.3% | -28% | 0.33 | 0.45 | 0.35 vs 0.42 | 0.31 vs 0.49 | +2.1% | 49% | fail |
| 34. BTC above its 200-day average only (BTC since 2014-09-17) | +54.1% | -70% | 1.10 | 0.94 | 1.28 vs 1.10 | 0.89 vs 0.76 | +51.2% | 94% | fail |
| 35. Vol-managed ETH (50% target) (ETH since 2017-11-10) | +19.3% | -76% | 0.59 | 0.65 | 0.83 vs 0.94 | 0.35 vs 0.27 | +18.6% | 43% | fail |
| 36. Low-volatility sectors, 3 of 9 (vs SPY) (sectors since 2000-01-03) | +8.3% | -40% | 0.62 | 0.49 | 0.39 vs 0.23 | 0.85 vs 0.82 | +7.9% | 71% | fail |
| 37. Risk parity SPY/TLT/GLD (vs 60/40) (since 2004-11-18) | +8.8% | -22% | 0.98 | 0.77 | 1.05 vs 0.77 | 0.92 vs 0.77 | +8.7% | 97% | **PASS** |
| 38. Stock/bond momentum switch (vs 60/40) (since 2004-11-18) | +7.3% | -31% | 0.53 | 0.77 | 0.46 vs 0.77 | 0.59 vs 0.77 | +7.0% | 50% | fail |
| 39. Buy SPY for 20 days after VIX > 30 (SPY since 2000-01-03) | +4.6% | -45% | 0.38 | 0.49 | 0.29 vs 0.23 | 0.54 vs 0.82 | +4.3% | 80% | fail |
