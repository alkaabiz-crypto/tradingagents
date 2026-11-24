# Liquidity brain: volume and liquidity as signals (US equities and oil)

Memory of the `liquidity` brain (tournament rules: `../RULES.md`; engine: `oil-brain/engine.py`, unchanged).
Data: Yahoo daily, downloaded by `fetch.py` into `data/` (HYG, LQD, ^IRX, ^TNX, ^FVX, 9 SPDR sectors, SPY,
QQQ, IWM, USO, DIA, IEF, SHY; to 2026-11-23). Helpers in `lib.py` (`port_eval` copies the engine's gates for
multi-asset weights, as oil-brain/study6.py does). Volume is Yahoo's split-adjusted share volume.

## Mechanisms and sources (abstract-level, from memory of the literature; numbers not re-verified)

- **Amihud (2002 JFM).** ILLIQ = average |return| / dollar volume. Expected market illiquidity raises expected
  returns; an unexpected rise lowers prices at once, more for small stocks (flight to liquidity).
- **Campbell, Grossman & Wang (1993 QJE).** For the aggregate market, daily moves on HIGH volume reverse more
  than moves on low volume (liquidity traders absorbed by market makers). Note: the brief said the opposite
  ("low volume reverses, high volume continues"); that pattern is Conrad, Hameed & Niden (1994) / the
  informed-trading case of Llorente et al.
- **Llorente, Michaely, Saar & Wang (2002 RFS).** The sign of the return x volume interaction depends on why
  people trade: hedging -> high-volume moves reverse; informed speculation -> high-volume moves continue.
- **Gervais, Kaniel & Mingelgrin (2001 JF).** Stocks with a volume jump vs their past 50 days earn more next month (visibility).
- **Flows as dumb money.** Frazzini & Lamont (2008 JFE); ETF demand shocks revert (Ben-David, Franzoni & Moussawi 2018 JF).
- **Funding / credit liquidity.** Brunnermeier & Pedersen (2009 RFS); intermediary risk capacity drives commodity
  premia (Etula 2013; Acharya, Lochstoer & Ramadorai 2013 JFE); credit spreads forecast (Gilchrist & Zakrajsek 2012 AER);
  relative bill rate predicts stocks negatively (Campbell 1991; Ang & Bekaert 2007 RFS).
- TED spread / repo data are not on Yahoo; proxies used: HYG-LQD return spread, ^IRX vs its 1-year mean.

## Results log (all 2026-11-24; 5 bp per turnover; every rule pre-registered in its script's docstring)

### Study 1 (`study1.py`): volume decides continuation vs reversal? 0 PASS of 3
Diagnostic regression r(t+1) = a + b r(t) + c r(t) log(RV(t)), RV = volume / prior-50-day mean:

| | IS c (t) | OOS c (t) | HOLDOUT c (t) |
|---|---|---|---|
| SPY | -0.127 (-3.95) | +0.083 (+1.46) | -0.322 (-6.88) |
| USO | +0.007 (+0.15) | -0.125 (-2.19) | +0.046 (+1.60) |

CGW's sign (high-volume moves reverse) holds for SPY in IS and strongly in HOLDOUT, but flips in 2014-2019.
For USO the interaction has no stable sign: volume does not decide continuation vs reversal in oil.

| rule | IS | OOS | HOLDOUT | post (bench) | t | placebo p | verdict |
|---|---|---|---|---|---|---|---|
| V1 SPY fade high-volume (RV>1.5) days, 1d (CGW) | 0.30 | -0.56 | 0.57 | 0.20 (0.80) | 0.73 | 0.03 | FAIL |
| V2 USO follow big (>2sd) high-volume day, 5d | -0.09 | 0.55 | 0.08 | 0.25 (0.05) | 0.89 | 0.14 | FAIL |
| V3 USO fade big low-volume (RV<1) day, 5d | 0.28 | 0.13 | 0.27 | 0.22 (0.05) | 0.78 | 0.17 | FAIL |

Event means, next-5-day return signed by the big day: high volume IS -0.07% (n 64), post +0.74% (t 1.10, n 140);
mid volume IS -2.41% (t -2.03, n 28), post -0.34%; low volume: only 8 and 10 events (too few).
The earlier "big USO days continue" finding is, if anything, a high-volume phenomenon post-2014, but not significant.

### Study 2 (`study2.py`): Amihud illiquidity timing. 0 PASS of 3

| rule | IS | OOS | HOLDOUT | post (bench) | t | placebo p | verdict |
|---|---|---|---|---|---|---|---|
| A1 SPY long the month after ILLIQ > its 12m mean | 0.04 | 0.70 | 0.29 | 0.41 (0.80) | 1.47 | 0.48 | FAIL |
| A2 IWM same with own ILLIQ | 0.32 | 0.65 | -0.05 | 0.25 (0.46) | 0.91 | 0.42 | FAIL |
| A3 long IWM / short SPY after SPY illiquidity shock | 0.02 | -0.11 | -0.47 | -0.34 (-0.32) | -1.21 | 0.63 | FAIL |

