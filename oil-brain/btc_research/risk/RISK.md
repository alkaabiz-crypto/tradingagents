# BTC breakout: risk study

Data: BTC-USD daily from Yahoo, 2014-09-17 to 2026-11-23 (file `replication/data/BTC-USD.csv`). The first signal is possible in April 2015, once the 200-day average exists.
Code: `bt.py` (backtest), `analyze.py` (splits, decay, live view), `mc.py` (Monte Carlo; `python3 mc.py 0.4` runs the stressed case).
Trade list: `trades_2015_now.csv` (130 trades; the last one is still open), with a copy in the Appendix.

## Rule as implemented

- Signal at the daily close (t). Trend: close above SMA200 allows longs only; close below allows shorts only.
- LONG if close > max(High[t-20..t-1]). SHORT if close < min(Low[t-20..t-1]).
- Entry at the open of t+1. Stop distance = 2 x ATR20, where ATR20 is the simple 20-day mean of true range at t. Target = 4 x the stop distance.
- Every bar from the entry bar onward is checked. If a bar touches both the stop and the target, the stop counts. A gap through a level fills at the open; this never happened, because BTC trades 24/7 and the open equals the prior close.
- Time exit at the close of the 30th bar, counting the entry bar. One position at a time. A new signal may come at the close of the exit day.
- Cost is 10 bp per side on notional. R = (signed move - 0.001 x (entry + exit)) / stop distance.

## 1. Headline check

| sample | n | avg R | median R | t | win % | total R | stop / target / time |
|---|---|---|---|---|---|---|---|
| All closed trades, 2015-now | 129 | **0.92** | -0.07 | 4.83 | 49% | 118.1 | 48 / 26 / 26% |
| 2019-now | 80 | **0.76** | -0.67 | **3.29** | 46% | 60.7 | 50 / 20 / 30% |
| 2019-2025 only | 74 | 0.70 | -0.67 | 3.00 | 46% | 51.9 | 50 / 18 / 32% |
| Claimed, 2019-2026 | 74 | 0.79 | | 3.28 | | | |

**The headline is confirmed to within rounding.**
- 2019-now: 80 closed trades at +0.76R with t 3.29. Counting the open trade at its mark, the figures are 81 trades, +0.78R and t 3.40.
- 2019-2025: exactly 74 trades, but at +0.70R and t 3.0.
- The claim probably ran 2019 to mid or late 2026 with slightly different bookkeeping.
- Changing the time exit to 29 or 31 bars moves avg R by about 0.04 or less.
- Open position: a SHORT entered 2026-11-13 at 71,343, marked at +2.24R on 2026-11-23.

## 2. Where the edge comes from

### Long vs short

| group | n | avg R | median R | t | win % | total R |
|---|---|---|---|---|---|---|
| 2015-now LONG | 91 | **1.20** | 0.85 | **5.11** | 53% | 109.4 |
| 2015-now SHORT | 38 | 0.23 | -1.02 | 0.80 | 39% | 8.7 |
| 2019-now LONG | 54 | **0.99** | 0.38 | **3.40** | 50% | 53.3 |
| 2019-now SHORT | 26 | 0.29 | -1.02 | 0.78 | 38% | 7.4 |

**The edge comes from the long side.** Shorts contribute 7% of total R and are not statistically different from zero (t 0.8).

### Bull vs bear years

A year counts as bull or bear by the sign of BTC's calendar-year return. Bear years: 2018, 2022, 2025 and 2026 to date.

| group | n | avg R | t | win % | total R |
|---|---|---|---|---|---|
| Bull years | 98 | 1.05 | 4.66 | 49% | 102.8 |
| Bull years, LONG | 81 | **1.35** | 5.37 | 56% | 109.3 |
| Bull years, SHORT | 17 | -0.38 | -1.09 | 18% | -6.4 |
| Bear years | 31 | 0.49 | 1.47 | 48% | 15.3 |
| Bear years, LONG | 10 | 0.02 | 0.03 | 30% | 0.2 |
| Bear years, SHORT | 21 | 0.72 | 1.75 | 57% | 15.1 |

The trend filter mostly does its job. Shorts help in real bear years such as 2018, 2022 and 2026, and lose in bull years. Bull-year longs are the core of the edge.

