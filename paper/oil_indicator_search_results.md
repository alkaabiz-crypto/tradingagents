# Oil indicator search (day trading + short swing)

Run 2026-11-22 19:39 UTC. Rules chosen on TRAIN only; judged on unseen TEST. PASS = positive at 0.02% and 0.05% costs, Sharpe > 0.5, >= 40 trades, luck check >= 99%.

## Hourly WTI futures, New York session only (day trading)

History 2024-07-02 to 2026-11-20; TRAIN to 2025-12-09, TEST after. Top 10 by TRAIN Sharpe go to TEST.

### Round 1: single indicators (15 tried)

| Rule | TRAIN Sharpe | TEST Sharpe | TEST total (0.02%) | TEST total (0.05%) | TEST trades | Luck (TEST) | Verdict |
|---|---|---|---|---|---|---|---|
| Stochastic 20/80 reversal | 0.34 | 0.12 | +2.8% | -7.5% | 176 | 78% | fail |
| VWAP stretch reversal | 0.16 | 0.35 | +8.0% | +1.5% | 104 | 88% | fail |
| RSI(14) 30/70 reversal | 0.15 | -0.23 | -5.8% | -9.7% | 71 | 0% | fail |
| RSI(2) 10/90 reversal | 0.07 | 0.13 | +3.2% | -8.0% | 191 | 80% | fail |
| CCI -100/+100 reversal | -0.00 | 0.16 | +4.6% | -9.0% | 231 | 79% | fail |
| EMA 9/21 cross | -0.02 | -0.16 | -12.5% | -26.2% | 284 | 0% | fail |
| Price vs 50-bar avg | -0.19 | 0.22 | +9.3% | -8.1% | 288 | 80% | fail |
| RSI(14) above/below 50 | -0.32 | -0.22 | -15.4% | -31.1% | 343 | 0% | fail |
| Bollinger 2-sd reversal | -0.40 | -0.13 | -4.8% | -12.5% | 141 | 0% | fail |
| MACD above signal | -0.45 | -0.59 | -31.6% | -43.5% | 318 | 0% | fail |

### Round 2: indicator pairs (105 tried)

| Rule | TRAIN Sharpe | TEST Sharpe | TEST total (0.02%) | TEST total (0.05%) | TEST trades | Luck (TEST) | Verdict |
|---|---|---|---|---|---|---|---|
| MACD above signal + RSI(2) 10/90 reversal | 0.63 | 0.07 | +0.6% | -1.6% | 38 | 65% | fail |
| Stochastic 20/80 reversal + VWAP stretch reversal | 0.38 | 0.21 | +4.3% | -1.2% | 90 | 80% | fail |
| RSI(14) 30/70 reversal + Stochastic 20/80 reversal | 0.33 | -0.22 | -5.3% | -8.8% | 63 | 0% | fail |
| Stochastic 20/80 reversal + CCI -100/+100 reversal | 0.27 | 0.47 | +15.3% | +4.5% | 165 | 94% | fail |
| MACD above signal + CCI -100/+100 reversal | 0.19 | -0.14 | -1.0% | -1.9% | 16 | 0% | fail |
| RSI(14) 30/70 reversal + VWAP stretch reversal | 0.18 | -0.27 | -5.1% | -8.4% | 58 | 0% | fail |
| RSI(14) 30/70 reversal + CCI -100/+100 reversal | 0.16 | -0.29 | -6.9% | -10.8% | 71 | 0% | fail |
| CCI -100/+100 reversal + VWAP stretch reversal | 0.11 | 0.37 | +8.3% | +2.0% | 101 | 89% | fail |
| RSI(14) 30/70 reversal + Bollinger 2-sd reversal | -0.05 | -0.36 | -6.9% | -10.2% | 60 | 0% | fail |
| RSI(2) 10/90 reversal + CCI -100/+100 reversal | -0.06 | 0.20 | +4.8% | -4.2% | 149 | 82% | fail |

