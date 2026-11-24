# BTC breakout: robustness review

Data: Yahoo BTC-USD daily, 2014-09-17 to 2026-11-23 (the partial 2026-11-24 bar is dropped). The prices match `../replication/data/BTC-USD.csv` exactly.
Code: `engine.py` (backtest), `analysis.py` (tasks 1 to 4), `null_test.py` (random-entry benchmark), `tables.py`.
Outputs: `results.json`, `grid_NxKxM.csv`, `one_at_a_time.csv`, `walkforward_trades.csv`, `null_results.json`, `tables_out.md` (every pivot table).
Periods are assigned by entry date. "New" = 2019-01-01 onward. "Old" = 2015 to 2018; it effectively starts in mid-2015, once the 200-day average exists.

## 1. Replication

The rule text leaves some details open. These are the choices made:
- The ATR is a 20-bar simple average of true range. Its window stays at 20 for every N.
- The channel uses highs and lows of bars t-20 to t-1.
- The time exit is at the close of the H-th bar held, counting the entry bar as bar 1.
- A new signal can fire on the close of the exit day.
- An opening gap through the stop fills at the open. BTC trades 24/7, so this never changes anything.
- The trade still open at the end of the data is marked at the last close.

| version | trades | avg R | t |
|---|---|---|---|
| **claimed 2019-2026** | 74 | +0.79 | 3.28 |
| as built, 2019 to 2026-11-23 | 81 | +0.78 | 3.40 |
| as built, closed trades only | 80 | +0.76 | 3.29 |
| no re-entry on the exit-day close | 75 | +0.81 | 3.39 |
| as built, ending 2025-12-31 | 74 | +0.70 | 3.00 |
| H = 29 / H = 31 | 81 / 80 | +0.74 / +0.78 | 3.28 / 3.34 |
| zero cost | 81 | +0.81 | 3.53 |
| Wilder ATR / EMA-200 / close-based channel | 83 / 89 / 94 | +0.72 / +0.72 / +0.60 | 3.19 / 3.36 / 2.94 |

**Result: confirmed within convention noise.** The average R and t match closely. The trade count differs (81 vs 74) because of the end date and the re-entry convention: a version with no re-entry on the exit day gives 75 trades at +0.81R. No single combination of conventions reproduced exactly 74 / 0.79 / 3.28, but every plausible reading lands at +0.70 to +0.81R with t from 3.0 to 3.4.

Base rule by year (2019 onward):

| year | trades | avg R | sum R |
|---|---|---|---|
| 2019 | 11 | 0.87 | 9.6 |
| 2020 | 12 | 2.18 | 26.1 |
| 2021 | 10 | -0.18 | -1.8 |
| 2022 | 6 | 0.90 | 5.4 |
| 2023 | 10 | 1.15 | 11.5 |
| 2024 | 16 | 0.16 | 2.6 |
| 2025 | 9 | -0.16 | -1.5 |
| 2026 | 7 | 1.58 | 11.0 |

The profit is concentrated:
- Removing 2020 leaves +0.53R, t 2.28.
- Taking only 2021 onward gives +0.47R, t 1.86.
- Removing the 5 best trades leaves +0.57R, t 2.54.

Long trades carry the result (2019+: longs +0.99R with t 3.4; shorts +0.36R with t 1.0). In 2015-18 the base made +1.17R with t 3.58 over 49 trades.

## 2. Parameter surface

Each one-at-a-time table changes one parameter and keeps the others at the base (N20, K2, M4, SMA200, H30).

| vary | values → avg R 2019+ (t) | avg R 2015-18 |
|---|---|---|
| N 10/15/20/30/40/55/80/100 | .52(2.7) .70(3.3) .78(3.4) .87(3.5) .94(3.7) .85(3.4) .67(2.7) .54(2.1) | .94 1.19 1.17 1.21 1.40 1.42 1.44 1.77 |
| K 1/1.5/2/2.5/3/4 | .44(2.2) .56(2.5) .78(3.4) .83(3.7) .69(3.3) .48(2.6) | 1.03 1.25 1.17 1.24 1.36 1.00 |
| M 2/3/4/6/8/trail | .42(3.0) .50(2.7) .78(3.4) .85(3.0) .96(3.0) .66(2.7) | .68 .93 1.17 1.79 1.85 1.68 |
| SMA none/50/100/150/200/300 | .65(3.5) .70(3.6) .75(3.7) .75(3.5) .78(3.4) .72(3.2) | .71 .80 .82 1.14 1.17 1.28 |
| H 10/20/30/60/none | .51(3.3) .71(3.4) .78(3.4) .70(2.7) .74(2.4) | 1.07 1.17 1.17 1.28 1.40 |

