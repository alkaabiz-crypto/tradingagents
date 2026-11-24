# Independent audit of four tournament survivors

Auditor's own re-implementation. I read only `engine.py` (for the gate definitions). I did not open any brain code, results, swarm or study files.
Data: a fresh Yahoo download (`audit/data/*.csv`, yfinance 1.8.0, `auto_adjust=False`, so both raw `Close` and `Adj Close` are kept), through 2026-11-23. The 2026-11-24 crypto bar is dropped because it may be partial.
Convention: the position is set at the close of day t and earns close t to t+1. Cost = |change in position| x bp.
Sharpe uses sqrt(365) for crypto (7-day series) and sqrt(252) for ETFs. t = mean/sd x sqrt(n) on daily returns.
Scripts: `audit/audit.py` writes `results.txt` and `audit/extras.py` writes `extras.txt`. Every number below comes from those two files.

## Verdicts

| Rule | Verdict | One-line reason |
|---|---|---|
| A. BTC 28d-mom OR >SMA100 | **WEAK** | The returns are real, but the Sharpe matches buy-and-hold (1.09 vs 1.00; 2022+: 0.37 vs 0.37). Alpha t = 1.64. It cuts drawdowns but shows no edge. |
| B. ETH 28d-mom | **WEAK** (borderline reject) | t = 2.42. Negative in 2018-19. 60% of P&L comes from 5 months. Its "beat B&H" depends on the data starting at the Jan-2018 top. |
| C. HYG-LQD 63d -> USO L/S weekly | **REJECTED** | Luck from two episodes: 2010-2019 Sharpe is 0.06, and without 2020 and 2026 alpha t = 1.16. The 126d neighbour is 0.00. |
| D. IEF last-3-days of month | **WEAK** (real effect, small trade) | The effect is real (gross t = 5.39, placebo p = 0.000, known pre-sample). Net it is only 1.5%/yr, it breaks even at 11 bp/side, and a 1-day delay halves it. |

None of the four is CONFIRMED. None clears the tournament luck bar (t = 4.19) net of the stated costs. D clears it only gross or at a realistic 1-2 bp/side (t 4.9 / 4.4).

## Data and look-ahead checks (all rules)
- **Adjusted closes:** the repo CSVs hold Yahoo *adjusted* closes for HYG/LQD/IEF (they match my `Adj Close` to 2e-6, and differ from raw `Close` by 50-70%). USO pays no dividends. Crypto repo files differ from today's Yahoo by up to 0.35%, because Yahoo revises crypto bars. Using adjusted prices is correct and consistent.
- **Dividend timing for D:** IEF ex-dates fall on the first trading day of the month in 267 cases (nearly all), outside the window. On raw closes, IEF buy-and-hold drops from Sharpe 0.54 to 0.10, which would flatter the month-end rule *relative to holding*. With adjusted data the comparison is fair.
- **Duplicates, gaps, stale prices:** no duplicate dates. Gaps of 5 days or more occur only for the 2007-01-02 Ford funeral and Hurricane Sandy (Oct 2012). The longest zero-return run is 4 days (SHY), with up to 75 single zero days in HYG/LQD, mostly 2007-08. Nothing material.
- **USO 2020 restructuring:** the 1:8 reverse split on 2020-04-29 is correctly back-adjusted. The largest USO daily move is -25% on 2020-03-09, which is real. Caveat for C: in April 2020 USO borrow was scarce and expensive, and the rule was short through much of the crash, so C's best month is the least executable.
- **HYG inception:** HYG starts 2007-04-11, so C's first signal is 2007-07-13.
- **ETH:** Yahoo ETH-USD starts 2017-11-09, so "2014-2019" for ETH means 2018-2019 only. ETH is also picked with survivorship hindsight: it is the coin that stayed number two.
- **Crypto close timing:** Yahoo's crypto bar closes at 00:00 UTC. Next-day Open equals that Close within a median of 1.8 bp, so an order placed seconds after the signal fills at about the same price. A full 1-day delay leaves A unchanged (1.09 -> 1.10) and improves B (0.82 -> 0.92). There is no look-ahead in A or B.
- **ETF closes:** HYG, LQD and USO all close at 16:00 ET, so the signal is synchronous. Building C's signal from Thursday's data instead *raises* full-sample Sharpe to 0.59, so there is no look-ahead in C.

## A. BTC trend (28d return > 0 OR price > SMA100), 10 bp/side, 365-day annualisation

