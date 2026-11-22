# Trend-following (time-series momentum) study

Run 2026-11-22 18:44 UTC. 0.10% cost per position change. No leverage. Sharpe = return per unit of risk (higher is better; buy and hold is the bar).

## BTC (weekly rebalance) (2014-09-17 to 2026-11-22)

Buy and hold: +49.3% a year, worst drop -83%, Sharpe 0.94. Second half only: +30.6% a year, worst drop -77%, Sharpe 0.75.

| Rule | Lookback | Per year (all) | Worst drop | Sharpe | 1st half Sharpe | 2nd half per year | 2nd half worst drop | 2nd half Sharpe | Luck check |
|---|---|---|---|---|---|---|---|---|---|
| long/cash | 7 days | +37.6% | -73% | 0.93 | 1.19 | +15.0% | -66% | 0.55 | 93% |
| long/cash | 14 days | +45.6% | -81% | 1.03 | 1.45 | +8.2% | -81% | 0.40 | 97% |
| long/cash | 28 days | +56.9% | -69% | 1.18 | 1.37 | +26.7% | -64% | 0.78 | 100% |
| long/cash | 56 days | +61.0% | -76% | 1.19 | 1.23 | +37.0% | -55% | 0.98 | 100% |
| long/cash | 91 days | +40.1% | -69% | 0.91 | 1.03 | +8.0% | -55% | 0.39 | 91% |
| long/cash | 182 days | +46.1% | -74% | 0.98 | 1.16 | -0.7% | -72% | 0.18 | 95% |
| long/cash | 365 days | +51.0% | -86% | 1.02 | 0.98 | +13.9% | -48% | 0.56 | 97% |
| long/cash + vol sizing | 7 days | +34.8% | -59% | 1.02 | 1.42 | +11.8% | -59% | 0.50 | 97% |
| long/cash + vol sizing | 14 days | +43.1% | -72% | 1.14 | 1.62 | +11.7% | -72% | 0.49 | 100% |
| long/cash + vol sizing | 28 days | +46.3% | -58% | 1.20 | 1.49 | +19.4% | -58% | 0.69 | 100% |
| long/cash + vol sizing | 56 days | +44.0% | -61% | 1.12 | 1.18 | +25.3% | -54% | 0.83 | 99% |
| long/cash + vol sizing | 91 days | +28.3% | -62% | 0.83 | 0.98 | +2.0% | -55% | 0.23 | 83% |
| long/cash + vol sizing | 182 days | +37.3% | -66% | 1.00 | 1.22 | +3.2% | -63% | 0.26 | 95% |
| long/cash + vol sizing | 365 days | +39.3% | -72% | 1.00 | 0.90 | +14.9% | -45% | 0.61 | 96% |
| long/short | 7 days | -0.6% | -92% | 0.32 | 0.50 | -12.9% | -92% | 0.04 | 87% |
| long/short | 14 days | +12.2% | -95% | 0.50 | 0.93 | -20.2% | -95% | -0.11 | 95% |
| long/short | 28 days | +32.6% | -80% | 0.76 | 0.86 | +13.2% | -78% | 0.50 | 99% |
| long/short | 56 days | +44.4% | -83% | 0.89 | 0.83 | +37.6% | -53% | 0.85 | 100% |
| long/short | 91 days | +9.4% | -89% | 0.47 | 0.52 | -9.4% | -74% | 0.09 | 92% |
| long/short | 182 days | +20.5% | -92% | 0.61 | 0.74 | -14.0% | -88% | -0.03 | 93% |
| long/short | 365 days | +32.8% | -94% | 0.77 | 0.54 | +17.0% | -53% | 0.57 | 97% |
| long/short + vol sizing | 7 days | +12.5% | -87% | 0.48 | 0.88 | -11.1% | -87% | -0.01 | 96% |
| long/short + vol sizing | 14 days | +27.4% | -88% | 0.73 | 1.24 | -8.2% | -88% | 0.06 | 99% |
| long/short + vol sizing | 28 days | +35.0% | -71% | 0.84 | 1.10 | +8.4% | -71% | 0.41 | 100% |
| long/short + vol sizing | 56 days | +34.1% | -69% | 0.83 | 0.85 | +23.3% | -55% | 0.68 | 99% |
| long/short + vol sizing | 91 days | +5.8% | -81% | 0.37 | 0.50 | -14.3% | -76% | -0.10 | 87% |
| long/short + vol sizing | 182 days | +19.2% | -80% | 0.60 | 0.74 | -7.8% | -78% | 0.04 | 94% |
| long/short + vol sizing | 365 days | +24.7% | -87% | 0.70 | 0.36 | +18.7% | -50% | 0.62 | 96% |

**Chosen on the first half only:** long/cash + vol sizing, 14-day lookback (first-half Sharpe 1.62). **On the unseen second half:** +11.7% a year, worst drop -72%, Sharpe 0.49 vs buy and hold Sharpe 0.75. Luck check 100%.

## Oil CL=F (monthly rebalance) (2000-08-23 to 2026-11-20)

Buy and hold: +3.7% a year, worst drop -93%, Sharpe 0.30. Second half only: -1.5% a year, worst drop -91%, Sharpe 0.21.

