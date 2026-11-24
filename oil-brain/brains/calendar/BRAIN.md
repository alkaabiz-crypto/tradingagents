# Calendar brain: overnight and calendar effects in US stocks, oil ETFs and Treasuries

Memory of the `calendar` brain (tournament rules: `../RULES.md`). Engine `../../engine.py`
unchanged. IS to 2013, OOS 2014-2019, HOLDOUT 2020-2026-11-23. Costs 5 bp per unit of
turnover (10 bp for a two-leg spread). **Rules used: 15 of 15.**

## Mechanisms and sources (from memory of the papers; tables not re-read)
- Overnight vs intraday: Cliff, Cooper & Gulen (2008); Kelly & Clark (2011); Lou, Polk & Skouras
  (2019 JFE). The equity premium accrues close->open; intraday ~0.
- Turn of the month (days -1..+3): Lakonishok & Smidt (1988); McConnell & Xu (2008).
- Pre-holiday: Ariel (1990). Option-expiration week: Stivers & Sun (2013).
- Month-end rebalancing (stocks vs bonds): Harvey, Mazzoleni & Melone (2025).
- Treasury month-end: index-extension demand (Barclays/Bloomberg index duration resets on the last
  business day; e.g. Hartley & Schwarz). Window used (last 3 days) was NOT checked against the paper.
- FOMC pre-announcement drift (Lucca & Moench 2015): NOT tested. federalreserve.gov is blocked
  from the sandbox (HTTP 403 at the proxy) and I could not list 1994-2026 scheduled dates from
  memory without error. Idea queue item 1.

## Method notes
- Overnight rules use a half-day series (overnight at 09:30, intraday at 16:00) fed to the engine:
  2 sides per day, 5 bp each. Engine Sharpe uses sqrt(252) on 504 obs/yr, so every Sharpe in
  study 1 (rule and benchmark) is understated by sqrt(2); t-stats are right.
- The placebo is structurally weak for strictly periodic rules: even shifts reproduce the same
  overnight rule and tie, so placebo p can never go below ~0.5 there.
- Disclosure: before pre-registering study 1 I printed period mean overnight/intraday returns for
  all six instruments (all periods) as a data sanity check. The overnight rules and instruments
  were fixed by the brief, not by that printout.
- Holidays: weekdays without SPY trading, minus 9/11/2001 week and Hurricane Sandy (unscheduled).
  ~8.9 pre-holiday days a year. Funeral closures (2004, 2007, 2018, 2025) kept: announced ahead.
- Yahoo Opens: SPY 1993-94, IWM 2001-02, XLE 1999-2004 have 5-14% of days with open == prior
  close (stale opens); all in IS, they bias IS overnight returns toward zero.

## Results log (2026-11-24)

### Study 1 (`study1.py`): overnight only, 5 bp per side. 0 of 4 pass
| rule | IS | OOS | HOLDOUT | post (x sqrt2) | bench (x sqrt2) | t post | verdict |
|---|---|---|---|---|---|---|---|
| O1 SPY overnight | -1.00 | -1.47 | -0.78 | -1.40 | 0.80 | -5.01 | FAIL 6/6 |
| O2 QQQ overnight | -0.48 | -0.86 | -0.52 | -0.89 | 0.86 | -3.18 | FAIL 6/6 |
| O3 IWM overnight | -0.63 | -1.40 | -0.31 | -0.86 | 0.46 | -3.10 | FAIL 6/6 |
| O4 USO overnight | -1.17 | -1.07 | -0.21 | -0.71 | 0.04 | -2.56 | FAIL 6/6 |
Diagnostics, same rules: **gross** the overnight premium is real and alive (post-2014 t 3.1 SPY,
3.6 QQQ, 3.6 IWM; ~3.5-7 bp a night) but at **2 bp/side it is already ~zero** (t -0.1 SPY,
0.9 QQQ/IWM). USO has no overnight premium (gross t 0.65). It is a fact about where returns
accrue, not a trade: a round trip costs more than the night earns.

