
### Baseline replication (claim: 74 trades, +0.79R, t 3.28)

| label | n | avgR | t | win | totR |
|---|---|---|---|---|---|
| Yahoo daily 2019-2026, 10 bp/side (this replication) | 75 | 0.81 | 3.39 | 0.48 | 60.7 |
| same, no costs | 75 | 0.841 | 3.51 | 0.48 | 63.1 |


### Task 1: avg R by daily close time, 2024-11-25 to 2026-11-24 (10 bp/side). _200 = 200-day SMA from Yahoo daily closes (ffill to the candle close); _100 = 100-candle SMA on the shifted candles (signals only after 100 candles)

| close_utc | n_200 | avgR_200 | t_200 | totR_200 | n_100 | avgR_100 | t_100 | first_sig_100 |
|---|---|---|---|---|---|---|---|---|
| 00:00 | 14 | 0.861 | 1.51 | 12.1 | 15.0 | 0.847 | 1.55 | 2025-04-07 |
| 04:00 | 15 | 0.713 | 1.31 | 10.7 | 15.0 | 0.821 | 1.52 | 2025-04-07 |
| 08:00 | 15 | 0.735 | 1.33 | 11.0 | 14.0 | 0.92 | 1.65 | 2025-04-07 |
| 12:00 | 14 | 0.818 | 1.46 | 11.5 | 14.0 | 0.749 | 1.38 | 2025-04-07 |
| 16:00 | 14 | 0.872 | 1.52 | 12.2 | 15.0 | 0.845 | 1.62 | 2025-04-07 |
| 20:00 | 14 | 0.755 | 1.38 | 10.6 | 16.0 | 0.706 | 1.35 | 2025-04-06 |
| Yahoo daily 00:00 (ref) | 14 | 0.83 | 1.46 | 11.6 |  |  |  |  |

Spread of avg R across the 6 close times (200-SMA): min 0.713, max 0.872, mean 0.792; 00:00 rank among 6: 2.


### Task 2: entry delay after the signal close (stop/target re-anchored to the actual fill; 10 bp/side)

| sample | delay | n | avgR | t | totR |
|---|---|---|---|---|---|
| 00:00 close, hourly path (2y) | 0h | 14 | 0.855 | 1.49 | 12.0 |
| 00:00 close, hourly path (2y) | 1h | 14 | 0.847 | 1.48 | 11.9 |
| 00:00 close, hourly path (2y) | 4h | 14 | 0.816 | 1.44 | 11.4 |
| 00:00 close, hourly path (2y) | 24h | 14 | 0.666 | 1.25 | 9.3 |
| pooled 6 close times, hourly path (2y) | 0h | 86 | 0.78 | 3.53 | 67.1 |
| pooled 6 close times, hourly path (2y) | 1h | 86 | 0.775 | 3.51 | 66.7 |
| pooled 6 close times, hourly path (2y) | 4h | 86 | 0.754 | 3.46 | 64.9 |
| pooled 6 close times, hourly path (2y) | 24h | 88 | 0.58 | 2.88 | 51.1 |
| Yahoo daily 2019-2026 | next open (0h) | 75 | 0.81 | 3.39 | 60.7 |
| Yahoo daily 2019-2026 | 24h | 71 | 0.77 | 3.23 | 54.7 |


### Task 2b: how far price moved against the entry during the delay, in R (positive = worse fill), 00:00 signals

| delay | matched | mean_adverse_entry_R | median | pct_worse |
|---|---|---|---|---|
| 1h | 14 | 0.013 | 0.022 | 0.57 |
| 4h | 14 | 0.001 | -0.038 | 0.36 |
| 24h | 14 | 0.105 | -0.026 | 0.5 |


### Task 3: how often a bar touched both stop and target

