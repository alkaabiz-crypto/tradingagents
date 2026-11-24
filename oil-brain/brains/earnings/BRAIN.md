# Earnings brain: earnings-announcement effects in large US stocks

Memory of brain `earnings` (tournament, rules in `../RULES.md`). Engine `../../engine.py` unchanged.
Splits: the engine's own (IS 2005-06..2013, OOS 2014-2019, HOLDOUT 2020-2026-11). EDGAR Item 2.02
dates reach back to late 2004, so the fallback split (IS 2010-15) was NOT needed.

## Data (fetch.py, data/)
- Universe: 92 large US stocks (S&P 100-type names public before 2005), Yahoo adjusted closes
  2004-2026. **Survivorship bias**: picked from today's survivors. Diagnostic (diag1.py): a long
  leg of ANY earnings-sorted group beat SPY in IS/OOS, which is mostly that bias. From study 2 on,
  long legs are hedged with the equal-weighted universe of the same 92 names, not SPY.
- Earnings dates: SEC EDGAR 8-K Item 2.02 (data.sec.gov submissions JSON, incl. older CIKs for
  GOOGL, XOM, MDT, DIS, ACN, ORCL, BNY). acceptanceDateTime is UTC; converted to New York time,
  at/after 16:00 -> day 0 = next trading day. Repeat 2.02 filings within 30 days dropped.
  8,350 events. Check vs Yahoo earnings dates (AAPL, JPM, IBM 2005-26): 263 of 264 day-0s match.
- Surprise proxy: CAR(0,+1) vs SPY (no free consensus data).
- Predicted dates (for anything traded BEFORE the announcement): day 0 of the event a year
  earlier + 364 days (Frazzini & Lamont 2007). IS accuracy: 62% within +-1 trading day, 76% +-3.

## Method
Own daily portfolio builder (common.py): each active position is a stock +-1 hedged (SPY or EW
universe), equal weighted across active positions, 10 bp per side on every weight change
(stocks and hedge). The net series goes into engine.evaluate with pos=1, cost 0, bench = SPY.
Engine's circular-shift placebo is degenerate for a constant position, so gate 4 uses an
event-date placebo (each event date moved by random +-10..50 trading days, rebuild, 200 times);
gate 5 is the 2x-cost series. Study 4 (an ETF timing rule) uses the engine natively.
Caveat on the event-date placebo: real dates cluster in earnings seasons, shifted dates do not,
which changes the equal-weight churn; for the daily rules (A1-A3) the placebo is worse partly
because of costs, so their p = 0.00 should not be read as strong evidence.

## Mechanisms and sources (abstract-level, not re-verified from paper tables)
- PEAD: Bernard & Thomas (1989); decline: Chordia, Subrahmanyam & Tong (2014); Martineau (2022)
  "Rest in peace post-earnings announcement drift": gone in large caps since ~2006.
- Announcement premium: Beaver (1968), Frazzini & Lamont (2007), Barber, De George, Lehavy &
  Trueman (2013); Savor & Wilson (2016) tie it to systematic risk.

## Rules tried: 7 of 15 budget. 0 PASS, 0 winners, 0 candidates

| # | rule | IS | OOS | HOLD | post (SPY) | t | placebo p | verdict |
|---|---|---|---|---|---|---|---|---|
| P1 | PEAD L/S top/bottom quintile CAR(0,1), hold 60d, SPY hedge | -0.27 | -0.12 | -1.02 | -0.70 (0.80) | -2.51 | 0.86 | FAIL 6/6 |
| P2 | same, hold 20d | -0.24 | -0.82 | -0.81 | -0.80 (0.80) | -2.86 | 0.72 | FAIL 6/6 |
| A1 | long P-2..P+1 around predicted date, EW hedge | 0.16 | 0.13 | -0.50 | -0.28 (0.80) | -0.99 | 0.00* | FAIL 5/6 |
| A2 | long P-10..P-3 (pre-announcement), EW hedge | -0.70 | -0.57 | -0.28 | -0.38 (0.80) | -1.37 | 0.00* | FAIL 5/6 |
| A3 | A1 with fixed 1/10 slots (no re-weighting churn) | -0.16 | -0.87 | -1.03 | -0.96 (0.80) | -3.43 | 0.00* | FAIL 5/6 |
| E1 | Frazzini-Lamont monthly: long predicted announcers vs EW | 0.51 | -0.12 | -0.07 | -0.09 (0.80) | -0.31 | 0.035 | FAIL 5/6 |
| M1 | SPY only when >= 9 of 92 names due in next 5 days | 0.51 | 0.60 | 0.74 | 0.67 (0.80) | 2.42 | 0.14 | FAIL 2/6 |
(* see placebo caveat above). All Sharpes net of costs.

## What the results say
1. **PEAD is dead in large caps** (agrees with Martineau 2022). Gross L/S Sharpe 60d: IS 0.09,
   OOS 0.41, HOLDOUT -0.72; 20d: 0.36, 0.06, -0.22. Net of 10 bp it is negative everywhere.
   Losers (bad reactions) did not keep falling relative to SPY; if anything large caps
   partially reverse. No reversal rule was run: it would be chosen from OOS/HOLDOUT results.
2. **The announcement premium exists gross, but costs eat it.** A1 gross: Sharpe 0.97 IS,
   1.08 OOS, 0.08 HOLDOUT; ~10%/yr gross post-2014 on the active book, i.e. ~16 bp per 4-day
   event vs ~40 bp round trip (stock + hedge at 10 bp/side). Net -7%/yr. The premium also
   faded after 2019. Fixed slots (A3) did not help: the problem is per-event cost, not churn.
3. **Monthly version (E1) has low cost but the premium decayed**: gross Sharpe 0.84 IS,
   0.33 OOS, 0.21 HOLDOUT, ~1.8%/yr gross post-2014 vs ~2.4%/yr cost.
4. **Market level (M1)**: SPY earned more on earnings-season days in all three periods
   (IS 11.1 vs 1.4 bp/day; 2014-19 6.6 vs 4.1; 2020-26 10.2 vs 4.1) but the difference is not
   significant (Welch t 1.30 IS, 1.14 post-2014; diag4.py) and the rule's Sharpe (0.67) is
   below SPY buy-and-hold (0.80), placebo p 0.14.

## Idea queue (not run; each would count against the budget)
- Cost is the binding constraint. At 2-3 bp/side (realistic for mega caps) A1 might be net
  positive pre-2020, but RULES require 10 bp for single stocks, and HOLDOUT gross is ~0 anyway.
- Intra-industry information transfer (Thomas & Zhang 2008): early announcers' reaction ->
  late announcers in the same industry. Same per-event cost wall.
- Options-implied earnings moves (no free data).
- M1 as a forward-test curiosity only; not a candidate (fails gates 2 and 4).