### Study 2 (`study2.py`): classic calendar rules, daily. 0 of 9 pass
| rule | IS | OOS | HOLDOUT | post | bench | t post | placebo p | verdict |
|---|---|---|---|---|---|---|---|---|
| C1 TOM SPY (-1..+3) | 0.40 | -0.12 | 0.50 | 0.25 | 0.80 | 0.91 | 0.34 | FAIL 4/6 |
| C2 TOM IWM | 0.20 | -0.34 | 0.10 | -0.07 | 0.46 | -0.24 | 0.75 | FAIL 6/6 |
| C3 pre-holiday SPY | -0.07 | -0.28 | 0.51 | 0.09 | 0.80 | 0.31 | 0.27 | FAIL 5/6 |
| C4 Thanksgiving Wed+Fri SPY | 0.23 | -0.05 | 0.02 | 0.00 | 0.80 | 0.01 | 0.52 | FAIL 6/6 |
| C5 opex week SPY | 0.23 | 0.74 | -0.54 | -0.08 | 0.80 | -0.29 | 0.94 | FAIL 5/6 |
| C6 month-end rebalancing SPY-TLT | 0.29 | 0.59 | 0.35 | 0.45 | 0.48 | 1.61 | 0.00 | FAIL 2/6 (bench, t) |
| C7 TLT last 3 days | 0.71 | 1.01 | 0.25 | 0.55 | 0.15 | 1.98 | 0.00 | FAIL 2/6 (HOLDOUT, t) |
| C8 TOM XLE | 0.21 | -0.35 | 0.28 | 0.03 | 0.36 | 0.11 | 0.50 | FAIL 6/6 |
| C9 TOM USO | 0.23 | -0.68 | 0.27 | -0.13 | 0.05 | -0.46 | 0.66 | FAIL 6/6 |
The famous equity calendar effects (TOM, pre-holiday, Thanksgiving, opex) are dead or too small
after 2014 once 5 bp per side is charged. Oil ETFs show nothing at the turn of the month.

### Study 3 (`study3.py`, pre-registered after study 2): 1 of 2 passes engine gates
| rule | IS | OOS | HOLDOUT | post | bench | t post | placebo p | CAGR | verdict |
|---|---|---|---|---|---|---|---|---|---|
| C10 quarter-end rebalancing SPY-TLT | -0.15 | 0.07 | 0.14 | 0.11 | 0.48 | 0.39 | 0.15 | 1% | FAIL 6/6 |
| C11 IEF last 3 days (C7 window, other instrument) | 0.58 | 0.83 | 0.58 | 0.67 | 0.29 | 2.39 | 0.00 | 1.5% | PASS engine, t < 3 |
TLT last-3-day mean: IS 13.9 bp/day, OOS 14.9, HOLDOUT 7.0; all other TLT days 0.0 bp.
Gross sum positive in 24 of 25 years (2026 YTD -3.3% is the only loss).

## Verdict
- **Winners (t >= 3): none.**
- **Candidate: C11 long IEF on the last 3 trading days of each month** (all 6 gates, t 2.39,
  placebo p 0.00). Caveats: chosen as a replication after seeing C7 fail; 15 rules tried, so a
  t ~2.4 is not proof; small (1.5% CAGR at ~14% time in market); 2x-cost P&L thin (+3.7% total
  post-2014). Supported by the TLT version (positive in every period, 24/25 years) and by a
  clear mechanism (index duration extension at month-end). Effect roughly halved since 2020.

## Idea queue
1. FOMC drift (Lucca & Moench) once the scheduled dates can be fetched (federalreserve.gov).
2. Forward paper test of C11 (and C7) from 2026-11-24: log each month's last 3 days.
3. Month-end bond effect with the window from the paper itself (needs the paper; do not pick
   the window on post-2014 data).
4. Overnight premium is only tradable for someone who is already long: e.g. do intraday
   rebalancing/entries at the open rather than the close (an execution rule, not alpha).
