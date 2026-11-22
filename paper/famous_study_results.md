# Famous daily / day-trading strategies

Run 2026-11-22 20:13 UTC.

## A. Intraday momentum (about 2 years of hourly data)

| Market / version | Trades | Win rate | Avg per trade (0.02% cost) | Sharpe | t-stat | 1st half / 2nd half avg | Avg at 0.05% cost | Luck check | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| Oil (CL=F): overnight+first hour -> 13:00 hour | 594 | 45% | -0.031% | -0.73 | -1.12 | -0.067% / +0.005% | -0.091% | 65% | fail |
| Oil (CL=F): EIA-day version (Wednesday uses the 10:00 report hour) | 594 | 47% | -0.020% | -0.47 | -0.72 | -0.069% / +0.030% | -0.080% | 79% | fail |
| SPY: overnight+first hour -> last half hour | 715 | 37% | -0.049% | -3.56 | -6.00 | -0.053% / -0.044% | -0.109% | 13% | fail |
| QQQ: overnight+first hour -> last half hour | 715 | 39% | -0.048% | -2.79 | -4.69 | -0.056% / -0.040% | -0.108% | 20% | fail |

## B. Connors RSI(2) (daily, since 1993)

| Test | Per year | Worst drop | Sharpe | Benchmark Sharpe | 1st half Sharpe (vs bench) | 2nd half Sharpe (vs bench) | Per year at stress cost | Luck check | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| Connors RSI(2) on SPY (since 1993-01-29) | +2.3% | -14% | 0.48 | 0.63 | 0.72 vs 0.46 | 0.29 vs 0.82 | +1.1% | 99% | fail |
| Connors RSI(2) on QQQ (since 1999-03-10) | +2.5% | -12% | 0.40 | 0.49 | 0.29 vs 0.23 | 0.53 vs 0.90 | +1.3% | 97% | fail |
| Connors RSI(2) on IWM (since 2000-05-26) | +1.7% | -19% | 0.31 | 0.45 | 0.26 vs 0.42 | 0.37 vs 0.49 | +0.5% | 91% | fail |
| Connors RSI(2) on DIA (since 1998-01-20) | +1.0% | -13% | 0.23 | 0.54 | 0.23 vs 0.37 | 0.23 vs 0.78 | -0.3% | 86% | fail |
