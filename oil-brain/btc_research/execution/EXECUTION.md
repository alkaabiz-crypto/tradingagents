# BTC breakout: how to execute it on a 24/7 CFD

Rule: daily close vs 200-day SMA sets direction. Go long on a close above the prior 20-day high, or short on a close below the prior 20-day low. Stop at 2x ATR(20), target at 4x the stop, exit after 30 days, one position at a time.
Data: Yahoo BTC-USD daily (2014 to 2026-11-23), Yahoo BTC-USD hourly (730 days, 2024-11-25 to 2026-11-24) and IBIT daily (2024-01-11 to 2026-11-23). Today's partial candle is dropped.
Code: `engine.py` holds the signal and the daily-bar and hourly-path simulators. `analysis.py` writes every table to `results/`.

## Baseline replication

| version | n | avg R | t | win | total R |
|---|---|---|---|---|---|
| Claimed, 2019-2026 | 74 | +0.79 | 3.28 | | |
| This replication, 10 bp/side | 75 | +0.810 | 3.39 | 0.48 | 60.7 |
| Same, no costs | 75 | +0.841 | 3.51 | 0.48 | 63.1 |

Details of the replication:
- ATR is a simple 20-day mean of true range.
- A signal on the same bar a trade exits is skipped. If it is taken instead, the result is 81 trades at +0.78R.
- Wilder ATR gives 74 trades at +0.82R.
- Longs: 51 trades at +0.94R. Shorts: 24 trades at +0.53R.
- Average hold is 16 days (median 11). The median stop distance is 7.1% of price.

All R figures below are per trade, after costs, for 2019-2026 unless noted.

## 1. Does it depend on the 00:00 UTC close?

Daily candles were rebuilt from hourly bars, closing at each of six times. Trend `_200` is the 200-day SMA of Yahoo 00:00 daily closes, taken as the latest value at each candle close. Trend `_100` is a 100-candle SMA computed on the shifted candles themselves; it only allows signals from April 2025. Cost is 10 bp per side.

| close (UTC) | n (200) | avg R (200) | t | total R | n (100) | avg R (100) | t |
|---|---|---|---|---|---|---|---|
| 00:00 | 14 | 0.861 | 1.51 | 12.1 | 15 | 0.847 | 1.55 |
| 04:00 | 15 | 0.713 | 1.31 | 10.7 | 15 | 0.821 | 1.52 |
| 08:00 | 15 | 0.735 | 1.33 | 11.0 | 14 | 0.920 | 1.65 |
| 12:00 | 14 | 0.818 | 1.46 | 11.5 | 14 | 0.749 | 1.38 |
| 16:00 | 14 | 0.872 | 1.52 | 12.2 | 15 | 0.845 | 1.62 |
| 20:00 | 14 | 0.755 | 1.38 | 10.6 | 16 | 0.706 | 1.35 |
| Yahoo daily 00:00 (reference) | 14 | 0.830 | 1.46 | 11.6 | | | |

**No, it does not depend on the 00:00 close.** All six close times are positive, ranging from +0.71R to +0.87R with a mean of +0.79R. The 00:00 close ranks 2nd of 6 under the 200-day trend and 3rd under the 100-day trend.

Limits of this test:
- Each close time has only about 14 trades, so no single row is significant (t about 1.3-1.6).
- The six rows are mostly the same breakouts caught a few hours apart. The test shows the rule is not fitted to the 00:00 close. It is not six independent confirmations.

## 2. Entry delay after the signal close

The stop and target are re-anchored to the actual fill price, using the ATR from the signal bar. The last 2 years use hourly prices. The older history is daily only, so only the 24h delay can be tested on it.

| sample | delay | n | avg R | t |
|---|---|---|---|---|
| 00:00 close, hourly path, 2y | 0h (at the close) | 14 | 0.855 | 1.49 |
| | 1h | 14 | 0.847 | 1.48 |
| | 4h | 14 | 0.816 | 1.44 |
| | 24h | 14 | 0.666 | 1.25 |
| All 6 close times pooled, hourly path, 2y | 0h | 86 | 0.780 | 3.53 |
| | 1h | 86 | 0.775 | 3.51 |
| | 4h | 86 | 0.754 | 3.46 |
| | 24h | 88 | 0.580 | 2.88 |
| Yahoo daily 2019-2026 | next open | 75 | 0.810 | 3.39 |
| | +24h (open of the day after) | 71 | 0.770 | 3.23 |

How much is lost by entering late:
- 1h late: almost nothing (about -0.01R).
- 4h late: about -0.03R.
- 24h late: -0.04R over 2019-2026, and -0.2R in the last 2 years.

On average, a 1h delay moves the fill 0.01R against you. A 24h delay moves it 0.1R against you, with a wide spread.

