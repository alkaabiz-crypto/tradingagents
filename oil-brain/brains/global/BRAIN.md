# Global brain: US-listed country equity ETFs

Memory of brain `global` (tournament, rules in `../RULES.md`). Engine `../../engine.py` unchanged
(daily rules use `engine.evaluate`; monthly weight-matrix rules use `lib.evaluate_w`, same splits,
same 6 gates, placebo = whole weight matrix circularly shifted in time as in `study6.py`).
Data: Yahoo auto-adjusted OHLCV for 20 country ETFs + NORW, EWM, EFA, ACWX, EEM, SPY in `data/`
(`fetch.py`). WTI from shared `../../data/CL_F.csv`. Costs: 10 bp per unit turnover monthly,
5 bp daily (ETF minimum; the 2x-cost gate then tests 10 bp). Benchmark: equal-weight country
basket (daily rules: the traded Asia basket buy-and-hold).
Verdict notation "FAIL (k of 6 gates)" = k gates FAILED.

## Data caveats
- 1996-2000 WEBS data are stale: 10-60% of days have zero close-to-close change (EWK, EWO worst),
  so early IS returns are partly fiction; daily rules start 2001.
- Universe is today's surviving ETFs (no dead country funds); small bias, mostly matters for
  long-only rules.
- CL=F continuous future has roll jumps; used only for the sign of the 1-month change.

## Mechanisms and sources (abstract-level, not re-verified from paper tables)
- Asness, Moskowitz & Pedersen (2013 JF): value and momentum in country indices, negatively correlated.
- Richards (1997 JF): country winner/loser reversal over 3-5 years.
- Chan, Hameed & Tong (2000 JFQA): momentum in country indices at short horizons.
- Rapach, Strauss & Zhou (2013 JF): lagged US returns predict non-US returns.
- Driesprong, Jacobsen & Maat (2008 JFE): oil rises predict lower stock returns next month.
- Engle & Sarkar (2006): ETF premiums; stale-NAV literature: home market catches up to the US move.

## Facts measured here
- IS diagnostic (diag2.py, 2001-2013): Asian ETF next-day NY close-to-close return is NEGATIVELY
  related to today's SPY return (t -4 to -10 per ETF) and to its own return. So the ETF's NY close
  does NOT under-react to the US session (the stale-NAV catch-up is already in the ETF price); if
  anything it over-reacts and partly reverses. Both overnight and intraday legs reverse. INDA none.
- The fade is real timing (placebo p 0.00-0.01) but its gross P&L is concentrated in crises
  (2008: +137% gross for T1, 2020: +38%); in calm years it is a few % gross, less than the cost of
  trading ~240 days a year.
- Cross-country 12-1 momentum L/S lost money in IS and post-2014 (post Sharpe -0.39); 1-month
  momentum strongly negative (post -0.57, t -2.05), i.e. 1-month country reversal. AMP-style
  value (5y reversal) weakly positive post-2014 (0.24) but negative IS.

## Rules tried (11 of 15 budget). 0 PASS, 0 winners, 0 candidates

| # | study | rule | IS | OOS | HOLD | post (bench) | t | placebo p | verdict |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 1 | G1 12-1 mom L/S 4/4 monthly | -0.04 | -1.02 | 0.01 | -0.39 (0.46) | -1.40 | 0.90 | FAIL 6 |
| 2 | 1 | G2 12-1 mom long-only top 5 | 0.48 | 0.03 | 0.53 | 0.33 (0.46) | 1.18 | 0.79 | FAIL 4 |
| 3 | 1 | G3 value (5y reversal) L/S 4/4 | -0.28 | 0.25 | 0.24 | 0.24 (0.46) | 0.87 | 0.11 | FAIL 5 |
| 4 | 1 | G4 value+mom rank combo L/S 4/4 | -0.30 | -0.62 | 0.47 | -0.02 (0.46) | -0.07 | 0.26 | FAIL 5 |
| 5 | 2 | T1 fade SPY day in Asia basket, daily | 0.63 | -0.08 | 0.19 | 0.09 (0.42) | 0.32 | 0.00 | FAIL 5 |
| 6 | 2 | T2 fade own Asia basket day, daily | 0.35 | -1.12 | 0.27 | -0.25 (0.42) | -0.88 | 0.01 | FAIL 5 |
| 7 | 3 | R1 EW basket if SPY 1m > 0 (Rapach) | 0.50 | -0.14 | 0.45 | 0.18 (0.46) | 0.64 | 0.82 | FAIL 4 |
| 8 | 3 | O1 EW basket if oil 1m < 0 (Driesprong) | 0.18 | 0.34 | 0.41 | 0.38 (0.46) | 1.36 | 0.27 | FAIL 3 |
| 9 | 3 | O2 exporters-importers x sign(oil 1m) | -0.03 | 0.13 | -0.43 | -0.21 (0.46) | -0.74 | 0.52 | FAIL 6 |
| 10 | 4 | T3 fade SPY >1.5% days in Asia basket | 0.86 | 0.40 | 0.50 | 0.44 (0.42) | 1.59 | 0.002 | FAIL 1 (t) |
| 11 | 4 | C1 1m country momentum L/S 4/4 | -0.36 | -0.95 | -0.36 | -0.57 (0.46) | -2.05 | 0.83 | FAIL 6 |

Best: T3 (5 of 6 gates; fails t >= 2). Its post-2014 P&L is mostly 2020 (+42%); 2014-2019 sums
to about +14% over 6 years, 2021-2026 about 0. It is a crisis-convexity trade, not a steady edge,
and 2008 (+111%) dominates IS. Not a candidate.

## Notes / honesty
- T3 was chosen after seeing study 2 IS year-by-year results (gross P&L concentrated in big days);
  the 1.5% threshold was set a priori, not searched. It also saw that T1 OOS was weak, which is a
  mild contamination: treat T3 as a hypothesis generated with partial OOS knowledge.
- C1's strongly negative result suggests 1-month cross-country REVERSAL; it was NOT tested because
  flipping a rule after seeing OOS/HOLDOUT is tuning on OOS. Logged for a forward test only.

## Idea queue (unused budget: 4)
- 1-month country reversal (forward test only, contaminated in backtest).
- Fade-big-US-days in Asia ETFs as a crisis overlay combined with a long position (convexity).
- Premium/discount with actual NAV data (iNAV / iShares NAV history) instead of SPY as a proxy.
- Real country value (CAPE / book-to-market) needs data Yahoo does not have.
