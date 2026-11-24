# crypto brain: memory

Data: Yahoo BTC-USD (2014-09-17+), ETH-USD (2017-11-09+), IBIT/FBTC (2024-01-11+), saved in
`data/`. Last bar used 2026-11-23 (today's partial bar dropped). 7-day-a-week daily bars (UTC days).
Shared QQQ from `oil-brain/data/`.

## Splits and measurement (stated before any study)
- Official: `engine.evaluate` unchanged. Its splits are hard-coded: IS <=2013 (EMPTY for crypto),
  OOS 2014-2019, HOLDOUT 2020+. Its Sharpe uses sqrt(252) on 365-day data, so all engine Sharpes
  (rule and benchmark alike) are understated by x1.20; trades_per_year is overstated by x1.45;
  engine `cagr_post` is wrong for 7-day data (use `cagr` from crypto splits).
- Brain splits (pre-registered): IS 2014-09..2018, OOS 2019-2021, HOLDOUT 2022+, sqrt(365), same
  6 gates, "post" = 2019+. Reported next to engine numbers for every rule (`common.crypto_eval`).
- Because the engine has no IS, no parameter was fitted: lookbacks (7d, 28d) come from Liu &
  Tsyvinski 2021; vol target 0.6 is a fixed round number.
- Costs 10 bp/side (gate 5 doubles to 20 bp); 25 bp stress reported as `post_25bp`.
- Caveat on "OOS": the papers' sample ends ~2018, so engine OOS 2014-2019 is largely the papers'
  own in-sample. The only truly post-publication period is 2022+ (brain HOLDOUT).

## Mechanisms (sources)
- Time-series momentum 1-4 weeks: Liu & Tsyvinski (2021, RFS) "Risks and Returns of Cryptocurrency";
  crypto momentum factor: Liu, Tsyvinski & Wu (2022, JF) "Common Risk Factors in Cryptocurrency".
- Volatility management: Moreira & Muir (2017, JF).
- Monday effect: Caporale & Plastun (2019, FRL).
- Crypto/Nasdaq co-movement after 2020 (lead-lag tested, prior weak).

## Rules tried (11 slots of 15)
| # | rule | engine OOS/HO/post (bench 0.78) | t_post | placebo p | engine verdict | brain-split OOS/HO/post (bench 0.89) | brain verdict | maxDD 2019+ (BH -0.77) |
|---|---|---|---|---|---|---|---|---|
| R1 | long BTC if 28d ret > 0 else flat | 1.08/1.14/1.10 | 4.62 | 0.00 | PASS, t>=3 -> WINNER | 1.97/0.71/1.30 | PASS | -0.50 |
| R2 | long BTC if 7d ret > 0 | 1.22/0.51/0.85 | 3.59 | 0.01 | PASS, t>=3 -> WINNER (fragile) | 1.41/0.05/0.72 | FAIL 3 | -0.68 |
| R3 | long ETH if 28d ret > 0 (bench ETH 0.54) | 0.35/0.93/0.77 | 2.79 | 0.01 | PASS, t<3 -> candidate | 1.40/0.53/0.94 (bench 0.81) | FAIL 1 (placebo .06) | -0.61 (BH -0.79) |
| R4 | BTC long/short sign 28d | 0.67/0.89/0.78 | 3.26 | 0.00 | FAIL 1 (ties bench) | 1.47/0.58/0.98 | PASS | -0.63 |
| R5 | diagnostic slot: R1 at L=14,21,35,42,56; 1- and 2-day delay; per-year; IBIT | all neighbours post 0.99-1.12 > 0.78; delay1 1.05, delay2 0.95 | 3.98-4.72 | - | robust | neighbours HO 0.38-0.77 | - | -0.48..-0.60 |
| R6 | BTC vol-managed min(1, 0.6/vol30) | 0.91/0.63/0.76 | 3.18 | 0.61 | FAIL 2 | 1.50/0.38/0.87 | FAIL 2 | -0.75 |
| R7 | R1 x R6 sizing | 1.22/1.14/1.18 | 4.94 | 0.00 | PASS, t>=3 -> WINNER | 2.18/0.73/1.38 | PASS | -0.44 |
| R8 | long BTC Monday (UTC) only | 0.63/0.32/0.46 | 1.91 | 0.00 | FAIL 2 | 0.65/0.26/0.43 | FAIL 4 | -0.51 |
| R9 | long BTC if QQQ 5d ret > 0 | 0.74/0.41/0.57 | 2.39 | 0.43 | FAIL 2 | 1.00/0.14/0.55 | FAIL 4 | -0.46 |
| R10 | hold ETH if ETH/BTC 28d up else BTC (bench BTC, 2017-11+) | 0.55/0.76/0.70 (bench 0.58) | 2.52 | 1.00* | FAIL 1 | 1.67/0.29/0.93 | FAIL 2 | -0.72 |
| R11 | hold stronger of BTC/ETH if its 28d > 0 else flat | -0.27/0.96/0.62 | 2.23 | 0.32 | FAIL 2 | IS -0.80, 1.45/0.63/1.01 | FAIL 1 | -0.65 |

*R10 is always invested, so the circular-shift placebo is structurally uninformative (p=1 by construction).

Post-publication check (2022-01-01..2026-11-23, Sharpe365, 10 bp): R1 0.71 (t 1.57, DD -40%, +145%),
R7 0.73 (t 1.61, DD -39%), R2 0.05, BTC buy-and-hold 0.37 (DD -67%, +32%). At 25 bp: R1 0.57, R7 0.59.
So R1/R7 beat buy-and-hold since 2022 too, but on their own the 2022+ t-stats are < 2: the t >= 3
comes mostly from 2015-2021, which overlaps the papers' sample.

Per-year (R1 vs BH Sharpe365): R1 lagged in 2017, 2019, 2024 (strong bull years: it gives up upside)
and won in 2015, 2016, 2020, 2021, 2023, 2026 YTD; 2018 and 2022 both lost (R1 -61% in 2018 vs -74%).
IBIT 2024-01..2026-11 (US hours, signal lagged 1 day, 5 bp): R1 Sharpe252 0.70 vs IBIT 0.43, DD -35% vs -54%.

## What I learned
1. The paper's own rule (28d BTC trend, long/flat) survives everything I could throw at it here:
   neighbours, delays, 25 bp, ETF execution, and post-publication 2022+. Its main value is drawdown
   cut (-50% vs -77%) at similar or higher Sharpe; it lags in strong bull years.
2. Fast (7d) momentum looked good through 2021 and died after 2022 -> the engine's splits would have
   crowned it; the crypto split (HO 2022+) shows it is not robust. Treat R2 as a false winner.
3. Calendar (Monday) mean effect is real in the raw data (t 3.3, present in all three periods) but at
   1/7 exposure cannot beat holding; Nasdaq lead-lag and ETH/BTC rotation add nothing over R1.
4. Vol-managing alone does not help (placebo p 0.61); it only helps as sizing on top of trend (R7),
   at 4x the turnover of R1 for a small Sharpe gain - R1 is preferred for simplicity.

## Idea queue (not run; 4 slots left)
- Hourly time-of-day effect (needs data beyond Yahoo's 730-day hourly window).
- Equal-weight BTC+ETH each with R1 filter (diversified trend).
- Forward test R1 on IBIT with a pre-registered log (Phase 4).