**Enter at, or within an hour of, the close.**

## 3. Bars where both stop and target were touched

| sample | trades | stop exits | bars touching both stop and target |
|---|---|---|---|
| Yahoo daily 2019-2026 | 75 | 36 | 0 |
| 2y candles, each of the 6 close times | 14-15 each | 7-8 each | 0 |
| Hourly bars inside the 2y trades | 14 | 7 | 0 |

The target is 8 ATR from entry and the stop is 2 ATR on the other side. No daily bar has ever spanned 10 ATR inside a trade, so the "assume the stop" tie-break never fires.

On the same 14 signals over 2 years, the daily-bar simulation and the hourly-path simulation agree on every exit reason:
- daily bars: +0.830R
- hourly path: +0.855R
- mean absolute difference per trade: 0.026R

The difference comes from the entry price, not from the order of exits. **This assumption has no effect on the result.**

## 4. Gaps and slippage

| sample | stop exits | gapped through the stop | typical overshoot beyond the stop |
|---|---|---|---|
| BTC daily 2019-2026 | 36 | 0 (24/7 market: each open = the prior close) | median low/high of the stop day: 130 bp beyond; median close of that day: 18 bp back inside the stop |
| Hourly, 6 close times pooled, 2y | 44 | 0 | extreme of the hour that hit the stop: median 25 bp, p90 82 bp. Close of that hour: median 8 bp back inside, p90 58 bp beyond |
| BTC with weekend candles deleted (ETF-like) | 28 | 2 | mean 14 bp, max 259 bp |
| IBIT, 100-day version | 4 gaps | | max 1,902 bp |

On a 24/7 instrument there are no session gaps, so the risk is the speed of the move within the hour, not gaps. A stop order on the CFD should fill within about 10-25 bp most of the time, and 50-80 bp in a fast hour (90th percentile).

Avg R with slippage on entries (rows) and on stop exits (columns), on top of 10 bp per side:

| entry slip \ stop slip | 0 | 10 bp | 25 bp | 50 bp |
|---|---|---|---|---|
| 0 | 0.810 | 0.803 | 0.793 | 0.776 |
| 10 bp | 0.795 | 0.788 | 0.778 | 0.760 |
| 25 bp | 0.772 | 0.765 | 0.755 | 0.737 |
| 50 bp | 0.733 | 0.726 | 0.716 | 0.699 |

The stop is 7.1% wide (median), so 10 bp of slippage costs only about 0.014R. Even 50 bp on both entries and stops leaves +0.70R. **Slippage is a minor issue for this rule.**

## 5. Weekends

Candles dated Saturday or Sunday close at 00:00 UTC on Sunday or Monday.

| subset | n | avg R | t |
|---|---|---|---|
| Mon-Fri signal candles, 2019-2026 | 62 | 0.776 | 2.98 |
| Sat/Sun signal candles, 2019-2026 | 13 | 0.973 | 1.58 |
| Mon-Fri, 2015-2026 | 96 | 1.020 | 4.55 |
| Sat/Sun, 2015-2026 | 23 | 0.780 | 1.80 |
| Rule taking weekday signals only, 2019-2026 | 72 | 0.814 | 3.35 |
| BTC with weekend candles deleted (ETF-like), 2019-2026, 30-bar exit | 57 | 0.647 | 2.49 |
| Same, 21-bar exit (about 30 calendar days) | 66 | 0.542 | 2.30 |

Avg R by weekday of the signal candle, 2019-2026:

| | Mon | Tue | Wed | Thu | Fri | Sat | Sun |
|---|---|---|---|---|---|---|---|
| n | 14 | 15 | 17 | 6 | 10 | 5 | 8 |
| avg R | -0.60 | 1.28 | 1.49 | 0.35 | 0.99 | 1.23 | 0.81 |

Weekend breakouts are neither clearly better nor clearly worse:
- They beat weekdays over 2019-2026 but trail them over 2015-2026.
- Both comparisons are within noise.
- The weak Monday bucket is 14 trades and is not something to trade on.

Removing the weekend data itself does hurt. The ETF-like BTC series earns +0.65R or +0.54R against +0.81R for the 24/7 series. Two reasons:
- it reacts late to weekend breakouts;
- it takes Monday gaps.

IBIT compared with 24/7 BTC over the same window:

| version | n | avg R | t | stop gaps |
|---|---|---|---|---|
| IBIT, 200-day SMA, 30-bar exit (from 2024-10-25) | 12 | 0.881 | 1.78 | 2 (max 87 bp) |
| IBIT, 200-day SMA, 21-bar exit | 14 | 0.635 | 1.32 | 2 |
| IBIT, 100-day SMA, 30-bar exit (from 2024-06-04) | 19 | 0.150 | 0.37 | 4 (max 1,902 bp) |
| IBIT, 100-day SMA, 21-bar exit | 20 | 0.445 | 1.06 | 4 |
| BTC-USD 24/7, from 2024-10-25 | 16 | 1.074 | 2.02 | 0 |
| BTC-USD 24/7, from 2024-06-04 | 21 | 0.574 | 1.28 | 0 |