### Round 3: best pairs + signal filters (60 tried)

| Rule | TRAIN Sharpe | TEST Sharpe | TEST total (0.02%) | TEST total (0.05%) | TEST trades | Luck (TEST) | Verdict |
|---|---|---|---|---|---|---|---|
| MACD above signal + RSI(2) 10/90 reversal | high volatility only | 0.67 | 0.02 | +0.1% | -1.4% | 25 | 58% | fail |
| RSI(14) 30/70 reversal + Stochastic 20/80 reversal | daily trend down | 0.58 | -0.21 | -3.8% | -5.5% | 30 | 0% | fail |
| RSI(14) 30/70 reversal + VWAP stretch reversal | daily trend down | 0.56 | -0.05 | -1.0% | -2.6% | 27 | 0% | fail |
| Stochastic 20/80 reversal + CCI -100/+100 reversal | skip Wednesday 9-12 (EIA) | 0.52 | 0.61 | +19.2% | +8.7% | 154 | 97% | fail |
| Stochastic 20/80 reversal + CCI -100/+100 reversal | high volatility only | 0.52 | 0.53 | +15.7% | +7.6% | 121 | 94% | fail |
| MACD above signal + RSI(2) 10/90 reversal | morning only (9-11) | 0.49 | -0.13 | -1.3% | -2.7% | 24 | 0% | fail |
| RSI(14) 30/70 reversal + CCI -100/+100 reversal | daily trend down | 0.44 | -0.15 | -3.0% | -4.8% | 32 | 0% | fail |
| Stochastic 20/80 reversal + CCI -100/+100 reversal | daily trend down | 0.42 | -0.19 | -4.7% | -8.6% | 70 | 0% | fail |
| Stochastic 20/80 reversal + VWAP stretch reversal | skip Wednesday 9-12 (EIA) | 0.37 | 0.32 | +6.0% | +1.0% | 80 | 84% | fail |
| Stochastic 20/80 reversal + VWAP stretch reversal | daily trend up | 0.34 | 0.12 | +1.6% | -1.2% | 48 | 72% | fail |

## Daily WTI futures since 2000 (1-5 day swing trades)

History 2000-08-23 to 2026-11-20; TRAIN to 2016-05-26, TEST after. Top 10 by TRAIN Sharpe go to TEST.

### Round 1: single indicators (15 tried)

| Rule | TRAIN Sharpe | TEST Sharpe | TEST total (0.02%) | TEST total (0.05%) | TEST trades | Luck (TEST) | Verdict |
|---|---|---|---|---|---|---|---|
| EMA 9/21 cross | 0.24 | 0.06 | -55.3% | -58.2% | 111 | 59% | fail |
| RSI(14) 30/70 reversal | 0.22 | 0.06 | -13.0% | -16.7% | 71 | 62% | fail |
| Bollinger 2-sd reversal | 0.17 | 0.01 | -16.5% | -24.0% | 157 | 59% | fail |
| Stochastic 20/80 reversal | 0.15 | -0.04 | -49.9% | -55.7% | 205 | 0% | fail |
| RSI(2) 10/90 reversal | 0.14 | -0.04 | -40.1% | -51.5% | 352 | 0% | fail |
| Price vs 50-bar avg | 0.07 | -0.10 | -79.2% | -81.7% | 209 | 0% | fail |
| RSI(14) above/below 50 | 0.06 | -0.13 | -82.0% | -85.1% | 319 | 0% | fail |
| CCI -100/+100 reversal | 0.04 | -0.24 | -75.0% | -78.6% | 256 | 0% | fail |
| VWAP stretch reversal | 0.00 | 0.51 | +280.0% | +263.6% | 73 | 98% | fail |
| Price vs VWAP | -0.02 | -0.28 | -91.2% | -91.4% | 43 | 0% | fail |

### Round 2: indicator pairs (105 tried)