The trailing-stop row keeps H = 30. With no time exit, the trailing stop gives +0.69R (t 2.6) and +1.81R. Two-way tables for SMA x H and N x SMA (30 and 48 cells) are positive in every cell in both periods. Their minimum avg R is +0.36 in 2019+ and +0.55 in 2015-18 (see `tables_out.md`).

The coarse full grid is N x K x M = 8 x 6 x 6 = **288 configs**, all with SMA200 and H30. Cells show avg R for 2019+, averaged over the third axis:

| N \ K | 1 | 1.5 | 2 | 2.5 | 3 | 4 |
|---|---|---|---|---|---|---|
| 10 | .49 | .46 | .45 | .42 | .36 | .26 |
| 15 | .70 | .70 | .67 | .59 | .54 | .45 |
| 20 | .72 | .73 | .69 | .68 | .62 | .47 |
| 30 | .73 | .69 | .71 | .68 | .62 | .48 |
| 40 | .70 | .75 | .78 | .74 | .68 | .54 |
| 55 | .61 | .73 | .77 | .73 | .67 | .50 |
| 80 | .36 | .42 | .59 | .57 | .55 | .40 |
| 100 | .41 | .36 | .46 | .45 | .47 | .33 |

| N \ M | 2 | 3 | 4 | 6 | 8 | trail |
|---|---|---|---|---|---|---|
| 10 | .25 | .33 | .39 | .47 | .56 | .45 |
| 20 | .38 | .53 | .63 | .79 | .90 | .68 |
| 40 | .41 | .57 | .67 | .83 | .99 | .73 |
| 55 | .40 | .55 | .67 | .82 | .94 | .63 |
| 100 | .23 | .34 | .41 | .52 | .64 | .33 |

| grid statistic | 2019+ | 2015-18 |
|---|---|---|
| share with avg R > 0 | **100%** | **100%** |
| share with t > 2 | 75% | 100% |
| median avg R | +0.53 | +1.24 |
| min / max avg R | +0.04 / +1.24 | +0.44 / +4.41 |
| **positive in both periods** | **288/288 = 100%** | |
| correlation of avg R across the two periods | 0.72 | |
| base rule rank (2019+) | 63rd of 288, top 22% | |

**Smoothness:** the surface is smooth, with no isolated peak.
- N has a broad plateau from 15 to 55.
- K has a broad plateau from 1.5 to 3.
- R rises steadily with M. This is partly mechanical, because a larger target means larger winners measured in R.
- The base sits on the plateau but a little toward its favourable side: it ranks in the top quarter, not at the top.
- The weak region is short-ish stops with very long channels (N 80-100, K 1, M 2). It is still positive but has t < 1 in 2019+.

**Caveat: being positive is not the same as having an edge.** BTC drifted upward over both samples. Random entries in the trend direction with the same stop, target and time exits earned money on their own (1,000 random runs, `null_test.py`):

| | base breakout | random-entry null, median | null 95th pct | p(null ≥ base) |
|---|---|---|---|---|
| 2019+ | +0.78R (81) | +0.19R (85) | +0.38R | <0.001 |
| 2015-18 | +1.17R (49) | +0.77R (42) | +1.14R | 0.04 |

So "100% of the grid is positive" overstates the breakout's contribution. In 2015-18 about two thirds of the R came from simply being long in a bull market. The breakout entry adds roughly +0.6R per trade over random timing in 2019+ and roughly +0.4R in 2015-18.

## 3. Walk-forward (re-tuned every January, 4-year trailing window)

The menu has 12 configs: N {20,55} x K {2,3} x M {3,4,trail}, all with SMA200 and H30. Each January the config with the best average R is chosen, using only trades that both entered and exited in the trailing 4 years, with at least 15 trades. That config trades the next calendar year. Positions do not overlap across the year boundary.

| year | chosen | train avg R (n) | OOS trades | OOS avg R | OOS sum R | base trades | base avg R | base sum R |
|---|---|---|---|---|---|---|---|---|
| 2018 | N55 K2 trail | 2.16 (23) | 4 | 2.17 | 8.7 | 10 | 0.26 | 2.6 |
| 2019 | N55 K2 trail | 2.16 (27) | 8 | 0.69 | 5.6 | 11 | 0.87 | 9.6 |
| 2020 | N55 K3 M4 | 1.51 (28) | 8 | 0.98 | 7.9 | 12 | 2.18 | 26.1 |
| 2021 | N55 K2 M4 | 1.27 (33) | 8 | -0.17 | -1.4 | 10 | -0.18 | -1.8 |
| 2022 | N55 K2 M4 | 0.90 (30) | 5 | 0.13 | 0.6 | 6 | 0.90 | 5.4 |
| 2023 | N20 K2 M4 | 1.01 (39) | 10 | 1.15 | 11.5 | 10 | 1.15 | 11.5 |
| 2024 | N20 K2 M4 | 1.09 (38) | 16 | 0.16 | 2.6 | 16 | 0.16 | 2.6 |
| 2025 | N55 K3 M3 | 0.59 (29) | 4 | 0.23 | 0.9 | 9 | -0.16 | -1.5 |
| 2026 | N55 K2 M4 | 0.71 (27) | 5 | 1.61 | 8.0 | 7 | 1.58 | 11.0 |
| **2018-2026** | | | **68** | **+0.65 (t 2.47)** | **+44.4** | **91** | **+0.72 (t 3.40)** | **+65.6** |
| 2019-2026 only | | | 64 | +0.56 (t 2.38) | +35.7 | 81 | +0.78 | +63.0 |

