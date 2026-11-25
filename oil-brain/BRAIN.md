# Oil brain: what we know about the US oil market, and what we tested

A living memory. Every run reads this first and adds to it. Facts carry a source; results carry
the date, the script and the verdict. Nothing is deleted: a failed idea stays, so it is not
retried by accident.

## Rules of the lab (fixed 2026-11-24)

- **Splits:** IS up to 2013, OOS 2014-2019, HOLDOUT 2020 on. Parameters are chosen on IS or
  taken from the paper. HOLDOUT is never tuned on.
- **PASS** (`engine.py`): OOS and HOLDOUT Sharpe > 0.3 after costs, post-2014 Sharpe above the
  benchmark, post-2014 t >= 2, placebo p <= 0.05 (500 time-shifted copies of the same
  positions), still positive at 2x costs.
- **Costs:** 5 bp per unit of turnover on ETFs (spread + slippage); double for the stress test.
- **A PASS is a candidate, not proof.** It must also hold on most neighbouring parameters and
  then survive a forward paper test (real dates after the test was written). Count how many
  rules were tried: with ~20 tries, one t = 2 result is expected by luck alone.
- **Instruments:** USO (real ETF; its returns include the roll cost of the front month). Not
  CL=F: Yahoo's continuous front-month series jumps at every roll and fakes returns.
- Paper money only. Research, not financial advice.

## How the market works (mechanisms)

- **Roll and curve shape.** USO holds the front WTI future and rolls monthly. In contango
  (later months dearer) each roll loses money; in backwardation it gains. USO fell 74% from
  2006 to 2026 while spot WTI rose: mostly roll drag. USL spreads over 12 months, so
  USO minus USL return is a free proxy for the curve shape.
- **Weekly calendar.** API inventory estimate Tuesday 16:30 ET; EIA Weekly Petroleum Status
  Report Wednesday 10:30 ET; Baker Hughes rig count Friday 13:00 ET; NYMEX settlement
  14:28-14:30 ET; CFTC Commitments of Traders Friday 15:30 ET (Tuesday data).
- **Holidays thin the market:** Thanksgiving (closed Thursday, early close Friday).
- Literature: see "Academic evidence" below.

## Academic evidence

From a literature review on 2026-11-24 (web search summaries of abstracts; paper tables not
read directly because ssrn.com / nber.org were unreachable, so treat unlisted numbers as
unverified). Grades: **A** replicated and alive after 2010; **B** published, thin or mixed;
**C** weak, decayed or not tradable.

| topic | key papers | what they say | grade |
|---|---|---|---|
| Curve shape / carry | Szymanowska et al. 2014 JF; Gorton, Hayashi & Rouwenhorst 2013 RoF; Koijen et al. 2018 JFE "Carry"; Erb & Harvey 2006 FAJ | Backwardation (low inventories) earns a premium, mostly **across** commodities. For crude alone, "long when backwardated" is weak (Peterson 2015: mostly random) | A cross-section, B-/C single oil |
| Basis-momentum | Boons & Porras Prado 2019 JF | 12m return of nearby minus 2nd contract predicts returns, beats basis and momentum (cross-section) | A- cross-section |
| Time-series momentum | Moskowitz, Ooi & Pedersen 2012 JFE; Hurst, Ooi & Pedersen 2017 | 12m sign, vol-scaled, works across 58 futures; century of evidence Sharpe ~0.77 for a diversified portfolio. Whipsaw years 2009-2013 | A portfolio, noisy for oil alone |
| Cross-sectional momentum | Miffre & Rallis 2007 JBF; Fuertes, Miffre & Rallis 2010 | Long winners / short losers across 20-30 commodities | B+, needs a broad universe |
| Hedging pressure (COT) | De Roon et al. 2000 JF; Kang, Rouwenhorst & Tang 2020 JF; Maréchal 2023 | Short-term changes in hedgers' positions earn a liquidity premium (prices rise after hedgers buy); the level premium does not survive | B+ for changes; C for levels in crude |
| EIA report | Halova, Kurov & Kucher 2014; Ye & Karali 2016; Geman & Li; Rousse & Sévi | A surprise build lowers prices within minutes; overshoot then partial reversal; informed trading before 10:30 | A direction (needs consensus data) |
| EIA-day intraday momentum | Wen, Indriawan, Lien & Xu 2023 Energy J; Wen et al. 2021 | 10:30-11:00 return predicts the last half hour on EIA days (USO) | B |
| Goldman roll front-running | Mou 2011 | 3.6%/yr transferred from index rolls (pre-2010); now arbitraged | C |
| USO roll days | Bessembinder et al. 2016 JFE | ~30 bp cost per roll; deeper books and narrower spreads on roll days; no predatory front-running | B (fact) |
| Seasonality / weekday | CXO; JP Morgan 2015; Auer 2014 | Mar-May strong, Nov-Dec weak, but too noisy; seasonality factor failed since 2010; Monday weak, not significant | C |
| Oil -> stocks | Driesprong et al. 2008 JFE; Ready 2018; Thorbecke 2019 | Lagged negative effect pre-2008; decayed; shale era flipped the sign at times | C |
| OPEC cuts | Demirer & Kutan 2010; IMF 2022 | Drift after cut announcements (1983-2008); later: ~3% jump that fades | B- |
| Variance risk premium | Trolle & Schwartz 2010 | Implied oil vol exceeds realized on average; needs options | B, not tradable here |
| Short-term reversal | mixed (Fin. Res. Letters 2020) | No reliable reversal profit across 29 commodities 1979-2017 | C |
| Liquidity / costs | Chung, Van Ness & Van Ness; Chan et al. (1990s) | Spreads U-shaped by time of day, widest after the open | practical rule: skip the first 5-15 minutes |