| Period | Rule Sh / CAGR / MDD / t | Buy & hold Sh / CAGR / MDD / t |
|---|---|---|
| Full 2014-12 to 2026-11 | 1.09 / 54.7% / -79.4% / 3.76 | 1.00 / 55.4% / -83.4% / 3.46 |
| 2014-2019 | 1.23 / 77.4% / -79.4% / 2.76 | 1.21 / 86.0% / -83.4% / 2.71 |
| 2020-now | 0.97 / 40.0% / -57.4% / 2.56 | 0.83 / 36.4% / -76.6% / 2.17 |
| 2022-now (post-publication) | 0.37 / 7.2% / -48.0% / 0.82 | 0.37 / 5.9% / -66.9% / 0.81 |

- **Alpha vs BTC** (regression on B&H): 15%/yr, t = 1.64 over the full sample. Since 2022 it is 3.9%/yr, t = 0.34. Beta is 0.65.
- **Stress tests** (Sharpe): delay1 1.10, 25 bp 1.02, both together 1.04. On sqrt(252) the full Sharpe would be 0.90.
- **Circular-shift placebo:** p = 0.07, so it fails the engine's 0.05 gate.
- **Neighbours:** all 29 momentum/SMA/OR variants (14-56d x 50-200d) have Sharpe 1.06-1.39 and all beat B&H. The chosen OR-combination sits near the *bottom* of that grid (mom28 alone: 1.36; sma50: 1.38). The trend effect is stable across parameters, but this particular rule is not special.
- **Regime:** ex-2020 Sharpe is 0.93 vs B&H 0.87. The 5 best months (four of them in 2017) supply 37% of P&L. Without them Sharpe is 0.76.
- **Verdict: WEAK.** This is a drawdown-control overlay on BTC, not an independent edge. Post-publication it earns the same Sharpe as holding.

## B. ETH trend (28d return > 0), 10 bp/side, 365-day annualisation

| Period | Rule Sh / CAGR / MDD / t | Buy & hold |
|---|---|---|
| Full 2018-02 to 2026-11 | 0.82 / 35.4% / -61.1% / 2.42 | 0.49 / 7.0% / -91.3% / 1.47 |
| 2018-2019 (data start) | -0.30 / -28.1% / -61.1% / -0.41 | -0.76 / -65.4% / -91.3% / -1.03 |
| 2020-now | 1.11 / 60.7% / -56.2% / 2.93 | 0.87 / 45.3% / -79.4% / 2.29 |
| 2022-now | 0.53 / 14.7% / -45.9% / 1.17 | 0.11 / -14.5% / -74.1% / 0.25 |

- **Alpha:** full 26.8%/yr, t = 1.95. Since 2022 it is t = 1.32.
- **Stress tests** (Sharpe): delay1 0.92, 25 bp 0.74, both together 0.84.
- **Placebo:** p = 0.01.
- **Neighbours:** Sharpe ranges 0.62 (mom21) to 0.97 (sma50). In 2022+ the range is 0.08 to 0.72.
- **Regime:** ex-2020 Sharpe is 0.55 (t 1.54). The 5 best months supply 60% of P&L. Without them Sharpe is 0.37 (t 1.06).
- **Overlap with A:** correlation with A's returns is 0.63, so A and B are largely one bet on crypto trend.
- **Verdict: WEAK.** The rule mostly sidesteps ETH's -91% drawdown, but its "advantage over B&H" depends on a sample that starts near the 2018 peak. t = 2.4 is far below the 4.19 bar. Forward-test only, and treat it as the same position as A.

## C. Credit appetite -> USO (weekly sign of HYG63 - LQD63, long/short USO), 5 bp per unit turnover, 252-day annualisation

| Period | Rule Sh / CAGR / MDD / t | USO buy & hold |
|---|---|---|
| Full 2007-07 to 2026-11 | 0.53 / 13.8% / -63.2% / 2.33 | 0.03 / -6.0% / -98.2% / 0.13 |
| 2014-2019 | 0.35 / 6.4% / -42.5% / 0.87 | -0.35 (always-short: +0.35) |
| 2020-now | 0.81 / 29.7% / -63.2% / 2.13 | 0.31 |

- **Random weekly L/S placebo** (57% long, 2000 draws): the 95th percentile is 0.30 and p = 0.004. The circular-shift placebo gives p = 0.022. These "pass" only because of the large episodes below.
- **Episode dependence:**
  - 2020 returned +72% (March +86%, April +44%, with USO -55%/-43%).
  - 2026 returned +277% (March +55%, April +39%, November +24% while USO fell 21%).
  - The 5 best months supply 58% of P&L. Without them Sharpe is 0.25 (t 1.09).
  - Excluding 2020 and 2026: Sharpe 0.28, alpha t = 1.16.
  - **2010-2019, a full decade: Sharpe 0.06.** It lost money in 2010-13, 2017-19 and 2023 (-39%).