### Sub-periods (Liu & Tsyvinski published in 2021)

| period | n | avg R | t | win % | LONG avg R (n) | SHORT avg R (n) |
|---|---|---|---|---|---|---|
| 2015-2018 | 49 | **1.17** | 3.58 | 53% | 1.52 (37) | 0.10 (12) |
| 2019-2021 | 33 | **1.03** | 2.77 | 52% | 1.37 (24) | 0.12 (9) |
| 2022-now | 47 | **0.57** | 1.94 | 43% | 0.68 (30) | 0.37 (17) |

After publication, expectancy roughly halved, from about 1.1R to 0.57R, and it is no longer significant at 5% (t 1.94). The edge is still positive. The long side fell the most, from about 1.4R to 0.7R. Since 2022, shorts are about as weak as before, with only 17 trades.

### By year

| year | BTC return | n | avg R | total R | win % |
|---|---|---|---|---|---|
| 2015 | +34% | 11 | 1.08 | 11.9 | 45% |
| 2016 | +124% | 16 | 1.64 | 26.3 | 62% |
| 2017 | +1369% | 12 | 1.39 | 16.6 | 50% |
| 2018 | -74% | 10 | 0.26 | 2.6 | 50% |
| 2019 | +92% | 11 | 0.87 | 9.6 | 45% |
| 2020 | +303% | 12 | **2.18** | 26.1 | 75% |
| 2021 | +60% | 10 | **-0.18** | -1.8 | 30% |
| 2022 | -64% | 6 | 0.90 | 5.4 | 67% |
| 2023 | +155% | 10 | 1.15 | 11.5 | 60% |
| 2024 | +121% | 16 | 0.16 | 2.6 | 25% |
| 2025 | -6% | 9 | **-0.16** | -1.5 | 33% |
| 2026 YTD | -30% | 6 | 1.47 | 8.8 | 50% |

Two of the last six years (2021 and 2025) lost money, and 2024 was roughly flat despite BTC more than doubling. Results depend heavily on a few trending years: 2016, 2020 and 2023.

### Exit reasons

| period | exit | share | avg R | avg days |
|---|---|---|---|---|
| 2015-now | stop | 48% | -1.03 | 9.1 |
| 2015-now | target | 26% | +3.95 | 11.6 |
| 2015-now | time | 26% | +1.53 | 30 |
| 2019-now | stop | 50% | -1.03 | 9.6 |
| 2019-now | target | 20% | +3.96 | 11.1 |
| 2019-now | time | 30% | +1.61 | 30 |
| 2022-now | stop | 55% | -1.03 | 9.0 |
| 2022-now | target | 17% | +3.96 | 12.2 |
| 2022-now | time | 28% | +1.69 | 30 |

- 30 of the 34 time exits were winners, and the worst was -0.34R. The 30-day exit catches trends that did not reach 4R; it is not a dead-money exit.
- The decline since 2022 shows up as more stops (55%) and fewer targets (17%).
- Concentration, 2019-now: the top 5 trades make up 33% of total R and the top 10 make up 65%. Without the top 10, average R is +0.30.

## 3. Monte Carlo (2019-now, 80 closed trades, 10 trades per year)

Setup:
- Equity compounds as equity x (1 + risk x R) at each trade close.
- 1 year = 10 trades and 3 years = 30 trades, which matches the 10.1 trades per year seen since 2019.
- 10,000 resamples each for an IID bootstrap and a circular block bootstrap (blocks of 5 trades, which keeps losing clusters together).
- Drawdowns are measured on closed-trade equity. Open-trade swings make the real figures somewhat worse.

### Base case (historical R, mean +0.76)

The IID and block results are almost the same. Block figures are shown; IID is in `mc_out.txt`.

| risk/trade | 1y return p5 / median / p95 | P(1y loss) | 3y return p5 / median / p95 | 3y maxDD median / p95 / p99 | P(DD>20%) | P(DD>30%) | P(DD>50%) |
|---|---|---|---|---|---|---|---|
| 0.5% | -2% / +3% / +10% | 14% | +2% / +12% / +24% | 2% / 5% / 6% | 0% | 0% | 0% |
| 1% | -3% / +7% / +22% | 15% | +3% / +24% / +53% | 5% / 9% / 12% | 0% | 0% | 0% |
| 2% | -7% / +14% / +47% | 15% | +5% / +52% / +130% | 9% / 17% / 22% | 2.0% | 0.1% | 0% |
| 3% | -10% / +21% / +76% | 16% | +7% / +85% / +239% | 13% / 25% / 31% | 12.9% | 1.4% | 0% |