**What the literature implies for us:** the robust oil premia (carry, momentum, basis-momentum,
hedging pressure) are slow (monthly) and strongest in a **diversified cross-section** of
commodities, not in oil alone. Short-horizon effects (EIA, OPEC, reversal) are either about
information we do not have (consensus forecasts) or too small after costs.

## Results log

### 2026-11-24, study 1 (`study1.py`): academic signals, daily data. 0 PASS of 9

| rule | OOS | HOLDOUT | post-2014 Sharpe (bench) | t | placebo p | verdict |
|---|---|---|---|---|---|---|
| H1 SPY only after oil fell last month (Driesprong et al. 2008) | 1.09 | 0.56 | 0.74 (0.80) | 2.66 | 0.21 | FAIL: just market exposure |
| H2 carry long/short, USO-USL 21d | 0.26 | 0.73 | 0.54 (0.05) | 1.92 | 0.01 | FAIL (near miss) |
| H2b carry long/flat | -0.08 | 0.83 | 0.48 | 1.74 | 0.01 | FAIL |
| H3 TSMOM 12m vol-scaled (Moskowitz et al. 2012) | 0.41 | 0.31 | 0.35 | 1.26 | 0.13 | FAIL |
| H3b TSMOM 1m vol-scaled | 0.42 | 0.52 | 0.47 | 1.70 | 0.05 | FAIL (t only) |
| H4 long 1 day after a -2 sd USO day | 0.13 | -0.22 | -0.12 | -0.41 | 0.52 | FAIL |
| H5 long USO on Wednesdays (EIA day) | -0.17 | -0.47 | -0.34 | -1.21 | 0.61 | FAIL |
| H6 long USO 5 days after OVX +20% | -0.50 | -0.38 | -0.34 | -1.23 | 0.89 | FAIL |
| H7 XLE catches up with oil next day | -0.40 | 0.38 | 0.08 (0.36) | 0.28 | 0.19 | FAIL |

### 2026-11-24, study 2 (`study2.py`): robustness grid for the near misses. Chosen after study 1

- **Carry is not robust:** lookbacks 21 and 126 days are close (t 1.9), 10 and 63 days are
  zero or negative. Not a candidate on its own.
- **Monthly-rebalanced time-series momentum is the first candidate:** all 5 lookbacks have a
  positive post-2014 Sharpe (0.33 to 0.70); 10, 42 and 126 days PASS every gate, 21 days
  misses only on t (1.70), 63 days fails. Weekly rebalancing is worse (more cost, more noise).
- **Carry + momentum average (21d each) PASSES:** post-2014 Sharpe 0.60, t 2.15, placebo 0.01.
- **Caveats:** IS (2008-2013) Sharpe is negative for most momentum lookbacks; post-2014
  includes two huge oil crashes (2014-15, 2020) where trend rules shine. 23 rules tried so
  far. Treat as candidates for a forward paper test, not as an edge.

### 2026-11-24, study 3 (`study3.py`): is momentum just the crashes? Mostly yes

Post-2014 Sharpe with the two crash windows removed (2014-07..2016-02, 2020-01-15..2020-06):

| rule | post-2014 | without crashes | t without | long leg | short leg | years positive |
|---|---|---|---|---|---|---|
| TSMOM 10d | 0.58 | 0.16 | 0.51 | 0.35 | 0.47 | 9/13 |
| TSMOM 21d | 0.47 | 0.13 | 0.41 | 0.25 | 0.41 | 10/13 |
| TSMOM 42d | 0.56 | 0.11 | 0.36 | 0.32 | 0.47 | 9/13 |
| TSMOM 63d | 0.33 | -0.01 | -0.02 | 0.14 | 0.32 | 6/13 |
| TSMOM 126d | 0.70 | 0.33 | 1.08 | 0.41 | 0.56 | 10/13 |
| carry + TSMOM | 0.60 | 0.17 | 0.54 | 0.51 | 0.37 | 8/13 |

TSMOM 42d by year: 2014 +45%, 2015 +39%, 2016 -4%, 2017 +21%, 2018 +21%, 2019 -17%, 2020 +48%,
2021 +4%, 2022 +13%, 2023 -11%, 2024 -21%, 2025 +13%, 2026 +20% (to Nov 23).

**Reading:** oil momentum is "crisis alpha": most of the profit comes from riding the big
crashes short. In normal years it is close to zero (t < 1.1). That matches the trend-following
literature. Useful as insurance inside a portfolio; not a steady edge for short-term trading.

### 2026-11-24, study 4 (`study4.py`): EIA Wednesday 10:30 reaction, hourly USO. 0 PASS of 4

