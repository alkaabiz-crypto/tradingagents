# Academic anomaly study

Run 2026-11-22 18:52 UTC. Rules and pass rules fixed before running. PASS = luck check >= 95%, Sharpe above the benchmark in BOTH halves, and positive after costs.

## Stocks: SPY (2000-01-03 to 2026-11-20); benchmark = holding SPY

| Test | Per year | Worst drop | Sharpe | Benchmark Sharpe | 1st half Sharpe (vs bench) | 2nd half Sharpe (vs bench) | Per year at stress cost | Luck check | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| 1. Turn of the month (SPY) | +1.7% | -19% | 0.25 | 0.49 | 0.32 vs 0.23 | 0.17 vs 0.82 | -1.9% | 88% | fail |
| 3. Halloween: hold Nov-Apr (SPY) | +4.9% | -34% | 0.42 | 0.49 | 0.40 vs 0.23 | 0.43 vs 0.82 | +4.6% | 90% | fail |
| 4. IBS reversal (SPY) | +8.8% | -29% | 0.65 | 0.49 | 0.58 vs 0.23 | 0.76 vs 0.82 | +0.4% | 100% | fail |

**2. Overnight drift:** holding SPY only overnight earned +7.1% a year before costs (daytime only: +0.7%), but buying every close and selling every open at 0.05% per side gives -16.7% a year. Holding SPY: +7.8% a year.

## Asset allocation (2006-02-06 to 2026-11-20)

| Test | Per year | Worst drop | Sharpe | Benchmark Sharpe | 1st half Sharpe (vs bench) | 2nd half Sharpe (vs bench) | Per year at stress cost | Luck check | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| 5. Faber 10-month trend, 5 ETFs (vs equal-weight hold) | +4.4% | -16% | 0.59 | 0.51 | 0.44 vs 0.37 | 0.78 vs 0.73 | +4.1% | 84% | fail |
| 6. Dual momentum SPY/EFA/AGG (vs SPY) | +6.2% | -36% | 0.47 | 0.62 | 0.43 vs 0.42 | 0.50 vs 0.85 | +5.6% | 54% | fail |

## Crypto (2017-11-15 to 2026-11-22); benchmark = equal-weight 12 coins

Holding BTC alone over this period: +26.4% a year, worst drop -83%, Sharpe 0.69.

| Test | Per year | Worst drop | Sharpe | Benchmark Sharpe | 1st half Sharpe (vs bench) | 2nd half Sharpe (vs bench) | Per year at stress cost | Luck check | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| 7. Crypto top-3 momentum (vs equal-weight 12 coins) | +13.1% | -89% | 0.57 | 0.94 | 0.87 vs 1.27 | 0.12 vs 0.46 | +1.1% | 14% | fail |
| 8. Crypto top-3 momentum + BTC trend filter (vs equal-weight 12 coins) | +53.4% | -62% | 0.99 | 0.94 | 1.28 vs 1.27 | 0.62 vs 0.46 | +41.3% | 91% | fail |