| sample | trades | stop_exits | bars_with_both_touched |
|---|---|---|---|
| Yahoo daily 2019-2026 | 75 | 36 | 0 |
| 2y candles closing 00:00 | 14 | 7 | 0 |
| 2y candles closing 04:00 | 15 | 8 | 0 |
| 2y candles closing 08:00 | 15 | 8 | 0 |
| 2y candles closing 12:00 | 14 | 7 | 0 |
| 2y candles closing 16:00 | 14 | 7 | 0 |
| 2y candles closing 20:00 | 14 | 7 | 0 |
| hourly bars inside the 2y trades (same-hour both touched) | 14 | 7 | 0 |


### Task 3b: daily-bar simulation vs hourly-path simulation of the same 2y signals (entry at the 00:00 open)

| matched_trades | same_exit_reason | avgR_dailybars | avgR_hourlypath | mean_abs_R_diff |
|---|---|---|---|---|
| 14 | 1.0 | 0.83 | 0.855 | 0.026 |

Mismatched trades (daily vs hourly):

none


### Task 4a: daily stop exits — gap at the open and how far the stop day traded beyond the stop

| sample | stop_exits | gapped_open_beyond_stop | mean_gap_bp | max_gap_bp | median_day_extreme_beyond_stop_bp | median_day_close_beyond_stop_bp |
|---|---|---|---|---|---|---|
| Yahoo daily 2019-2026 (stop exits) | 36 | 0 | 0.0 | 0.0 | 130 | -18 |


### Task 4b: hourly stop exits — gap at the hourly open, extreme of the touching hour, close of the touching hour (bp beyond stop)

| sample | stop_exits | hour_open_gapped_beyond_stop | mean_gap_bp | max_gap_bp | median_hour_extreme_beyond_stop_bp | p90_hour_extreme_bp | median_hour_close_beyond_stop_bp | p90_hour_close_bp |
|---|---|---|---|---|---|---|---|---|
| hourly, pooled 6 close times, 2y (stop exits) | 44 | 0 | 0.0 | 0.0 | 24.5 | 82.0 | -8.3 | 57.7 |


### Task 4c: avg R, 2019-2026, 10 bp/side plus slippage on entries (rows) and stop exits (columns)

| entry_slip_bp | stop_slip_0 | stop_slip_10 | stop_slip_25 | stop_slip_50 |
|---|---|---|---|---|
| 0 | 0.81 | 0.803 | 0.793 | 0.776 |
| 10 | 0.795 | 0.788 | 0.778 | 0.76 |
| 25 | 0.772 | 0.765 | 0.755 | 0.737 |
| 50 | 0.733 | 0.726 | 0.716 | 0.699 |

Median stop distance = 713 bp of price, so 10 bp of slippage costs about 0.014R per occurrence.


### Task 5a: weekend vs weekday breakouts (Yahoo daily; candle dated Sat/Sun = signal at the Sun/Mon 00:00 UTC close)

| label | n | avgR | t | win | totR |
|---|---|---|---|---|---|
| Mon-Fri candle | 62 | 0.776 | 2.98 | 0.48 | 48.1 |
| Sat/Sun candle | 13 | 0.973 | 1.58 | 0.46 | 12.7 |
| Mon-Fri candle, 2015-2026 | 96 | 1.02 | 4.55 | 0.51 | 98.0 |
| Sat/Sun candle, 2015-2026 | 23 | 0.78 | 1.8 | 0.48 | 17.9 |
| rule taking weekday signals only, 2019-2026 | 72 | 0.814 | 3.35 | 0.5 | 58.6 |
| BTC with weekend candles deleted (ETF-like), 2019-2026, 30-bar exit | 57 | 0.647 | 2.49 | 0.49 | 36.9 |
| same, 21-bar (~30 calendar days) exit | 66 | 0.542 | 2.3 | 0.47 | 35.8 |

By weekday of the signal candle (2019-2026):

| sig_time | count | mean |
|---|---|---|
| Friday | 10 | 0.988 |
| Monday | 14 | -0.601 |
| Saturday | 5 | 1.227 |
| Sunday | 8 | 0.814 |
| Thursday | 6 | 0.346 |
| Tuesday | 15 | 1.283 |
| Wednesday | 17 | 1.489 |