| Rule | Lookback | Per year (all) | Worst drop | Sharpe | 1st half Sharpe | 2nd half per year | 2nd half worst drop | 2nd half Sharpe | Luck check |
|---|---|---|---|---|---|---|---|---|---|
| long/cash | 21 days | +5.0% | -52% | 0.32 | 0.34 | +4.7% | -52% | 0.31 | 82% |
| long/cash | 63 days | +2.8% | -57% | 0.24 | 0.51 | -3.5% | -53% | 0.00 | 57% |
| long/cash | 126 days | +3.2% | -67% | 0.25 | 0.34 | +1.2% | -61% | 0.18 | 65% |
| long/cash | 252 days | +3.4% | -62% | 0.26 | 0.33 | +2.4% | -49% | 0.22 | 70% |
| long/cash + vol sizing | 21 days | +1.5% | -46% | 0.18 | 0.20 | +1.1% | -46% | 0.15 | 39% |
| long/cash + vol sizing | 63 days | +1.1% | -60% | 0.16 | 0.39 | -2.8% | -48% | -0.04 | 37% |
| long/cash + vol sizing | 126 days | +2.1% | -59% | 0.20 | 0.30 | +0.6% | -53% | 0.13 | 52% |
| long/cash + vol sizing | 252 days | +3.4% | -41% | 0.27 | 0.40 | +1.6% | -40% | 0.18 | 74% |
| long/short | 21 days | -5.5% | -90% | 0.08 | 0.00 | -4.7% | -90% | 0.13 | 64% |
| long/short | 63 days | -9.4% | -97% | -0.02 | 0.25 | -19.1% | -97% | -0.22 | 42% |
| long/short | 126 days | -8.7% | -98% | -0.00 | 0.03 | -10.6% | -92% | -0.00 | 48% |
| long/short | 252 days | -8.2% | -96% | 0.01 | 0.03 | -10.6% | -92% | -0.00 | 52% |
| long/short + vol sizing | 21 days | -2.0% | -68% | 0.07 | -0.16 | +3.1% | -59% | 0.25 | 60% |
| long/short + vol sizing | 63 days | -2.3% | -71% | 0.05 | 0.15 | -4.1% | -69% | -0.00 | 53% |
| long/short + vol sizing | 126 days | -0.6% | -70% | 0.11 | 0.01 | +2.6% | -70% | 0.23 | 70% |
| long/short + vol sizing | 252 days | +2.0% | -58% | 0.21 | 0.19 | +2.5% | -53% | 0.23 | 87% |

**Chosen on the first half only:** long/cash, 63-day lookback (first-half Sharpe 0.51). **On the unseen second half:** -3.5% a year, worst drop -53%, Sharpe 0.00 vs buy and hold Sharpe 0.21. Luck check 57%.

## Oil USO (monthly rebalance) (2006-04-10 to 2026-11-20)

Buy and hold: -6.4% a year, worst drop -98%, Sharpe 0.01. Second half only: +5.8% a year, worst drop -87%, Sharpe 0.34.

| Rule | Lookback | Per year (all) | Worst drop | Sharpe | 1st half Sharpe | 2nd half per year | 2nd half worst drop | 2nd half Sharpe | Luck check |
|---|---|---|---|---|---|---|---|---|---|
| long/cash | 21 days | +6.2% | -48% | 0.38 | 0.18 | +11.1% | -39% | 0.54 | 99% |
| long/cash | 63 days | -0.6% | -71% | 0.09 | -0.21 | +5.2% | -51% | 0.33 | 73% |
| long/cash | 126 days | +4.8% | -66% | 0.32 | -0.04 | +11.6% | -49% | 0.55 | 97% |
| long/cash | 252 days | -1.3% | -82% | 0.06 | -0.32 | +6.5% | -42% | 0.37 | 67% |
| long/cash + vol sizing | 21 days | +2.4% | -52% | 0.22 | 0.01 | +6.3% | -40% | 0.40 | 90% |
| long/cash + vol sizing | 63 days | -1.7% | -69% | 0.01 | -0.31 | +3.3% | -47% | 0.26 | 57% |
| long/cash + vol sizing | 126 days | +3.2% | -61% | 0.26 | -0.02 | +7.6% | -43% | 0.46 | 94% |
| long/cash + vol sizing | 252 days | -1.0% | -71% | 0.03 | -0.19 | +3.4% | -38% | 0.27 | 61% |
| long/short | 21 days | +10.4% | -74% | 0.45 | 0.57 | +6.9% | -59% | 0.37 | 99% |
| long/short | 63 days | -2.9% | -84% | 0.11 | 0.14 | -3.0% | -78% | 0.11 | 72% |
| long/short | 126 days | +6.6% | -80% | 0.36 | 0.26 | +10.2% | -76% | 0.44 | 96% |
| long/short | 252 days | -5.7% | -89% | 0.02 | -0.05 | -0.7% | -74% | 0.17 | 60% |
| long/short + vol sizing | 21 days | +5.1% | -73% | 0.32 | 0.39 | +3.9% | -50% | 0.28 | 94% |
| long/short + vol sizing | 63 days | -2.7% | -74% | 0.03 | -0.02 | -0.7% | -71% | 0.12 | 60% |
| long/short + vol sizing | 126 days | +5.6% | -68% | 0.34 | 0.26 | +8.1% | -68% | 0.42 | 94% |
| long/short + vol sizing | 252 days | -3.2% | -79% | 0.01 | 0.02 | -1.4% | -58% | 0.08 | 56% |

**Chosen on the first half only:** long/short, 21-day lookback (first-half Sharpe 0.57). **On the unseen second half:** +6.9% a year, worst drop -59%, Sharpe 0.37 vs buy and hold Sharpe 0.34. Luck check 99%.
