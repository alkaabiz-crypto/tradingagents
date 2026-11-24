# Statarb brain: short-term reversal and pairs across large US stocks

Memory of brain `statarb` (tournament, rules in `../RULES.md`). Engine `../../engine.py` imported
unchanged (sharpe, tstat, splits); `lib.py` applies the same 6 gates to a weight matrix
(placebo = 500 circular time shifts of the whole matrix, as `oil-brain/study6.py`).
IS 2005-07..2013 (residual rules start ~2006-03 after 2x252 days of warm-up), OOS 2014-2019,
HOLDOUT 2020-2026-11. Dollar-neutral books, $1 long / $1 short. Cost 5 bp per unit of turnover
(sum |dw|); the 2x-cost gate is the 10 bp stress. Benchmark for gate 2: SPY buy-and-hold
(post-2014 Sharpe 0.80), strict for a market-neutral book.

## Data and biases
- `fetch.py`: 110 large US stocks (Yahoo adjusted closes, 2004-06..2026-11-23), all listed
  before 2005, 11 hand-labelled GICS sectors (`data/sectors.json`). BK, MMC failed to download,
  EQR had only 2026 data: dropped. Extreme returns checked (AIG/C/MS 2008, OXY/APA 2020): real.
- Survivorship: the list is today's survivors. Long/short books are less affected, but a
  reversal book that buys losers is helped by knowing the losers did not die (e.g. AIG, C in
  2008-09 are kept and recovered). This flatters IS 2008-09 numbers.