- **Neighbours** (full / 2014-19):
  - 21d: 0.54 / 0.10
  - 42d: 0.56 / 0.17
  - **126d: 0.00 / -0.11**
  - monthly rebalance at 63d: 0.57 / -0.15
  - Before 2014, 63d gives only 0.32.
- **Data and cost stress:** on raw (unadjusted) HYG/LQD closes, Sharpe falls to 0.44 (t 1.92). At 25 bp it is 0.45 (t 1.99).
- **Verdict: REJECTED.** This is not a persistent credit-to-oil link. It is a crash/shock detector that paid off in two oil episodes (COVID 2020, 2026) and was flat to negative for a decade. With about 2,930 rules tried, t = 2.3 is what the best of many noise rules look like.

## D. Month-end Treasuries (IEF, last 3 trading days), 5 bp/side, 252-day annualisation

| Period | Rule Sh / CAGR / MDD / t | IEF buy & hold |
|---|---|---|
| Full 2002-07 to 2026-11 | 0.60 / 1.5% / -6.4% / 2.97 | 0.54 / 3.5% / -23.9% / 2.66 |
| 2014-2019 | 0.83 / 1.5% / -2.1% / 2.03 | 0.75 / 3.8% / -8.8% / 1.83 |
| 2020-now | 0.53 / 1.3% / -3.4% / 1.38 | 0.02 / -0.2% / -23.9% / 0.04 |

- **Size of the effect:** the in-window mean is 7.4 bp/day vs 0.4 bp/day otherwise. Gross (zero cost) Sharpe is 1.10, **t = 5.39**. Net t is 4.91 at 1 bp/side and 4.43 at 2 bp/side. Breakeven cost is 11.2 bp/side. IEF's real spread is about 1 bp, so 25 bp is unrealistic, but at 25 bp the rule is deeply negative (Sh -1.24).
- **Placebos:** 1000 random 3-consecutive-day windows per month give a 95th percentile Sharpe of -0.00, p = 0.000. Random scattered days give a 95th percentile of -0.74. Circular shift gives p = 0.000.
- **vs holding IEF:** Sharpe is slightly higher (0.60 vs 0.54) at 14% exposure, alpha 1.0%/yr (t 2.16). CAGR is 1.5% vs 3.5%.
- **1-day delay:** shifting to the last 2 days plus the first day of the next month drops Sharpe to 0.30 (t 1.50), and 2014-19 turns negative. The edge needs market-on-close execution on the exact day.
- **Neighbours on IEF:**
  - k=2: 0.52
  - k=3: 0.60
  - k=4: 0.54
  - k=5: 0.64
  - Fragility: k=2 in 2014-19 is -0.18. The best day moved: 2002-13 the gains were on days E2-E1, in 2014-19 they were on E3 (+14.7 bp) and E1.
- **Other maturities:** TLT has the same pattern (k3 Sharpe 0.61, 3.0% CAGR), but only 0.20 for 2020+. On SHY the effect is real gross (t 8.4) but only 0.9%/yr, so 5 bp costs make every SHY variant negative.
- **Regime:** ex-2020 Sharpe is 0.57 (t 2.77). The 5 best months supply 27% of P&L. Without them Sharpe is 0.46 (t 2.24). It is positive in 18 of 25 years.
- **Verdict: WEAK, and the most credible of the four.** The month-end Treasury bid (index-duration extension, documented in the literature well before 2014) is genuine and not a data-mining artifact. But as a trade it makes about 1.5-2% a year and depends on low-cost, exact-close execution. Forward-test with MOC orders, and do not size it as an alpha source.

## Multiple-testing context
About 2,930 rules were tried, and the 95% luck bar for the best of 2,784 is t = 4.19. Net of the stated costs, the full-sample t-stats are A 3.76, B 2.42, C 2.33 and D 2.97. None clears the bar. A's t comes almost entirely from the BTC beta it shares with buy-and-hold (alpha t 1.64). Only D's *underlying effect* clears the bar (gross t 5.4, and t 4.4-4.9 at realistic 1-2 bp IEF costs), supported by a pre-existing economic explanation. C is consistent with selection luck plus two oil shocks. A and B are the same crypto-trend exposure: they reduce drawdowns, but post-2022 they show no significant alpha over simply holding the coin.
