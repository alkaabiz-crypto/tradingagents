# Energy brain: energy equities vs oil (tournament brain `energy`)

Memory for this brain. Reads `../RULES.md`, `../../engine.py` (unchanged) and the oil brain's
`../../BRAIN.md` first. Nothing is deleted. All dates 2026-11-24.

## Data
- Shared: XLE, XOP, USO, USL, UGA, SPY (oil-brain/data).
- Own (`data/`, Yahoo adjusted closes via `fetch.py`): OIH, VDE, AMLP, CRAK (2015-), XES, IXC,
  XOM, CVX, COP, OXY, SLB, HAL, BKR, EOG, DVN, APA, VLO, MPC (2011-), PSX (2012-), KMI (2011-),
  WMB, OKE. HES and MRO are delisted on Yahoo, so the stock universe is survivors only (bias
  favours long-the-winners rules; noted, did not rescue anything).
- `common.py`: rolling 252-day OLS betas (known at t, hedge uses yesterday's), weekly/monthly
  sampling, and `xs_evaluate` = engine.evaluate's 6 gates for a cross-section of weights
  (placebo = circular time shift of the whole weight matrix). Used only for study 3.

## Mechanisms and sources
- Slow diffusion oil -> stocks (Driesprong, Jacobsen & Maat 2008 JFE; Hong, Torous & Valkanov
  2007 JFE). Graded C by the oil brain (decayed); the 1-day XLE catch-up (H7) had failed.
- Equity holders do not pay the futures roll; USO does (roll drag in contango). Equities price
  long-dated oil, USO the front month.
- Pairs trading: Gatev, Goetzmann & Rouwenhorst 2006 RFS (2 sd divergence, exit at convergence).
- Residual momentum: Blitz, Huij & Martens 2011 JEF. Residual short-term reversal:
  Da, Liu & Schaumburg 2014 Mgmt Sci.
- Backwardation = low inventories = high spot cash flows (Gorton, Hayashi & Rouwenhorst 2013).

## Results log (13 rules, 0 PASS, 0 candidates)

| # | rule | study | IS | OOS | HOLDOUT | post-2014 (bench) | t | placebo p | verdict |
|---|---|---|---|---|---|---|---|---|---|
| E1 | XLE 5d residual (on SPY, USO) -> USO next week | 1 | -0.28 | -0.64 | -0.18 | -0.36 (0.05) | -1.29 | 0.84 | FAIL 6/6 |
| E2 | XLE lagged its fitted move -> long XLE-SPY next week | 1 | -0.87 | -0.17 | 0.10 | 0.02 (-0.19) | 0.05 | 0.25 | FAIL 5/6 |
| E3 | same for XOP | 1 | -0.51 | -0.75 | 0.44 | -0.04 (-0.35) | -0.14 | 0.35 | FAIL 4/6 |
| P1 | pair XLE vs USO, 2 sd in, exit at 0 / 10 days | 2 | 0.12 | 0.07 | -0.36 | -0.23 (0.38) | -0.82 | 0.71 | FAIL 6/6 |
| P2 | pair XOP vs XLE | 2 | 0.28 | -0.01 | -0.26 | -0.17 (-0.26) | -0.59 | 0.58 | FAIL 5/6 |
| P3 | refiners (VLO/MPC/PSX) vs XLE + crack (UGA-USO) | 2 | -0.44 | -0.27 | -0.04 | -0.13 (0.44) | -0.45 | 0.53 | FAIL 6/6 |
| C1 | residual momentum 12-1, 16 stocks, monthly | 3 | 0.20 | 0.03 | 0.57 | 0.33 (0.44) | 1.20 | 0.11 | FAIL 4/6 |
| C2 | residual reversal 5d, 16 stocks, weekly | 3 | 0.07 | -0.97 | -0.53 | -0.70 (0.44) | -2.51 | 0.39 | FAIL 6/6 |
| B1 | contango -> long XLE / short USO (roll yield), monthly | 4 | 0.11 | 0.41 | -0.20 | -0.00 (0.38) | -0.01 | 0.48 | FAIL 5/6 |
| B2 | backwardation -> long XLE / short SPY, monthly | 4 | -0.05 | 0.01 | 0.51 | 0.33 (-0.19) | 1.19 | 0.12 | FAIL 3/6 |
| T1 | follow a 2.5 sd XLE day for 5 days | 5 | -0.35 | -0.24 | 0.36 | 0.19 (0.36) | 0.67 | 0.15 | FAIL 4/6 |
| T2 | same, XOP | 5 | -0.27 | 0.02 | 0.15 | 0.11 (0.15) | 0.38 | 0.33 | FAIL 5/6 |
| T3 | same, OIH | 5 | -0.06 | -0.25 | 0.34 | 0.17 (0.04) | 0.60 | 0.26 | FAIL 3/6 |

Costs: 5 bp outright ETF, 10 bp two-leg hedges and single stocks, 15 bp three-leg (P3).

### Notes per study
- **Study 1 (diffusion, weekly):** no catch-up at a week either; the 1-day H7 failure extends to
  5 days. E1 is negative in all three periods (XLE outperforming its oil/market fit is followed
  by WEAKER oil). That flipped rule was not pre-registered: hypothesis only, t ~1.3, do not count.
- **Study 2 (pairs):** hedged energy spreads do not mean-revert at a 2-sd/20-day trigger after
  2014; in position only ~10% of days. Divergences between equities and USO are mostly roll
  drag and regime change (shale, 2020), not noise.
- **Study 3 (cross-section):** residual momentum is the most stable sign (gross +2.3% / +0.8% /
  +6.5% a year IS/OOS/HOLDOUT, market and oil beta ~0) but far too small (t 1.2). Weekly
  residual reversal earned ~8% gross a year 2008-2013, then died (-1.4% OOS, +0.9% HOLDOUT):
  with ~52 rebalances a year, costs make it a clear loser (t -2.5).
- **Study 4 (curve):** XLE's oil beta barely changes with the curve proxy (0.32 in contango
  months vs 0.39 in backwardation, with SPY control; correlation 0.64 vs 0.63). The roll-yield
  pair B1 is zero after 2014: the USO-hedged XLE spread just earns its long-run drift (0.38
  held long) regardless of regime. B2 positive only in HOLDOUT (2021-22 tight market).
- **Study 5 (extreme days):** the oil brain's untested idea ("oil keeps going for 5 days after a
  2.5 sd day") does NOT transfer to energy equities: IS negative for all three, post-2014
  t < 0.7. Weakens the forward-test case for the USO version too.

## Lessons
1. At daily-to-weekly horizons, energy equities and USO share information fast; no measurable
   lead-lag in either direction after costs (1-day and 5-day both fail).
2. The slower, published effects (residual momentum, backwardation tilt) keep the paper's sign
   but are t ~1.2: too weak for a single sector of 16 stocks / one ETF.
3. Effects that worked before 2014 (residual reversal, E3-type catch-up) decayed: consistent
   with the oil brain's general finding.

## Idea queue (2 of 15 rules left, deliberately unspent)
1. E1 flipped (XLE residual up -> oil down next week): needs a fresh, pre-registered forward test
   only; do not re-fit on history.
2. Residual momentum on a wider, survivorship-free energy universe (needs delisted names; Yahoo
   lacks them).
3. OPEC/earnings event studies need hand-built date lists.