- Close-to-close fills: some reversal profit at the close is bid-ask bounce. Diagnostic: 1-day
  delayed weights (GGR's "wait one day").

## Mechanisms and sources (abstract level, not re-verified from paper tables)
- Lehmann (1990 QJE), Lo & MacKinlay (1990 RFS): weekly losers beat weekly winners; contrarian
  profits partly from lead-lag, not only overreaction.
- Nagel (2012 RFS) "Evaporating liquidity": reversal returns are a compensation for liquidity
  provision; expected return rises with VIX.
- Da, Liu & Schaumburg (2014 MS): reversal within industries is stronger (removes industry news).
- Blitz, Huij, Lansdorp & Verbeek (2013): residual (factor-adjusted, vol-scaled) reversal is
  stronger and less risky.
- Gatev, Goetzmann & Rouwenhorst (2006 RFS): distance pairs, 12m formation / 6m trading /
  2 sigma; Do & Faff (2010 FAJ): profits declined after the 1990s, partly back in crises.

## Rules tried (11 of 15 budget). 0 PASS, 0 winners, 0 candidates

| # | rule | IS | OOS | HOLD | post (SPY 0.80) | t | placebo p | gross post | net 10bp post | turn/yr | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|
| R1 | weekly 5d reversal, raw | 0.35 | -0.79 | -0.22 | -0.38 | -1.35 | 0.19 | 0.00 | -0.75 | 148 | FAIL 6/6 |
| R2 | daily 1d reversal | -1.65 | -2.60 | -1.50 | -1.82 | -6.52 | 0.00 | 0.06 | -3.70 | 726 | FAIL 5/6 |
| R3 | weekly industry-adjusted reversal (DLS) | 0.44 | -0.82 | -0.20 | -0.39 | -1.41 | 0.01 | 0.19 | -0.97 | 149 | FAIL 5/6 |
| R4 | R3 x VIX/1y-mean VIX (Nagel scaling) | 0.67 | -0.65 | 0.23 | 0.02 | 0.06 | 0.00 | 0.38 | -0.34 | 151 | FAIL 5/6 |
| R5 | R3 only when VIX > 25 (Nagel regime) | 0.47 | 0.09 | 0.72 | 0.53 | 1.90 | 0.00 | 0.66 | 0.40 | 27 | FAIL 3/6 (OOS, SPY, t) |
| R6 | GGR distance pairs, top 20, all stocks | 0.61 | 0.04 | 0.42 | 0.29 | 1.04 | 0.04 | 0.41 | 0.16 | 10 | FAIL 3/6 |
| R7 | GGR pairs, same sector only | 0.55 | 0.15 | 0.08 | 0.10 | 0.37 | 0.15 | 0.25 | -0.04 | 9 | FAIL 6/6 |
| R8 | weekly residual reversal (Blitz et al.) | 0.44 | -0.77 | -0.22 | -0.39 | -1.39 | 0.01 | 0.38 | -1.14 | 145 | FAIL 5/6 |
| R9 | R8 only when VIX > 25 | 0.69 | -0.11 | 0.70 | 0.49 | 1.77 | 0.00 | 0.67 | 0.32 | 27 | FAIL 3/6 |
| R10 | R8 with weekly partial adjustment 0.5 (a from IS) | 0.67 | -0.25 | -0.12 | -0.15 | -0.55 | 0.01 | 0.35 | -0.65 | 59 | FAIL 5/6 |
| R11 | R10 with VIX > 25 target | 0.64 | 0.16 | 0.65 | 0.49 | 1.75 | 0.00 | 0.61 | 0.36 | 11 | FAIL 3/6 |

Gross IS Sharpe (before costs): R1 0.66, R2 -0.06, R3 0.88, R4 0.94, R5 0.59, R6 0.71, R7 0.66,
R8 1.07, R9 0.89, R10 1.12, R11 0.78.
1-day-delay diagnostic (not counted as rules): R6 post 0.29 -> 0.29 (pairs are not bounce);
R10 IS 0.67 -> 0.27; R11 post 0.49 -> 0.33 (some of the reversal edge is close-price bounce).
Placebo p is low for many losing rules because the shifted books pay the same costs with no
edge; it is only meaningful together with a positive Sharpe.

## Facts measured here
1. **Short-term reversal in megacaps is gross-dead after 2014 in calm markets.** Weekly
   industry-adjusted reversal (R3) earned gross 22 bp/week IS when VIX < 15 but -9 bp/week
   post-2014 for VIX < 20 (t -1.5 and -0.8). Costs at 5 bp are ~14 bp/week. Daily reversal (R2)
   has zero gross edge even IS and loses ~36%/yr at 5 bp.
2. **Nagel (2012) holds out of sample in direction.** Post-2014 gross R3 return per week by VIX
   at formation: <15: -9 bp, 15-20: -9 bp, 20-25: +10 bp, 25-35: +52 bp (t 2.35), >35: +197 bp
   (t 1.24, 16 weeks). The VIX>25 books (R5, R9, R11) are the only reversal rules with positive
   post-2014 net Sharpe (~0.5) and placebo p ~0, but they are in the market ~20% of weeks, made
   most of their money in 2008-09 and 2020, and 2014-2019 (few VIX spikes) is flat to negative.
3. **Industry and residual adjustment help gross, not net.** Gross IS Sharpe 0.66 (raw) ->
   0.88 (industry) -> 1.07 (residual) as DLS 2014 and Blitz 2013 say, but turnover ~145x/yr
   at 5 bp costs ~7%/yr and post-2014 gross is only 0.2-0.4.
4. **Partial adjustment (R10) cuts turnover 145 -> 59 and lifted IS net 0.44 -> 0.67,** but
   post-2014 net is still negative: there is not enough gross edge left to save.
5. **Distance pairs decayed (Do & Faff confirmed).** R6 net post Sharpe 0.29 (t 1.0), 1-2%/yr,
   with profit again concentrated in 2008-09, 2020 and 2026 (crisis = liquidity provision).
   Same-sector pairs (R7) are worse, not better.

## Readings
- The common thread across all 11 rules: short-horizon contrarian profits in large US stocks
  are now a crisis-only liquidity premium. Outside VIX > 25 they are zero or negative gross.
- A VIX-gated reversal book is a reasonable "crisis overlay" idea but cannot pass a 6-gate test
  with a 2014-2019 OOS window that has almost no high-VIX weeks; t ~1.8-1.9, far from 3.

## Idea queue (4 rules of budget left, not used on purpose: more VIX-threshold variants would be
tuning on already-seen post-2014 data)
- Intraday/open-to-close reversal would avoid close bounce but needs intraday data.
- A forward log of R5 (VIX>25 industry-adjusted weekly reversal) costs nothing to keep and
  would accumulate high-VIX weeks honestly; it is NOT a candidate under the rules.
