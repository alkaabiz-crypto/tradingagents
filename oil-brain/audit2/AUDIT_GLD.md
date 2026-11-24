# Audit: GLD pullback rule (SMA200 + RSI(2) < 10, 2/3 ATR stop and trail)

Auditor: independent re-implementation from the text description only (no reading of combo/brains/swarm/audit).
Data: Yahoo daily via yfinance, downloaded 2026-11-24 (`data/`), last full bar 2026-11-23 (today's partial bar dropped).
Code: `src/engine.py`, `src/run.py` (arg A or B), `src/extra.py`. Raw output: `out_A.txt`, `out_B.txt`. Trades: `trades_base_A.csv`, `trades_base_B.csv`.

## VERDICT: WEAK

The claim reproduces exactly, but the edge is fragile. It comes mostly from 3 trades in gold's 2019 and 2024-25 bull legs. Signals on a stop-out day are an undocumented choice, and handling them the other way removes about a quarter of the edge. Under a realistic retail CFD setup (0.02%/day financing) the result is no longer statistically meaningful (t 1.2 to 1.4). It also underperforms simply holding GLD.

## Reproduction and an ambiguity that matters

The description does not say whether a signal on the close of the day a stop was hit may be taken.

- **A**: ignore signals on the exit day. This gives 54 trades, +0.86R, t 2.08, and +0.72R / +0.95R for 2014-19 / 2020+, which matches the claim exactly. It is used as the base below.
- **B**: allow re-entry on the exit-day close, which a literal reading also permits ("flat by the close"). This gives 65 trades, +0.66R, t 1.91, and the non-overlapping placebo p rises from 0.018 to 0.16.

## 1. Base results (A; costs 5 bp/side; R = net P&L / (2 x ATR20 at signal))

| Period | Trades | Win | Avg R | t | Total R | Max DD (R) |
|---|---|---|---|---|---|---|
| 2006-2013 | 44 | 36% | +0.31 | 1.03 | +13.4 | 6.5 |
| 2014-2019 | 23 | 35% | +0.72 | 1.10 | +16.6 | 3.1 |
| 2020-now | 31 | 48% | +0.95 | 1.79 | +29.6 | 5.8 |
| 2014-now | 54 | 43% | +0.86 | 2.08 | +46.2 | 5.8 |
| (B) 2014-now | 65 | 42% | +0.66 | 1.91 | +43.2 | 8.3 |
| (B) 2006-2013 | 48 | 42% | +0.26 | 0.94 | +12.7 | 8.8 |

The pre-2014 out-of-sample period is positive but not significant: +0.31R, t 1.0. No trade was open at the end of the data.

## 2. Neighbours (2014-now; pass = avg R > 0 and t > 1.5; R unit kept at 2 x ATR for all)

| Variant | n | Avg R | t | Pass | 2006-13 avg R (t) |
|---|---|---|---|---|---|
| RSI<5 | 36 | +1.33 | 2.28 | yes | +0.73 (1.55) |
| RSI<15 | 65 | +0.78 | 2.20 | yes | +0.34 (1.16) |
| RSI<20 | 72 | +0.76 | 2.25 | yes | +0.55 (1.97) |
| RSI(3)<10 | 23 | +0.68 | 1.43 | **no** | -0.15 (-0.39) |
| SMA150 | 47 | +1.05 | 2.22 | yes | +0.31 (0.96) |
| SMA250 | 56 | +0.87 | 2.18 | yes | +0.22 (0.74) |
| Init stop 1.5 ATR | 57 | +0.81 | 2.10 | yes | +0.21 (0.75) |
| Init stop 2.5 ATR | 51 | +0.81 | 1.87 | yes | +0.31 (0.99) |
| Trail 2 ATR | 69 | +0.36 | 1.57 | yes (barely) | -0.02 (-0.09) |
| Trail 2.5 ATR | 65 | +0.46 | 1.78 | yes | +0.31 (1.19) |
| Trail 3.5 ATR | 49 | +0.90 | 2.09 | yes | +0.55 (1.29) |
| Trail 4 ATR | 43 | +0.73 | 1.69 | yes | +0.21 (0.53) |

**11 of 12 pass under A, and 10 of 12 under B** (B fails RSI(3) and trail 2). The parameter surface is smooth, so this does not look like a point overfit. But 2006-2013 is t < 2 for every neighbour, and below 1.0 for half of them.

## 3. Benchmarks

**(a) Buy-and-hold.** The rule is fully invested only while in a trade (about 41% of the time) and compounded per exit year.

| | 2006-now CAGR | 2014-now CAGR |
|---|---|---|
| GLD buy-and-hold | +9.3% | +8.5% |
| Rule (unlevered) | +5.6% | +6.8% |

The rule lost to buy-and-hold in 14 of 21 years. Its biggest wins were in 2011, 2019, 2024 and 2025. It mostly sat out 2013 (-28%) and 2015 (-11%). Its value is lower exposure, not higher return. Per-year figures are in `out_A.txt`, section 3a.

**(b) Random-entry placebo** (2014-now; entries on random days with close > SMA200; same stop, trail and costs; 500 runs):

- Mean R over every eligible day is **+0.48R**. Just being long gold above the SMA200 with this trailing exit earns most of the claimed edge.
- Non-overlapping, one position at a time (about 56 trades per run): placebo mean +0.51R, real +0.86R, **p = 0.018** (A) / **0.16** (B).
- Independent draws of N = 54 days: placebo mean +0.45R, **p = 0.11** (A) / 0.24 (B).
- The claimed p = 0.01 is only roughly reproduced, and only under A with the sequential design. The RSI filter adds about +0.35R over random timing.

**(c) Other instruments** (same rule, A):

| Instrument | 2006-13 avg R (t) | 2014-now n | 2014-now avg R | 2014-now t |
|---|---|---|---|---|
| IAU | +0.19 (0.70) | 52 | +0.76 | 1.79 |
| GC=F | +0.55 (1.64) | 50 | +0.40 | 1.44 |
| SLV | +0.62 (1.17) | 39 | +0.49 | 1.30 |

All are positive, but none reaches t 2 after 2014. GC=F is weaker after 2014, and its data quality is poor (see section 6).

## 4. Execution realism (GLD, A, 2014-now)

| Scenario | Avg R | t | Total R | Max DD |
|---|---|---|---|---|
| Base 5 bp | +0.86 | 2.08 | +46.2 | 5.8 |
| Entry delayed 1 day | +0.83 | 2.02 | +44.1 | 5.5 |
| 10 bp/side | +0.81 | 1.97 | +43.7 | 6.0 |
| 20 bp/side | +0.72 | 1.75 | +38.6 | 7.0 |
| **CFD financing 0.02%/day** | **+0.53** | **1.40** | +28.4 | 8.8 |
| Financing + 10 bp | +0.48 | 1.28 | +25.9 | 9.4 |
| Financing + 10 bp + 1-day delay | +0.46 | 1.21 | +24.3 | 10.2 |
| (B) Financing only | +0.37 | 1.16 | +23.9 | 12.1 |

- Trades last about 36 calendar days on average, because the trend-following trail keeps winners open. Financing therefore costs about **0.33R per trade**, roughly 40% of the edge.
- With financing, 2014-2019 falls to +0.34R (t 0.6) and 2006-2013 to +0.13R (t 0.45).
- Delay and spread costs alone are tolerable. Financing is what breaks it.

## 5. Regime dependence (A)

- 2014-now **excluding 2020-2025 entries**: 27 trades, +0.52R, t 0.93.
- 2006-now excluding 2020-2025: 71 trades, +0.39R, t 1.38.
- Top 3 trades of 2014-now (+12.9R, +11.8R, +8.5R, in 2019 and 2024-25) make up **33.2R of 46.2R (72%)**. Without them: 51 trades, +0.26R, t 1.09. Under B the share is 76%, and the remainder is +0.17R, t 0.81.
- R by entry year after 2014 (a dash means no trades that year):

| Year | 14 | 15 | 16 | 17 | 18 | 19 | 20 | 21 | 22 | 23 | 24 | 25 | 26 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Sum R | -2.0 | - | +2.3 | -0.6 | -1.2 | +18.2 | +1.7 | -3.3 | -1.4 | +1.2 | +13.9 | +19.9 | -2.5 |

- 7 of 12 traded years are at or below +1.3R. 2026 so far is -2.5R over 4 trades.
- 2024-now alone: 13 trades, +2.41R. The headline figure is a 2024-25 gold bull-run artefact on top of a modest base.

## 6. Data checks

- GLD: raw and auto-adjusted closes are identical. There are no splits and no distributions (expected: the expense ratio is taken from NAV). No NaN rows, no OHLC inconsistencies, no non-positive prices.
- Missing weekdays: 205 over 22 years, which is the exchange-holiday count. The two gaps of 5 days are 2007-01-02 (the Ford national day of mourning) and Oct 2012 (Hurricane Sandy), both real closures.
- IAU had splits on 2010-06-24 (10:1) and 2021-05-24 (1:2 reverse), and SLV on 2008-07-24 (10:1). Yahoo's OHLC is already split-adjusted (raw = adj, no jumps), and R is scale-free, so there is no impact.
- GC=F is an unadjusted continuous front month with **386 OHLC-inconsistent rows** (High below the open or close, or Low above them; stale opens). There are 25 overnight gaps above 3%, mostly 2006-2009, some of which coincide with rolls. Opens and lows drive both the stops and the entry fill, so the GC=F results are low-confidence. Gold's roll gaps are small (contango below 1%), so the RSI(2) contamination is minor.

## Bottom line

- **Mechanics**: the rule is reproducible and smoothly parameterised.
- **Source of returns**: most of the return is gold beta plus a trend-following exit (+0.48R for a random entry), and 72% of the R comes from three bull-run trades.
- **Statistical weight**: the RSI timing increment (about +0.35R) is not robust to an implementation detail (p 0.02 vs 0.16).
- **As a CFD**: 0.02%/day financing pushes it to +0.53R, t 1.4, which does not justify trading it as a standalone edge.
- **Better vehicle**: if traded at all, it should be through an unlevered ETF such as GLD or IAU, which carries no financing charge.