~150 Wednesdays (2023-12 to 2026-11), 5 bp round trip. Every |t| < 2:
following the 10:30-11:30 move to the close: -6.2 bp (t -0.59); fading it: -3.8 bp (t -0.36);
only big reactions (> 0.75%): +10.8 bp (t 0.40, n 42); drifting into the report
(Tue close -> Wed 10:30): -6.6 bp (t -0.39). Other weekdays at the same hour look the same, so
the report adds noise, not a pattern. Matches the lab's earlier hourly finding
(skipping Wednesdays did not help). CL=F hourly bars start on the hour, not at :30, so the
futures test was not valid; USO answers the question.

### 2026-11-24, study 5 (`study5.py`): literature's top intraday and curve ideas. 0 PASS of 9

Intraday momentum into the last half hour (Wen et al. 2021, 2023), hourly USO 2023-12 to 2026-11:

| rule | n | mean at 2 bp | t | win |
|---|---|---|---|---|
| EIA Wed: sign(10:30-11:30) -> 15:30-16:00 | 146 | -3.5 bp | -2.00 | 42% |
| same, only big first moves | 79 | -3.0 bp | -1.26 | 43% |
| control: other days | 577 | -1.6 bp | -1.36 | 41% |
| non-EIA: sign(prev close -> 10:30) -> 15:30-16:00 | 577 | -3.0 bp | -2.63 | 39% |
| control: Wednesdays | 146 | -0.4 bp | -0.22 | 49% |

The published effect is **absent** after publication: gross returns are about zero to slightly
negative, so costs make it a loser. Do not retry with other bar times (that would be a search).

Basis-momentum proxy (USO minus USL return), month-end, 2009 on:
252d long/short: OOS 0.42, HOLDOUT 0.37, post-2014 Sharpe 0.39, t 1.39, placebo 0.05, FAIL;
252d long/flat: t 1.31, FAIL; 63d long/short: t 1.18, FAIL; 63d long/flat: t 1.11, FAIL.
Positive like the paper says, but for oil alone too weak to clear t >= 2.

### 2026-11-24, study 6 (`study6.py`): diversified commodity trend and carry. 0 PASS of 4

12 commodity ETFs (USO, UNG, UGA, GLD, SLV, DBB, DBA, CORN, WEAT, SOYB, PALL, PPLT), equal risk,
month-end, 5 bp. Benchmark DBC (post-2014 Sharpe 0.22).

| rule | IS | OOS | HOLDOUT | post-2014 | t | placebo p | max DD | verdict |
|---|---|---|---|---|---|---|---|---|
| P1 trend blend 1/3/12m (Hurst et al.) | 0.07 | -0.06 | 0.78 | 0.42 | 1.49 | 0.10 | -11% | FAIL |
| P2 trend 12m (Moskowitz et al.) | 0.12 | 0.11 | 0.56 | 0.35 | 1.26 | 0.15 | -17% | FAIL |
| P3 carry, oil and gas only | 0.65 | 0.43 | 0.31 | 0.37 | 1.32 | 0.09 | -6% | FAIL |
| P4 trend blend + carry | 0.22 | -0.08 | 0.79 | 0.41 | 1.48 | 0.08 | -12% | FAIL |

P1 by year: losing or flat 2014-2019, strong 2020-2022, mixed since. Matches the literature's
post-2009 trend whipsaw. Carry is the most stable (positive in all three periods, smallest
drawdown) but only two ETF pairs exist, so it is thin. At month-end Nov 2026 P1 was short
almost everything except a small long in USO.

### 2026-11-24, study 7 (`study7.py`): extreme days, Brent-WTI, crack spread. 0 PASS of 7

| rule | IS | OOS | HOLDOUT | post-2014 | t | placebo p | verdict |
|---|---|---|---|---|---|---|---|
| X1 fade a +/-2.5 sd USO day, hold 1d | -0.33 | 0.40 | -0.67 | -0.35 | -1.24 | 0.78 | FAIL |
| X2 same, hold 3d | -0.25 | -0.36 | -0.53 | -0.45 | -1.63 | 0.92 | FAIL |
| X3 same, hold 5d | -0.08 | -0.74 | -0.70 | -0.70 | -2.49 | 0.99 | FAIL |
| X4 fade, hold 3d, OVX high | 0.04 | -0.01 | -0.70 | -0.46 | -1.64 | 0.94 | FAIL |
| X5 fade, hold 3d, OVX low | -0.38 | -0.72 | 0.45 | -0.08 | -0.28 | 0.60 | FAIL |
| S1 Brent-WTI z>2 reversion | -0.65 | 0.42 | -0.47 | -0.11 | -0.38 | 0.38 | FAIL |
| C1 crack spread z>1, long USO | 0.12 | -0.38 | 0.30 | 0.04 | 0.15 | 0.38 | FAIL |

**Fading big oil days loses, and the loss grows with the holding period** (t -2.49 at 5 days):
after a shock, oil tends to keep going, not snap back. This contradicts the reversal idea and
fits short-term momentum. The flipped rule ("follow a +/-2.5 sd day for 5 days") was NOT
pre-registered and its IS was flat (+0.08), so it is only a hypothesis for a forward test.

### 2026-11-24, study 8 (`study8.py`, data `fetch_cot.py`): CFTC positioning in WTI. 0 PASS of 5

CFTC Commitments of Traders (legacy 1986-, disaggregated 2006-), WTI code 067651. Positions are
as of Tuesday and released Friday 15:30 ET; the signal is used from the next trading day's close
(no look-ahead), traded on USO.