Longest run of consecutive losers, over 1 year: median 3, 95th percentile 6. Over 3 years: median 4, 95th percentile 8, 99th percentile 11. The worst historical run is 9 (both 2015-now and 2019-now).

### Stress case (every R cut by 0.4, giving mean +0.36, close to the last 30 trades' +0.36)

This case matters more for anyone starting today.

| risk/trade | 1y return p5 / median / p95 | P(1y loss) | 3y return p5 / median / p95 | P(3y loss) | 3y maxDD median / p95 / p99 | P(DD>20%) | P(DD>30%) | P(DD>50%) |
|---|---|---|---|---|---|---|---|---|
| 0.5% | -4% / +1% / +8% | 33% | -4% / +5% / +17% | 20% | 4% / 8% / 10% | 0% | 0% | 0% |
| 1% | -7% / +3% / +17% | 34% | -9% / +10% / +36% | 20% | 7% / 15% / 18% | 0.4% | 0% | 0% |
| 2% | -14% / +5% / +36% | 35% | -17% / +20% / +82% | 22% | 14% / 28% / 34% | 21% | 2.7% | 0% |
| 3% | -21% / +7% / +57% | 36% | -26% / +29% / +139% | 23% | 21% / 39% / 47% | 54% | 18% | 0.4% |

Under stress, longest losing run over 3 years: median 5, 95th percentile 10.

### Kelly

| R set | full Kelly | half | quarter |
|---|---|---|---|
| 2019-now (mean 0.76) | 25.6% | 12.8% | 6.4% |
| Stressed (mean 0.36) | 9.6% | 4.8% | 2.4% |

Kelly here is mechanically huge because the payoff is skewed: wins average about 2.8R and losses about -1R. It assumes the 80-trade sample is the true distribution, and it is not. The edge already fell by half after publication. Even half-Kelly on the stressed numbers (4.8%) gives a 3-year 95th-percentile drawdown above 40%.

### Recommendation

| account | risk per trade |
|---|---|
| Demo, and the first 20 real trades | **0.5%** |
| Small real account, steady state | **1%** (never above 2%) |

- At 1%, the base case gives a 3-year median of about +24%, a 95th-percentile drawdown of 9%, and essentially no chance of a 20% drawdown.
- Under stress, 1% still keeps the 99th-percentile drawdown under 20%. The cost is a one-in-three chance of a losing year.
- At 2%, a 20% drawdown has roughly a one-in-five chance if the recent edge (about 0.36R) is the true one.
- 1% is roughly quarter-Kelly of the stressed case.
- Position size at 1% risk is about 14% of equity in BTC (median stop is 7.1% of price), and at most 32% (tightest stop 3.1%). No leverage is needed below 3% risk.

## 4. Expectancy decay

Rolling 20-trade average R, sampled every 5 trades (the date is the exit of the last trade in the window):

| window ending | 20-trade avg R |
|---|---|
| 2016-12 | 1.74 |
| 2017-09 | 1.76 |
| 2018-09 | 0.97 |
| 2019-12 | 0.66 |
| 2020-12 | 1.40 |
| 2021-10 | 1.17 |
| 2022-05 | 1.24 |
| 2023-02 | 0.72 |
| 2023-09 | 0.35 |
| 2024-06 | 0.91 |
| 2024-09 | 0.36 |
| 2025-02 | 0.47 |
| 2025-08 | 0.20 |
| 2026-02 | **0.02** |
| 2026-10 (latest) | 0.51 |

- **The edge is fading.** The rolling average peaked around 1.7R in 2016-17 and has stayed below about 0.9 since 2023. It reached about zero in February 2026 and has partly recovered to 0.51.
- An OLS fit of R on trade number gives -0.008R per trade (t -1.64). The fitted expectancy falls from 1.45R at the first trade to 0.39R at the latest.
- First half of trades: +1.09R (t 3.9). Second half: +0.74R. Last 30 trades: +0.36R (t 0.97, not significant).
- Only 3% of 20-trade windows were ever below zero, so the edge has not disappeared. It is weaker now and cannot yet be told apart from zero.