**Wrong sign for the tradable version:** next-month SPY return by ILLIQ-ratio tercile was low/mid/high =
0.99/1.12/0.33% in IS and 1.27/1.43/0.72% post-2014. High illiquidity (which is mostly high volatility,
since |r| is the numerator) is followed by LOWER returns, the vol-timing pattern (Moreira & Muir 2017),
not Amihud's premium. Not tested as a flipped rule (not pre-registered; budget spent).

### Study 3 (`study3.py`): high-volume premium in sector ETFs (GKM). 0 PASS of 2

| rule | IS | OOS | HOLDOUT | post (bench EW sectors) | t | placebo p | verdict |
|---|---|---|---|---|---|---|---|
| G1 long top-3 / short bottom-3 volume shock | 0.07 | 0.31 | -0.50 | -0.21 (0.77) | -0.76 | 0.65 | FAIL |
| G2 long top-3 volume shock | 0.46 | 0.94 | 0.53 | 0.65 (0.77) | 2.34 | 0.59 | FAIL |

G2's t is just market beta (placebo 0.59, below the equal-weight basket). ETF volume mostly reflects
hedging/flows in the wrapper, not visibility of the underlying stocks, so GKM does not transfer.

### Study 4 (`study4.py`): funding and credit liquidity proxies. 0 PASS of 3

| rule | IS | OOS | HOLDOUT | post (bench) | t | placebo p | verdict |
|---|---|---|---|---|---|---|---|
| F1 SPY long when HYG beats LQD over 21d, weekly | -0.05 | 0.22 | 0.49 | 0.39 (0.80) | 1.39 | 0.79 | FAIL |
| F2 SPY long when ^IRX below its 1y mean, monthly | 0.23 | 0.89 | 0.69 | 0.70 (0.80) | 2.50 | 0.24 | FAIL |
| F3 USO long/short on sign(HYG-LQD 21d), weekly | 0.52 | 0.10 | 0.85 | 0.55 (0.05) | 1.97 | 0.03 | FAIL (OOS, t) |

Timing SPY with liquidity proxies never beats buy-and-hold. Credit risk appetite does carry information for oil (F3).

### Study 5 (`study5.py`, `diag5b.py`): is F3 robust? 1 PASS of 2, fragile

| rule | IS | OOS | HOLDOUT | post (bench) | t | placebo p | verdict |
|---|---|---|---|---|---|---|---|
| F3a credit lookback 10d | 0.36 | 0.41 | -0.41 | -0.09 (0.05) | -0.31 | 0.52 | FAIL |
| F3b credit lookback 63d | 0.32 | 0.35 | 0.81 | 0.62 (0.05) | 2.24 | 0.03 | PASS (t<3: candidate) |

Diagnostics (no selection): F3 (21d) agrees with USO's own 21d momentum sign 64% of days and earns
nothing on the days they disagree (post Sharpe 0.05), so F3 is mostly oil momentum in disguise.
F3b is more distinct: 70% agreement with USO 63d momentum, daily P&L correlation 0.55, but USO 63d momentum
alone earns only 0.25 post-2014 and F3b's disagree days earn 0.70 (t 1.37). Without the 2014-16 and 2020
crash windows F3b falls to Sharpe 0.42 (t 1.38). Both legs positive (long 0.52, short 0.40).
F3b by year %: 2014 +43, 2015 +11, 2016 +30, 2017 -9, 2018 -2, 2019 -2, 2020 +79, 2021 +24, 2022 +28,
2023 -44, 2024 0, 2025 +12, 2026 +145. Lumpy; the 10d neighbour fails, so treat as weak.
Current (2026-11-23 data): HYG-LQD 63d = -1.26% -> F3b SHORT USO.

### Study 6 (`study6.py`): ETF dollar-volume surges as dumb money. 0 PASS of 2

| rule | IS | OOS | HOLDOUT | post (bench) | t | placebo p | verdict |
|---|---|---|---|---|---|---|---|
| E1 short USO the month after 21d $vol > 1.5x prior year | 0.03 | 0.50 | -0.43 | -0.12 (0.05) | -0.41 | 0.58 | FAIL |
| E2 same on XLE | -0.11 | 0.15 | -0.13 | -0.06 (0.36) | -0.22 | 0.33 | FAIL |

## Scorecard
Rules tried: **15 of 15** (budget spent). Winners: none. Candidate: F3b (all 6 gates, t 2.24 < 3).
With 15 tries, one t ~ 2.2 result is roughly what luck alone delivers; F3b needs a forward test.

## Idea queue (for a future brain; budget here is spent)
1. Forward-test F3b (weekly sign of HYG-LQD 63d return -> long/short USO) from 2026-11-24.
2. Vol-managed SPY (Moreira & Muir 2017): Amihud's ILLIQ high-tercile months were followed by low returns in
   IS and post; a scaled-exposure rule could be pre-registered from the paper.
3. CGW interaction on SPY flipped sign in 2014-2019; check whether it is a crisis-only effect (HOLDOUT t -6.9 is
   probably 2020/2022 stress days).
4. Combine F3b with USO TSMOM 126d (lab candidate) as a two-signal oil trend/risk-appetite vote.