| rule | IS | OOS | HOLDOUT | post-2014 | t | placebo p | verdict |
|---|---|---|---|---|---|---|---|
| K1 hedgers (commercials) bought last week -> long (Kang et al. 2020) | 0.09 | 0.09 | 0.37 | 0.26 | 0.92 | 0.12 | FAIL |
| K2 producers/merchants bought -> long | -0.32 | 0.10 | -0.27 | -0.12 | -0.43 | 0.57 | FAIL |
| K3 fade managed-money weekly change | 0.49 | -0.14 | 0.13 | 0.02 | 0.08 | 0.41 | FAIL |
| K4 hedgers' 4-week change | 0.27 | -0.08 | 0.06 | 0.01 | 0.02 | 0.46 | FAIL |
| K5 hedging pressure level high -> long (insurance premium) | 0.11 | -0.68 | -0.13 | -0.36 | -1.30 | 0.97 | FAIL |

**Reading:** the liquidity premium keeps the paper's sign (K1 positive in every period) but is
far too weak for crude alone once the 3-day publication lag is respected. The papers measure
it across many commodities, and often from the Tuesday position date, which a trader cannot
use until Friday. The level premium is negative, as Maréchal (2023) found.
Latest report (2026-11-17): commercials net -4.5% of open interest, +0.8 pt on the week;
managed money net +0.8%, -0.5 pt (speculators trimming longs).

### 2026-11-24, study 9 (`study9.py`): month-end pension rebalancing. 0 PASS of 2

Harvey, Mazzoleni & Melone (2025): balanced funds sell whatever outperformed over the month near
month-end. Rule: 4 trading days before month-end, bet on IEF minus SPY against the month-to-date
winner for the last 3 days (10 bp a round trip for two legs).

| rule | IS | OOS | HOLDOUT | post-2014 | t | placebo p | verdict |
|---|---|---|---|---|---|---|---|
| R1 against the month-to-date winner | 0.20 | 0.27 | -0.27 | -0.06 | -0.23 | 0.14 | FAIL |
| R2 only when the gap is > 2% | 0.35 | 0.25 | -0.03 | 0.07 | 0.24 | 0.09 | FAIL |

Right sign before 2020, gone since. The month-end bond effect that the audit found real (IEF over the
last 3 days) is about bond index extension, not this stock-bond rebalancing flow.

### 2026-11-24, study 10 (`study10.py`): natural gas storage report (Thursday 10:30) on UNG. 0 PASS of 3

722 days of hourly UNG (2023-12 to 2026-11), 144 report Thursdays. At 2 bp a round trip:
continuation of the 10:30 bar to the close -16.6 bp (t -1.13); fading it +12.6 bp (t 0.86); last half
hour in its direction -4.6 bp (t -1.97). Nothing passes on report days.
Side note (a control, not a pre-registered rule): on the other weekdays the 10:30 bar's direction
continued to the close, +14.8 bp at 2 bp (t 2.32) but t 1.85 at 5 bp. Below every bar; logged only as
a possible forward-test idea, not a result.
**OPEC production-cut drift:** not testable with free data: only ~6-8 surprise cut announcements since
2014, too few for t >= 2 under any rule. Removed from the queue.

### 2026-11-24, study 11 (`study11.py`): overnight move -> daytime move, USO and XLE. 0 PASS of 6

Sources: Energy Economics 2017 (inventory announcements, intraday CL); Wen et al. 2021 (USO, overnight
carries the signal); INE China 2021 (night predicts day negatively). Trade open -> close in the
direction (or against) the overnight gap, 10 bp a day traded.

| rule | gross post-2014 Sharpe | net post-2014 | t | verdict |
|---|---|---|---|---|
| continuation, USO | -0.04 | -0.99 | -3.56 | FAIL |
| reversal, USO | 0.04 | -0.91 | -3.27 | FAIL |
| continuation, big gaps only, USO | 0.10 | -0.53 | -1.90 | FAIL |
| continuation, XLE | 0.06 | -1.12 | -4.03 | FAIL |
| reversal, XLE | -0.06 | -1.24 | -4.44 | FAIL |
| continuation, big gaps only, XLE | 0.05 | -0.72 | -2.59 | FAIL |

Before costs the overnight gap says nothing about the US daytime move in either direction (gross
Sharpe within +/-0.1); paying the spread twice a day turns every version into a steady loser.
Sources: https://www.sciencedirect.com/science/article/abs/pii/S0140988316302110 ,
https://ideas.repec.org/a/eee/ecmode/v95y2021icp374-384.html , https://ideas.repec.org/a/eee/ecmode/v96y2021icp209-219.html

### 2026-11-24, oil brain v2 (`brain_v2.py`, `study12.py`, `history.py`, `KNOWLEDGE.md`)

New data: EIA weekly petroleum (www.eia.gov allowed 2026-11-24; `fetch_eia.py`): commercial crude,
SPR, Cushing, production, refinery utilization, gasoline, distillate, imports, exports, product
supplied, 1982-2026. Each input is lagged to its public release (EIA Wednesday, CFTC Friday).
Brain v2 = average of 7 votes with signs fixed beforehand: trend, curve, stocks vs 5-year same week,
4-week draws vs normal, Cushing vs normal, fund crowding (contrarian), dollar.