## 5. What a trader would see live (2019-now)

| item | value |
|---|---|
| Trades per year | 10.1 on average (range 6-16 per year) |
| Days between entries | mean 33, median 30, longest 106 |
| Flat days between exit and next entry | mean 18.5, median 10, 90th percentile 46 |
| Time in a position | 45% of days |
| Calendar months with no position at all | about 1.6 per year |
| Calendar months with no new entry | about 3.9 per year (7 in 2022) |
| Days held | median 11, mean 16 |
| Winners (46%) | mean +2.77R, median +3.0R. 16 of 37 are full +3.96R targets; the rest are time exits averaging +1.6R |
| Losers (54%) | mean -0.97R, median -1.03R. Almost all are full stops; only 3 small losses came from time exits |
| Stop distance | median 7.1% of price (range 3.1%-23%) |

In practice: about one trade a month. More than half are full 1R losses within about 9 days. The occasional 4R winner pays for them. Runs of 4-6 straight losses are normal in any given year. A year can easily end flat or down (2021, 2024 and 2025 did), even when BTC itself rallied.

## Verdict

- **The rule is real but weakening, and the edge is long-only.** The published figures reproduce (+0.76R, t 3.3 on 2019-now).
- The edge is concentrated in long trades during bull years and in a handful of 4R winners. Shorts add little (t 0.8).
- Since publication (2022-now), expectancy has halved to +0.57R (t 1.9). The last 30 trades average +0.36R and are not statistically significant.
- The fat-tailed payoff of about +2.8R wins against -1R losses keeps drawdowns modest at small risk. That makes the rule acceptable to trade small. It does not justify large size.
- **Trade it at 0.5% risk on demo or a new account, and at most 1% after about 20 live trades.** Treat 2% as the absolute cap.
- Consider running the long side only, or shorts at half size.
- Stop trading the rule if the rolling 20-trade average R stays below zero, or if the account draws down more than 15% at 1% risk. Under the stress case that has about a 5% chance of happening over 3 years.

## Appendix: full trade list (2015-now)