The IBIT sample is too short to prove anything. Every IBIT variant trails BTC 24/7 over the same window, and only IBIT shows stop gaps. **The rule belongs on a 24/7 instrument**, which is a point in favour of the Exness CFD.

## 6. CFD costs: spread and swap

These replace the 10 bp per side commission. The spread is charged once per round trip. The swap is charged on notional for every day held, for both longs and shorts.

Spread in fixed dollars per BTC, applied at historical prices (harsh on 2019-2020 trades, when BTC was $4-10k):

| spread \ swap per year | 0% | 10% | 20% | 30% |
|---|---|---|---|---|
| $10 | 0.833 | 0.769 | 0.704 | 0.639 |
| $20 | 0.826 | 0.761 | 0.696 | 0.632 |
| $40 | 0.811 | 0.746 | 0.681 | 0.617 |

Spread scaled to today's price ($61,211). $10, $20 and $40 are 1.6, 3.3 and 6.5 bp:

| spread \ swap per year | 0% | 10% | 20% | 30% |
|---|---|---|---|---|
| $10 | 0.838 | 0.774 | 0.709 | 0.644 |
| $20 | 0.836 | 0.771 | 0.707 | 0.642 |
| $40 | 0.831 | 0.766 | 0.701 | 0.637 |

**The spread barely matters, because the stop is 7% wide. The swap is what counts.** Each 10% a year of swap costs about 0.065R per trade over the average 16-day hold.

All-in expectancy, 2019-2026:

| case | n | avg R | t | win | total R |
|---|---|---|---|---|---|
| Claim-like: 10 bp/side, next open | 75 | 0.810 | 3.39 | 0.48 | 60.7 |
| **CFD mid: $20 spread, 20% a year swap, 10 bp slippage on entries and stops** | 75 | **0.684** | 2.89 | 0.48 | 51.3 |
| CFD bad: $40 spread, 30% a year swap, 25 bp slippage | 75 | 0.581 | 2.46 | 0.47 | 43.6 |
| CFD bad, with the fixed-dollar spread at historical prices | 75 | 0.561 | 2.38 | 0.47 | 42.1 |

CFD mid case by year:

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|---|---|
| n | 10 | 12 | 10 | 6 | 10 | 14 | 8 | 5 |
| avg R | 0.66 | 1.67 | -0.25 | 0.73 | 0.93 | 0.19 | -0.21 | 2.50 |

There are two losing years (2021 and 2025) and the results are lumpy. That is normal for a trend rule with about 10 trades a year.

## Verdict: how to execute it on Exness BTCUSD

Execution is not where this rule breaks. Realistic CFD frictions take it from about +0.81R to about **+0.68R per trade** (+0.56R to +0.58R in a bad case), with t still above 2.4. Of that loss:
- about two thirds is the overnight swap;
- the spread, the slippage and the stop-versus-target tie-break each cost little or nothing.

How to run it:
1. **Use 00:00 UTC daily candles.** Exness terminals show GMT+0 server time, but check yours. Exness candles are built from its own quotes, not Yahoo's index, so expect small differences in the signals. Other close times work about as well, so the exact close hour is not critical; just keep it fixed.
2. **Act within the first hour after the close** with a market order. Do not wait for the next day: a 24h delay cost up to 0.2R in the last 2 years.
3. **Size from the fill price.** Set the stop at fill -/+ 2x ATR(20) from the signal bar and the target at 4x that distance. Place both as resting orders on the platform so they work over weekends and overnight.
4. **Take weekend signals.** They are not worse, and dropping weekend data (ETF-style) clearly hurts. Note that CFD spreads are often wider on weekends; this test shows a wider spread costs only about 0.01R.
5. **Check the swap before trading.** It is the main cost of carrying a position and it compounds with the 30-day time exit. At 30% a year the rule still holds +0.6R. If the broker's rate is much higher, or charged triple on some days, recompute with `analysis.py` (`swap_pa`). The 30-day time exit could also be shortened, but that was not tested here.
6. **Expect 8-15 trades a year, about 48% winners**, and losing years like 2021 and 2025. The edge rests on a few 4R targets, so do not skip signals.

What this study did not test: Exness's own historical quotes and its actual swap and spread history (the grids above stand in for them), and the time exit at 30 days, which is part of the rule. The 2-year hourly tests (tasks 1-3) have about 14 trades per variant, so they are for direction only.