| rule (weekly, Wednesday close, USO) | IS | OOS | HOLDOUT | post-2014 | t | placebo p | verdict |
|---|---|---|---|---|---|---|---|
| B1 brain long/short, |c| >= 0.25 | 0.17 | 0.83 | -0.07 | 0.28 | 1.02 | 0.13 | FAIL |
| B2 brain long/flat | -0.09 | 0.61 | -0.01 | 0.10 | 0.37 | 0.30 | FAIL |
| B3 brain scaled by composite | 0.33 | 0.63 | 0.17 | 0.35 | 1.26 | 0.09 | FAIL |
| C1 stocks vs normal alone | -0.18 | 0.37 | 0.02 | 0.16 | 0.57 | 0.20 | FAIL |
| C2 4-week draws alone | 1.03 | 0.86 | -0.38 | 0.11 | 0.40 | 0.35 | FAIL |
| C3 Cushing alone | -0.36 | -0.43 | 0.34 | 0.03 | 0.12 | 0.35 | FAIL |
| C4 fund crowding alone (contrarian, weekly) | -0.15 | -0.02 | -0.15 | -0.09 | -0.33 | 0.55 | FAIL |

B1 by year: 2014 +41%, 2015 +52%, 2018 +74%, 2020 **-73%** (tight stocks read as bullish into
COVID), 2023 -19%, 2025 -20%, 2026 +58%. US weekly fundamentals predicted oil until 2019 and not
since 2020. History study (38 swings of 25%+ since 2008): 11 of 19 rallies began with funds' net long
in the bottom quarter of 3 years and none with funds above 70%; 7 of 19 crashes began with funds
crowded, 10 of 19 in backwardation; the brain was bearish (median -0.43) at rally starts.
**Use:** `python3 oil-brain/oil_brain.py now` gives the reading; `brain_forward.py` scores it from
2026-11-25. Rules tried: +7 (study 12).

### 2026-11-24, study 13 (`study13.py`): turning-point brain (funds' positioning extremes). 0 PASS of 4

Built from the history study's pattern on the same data (biased in its favour), and it still fails:

| rule | IS | OOS | HOLDOUT | post-2014 | t | verdict |
|---|---|---|---|---|---|---|
| T1 long when funds' net long < 25th percentile | -0.35 | 0.06 | -0.18 | -0.08 | -0.29 | FAIL |
| T2 same + USO above its 20-day average (turn confirmed) | 0.25 | 0.11 | -0.09 | -0.02 | -0.06 | FAIL |
| T3 short: crowded (>70%) + backwardation + below 20-day average | -0.03 | 0.12 | -0.03 | 0.05 | 0.18 | FAIL |
| T4 T2 + T3 | 0.14 | 0.15 | -0.10 | 0.00 | 0.01 | FAIL |

T2: 104 trades, 30% winners, +0.2% average trade, in the market 16% of the time; 2026 +47% but
2024 -11%, 2025 -21%. **Why the history pattern does not trade:** funds stay "given up" for months
while oil keeps falling; the 11 rallies that began there are found only in hindsight, among many
more weeks when nothing followed. Positioning tells you where the risk is, not when it turns.
Rules tried: +4.

### 2026-11-24, combo lab (`combo/`): STRATEGY (daily regime) x INDICATOR (entry) x SKILLS (exits, sizing)

**Round 1, hourly** (`combo_lab.py`, 6 markets, Dec 2023 - Nov 2026, 390 systems): selected on Dec 2023 -
Jun 2025, judged on Jul 2025 - Nov 2026. The 15 best in-sample systems were 53% positive out of sample
(luck ~50%); in-sample vs out-of-sample t correlation 0.15. No survivor. Lessons: trend filters beat
trading both ways; trailing exits beat fixed targets; RSI pullbacks were worst intraday; gold with the
200-day filter and a trailing stop was positive out of sample for 5 of 6 entries (none significant alone).

**Round 2, daily** (`combo_daily.py`, 9 markets, ~20 years, 324 systems): gates = positive avg R in
2014-19 and 2020+ (BTC: 2019-21, 2022+), post t >= 2, positive at 2x cost, and beating random entries
(same exits and regime, 200 runs) at p <= 0.01. 30 pass the period gates (~16 expected by luck),
**12 also beat random entries**:
- 11 x BTC: 20/55-day breakouts, mostly in the 200-day trend's direction, stop 2 x ATR, 4R target or
  trailing; post t 2.0-3.3, placebo p 0.00-0.01 (e.g. BTC R2 D1 T2: 74 trades, avg +0.79R, t 3.28).
- 1 x GLD: above the 200-day average, buy RSI(2) < 10, stop 2 x ATR, trail 3 x ATR: 54 trades, avg
  +0.86R, t 2.09, p 0.01 (4 neighbours t 1.84-1.94).
- Best oil: USO 55-day breakout with the 200-day trend, trailing stop: 2014-19 +1.02R, 2020+ +0.42R,
  t 1.5 (not a pass).
About 714 combos tried across both rounds: a few p = 0.01 passes are expected by luck. The BTC family is
too large and consistent to be luck; gold is borderline.
**Live:** `combo/combo_live.py` paper-trades BTC_BREAKOUT, GLD_PULLBACK and USO_TURTLE (forward only)
with $2,000 each from 2026-11-24, 1% risk per trade, issuing tickets after each close.