| # | entry | exit | side | entry px | exit px | stop % | R | days | exit |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 2015-04-11 | 2015-05-10 | SHORT | 236 | 240 | 7.98 | -0.25 | 30 | time |
| 2 | 2015-06-01 | 2015-06-15 | SHORT | 230 | 237 | 2.87 | -1.07 | 15 | stop |
| 3 | 2015-06-30 | 2015-07-11 | LONG | 257 | 298 | 4.02 | +3.95 | 12 | target |
| 4 | 2015-07-13 | 2015-07-13 | LONG | 311 | 293 | 5.86 | -1.03 | 1 | stop |
| 5 | 2015-08-19 | 2015-09-06 | SHORT | 226 | 241 | 6.91 | -1.03 | 19 | stop |
| 6 | 2015-10-07 | 2015-10-17 | LONG | 246 | 273 | 2.76 | +3.92 | 11 | target |
| 7 | 2015-10-18 | 2015-10-18 | LONG | 271 | 262 | 3.19 | -1.06 | 1 | stop |
| 8 | 2015-10-23 | 2015-10-29 | LONG | 274 | 317 | 3.96 | +3.94 | 7 | target |
| 9 | 2015-10-30 | 2015-11-03 | LONG | 314 | 376 | 4.92 | +3.96 | 5 | target |
| 10 | 2015-11-04 | 2015-11-06 | LONG | 404 | 374 | 7.35 | -1.03 | 3 | stop |
| 11 | 2015-12-06 | 2016-01-04 | LONG | 390 | 433 | 6.74 | +1.63 | 30 | time |
| 12 | 2016-02-15 | 2016-03-15 | LONG | 408 | 417 | 4.59 | +0.45 | 30 | time |
| 13 | 2016-03-28 | 2016-03-29 | LONG | 427 | 416 | 2.39 | -1.08 | 2 | stop |
| 14 | 2016-04-16 | 2016-04-25 | LONG | 430 | 465 | 2.04 | +3.90 | 10 | target |
| 15 | 2016-04-26 | 2016-04-27 | LONG | 462 | 451 | 2.38 | -1.08 | 2 | stop |
| 16 | 2016-05-28 | 2016-05-28 | LONG | 473 | 522 | 2.59 | +3.92 | 1 | target |
| 17 | 2016-05-29 | 2016-06-11 | LONG | 527 | 599 | 3.41 | +3.94 | 14 | target |
| 18 | 2016-06-12 | 2016-06-16 | LONG | 610 | 764 | 6.34 | +3.96 | 5 | target |
| 19 | 2016-06-17 | 2016-06-21 | LONG | 768 | 707 | 8.03 | -1.02 | 5 | stop |
| 20 | 2016-09-04 | 2016-10-03 | LONG | 599 | 612 | 2.42 | +0.85 | 30 | time |
| 21 | 2016-10-08 | 2016-10-22 | LONG | 617 | 652 | 1.39 | +3.85 | 15 | target |
| 22 | 2016-10-23 | 2016-10-29 | LONG | 658 | 708 | 1.91 | +3.89 | 7 | target |
| 23 | 2016-10-30 | 2016-10-31 | LONG | 714 | 695 | 2.74 | -1.07 | 2 | stop |
| 24 | 2016-11-02 | 2016-11-03 | LONG | 730 | 707 | 3.18 | -1.06 | 2 | stop |
| 25 | 2016-12-02 | 2016-12-22 | LONG | 758 | 871 | 3.76 | +3.94 | 21 | target |
| 26 | 2016-12-23 | 2016-12-28 | LONG | 865 | 957 | 2.66 | +3.92 | 6 | target |
| 27 | 2016-12-29 | 2016-12-30 | LONG | 975 | 936 | 4.02 | -1.05 | 2 | stop |
| 28 | 2017-01-02 | 2017-01-05 | LONG | 999 | 950 | 4.86 | -1.04 | 4 | stop |
| 29 | 2017-02-01 | 2017-02-24 | LONG | 971 | 1,193 | 5.71 | +3.96 | 24 | target |
| 30 | 2017-03-02 | 2017-03-08 | LONG | 1,225 | 1,162 | 5.14 | -1.04 | 7 | stop |
| 31 | 2017-04-07 | 2017-05-06 | LONG | 1,179 | 1,579 | 10.02 | +3.36 | 30 | time |
| 32 | 2017-05-09 | 2017-05-21 | LONG | 1,724 | 2,095 | 5.38 | +3.96 | 13 | target |
| 33 | 2017-05-23 | 2017-05-27 | LONG | 2,192 | 1,968 | 10.19 | -1.02 | 5 | stop |
| 34 | 2017-06-07 | 2017-06-14 | LONG | 2,869 | 2,444 | 14.83 | -1.01 | 8 | stop |
| 35 | 2017-08-06 | 2017-09-02 | LONG | 3,258 | 4,951 | 12.99 | +3.98 | 28 | target |
| 36 | 2017-10-02 | 2017-10-31 | LONG | 4,396 | 6,468 | 13.24 | +3.54 | 30 | time |
| 37 | 2017-11-01 | 2017-11-12 | LONG | 6,441 | 5,768 | 10.45 | -1.02 | 12 | stop |
| 38 | 2017-11-17 | 2017-12-06 | LONG | 7,854 | 12,082 | 13.46 | +3.98 | 20 | target |
| 39 | 2017-12-07 | 2017-12-22 | LONG | 14,266 | 12,756 | 10.58 | -1.02 | 16 | stop |
| 40 | 2018-02-06 | 2018-02-14 | SHORT | 7,052 | 9,437 | 33.83 | -1.01 | 9 | stop |
| 41 | 2018-02-21 | 2018-03-09 | LONG | 11,372 | 9,327 | 17.98 | -1.01 | 17 | stop |
| 42 | 2018-03-15 | 2018-04-13 | SHORT | 8,291 | 7,896 | 18.44 | +0.25 | 30 | time |
| 43 | 2018-05-12 | 2018-06-10 | SHORT | 8,441 | 6,786 | 10.06 | +1.93 | 30 | time |
| 44 | 2018-06-11 | 2018-07-10 | SHORT | 6,799 | 6,330 | 8.39 | +0.80 | 30 | time |
| 45 | 2018-08-08 | 2018-09-04 | SHORT | 6,747 | 7,362 | 9.12 | -1.02 | 28 | stop |
| 46 | 2018-09-09 | 2018-09-21 | SHORT | 6,223 | 6,686 | 7.44 | -1.03 | 13 | stop |
| 47 | 2018-10-12 | 2018-10-15 | SHORT | 6,239 | 6,507 | 4.28 | -1.05 | 4 | stop |
| 48 | 2018-11-15 | 2018-11-20 | SHORT | 5,736 | 4,768 | 4.22 | +3.96 | 6 | target |
| 49 | 2018-11-21 | 2018-12-20 | SHORT | 4,466 | 4,134 | 9.35 | +0.77 | 30 | time |
| 50 | 2019-01-14 | 2019-02-12 | SHORT | 3,557 | 3,654 | 8.62 | -0.34 | 30 | time |
| 51 | 2019-04-03 | 2019-05-02 | LONG | 4,880 | 5,505 | 4.31 | +2.92 | 30 | time |
| 52 | 2019-05-04 | 2019-05-11 | LONG | 5,769 | 6,974 | 5.22 | +3.96 | 8 | target |
| 53 | 2019-05-12 | 2019-06-10 | LONG | 7,204 | 8,000 | 6.28 | +1.73 | 30 | time |
| 54 | 2019-06-21 | 2019-06-26 | LONG | 9,525 | 12,347 | 7.41 | +3.97 | 6 | target |
| 55 | 2019-06-27 | 2019-06-27 | LONG | 13,017 | 11,965 | 8.08 | -1.02 | 1 | stop |
| 56 | 2019-08-06 | 2019-08-14 | LONG | 11,812 | 10,797 | 8.59 | -1.02 | 9 | stop |
| 57 | 2019-09-27 | 2019-10-26 | SHORT | 8,113 | 8,734 | 7.65 | -1.03 | 30 | stop |
| 58 | 2019-10-27 | 2019-11-15 | LONG | 9,242 | 8,554 | 7.44 | -1.03 | 20 | stop |
| 59 | 2019-11-16 | 2019-12-15 | SHORT | 8,491 | 7,152 | 6.33 | +2.46 | 30 | time |
| 60 | 2019-12-18 | 2019-12-18 | SHORT | 6,648 | 7,120 | 7.11 | -1.03 | 1 | stop |
| 61 | 2020-01-29 | 2020-02-26 | LONG | 9,357 | 8,776 | 6.22 | -1.03 | 29 | stop |
| 62 | 2020-03-09 | 2020-03-12 | SHORT | 8,111 | 5,442 | 8.23 | +3.98 | 4 | target |
| 63 | 2020-03-13 | 2020-03-19 | SHORT | 5,018 | 5,966 | 18.9 | -1.01 | 7 | stop |
| 64 | 2020-04-30 | 2020-05-29 | LONG | 8,798 | 9,439 | 6.34 | +1.12 | 30 | time |
| 65 | 2020-06-02 | 2020-06-11 | LONG | 10,163 | 9,394 | 7.57 | -1.02 | 10 | stop |
| 66 | 2020-07-23 | 2020-07-27 | LONG | 9,527 | 10,738 | 3.18 | +3.93 | 5 | target |
| 67 | 2020-07-28 | 2020-08-26 | LONG | 11,017 | 11,488 | 3.89 | +1.05 | 30 | time |
| 68 | 2020-10-11 | 2020-10-27 | LONG | 11,296 | 13,416 | 4.69 | +3.95 | 17 | target |
| 69 | 2020-10-28 | 2020-11-16 | LONG | 13,654 | 16,610 | 5.41 | +3.96 | 20 | target |
| 70 | 2020-11-17 | 2020-12-16 | LONG | 16,686 | 21,311 | 8.48 | +3.24 | 30 | time |
| 71 | 2020-12-17 | 2020-12-27 | LONG | 21,308 | 28,112 | 7.98 | +3.97 | 11 | target |
| 72 | 2020-12-31 | 2021-01-07 | LONG | 28,842 | 39,265 | 9.04 | +3.97 | 8 | target |
| 73 | 2021-01-08 | 2021-01-11 | LONG | 39,382 | 35,162 | 10.71 | -1.02 | 4 | stop |
| 74 | 2021-02-07 | 2021-03-08 | LONG | 39,250 | 52,247 | 14.21 | +2.31 | 30 | time |
| 75 | 2021-03-14 | 2021-03-24 | LONG | 61,221 | 53,098 | 13.27 | -1.01 | 11 | stop |
| 76 | 2021-04-14 | 2021-04-18 | LONG | 63,524 | 58,993 | 7.13 | -1.03 | 5 | stop |
| 77 | 2021-05-20 | 2021-06-18 | SHORT | 36,754 | 35,787 | 23.03 | +0.11 | 30 | time |
| 78 | 2021-07-20 | 2021-07-24 | SHORT | 30,838 | 33,795 | 9.59 | -1.02 | 5 | stop |
| 79 | 2021-08-10 | 2021-09-08 | LONG | 46,281 | 46,091 | 10.44 | -0.06 | 30 | time |
| 80 | 2021-09-21 | 2021-10-01 | SHORT | 43,012 | 47,901 | 11.37 | -1.02 | 11 | stop |
| 81 | 2021-10-06 | 2021-11-04 | LONG | 51,487 | 61,452 | 9.6 | +1.99 | 30 | time |
| 82 | 2021-11-09 | 2021-11-16 | LONG | 67,550 | 62,024 | 8.18 | -1.02 | 8 | stop |
| 83 | 2022-01-06 | 2022-02-04 | SHORT | 43,566 | 41,501 | 9.05 | +0.50 | 30 | time |
| 84 | 2022-04-12 | 2022-04-21 | SHORT | 39,534 | 42,567 | 7.67 | -1.03 | 10 | stop |
| 85 | 2022-04-27 | 2022-05-26 | SHORT | 38,120 | 29,267 | 7.77 | +2.96 | 30 | time |
| 86 | 2022-06-13 | 2022-07-12 | SHORT | 26,738 | 19,324 | 9.2 | +3.00 | 30 | time |
| 87 | 2022-08-20 | 2022-09-13 | SHORT | 20,873 | 22,598 | 8.27 | -1.02 | 25 | stop |
| 88 | 2022-11-09 | 2022-12-08 | SHORT | 18,544 | 17,233 | 7.0 | +0.98 | 30 | time |
| 89 | 2023-01-14 | 2023-01-20 | LONG | 19,911 | 22,368 | 3.09 | +3.93 | 7 | target |
| 90 | 2023-01-21 | 2023-02-10 | LONG | 22,677 | 21,599 | 4.76 | -1.04 | 21 | stop |
| 91 | 2023-02-16 | 2023-02-25 | LONG | 24,307 | 22,948 | 5.59 | -1.03 | 10 | stop |
| 92 | 2023-03-15 | 2023-04-13 | LONG | 24,771 | 30,399 | 7.39 | +3.04 | 30 | time |
| 93 | 2023-06-21 | 2023-07-20 | LONG | 28,311 | 29,792 | 6.07 | +0.83 | 30 | time |
| 94 | 2023-08-18 | 2023-08-29 | SHORT | 26,636 | 27,840 | 4.52 | -1.04 | 12 | stop |
| 95 | 2023-09-12 | 2023-09-12 | SHORT | 25,161 | 26,434 | 5.06 | -1.04 | 1 | stop |
| 96 | 2023-10-17 | 2023-10-23 | LONG | 28,522 | 33,964 | 4.77 | +3.95 | 7 | target |
| 97 | 2023-10-24 | 2023-11-22 | LONG | 33,077 | 37,432 | 5.34 | +2.42 | 30 | time |
| 98 | 2023-12-02 | 2023-12-31 | LONG | 38,689 | 42,265 | 6.05 | +1.49 | 30 | time |
| 99 | 2024-01-03 | 2024-01-03 | LONG | 44,962 | 42,192 | 6.16 | -1.03 | 1 | stop |
| 100 | 2024-01-09 | 2024-01-12 | LONG | 46,988 | 43,703 | 6.99 | -1.03 | 4 | stop |
| 101 | 2024-02-08 | 2024-02-26 | LONG | 44,332 | 53,693 | 5.28 | +3.96 | 19 | target |
| 102 | 2024-02-27 | 2024-03-04 | LONG | 54,519 | 67,506 | 5.96 | +3.96 | 7 | target |
| 103 | 2024-03-05 | 2024-03-05 | LONG | 68,341 | 63,889 | 6.51 | -1.03 | 1 | stop |
| 104 | 2024-03-12 | 2024-03-15 | LONG | 72,125 | 65,847 | 8.71 | -1.02 | 4 | stop |
| 105 | 2024-05-16 | 2024-06-14 | LONG | 66,256 | 66,011 | 7.88 | -0.07 | 30 | time |
| 106 | 2024-07-05 | 2024-07-14 | SHORT | 57,023 | 60,707 | 6.46 | -1.03 | 10 | stop |
| 107 | 2024-07-16 | 2024-08-03 | LONG | 64,784 | 60,099 | 7.23 | -1.03 | 19 | stop |
| 108 | 2024-08-05 | 2024-08-23 | SHORT | 58,110 | 63,234 | 8.82 | -1.02 | 19 | stop |
| 109 | 2024-08-24 | 2024-09-01 | LONG | 64,104 | 57,507 | 10.29 | -1.02 | 9 | stop |
| 110 | 2024-09-07 | 2024-09-13 | SHORT | 53,949 | 58,765 | 8.93 | -1.02 | 7 | stop |
| 111 | 2024-09-27 | 2024-10-01 | LONG | 65,181 | 61,135 | 6.21 | -1.03 | 5 | stop |
| 112 | 2024-10-16 | 2024-11-11 | LONG | 67,042 | 83,635 | 6.19 | +3.96 | 27 | target |
| 113 | 2024-11-12 | 2024-12-11 | LONG | 88,706 | 101,173 | 6.65 | +2.08 | 30 | time |
| 114 | 2024-12-16 | 2024-12-19 | LONG | 104,294 | 96,325 | 7.64 | -1.02 | 4 | stop |
| 115 | 2025-01-18 | 2025-02-02 | LONG | 104,125 | 97,024 | 6.82 | -1.03 | 16 | stop |
| 116 | 2025-04-07 | 2025-04-12 | SHORT | 78,221 | 84,254 | 7.71 | -1.03 | 6 | stop |
| 117 | 2025-04-23 | 2025-05-22 | LONG | 93,428 | 111,673 | 7.74 | +2.49 | 30 | time |
| 118 | 2025-05-23 | 2025-05-29 | LONG | 111,679 | 105,984 | 5.1 | -1.04 | 7 | stop |
| 119 | 2025-07-10 | 2025-08-08 | LONG | 111,329 | 116,689 | 4.55 | +1.01 | 30 | time |
| 120 | 2025-08-14 | 2025-08-14 | LONG | 123,339 | 118,043 | 4.29 | -1.05 | 1 | stop |
| 121 | 2025-09-17 | 2025-09-22 | LONG | 116,841 | 112,279 | 3.9 | -1.05 | 6 | stop |
| 122 | 2025-10-02 | 2025-10-10 | LONG | 118,652 | 114,222 | 3.73 | -1.05 | 9 | stop |
| 123 | 2025-11-05 | 2025-12-04 | SHORT | 101,579 | 92,142 | 7.25 | +1.26 | 30 | time |
| 124 | 2026-01-26 | 2026-02-05 | SHORT | 86,567 | 67,737 | 5.44 | +3.97 | 11 | target |
| 125 | 2026-02-06 | 2026-02-06 | SHORT | 62,704 | 70,216 | 11.98 | -1.02 | 1 | stop |
| 126 | 2026-05-23 | 2026-06-05 | SHORT | 75,488 | 60,165 | 5.07 | +3.96 | 14 | target |
| 127 | 2026-06-06 | 2026-06-14 | SHORT | 60,924 | 65,447 | 7.42 | -1.03 | 9 | stop |
| 128 | 2026-08-20 | 2026-08-25 | LONG | 69,268 | 80,387 | 4.01 | +3.95 | 6 | target |
| 129 | 2026-09-22 | 2026-10-08 | LONG | 86,604 | 81,874 | 5.46 | -1.04 | 17 | stop |
| 130 | 2026-11-13 | 2026-11-23 | SHORT | 71,343 | 61,211 | 6.25 | +2.24 | 11 | open |