| Rule | TRAIN Sharpe | TEST Sharpe | TEST total (0.02%) | TEST total (0.05%) | TEST trades | Luck (TEST) | Verdict |
|---|---|---|---|---|---|---|---|
| RSI(14) 30/70 reversal + Bollinger 2-sd reversal | 0.57 | 0.08 | -0.6% | -3.4% | 49 | 66% | fail |
| EMA 9/21 cross + Stochastic 20/80 reversal | 0.54 | -0.38 | -24.9% | -26.7% | 39 | 0% | fail |
| RSI(14) 30/70 reversal + RSI(2) 10/90 reversal | 0.45 | 0.06 | -6.5% | -10.5% | 72 | 66% | fail |
| EMA 9/21 cross + RSI(2) 10/90 reversal | 0.44 | -0.04 | -13.0% | -19.3% | 124 | 0% | fail |
| RSI(14) 30/70 reversal + VWAP stretch reversal | 0.35 | 0.05 | -14.3% | -16.6% | 45 | 58% | fail |
| Price vs 50-bar avg + RSI(2) 10/90 reversal | 0.29 | -0.22 | -28.1% | -31.6% | 82 | 0% | fail |
| Bollinger 2-sd reversal + Stochastic 20/80 reversal | 0.29 | 0.15 | +11.6% | +3.2% | 131 | 69% | fail |
| EMA 9/21 cross + CCI -100/+100 reversal | 0.28 | -0.12 | -8.5% | -10.6% | 39 | 0% | fail |
| RSI(14) above/below 50 + RSI(2) 10/90 reversal | 0.28 | -0.52 | -43.1% | -44.5% | 44 | 0% | fail |
| RSI(14) 30/70 reversal + CCI -100/+100 reversal | 0.27 | -0.03 | -28.0% | -31.0% | 69 | 0% | fail |

### Round 3: best pairs + signal filters (60 tried)

| Rule | TRAIN Sharpe | TEST Sharpe | TEST total (0.02%) | TEST total (0.05%) | TEST trades | Luck (TEST) | Verdict |
|---|---|---|---|---|---|---|---|
| RSI(14) 30/70 reversal + Bollinger 2-sd reversal | skip Mondays | 0.67 | -0.03 | -16.1% | -18.7% | 53 | 0% | fail |
| RSI(14) 30/70 reversal + Bollinger 2-sd reversal | high volatility only | 0.63 | 0.07 | -2.2% | -3.9% | 30 | 63% | fail |
| RSI(14) 30/70 reversal + RSI(2) 10/90 reversal | high volatility only | 0.60 | 0.04 | -10.3% | -12.4% | 39 | 60% | fail |
| RSI(14) 30/70 reversal + Bollinger 2-sd reversal | long side only | 0.57 | 0.08 | -0.6% | -3.4% | 49 | 66% | fail |
| RSI(14) 30/70 reversal + RSI(2) 10/90 reversal | skip Mondays | 0.55 | 0.04 | -8.8% | -12.8% | 75 | 63% | fail |
| EMA 9/21 cross + Stochastic 20/80 reversal | long side only | 0.54 | -0.38 | -24.9% | -26.7% | 39 | 0% | fail |
| Bollinger 2-sd reversal + Stochastic 20/80 reversal | high volatility only | 0.54 | 0.24 | +30.6% | +24.8% | 75 | 79% | fail |
| EMA 9/21 cross + RSI(2) 10/90 reversal | above 200-day avg | 0.51 | 0.48 | +33.7% | +28.7% | 64 | 93% | fail |
| RSI(14) 30/70 reversal + CCI -100/+100 reversal | high volatility only | 0.50 | -0.03 | -27.3% | -29.0% | 39 | 0% | fail |
| RSI(14) 30/70 reversal + VWAP stretch reversal | above 200-day avg | 0.49 | 0.12 | +8.5% | +6.6% | 29 | 77% | fail |

## Summary

Hourly passes: none

Daily passes: none
