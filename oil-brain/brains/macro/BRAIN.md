# Macro brain: cross-asset and macro signals for oil and US stocks

Memory of brain `macro` (tournament, rules in `../RULES.md`). Engine `../../engine.py` unchanged.
IS 2007-06..2013 (limited by HYG/DBB/UUP history; contains the GFC), OOS 2014-2019, HOLDOUT
2020-now. All rules monthly (signal at month-end close, held one month), 5 bp per unit turnover.
Extra Yahoo data in `data/` (^IRX, ^FVX, HYG, LQD, IEF, SHY, UUP, JNK) via `fetch.py`.

## Mechanisms and sources (abstract-level, not re-verified from paper tables)
- Dollar and oil: oil is priced in dollars, so a weaker dollar historically lifted oil; ECB
  (2024) notes the correlation weakened / changed sign as the US became a net oil exporter.
- Copper/gold ratio: growth vs fear; used by practitioners as a growth and yield signal.
- Credit spreads: Gilchrist & Zakrajsek (2012 AER) excess bond premium predicts activity and
  stock returns. HYG/LQD relative return is a crude tradable proxy.
- Lead-lag: Hong, Torous & Valkanov (2007 JFE): some industries (incl. metals, petroleum) lead
  the market; Rapach, Strauss & Zhou (2013 JF): lagged US returns predict other markets.
- Stock-bond correlation: positive in inflation-driven regimes (pre-2000, 2022 on), negative
  in demand-driven regimes.

## Facts measured here
- **ECB claim confirmed in data** (study2 part A): yearly corr of daily DXY and USO returns was
  -0.38 to -0.47 in 2008-2012, about -0.1 in 2013-2019, then 0.08 (2020), 0.00 (2024),
  +0.22 (2025), +0.23 (2026). A fixed-sign dollar rule is therefore unsafe.
- IS lead-lag table (2007-2013, monthly, 21 pairs): strongest |t| were credit (HYG-LQD) -> next
  month USO (t 2.99), SPY -> USO (2.93), USO -> USO (2.74), GLD -> XLE (-2.39). Expected
  maximum |t| over 21 mostly-null pairs is about 2.5, so none is convincing on its own.

## Rules tried (13 of 15 budget). 0 PASS, 0 winners, 0 candidates

| # | rule | IS | OOS | HOLD | post (bench) | t | placebo p | verdict |
|---|---|---|---|---|---|---|---|---|
| M1 | -sign(DXY 21d) -> USO L/S | 0.32 | 0.67 | -0.05 | 0.23 (0.05) | 0.84 | 0.20 | FAIL: died when the sign flipped |
| M2 | Cu/Au 63d up -> USO L/F | 0.77 | -0.14 | 0.57 | 0.30 (0.05) | 1.07 | 0.14 | FAIL |
| M3 | Cu/Au 63d up -> SPY L/F | 0.82 | 0.92 | 0.76 | 0.80 (0.80) | 2.85 | 0.11 | FAIL: = market exposure |
| M4 | HYG/LQD 21d up -> SPY L/F | 0.09 | 0.37 | 1.16 | 0.85 (0.80) | 3.04 | 0.10 | FAIL: placebo |
| M5 | HYG/LQD 21d up -> USO L/F | 0.20 | -0.31 | 1.08 | 0.53 (0.05) | 1.90 | 0.01 | FAIL |
| M6 | TNX 63d up -> XLE L/F | 0.40 | -0.45 | 0.97 | 0.46 (0.36) | 1.66 | 0.14 | FAIL |
| M7 | corr(SPY,TLT)>0 -> XLE-SPY | -0.06 | -0.02 | 0.03 | 0.02 (-0.16) | 0.06 | 0.32 | FAIL: nothing |
| M8 | DBB 1m down -> SPY L/F (HTV07) | -0.04 | 0.58 | 0.65 | 0.61 (0.80) | 2.18 | 0.30 | FAIL |
| M9 | composite (Cu/Au, credit, TNX) -> USO L/S | 0.60 | -0.02 | 0.84 | 0.51 (0.05) | 1.84 | 0.04 | FAIL |
| M10 | IS-selected credit 1m -> USO L/S | 0.21 | -0.13 | 1.10 | 0.60 (0.05) | 2.16 | 0.01 | FAIL: OOS |
| M11 | credit switch SPY/IEF | 0.37 | 0.56 | 1.14 | 0.91 (0.80) | 3.25 | 0.056* | FAIL: placebo, and = static mix |
| M12 | HYG/LQD 63d up -> USO L/F | 0.35 | -0.43 | 1.03 | 0.50 (0.05) | 1.79 | 0.01 | FAIL |
| M13 | HYG/LQD 21d up -> XLE L/F | 0.27 | -0.70 | 1.27 | 0.58 (0.36) | 2.07 | 0.05 | FAIL: OOS |

*M11's engine placebo is degenerate (constant position, p = 1.00); study2b applies the same
placebo method to the switch path: p = 0.056. A static 56% SPY / 44% IEF mix (same average
weight) has post-2014 Sharpe 0.89 vs the switch's 0.91, so the "beat SPY" is diversification,
not timing. Outside 2020H1 and 2022 the switch (1.15) trails SPY (1.21).

## Readings
1. **Credit signals carry the paper's sign but only in crises.** Every credit rule on oil
   (M5, M10, M12, M13) lost money in OOS 2014-2019 (Sharpe -0.1 to -0.7) and made all its
   profit in 2020-2022 (M5: +57% 2020, +56% 2021, +58% 2022) and 2026. Same "crisis alpha"
   shape as oil momentum (main BRAIN.md study 3): a risk-off filter, not a steady edge.
2. **Long/flat SPY timers do not beat buy-and-hold on a timing test.** M3, M4, M8 have
   t 2.2-3.0 but placebo p 0.10-0.30: the t comes from being long stocks in a bull market.
3. **Dollar -> oil is regime-dependent** (sign flipped 2020-2026), so do not trade it with a
   fixed sign. Stock-bond correlation regime says nothing about XLE vs SPY (M7, t 0.06).

## Idea queue (2 rules of budget left, not used on purpose)
- Forward-test only, no new backtests: track M5 (credit -> USO long/flat) as a risk-off
  overlay for the main brain's momentum candidates; do not count it as an edge.
- If re-opened: cross-sectional macro betas across many commodities (needs a broader
  universe), or the true GZ excess bond premium series (Fed website), not an ETF proxy.