An honest re-tuner would have made money: positive in 8 of 9 years, +44R in total. The re-tuner did worse than the fixed base rule (+44R vs +66R). Most of the gap comes from 2020: the re-tuner switched to N55 and caught 8 trades instead of 12.

The training-window average R fell steadily, from about 2.2 in 2018 to about 0.6-0.7 in 2025-26. Realized OOS R fell with it.

## 4. Overfitting statistics

**Deflated Sharpe Ratio** (Bailey & López de Prado 2014), base rule, 2019+, using the per-trade Sharpe:
- Per-trade Sharpe SR = 0.378 over T = 81 trades. Skew is +0.52 and kurtosis 1.58. Kurtosis is low because the R outcomes are bounded at about -1 and +4.
- PSR against 0 is 0.9999.
- Trials: **353 distinct configs** were evaluated in this study. Their per-trade Sharpe has variance 0.0072, mean 0.30 and max 0.50.
- Effective independent trials: the average pairwise correlation of daily R-pnl is 0.70, which gives N_eff ≈ 108.

| trials N | SR₀ (expected max under null) | DSR |
|---|---|---|
| 10 | 0.133 | 0.99 |
| 50 | 0.193 | 0.97 |
| 100 | 0.214 | 0.95 |
| 108 (effective) | 0.216 | **0.94** |
| 353 (all) | 0.249 | **0.90** |

The DSR passes at 0.90 to 0.95, but treat it with care:
- The trial variance is small because the configs are highly correlated and the whole grid shares the BTC-drift component.
- The DSR tests "Sharpe > 0", not "better than a random entry in a bull market".
- It is unknown how many rules the original author tried before reporting this one.

**PBO / CSCV** (Bailey et al. 2017): the matrix is daily R-pnl, the metric is Sharpe, the data is split into S = 16 blocks, giving 12,870 splits.

| set | configs | PBO | median logit | IS-best OOS ann. Sharpe (median) | IS-best positive OOS |
|---|---|---|---|---|---|
| N x K x M grid, 2015-06 to 2026-11 | 288 | **0.20** | +1.28 | 1.55 | 100% |
| N x K x M grid, 2019+ | 288 | **0.28** | +0.64 | 1.10 | 99.8% |
| all 353 trials, 2015-11 to 2026-11 | 353 | **0.39** | +0.55 | 1.40 | 100% |

PBO is 0.2 to 0.4, below 0.5. The in-sample winner usually ranks above the out-of-sample median, and it essentially never loses money out of sample. Selection adds little, because most of the grid performs similarly, but it does not destroy value either.

## Verdict

The published numbers are reproducible: +0.70 to +0.81R and t 3.0 to 3.4 under any reasonable reading, and the 74 vs 81 trade-count gap is a convention and end-date difference.

The rule is **not a fragile, curve-fit point**:
- Every one of the 288 grid configs and every one-way and two-way variation is positive in both 2015-18 and 2019+.
- The surface is a broad plateau around N 15-55 and K 1.5-3.
- The base is near the top quarter, not the peak.
- An honest annual re-tuner would have made +0.65R per trade out of sample.
- DSR ≈ 0.90-0.94 and PBO ≈ 0.2-0.4.

**Expect less than the headline.**
1. A large share of the R in every config comes from being long BTC during a secular bull market. Random entries in the trend direction with the same exits made +0.19R (2019+) and +0.77R (2015-18). The breakout-specific edge is about +0.4 to +0.6R per trade.
2. Returns are lumpy and fading. 2020 alone is 41% of the 2019+ R, and from 2021 onward the result is +0.47R with t 1.9. In-sample averages in the walk-forward fell from about 2R to about 0.6R.
3. The short side does not show an edge (+0.36R, t 1.0 in 2019+; +0.10R in 2015-18).

A realistic forward expectation is about +0.3 to +0.6R per trade at roughly 10 trades a year, conditional on BTC continuing to trend. The fixed base rule is as good a choice as any re-tuned variant.