ETF-like BTC stop exits gapped through the stop at the open in 2 of 28 cases, mean gap 14 bp, max 259 bp.


### Task 5b: IBIT daily (2024-01-11 to 2026-11-23) vs BTC 24/7

| label | n | avgR | t | win | totR | first_signal_possible | stop_gaps | max_gap_bp |
|---|---|---|---|---|---|---|---|---|
| IBIT, 200-day SMA, 30-bar exit | 12 | 0.881 | 1.78 | 0.67 | 10.6 | 2024-10-25 | 2.0 | 87.0 |
| IBIT, 200-day SMA, 21-bar exit | 14 | 0.635 | 1.32 | 0.5 | 8.9 | 2024-10-25 | 2.0 | 87.0 |
| IBIT, 100-day SMA, 30-bar exit | 19 | 0.15 | 0.37 | 0.47 | 2.8 | 2024-06-04 | 4.0 | 1902.0 |
| IBIT, 100-day SMA, 21-bar exit | 20 | 0.445 | 1.06 | 0.5 | 8.9 | 2024-06-04 | 4.0 | 1902.0 |
| BTC-USD 24/7, same window from 2024-10-25 | 16 | 1.074 | 2.02 | 0.56 | 17.2 |  |  |  |
| BTC-USD 24/7, from 2024-06-04 (100-day IBIT window) | 21 | 0.574 | 1.28 | 0.43 | 12.1 |  |  |  |


### Task 6a: avg R, 2019-2026, spread in fixed $ per BTC round trip (historical prices, so early trades at $4-10k pay a lot) + swap per year on notional, no commission

| spread_usd | swap_0% | swap_10% | swap_20% | swap_30% |
|---|---|---|---|---|
| 10 | 0.833 | 0.769 | 0.704 | 0.639 |
| 20 | 0.826 | 0.761 | 0.696 | 0.632 |
| 40 | 0.811 | 0.746 | 0.681 | 0.617 |


### Task 6b: same, spread scaled to today's price ($61,211) i.e. charged as bp of price

| spread_usd | spread_bp_at_today | swap_0% | swap_10% | swap_20% | swap_30% |
|---|---|---|---|---|---|
| 10 | 1.6 | 0.838 | 0.774 | 0.709 | 0.644 |
| 20 | 3.3 | 0.836 | 0.771 | 0.707 | 0.642 |
| 40 | 6.5 | 0.831 | 0.766 | 0.701 | 0.637 |

Average holding period: 16.0 days; median stop distance 7.1% of price. Each 10%/yr of swap costs about 0.062R per trade on average.


### Task 6c: all-in expectancy, 2019-2026 Yahoo daily

| label | n | avgR | t | win | totR |
|---|---|---|---|---|---|
| claim-like: 10 bp/side, next open | 75 | 0.81 | 3.39 | 0.48 | 60.7 |
| CFD mid: $20 spread (today bp), 20% swap, 10 bp entry+stop slip | 75 | 0.684 | 2.89 | 0.48 | 51.3 |
| CFD bad: $40 spread (today bp), 30% swap, 25 bp entry+stop slip | 75 | 0.581 | 2.46 | 0.47 | 43.6 |
| CFD bad, fixed-$ spread on historical prices | 75 | 0.561 | 2.38 | 0.47 | 42.1 |

CFD mid case by year:

| sig_time | count | mean | sum |
|---|---|---|---|
| 2019 | 10 | 0.66 | 6.59 |
| 2020 | 12 | 1.67 | 19.99 |
| 2021 | 10 | -0.25 | -2.51 |
| 2022 | 6 | 0.73 | 4.37 |
| 2023 | 10 | 0.93 | 9.32 |
| 2024 | 14 | 0.19 | 2.7 |
| 2025 | 8 | -0.21 | -1.64 |
| 2026 | 5 | 2.5 | 12.52 |