### 2026-11-24, CFD cost stress (`combo/cfd_costs.py`): survivors with overnight financing (Exness swaps)

| system | trades | avg hold | avg stop | 0%/yr | mid | high | highest |
|---|---|---|---|---|---|---|---|
| BTC 20-day breakout, trend, 4R (R2 D1 T2) | 74 | 16 days | 7.4% | +0.79R t 3.28 | 10%: +0.73R t 3.03 | 20%: +0.66R t 2.77 | 30%: +0.60R t 2.51 |
| BTC 55-day breakout, trend, 4R | 56 | 17 days | 7.5% | +0.74R t 2.87 | 10%: +0.68R t 2.62 | 20%: +0.61R t 2.37 | 30%: +0.54R t 2.11 |
| GLD uptrend RSI(2) pullback, trail | 54 | 37 days | 2.5% | +0.86R t 2.08 | 3.5%: +0.69R t 1.76 | 7%: +0.53R t 1.41 | 15%: +0.16R t 0.47 |
| USO 55-day breakout, trend, trail | 58 | 28 days | 5.2% | +0.67R t 1.53 | 3.5%: +0.61R | 7%: +0.54R | 15%: +0.40R t 1.02 |

BTC survives even 30% a year of financing because its stops are wide (7%) and holds short (16 days).
Gold needs a swap-free account or the GLD ETF itself: at a typical 7%/yr CFD financing, t falls to 1.4.
Spreads (Exness 2026, third-party lists): XAUUSD ~$0.20, BTCUSD ~$10-30, USOIL ~$0.03-0.05 per unit,
within the backtest's 5-10 bp per side. Exact swaps: MT5 > right-click symbol > Specification.

### 2026-11-24, independent audit of the GLD pullback (`audit2/AUDIT_GLD.md`): WEAK

Rebuilt from its description: 54 trades, +0.86R, t 2.08 (matches). But: with 0.02%/day CFD financing
+0.53R, t 1.40; random entries above the 200-day average with the same exits already earn +0.48R
(the RSI timing adds ~0.35R, placebo p 0.018, or 0.16 if re-entry on a stop-out day is allowed);
the top 3 trades are 72% of the R since 2014 (without them t 1.1); 2006-2013 t 1.03; buy-and-hold GLD
grew 8.5%/yr vs the rule's 6.8% since 2014. Robust to neighbours (11 of 12) and positive on IAU, SLV
and gold futures. Verdict: weak; only on an unlevered ETF (GLD/IAU), never on a financed CFD. The paper
sleeve stays as registered, as a forward test.

### 2026-11-24, Bitcoin breakout deep research (`btc_research/BTC_REPORT.md`, 4 independent agents)

Real, not curve-fit (288/288 neighbours positive; honest yearly re-tuning +0.65R t 2.47; deflated Sharpe
0.90-0.94), but smaller than the headline: random entries with the same trend filter and exits earn
+0.19R since 2019, so the breakout adds ~+0.4-0.6R. Longs carry it (+1.20R, t 5.1 since 2015); shorts
do not (+0.23R; +0.06R across 13 coins). ETH replicates (+0.74R, t 3.0); 12 of 13 coins positive.
Fading: 2022-now +0.57R (t 1.9). Exness execution: mid-cost case +0.68R, t 2.89. Expect +0.3-0.5R per
trade. New paper sleeve BTC_BREAKOUT_LONG (long-only, 0.5% risk) registered today; demo tickets now
0.5% risk with shorts optional at half size.

### 2026-11-24, study 14 (`study14.py`): independent check of another chat's findings

