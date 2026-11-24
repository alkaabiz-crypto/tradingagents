# Brain `sectors`: cross-sectional and timing rules on US sector ETFs

Memory of the `sectors` brain (tournament rules: `../RULES.md`; engine: `../../engine.py`, imported
unchanged via `lib.py`). Nothing is deleted.

## Setup (fixed 2026-11-24, before any rule ran)
- Data: `fetch.py` -> `data/` (Yahoo, adjusted closes): XLB XLE XLF XLI XLK XLP XLU XLV XLY
  (1998-12-22), XLRE (2015-10), XLC (2018-06), SPY, XOP (2006-06), OIH (2001-02), JETS (2015-04),
  IYT (2004-01), USO (2006-04). Data checked: no NaNs, largest daily moves are real (2008, 2020).
- `lib.py`: portfolio P&L = sum(w_{t-1} * r_t) - 5 bp x sum|dw| (10 bp stress); the 6 engine gates;
  placebo = the whole weight matrix circularly shifted in time (500 shifts), as `study6.py`.
  A name joins the universe after 300 days of history. Weights known at the rebalance close.
- Benchmark for every rule: equal-weight buy-and-hold of the alive sectors (post-2014 Sharpe 0.75;
  IS 0.46, OOS 0.89, HOLDOUT 0.70). For dollar-neutral rules this is a strict bar, but the
  tournament's t >= 3 bar (post-2014 Sharpe ~0.83 over 12.9 years) is stricter anyway.
- Long/short legs: +1/3 on each of the top 3, -1/3 on each of the bottom 3 (gross 2). Short
  borrow cost is not modelled (small for these ETFs), which flatters the L/S rules slightly.

## Mechanisms and literature (from memory of the papers; not re-read here)
- Industry momentum (Moskowitz & Grinblatt 1999 JF): 6m-formation industry winners beat losers,
  much of stock momentum is industry momentum; 1-month industry returns show momentum, not reversal.
- 52-week high (George & Hwang 2004 JF): nearness to the 52w high predicts returns (anchoring).
- Residual momentum (Blitz, Huij & Martens 2011 JEF): momentum in factor-model residuals,
  about half the volatility of raw momentum and no crash exposure.
- Short-term reversal (Lehmann 1990; Jegadeesh 1990): weekly/monthly reversal in single stocks;
  at the industry level the 1-month effect is momentum (MG99), so the reversal side was a test.
- TSMOM (Moskowitz, Ooi & Pedersen 2012) and the 10-month SMA filter (Faber 2007).
- Oil -> stocks with a lag (Driesprong, Jacobsen & Maat 2008 JFE): decayed after 2008 (main BRAIN.md).
- Caveat: only 9-11 sector ETFs; the papers use 20-48 industries, so the cross-section is thin
  and the top-3/bottom-3 spread is noisy.

## Results log

### 2026-11-24, study 1 (`study1.py`): cross-sectional sector rules, month-end unless noted. 0 of 6

| rule | IS | OOS | HOLDOUT | post-2014 | t | placebo p | verdict |
|---|---|---|---|---|---|---|---|
| S1 industry momentum 6m, L/S top/bottom 3 (MG99) | 0.02 | 0.07 | -0.10 | -0.04 | -0.13 | 0.51 | FAIL |
| S2 industry reversal 1m, L/S | -0.02 | 0.57 | -0.63 | -0.21 | -0.75 | 0.60 | FAIL |
| S3 industry reversal 1w, weekly, L/S | -0.11 | -0.69 | -0.15 | -0.33 | -1.19 | 0.20 | FAIL |
| S4 52-week-high, L/S (GH04) | -0.11 | -0.27 | -0.07 | -0.13 | -0.48 | 0.56 | FAIL |
| S5 residual momentum vs SPY, 36m regression, 12-1 (BHM11) | -0.05 | -0.48 | 0.37 | 0.08 | 0.28 | 0.39 | FAIL |
| S6 long-only top 3 by 12-1m return | 0.46 | 0.59 | 0.75 | 0.68 (EW 0.75) | 2.45 | 0.53 | FAIL: just market beta |

(A chained-assignment bug left S5 empty on the first run; fixed and rerun, no parameter changed.)
**Reading:** among SPDR sectors no cross-sectional signal has worked since 2000, not even
in-sample (every IS Sharpe within +/-0.11). Sector momentum, reversal and 52w-high are dead or
were never there at this coarse a level. Weekly reversal has 139x/yr turnover and costs kill it.

### 2026-11-24, study 2 (`study2.py`): sector timing and oil-linked spreads. 0 of 5

| rule | IS | OOS | HOLDOUT | post-2014 | t | placebo p | verdict |
|---|---|---|---|---|---|---|---|
| S7 TSMOM 12m per sector, vol-scaled L/S | 0.59 | 0.54 | 0.27 | 0.39 | 1.41 | 0.78 | FAIL |
| S8 Faber 10m SMA per sector, long/flat | 0.68 | 0.80 | 0.75 | 0.77 (EW 0.75) | 2.78 | 0.19 | FAIL (placebo only) |
| S9 XLE minus SPY in the direction of USO's 21d return | -0.53 | 0.14 | -0.25 | -0.12 | -0.45 | 0.62 | FAIL |
| S10 IYT minus SPY against USO's 21d return | -0.36 | 0.09 | -0.15 | -0.06 | -0.21 | 0.50 | FAIL |
| S11 XLE/XOP/OIH: long best / short worst 6m return | -0.44 | 0.21 | 0.02 | 0.10 | 0.36 | 0.43 | FAIL |

**Reading:** S8 passes 5 of 6 gates but its edge over EW buy-and-hold is 0.02 Sharpe and the
placebo (same exposure, random timing) does as well 19% of the time: it is mostly long-market
exposure with a smaller drawdown (-15%), not timing skill. Its t (2.78) is below the winner bar
anyway. Energy equities do not "catch up" with last month's oil move (S9 IS -0.53, wrong sign;
the flipped rule was NOT pre-registered and is not claimed). Transports vs oil: nothing.

### 2026-11-24, study 3 (`study3.py`): XLE residual momentum (main idea queue item 5). 0 of 1

| rule | IS | OOS | HOLDOUT | post-2014 | t | placebo p | verdict |
|---|---|---|---|---|---|---|---|
| S12 sign(12-1 residual of XLE on SPY+USO) x hedged XLE | -0.96 | 0.03 | -0.32 | -0.20 | -0.72 | 0.61 | FAIL |

Hedge ratios are sane (b_SPY 0.8-1.2, b_USO 0.2-0.35); lost 71% in 2020 when the USO leg
crashed. Hedged-XLE residuals do not trend; if anything they revert (IS -0.96, not pre-registered).

## Scorecard
Rules tried: **12** of 15 (3 left unused on purpose: no rule came close enough to justify a
neighbour-parameter check, and spending them on flipped signs would be a search).
Winners: none. Candidates: none.

## Idea queue (top first; NOT run)
1. Industry momentum needs a wider cross-section: 30-50 industry portfolios (Ken French data
   library, if reachable) or iShares/SPDR industry ETFs (from ~2006) rather than 9-11 sectors.
2. Reversal side of S12 (hedged XLE residual mean reversion, IS -0.96 for momentum): only as a new
   pre-registered study with its own IS choice, and it would count against a fresh budget.
3. S8-style trend filters are a risk-reduction tool (drawdown -15% post-2014), not alpha; evaluate
   on drawdown, not Sharpe, if ever revisited.