| claim | my result | verdict |
|---|---|---|
| QQQ volatility control (15% / vol, monthly) is the best | post-2014 Sharpe 0.82 vs holding QQQ 0.86, placebo p 0.55 | **not confirmed**: lower risk, no better risk-adjusted return |
| same on SPY | 0.73 vs 0.79, p 0.83 | not confirmed |
| same on GLD | 0.66 vs 0.58, t 2.38, p 0.05 (OOS 0.33, HOLDOUT 0.90) | passes, borderline |
| BTC weekly trend (4w/8w, half each) | Sharpe 1.04 vs 0.83, t 4.32, p 0.00; 2022+ 0.61 vs 0.36, max DD -39% vs -67% | **confirmed** (same family as our BTC trend) |
| ETH weekly trend | 0.89 vs 0.53, t 3.21; 2014-19 0.18 fails; 2022+ 0.85 vs 0.11 | mostly confirmed (fails 1 gate) |
| Permanent Portfolio / risk parity / min variance | 2008-26 Sharpe 0.86 / 0.88 / 0.94 vs SPY 0.62, 60/40 0.75; max DD -19 / -23 / -23% vs -52%; CAGR 6.5 / 8.3 / 8.7% vs 10.8% | **confirmed**: much smaller crashes, lower return |
| DCA: SPY beats oil; BNO beats USO | $100/month since 2011: SPY +13.8%/yr, BNO +10.8%, USO +5.2% | **confirmed** (USO's roll drag) |
| 10-stock momentum account | top-10 vs equal-weight same 113 stocks: t 1.26 post-2014 | **no edge** (its +14% week is noise) |
Not testable here: funding carry, ETF flows, news timing (no data hosts). Rules tried: +10.

## Candidates for forward paper testing

1. TSMOM on USO, monthly rebalance, vol-scaled to 20% a year, lookback 126 days
   (the most robust: positive without crashes too, but t only 1.08). Crisis-alpha profile.
2. Carry + momentum average.
Neither is a 1-3 day trading edge.

## Idea queue (top first)

1. Forward-test "follow a +/-2.5 sd USO day for 5 days" from 2026-11-24 (not pre-registered;
   only forward results count). Log each event in oil-brain/forward.csv.
2. ~~CFTC COT signals~~ done (study 8): FAIL. Hosts publicreporting.cftc.gov and www.cftc.gov are
   allowed (2026-11-24); refresh with fetch_cot.py.
3. ~~Diversified commodity trend + carry~~ done (study 6): FAIL, whipsaw 2014-2019.
4. ~~Extreme-day fades, Brent-WTI, crack spread~~ done (study 7): FAIL.
5. Energy equities: XLE/XOP vs oil (beta-hedged residual momentum), daily.
6. ~~OPEC cut drift~~ untestable (too few events); ~~gas storage report~~ done (study 10): FAIL.
7. ~~Check momentum candidates for crash dependence~~ done (study 3): crash-driven.
8. ~~EIA 10:30 Wednesday reaction~~ done (study 4); ~~EIA-day intraday momentum~~ done (study 5).
9. ~~Basis-momentum on USO/USL~~ done (study 5): positive, not significant.

**Rules tried so far: 74** (oil brain; the tournament adds ~2,930) (study 1: 9, study 2: 14, study 4: 4, study 5: 9, study 6: 4,
study 7: 7, study 8: 5, study 9: 2, study 10: 3, study 11: 6, study 12: 7, study 13: 4; study 3 re-scored old rules). At this count, a couple of t = 2 results are expected by chance alone.

## 2026-11-25 Oil DCA study (dca/dca_study.py, dca/dca_neighbours.py, notes in dca/RESEARCH_NOTES.md)
Asked by the user: plain DCA into oil vs DCA with entry conditions and exits. Pre-registered, 150 systems
(10 entries x 5 exits x USO/XLE/BNO), $100 a week, idle cash at 0%, 5 bp a side.
- Plain DCA money multiple (final / added): USO 0.85 (2006-13), 0.95 (2014-19), 2.26 (2020-26); XLE 1.50 / 0.96 / 2.07;
  BNO 1.22 (2010-13) / 1.14 / 2.53. Account drawdowns -21% to -74%. Result depends on the start date.
- 4 of 147 variants beat plain DCA in both OOS and HOLDOUT; 1 passed the 200-run placebo (USO RSI14<35 + take profit
  +50%, p 0.01). Neighbour check (25 RSI x take-profit settings, 1000-run placebo): only 24% of USO neighbours beat
  plain DCA, median p 0.34; the survivor itself has p 0.027 on 1000 runs. VERDICT: luck. No timing rule beats plain DCA.
- Literature agrees: ~7,800 technical rules on WTI/USO 2006-15 failed out of sample (Psaradellis et al. 2016);
  backwardation/inventory signals are the best-supported but mostly cross-sectional; stop-losses only help in
  trending markets (Kaminski & Lo 2014); take-profits have no support.
- Next (from the notes): test plain DCA in XLE vs USO with dividends, a true 2nd-month backwardation gate from
  futures-chain data, a T-bill baseline, and Exness USOIL swaps as a cost range.

## 2026-11-25 Small wins, many trades (smallwins/smallwins.py, smallwins/neighbours.py)
Asked by the user: small frequent wins rather than big ones. 8 short-term setups (IBS dip, RSI(2) dip, 3 down
closes, Bollinger, overnight hold, IBS + small ATR target; each also mirrored short) x 9 markets = 144 systems,
entry at the close, 5 bp a side, placebo gate.
- OIL: every oil setup FAILS (USO/BNO/XLE/XOP). Win rates 50-72% but the losses are bigger than the wins
  (e.g. USO IBS + small target: wins 71% of trades yet loses 18 bp a trade). Small wins in oil = a trap.
- Stock indexes: 5 pass the placebo (QQQ IBS dip, SPY IBS dip, SPY RSI2 dip, SPY RSI2 + trend, SPY below Bollinger).
  Neighbour check at 2x cost, with IWM and DIA as unseen markets: ONLY QQQ IBS dip holds (73% of 15 settings);
  SPY 13%, IWM 0%, DIA 0%. So it is likely a QQQ/tech effect of 2014-2026, not a universal law.
- QQQ IBS dip: ~34 trades a year, 65% wins, +31 bp a trade net (t 3.4). Entry at the next open halves it
  (+16 bp, t 2.1): it must be placed just before the close.
- Registered as a forward paper sleeve: smallwins/ibs_live.py (QQQ_IBS $2,000; SPY as a comparison sleeve).

## 2026-11-25 Candle brain (candles/CANDLES.md, candles/candle_study.py)
1,248 systems (26 named patterns x 4 holds x 12 markets, next-open entry). 3 passed the per-test bar; with the
family-wise luck bar (~t 4.0) only QQQ bullish harami (t 4.24, 34 events); its neighbour check FAILED (39%).
Engulfing patterns point the WRONG way in 11/12 markets; doji/hammer/stars = myths; wicks alone predict nothing.
The only candle feature with real support is close location (IBS) in US stock indexes (already a paper sleeve).
Oil: no candle edge. Full brain + rules for the bot: candles/CANDLES.md. Mistake log: MISTAKES.md.

## 2026-11-25 IBS on Exness USTEC-style candles (smallwins/ibs_ustec.py)
Candles rebuilt from NQ=F; Exness-style costs (1 bp spread a side + 1.7 bp swap a night).
- NQ futures daily 2000-2026: IS +22 bp (t 2.1), OOS +28 bp (t 2.6), HOLDOUT +41 bp (t 3.0); post-2014 +36 bp a trade,
  t 3.9, 64% wins, placebo p 0.000 -> PASSES on the CFD's underlying price, net of CFD costs.
- Last 2.4 years (1h data): US-session candle on the USTEC price +36 bp (t 1.4) = QQQ +35 bp (t 1.3): same result,
  too few trades to be significant. Exness's own UTC-midnight daily candle is weaker: +19 bp (t 0.7).
- Lesson: read the IBS on the US-SESSION candle (QQQ, or USTEC's 6:30 pm-1:00 am Abu Dhabi part), not on the
  Exness midnight candle, and trade USTEC just before the US close.

## 2026-11-25 IBS improvement study (smallwins/ibs_improve.py): 80 variants, chosen on 2000-2013 only
- The 3 versions chosen on 2000-13 (not-in-crash filter, down-day filter, wide-range + close>prior high) all
  FAILED to beat the plain rule on 2014-26 / NQ futures. The plain rule stays.
- Robust in BOTH periods: a 2 x ATR stop-loss makes it WORSE (MAR 10.8 -> 7.0 and 13.8 -> 8.5 on NQ), and
  volatility-scaled size (min(1, 1% / ATR%)) cuts drawdowns (-35% -> -7% in 2000-13; -19% -> -14% after) and the
  worst trade (-8.2% -> -5.5% of the sleeve), at the price of less total profit.
- "Exit at the first up close" was worse in 2000-13 but best after 2014 (71% wins): inconsistent, hypothesis only.
- New forward-only comparison sleeves in ibs_live.py: QQQ_IBS_VOLSIZED and QQQ_IBS_UPCLOSE (main sleeve unchanged).
- Replay check 2025-01 -> now: QQQ_IBS +14.6% (31 trades, 19 wins), VOLSIZED +7.9%, UPCLOSE +8.8%, SPY -3.2%.

## 2026-11-25 BTC wicks / "John Wick" candle (candles/btc_wicks.py + btc_wicks2.py): 276 systems, 0 pass
John Wick, sweep, SFP, Turtle Soup, trend-filtered, liquidation wicks, pin bars, confirmed sweeps; long/short;
D1 2014-2026, H4/H1 2024-2026; 10 bp a side. Best t 1.4 vs luck bar ~3.5. Shorting upper wicks loses (BTC momentum);
hourly is eaten by costs. The BTC edge remains the long-only 20-day breakout. Details: candles/CANDLES.md section 4b.

## 2026-11-25 All 61 TA-Lib candlestick patterns (candles/talib_study.py): 5,856 systems, 0 pass
Luck bar t 4.56 (1,988 judged systems). "Right in >= 9/12 markets": 18 groups vs ~13 by luck (noise); "wrong in
>= 9/12": 27 vs ~17 by luck. Engulfing wrong-way replicated (own code + TA-Lib); Three Outside worst. Table of all
61 in candles/CANDLES.md section 4c. Running total of candle systems tested: 1,248 + 276 BTC + 5,856 = 7,380.

## 2026-11-25 WIDE candle test (candles/wide_study.py): 51 markets, daily+weekly, 65 signals, 5 contexts
2,550 pooled combinations (events averaged by date across markets). 0 pass; best t 2.8 < the ~3.4 expected from luck
for 1,653 judged combos. Context and weekly candles add nothing. IBS low in an uptrend (3 days) +7 bp, stable in all
periods, 70% of markets, t 2.6 — real but tiny. Candle tests so far: ~9,930 combinations.

## 2026-11-25 morning research run (13:39 UTC)
- MISTAKES C4 fixed: smallwins.py placebo seeds are now fixed integers; two runs give identical results. With the new
  seeds 7 setups pass the placebo (was 5): the two new ones (3 down closes on SPY/QQQ, p 0.005) were sitting near the
  0.01 line. Their neighbour check (smallwins/down_neighbours.py) FAILS: 0-22% of 9 settings on SPY/QQQ/IWM/DIA.
- OIL, EIA report hour on USO 1h bars (candles/eia_hour.py; 146 Wednesdays, 2023-12 -> 2026-11): continuation,
  fade, big-move versions and the inventory-surprise rule all FAIL (best t 0.2); no edge after the release hour.
- IBS by weekday (smallwins/ibs_weekday.py, ONE pre-registered hypothesis from the literature): QQQ IBS trades
  entered on a MONDAY close beat the rest in both periods (2000-13: +74 vs +23 bp; 2014-26: +48 vs +28 bp), Monday
  t 2.2 and 2.3 -> HOLDS. A sizing hint only (no new sleeve). Not pre-registered, observation only: Thursday entries
  were the weakest in both periods (+10 / +5 bp).
