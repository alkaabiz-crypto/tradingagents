# BTC paper trader

Paper money only: no real orders are placed. There are five separate paper
accounts, each starting with $300:

| Mode | Candles | Stop-loss | Take half profit at | Files |
|---|---|---|---|---|
| `2h` (intraday) | 2-hour | 1.5% below entry | +3% | `ledger_2h.json`, `journal_2h.md` |
| `daily` (swing) | daily | 4% below entry | +7% | `ledger.json`, `journal.md` |
| `range2h` (range) | 2-hour | 0.5% below range low | middle of range | `ledger_range2h.json`, `journal_range2h.md` |
| `oil_range2h` (OIL EXPERIMENT) | 2-hour, WTI crude (CL=F) | 0.5% below range low | middle of range | `ledger_oil_range2h.json`, `journal_oil_range2h.md` |
| `dip2h` (EXPERIMENT) | 2-hour | 2% below entry | +2.5% | `ledger_dip2h.json`, `journal_dip2h.md` |

A scheduled task runs all modes every 2 hours, 5 minutes after each 2-hour
candle closes (even UTC hours). The daily mode keeps one journal row per day.

    python3 paper/btc_paper.py --mode 2h
    python3 paper/btc_paper.py --mode daily

## Rules (spot only, no leverage)
- **Buy** only when, on the last completed candle:
  - the price is above its 20-candle average,
  - the 20-candle average is above the 50-candle average,
  - RSI(14) is between 40 and 65,
  - and the price is just above the 20-candle average (within 1% for 2h,
    3% for daily).
  - 2h only: the last daily close is above the 20-day average (daily trend
    filter, added after the first backtest).
- **Size:** half the account.
- **Take profit:** sell half at the target, then move the stop up to the entry
  price.
- **Exit the rest** when a candle closes below the 20-candle average.
- **After any exit:** wait for a fresh candle before buying again.
- **Brakes:**
  - after 2 losing trades in a row, no buys for the rest of the day (2h) or the
    next day (daily);
  - if the account is down $20 in a week, no buys until next Monday.
- **Fees:** 0.4% is charged on every paper fill (about 0.8% per round trip).

## Statuses
- `WAIT`: the trend is down; stay in cash.
- `GET READY`: price is back near or above the 20-candle average.
- `BUY SIGNAL`: all checks pass; a paper buy is made.
- `HOLD`: a paper position is open.

## Dip-buy EXPERIMENT (`dip2h`)
Counter-trend and riskier: it buys bounces after sharp drops, so it is a test,
not a recommended strategy.
- **Buy** when RSI(14) was below 30 in one of the 3 candles before the last,
  and the last 2-hour candle closes green, above the previous close, with RSI
  back at 30 or more.
- **Size:** a quarter of the account (about $75).
- **Stop-loss:** 2% below entry. **Take profit:** sell half at +2.5%, then
  move the stop to entry.
- **Exit the rest** when a candle closes back at or above the 20-candle
  average, or after 12 candles (24 hours), whichever comes first.
- The same brakes and fees apply.

## Range trading (`range2h`)
Buys near the bottom of a sideways range and sells in the middle and near the
top. It buys only when **every** check passes on the last completed 2-hour candle:
- **Range:** the high and low of the last 24 candles (48 hours) are 2-8% apart.
- **Sideways:** the 20-candle average moved less than 1% over the last 10 candles.
- **Bottom quarter:** the live price is in the bottom 25% of the range.
- **Bounce:** the last candle closed green, with RSI below 50.
- **Reward vs risk:** the distance to the middle of the range is at least 1.2x
  the distance to the stop.
- **Calm:** the last candle is no more than 2.5x the size of the 20 before it.
- **News:** `news_gate.json` says OK and is less than 2 hours old. Before each
  run the latest Bitcoin headlines are checked; the gate is set to BLOCK on
  hacks, exchange problems, regulatory action, a big scheduled macro event
  (Fed, CPI, jobs) within a few hours, or a crash in progress.

- **Size:** 30% of the account (about $90).
- **Stop-loss:** 0.5% below the range low.
- **Take profit:** sell half at the middle of the range, then move the stop to
  the entry price.
- **Sell the rest** near the top of the range (85% of the way up), or after 12
  candles (24 hours).

## Oil range EXPERIMENT (`oil_range2h`)
The same range rules on WTI crude oil futures (Yahoo Finance `CL=F`, hourly,
merged into 2-hour candles), with extra oil blackouts. No new trades:
- while the oil market is closed (no candle for 2 hours, e.g. weekends);
- Wednesday 9:00-13:00 New York time, around the weekly EIA inventory report
  (10:30 New York);
- Friday after 13:00 New York time (weekend gap risk);
- unless `oil_news_gate.json` is OK and less than 2 hours old.

**Backtest (2 years): it lost money** (-13% with 0.4% fees, -3% with 0.05%
fees; about 1 in 3 trades won), so it is tracked on paper only.

### Why there is no EIA-report trade
Over 123 Wednesday reports (2024-2026), the report hour moved about 1.7x more
than a normal hour, but following the first move after a big reaction won only
50-56% of the time, and the average gain was smaller than the fees. Betting
against it did not work either. Traders who profit from the report use the
analyst forecast, the paid API report from the day before, and very fast
execution, none of which this setup has. The useful edge here is staying out
of that window.

## BTC weekly trend (`trend_paper.py`) - the one that passed the edge study
Time-series momentum, the best-documented edge in the research (see
`edge_study.py` / `edge_study_results.md`). Once a week:
- 50% of the target if BTC is up over the last 28 days, plus 50% if it is up
  over the last 56 days;
- scaled down when BTC is wild (target at most 50% yearly volatility);
- buy or sell to that target; otherwise cash. No leverage, no shorting.

Backtest 2014-2026 (0.10% costs): +46% a year, worst drop -54%, Sharpe 1.23,
vs holding BTC +49% a year, worst drop -83%, Sharpe 0.94. It beat holding on a
risk-adjusted basis in both halves of the history.

## ETH weekly trend (`trend_paper.py --asset ETH`) - account #7
The BTC weekly trend rule, unchanged, on ETH. ETH was never used to design
the rule, so the backtest is a true out-of-sample test (`anomaly_study2.py`
test 13): 2017-2026 +33.5% a year, worst drop -55%, Sharpe 0.95, vs holding
ETH Sharpe 0.65; second half 0.83 vs 0.27; luck check 97%.

## S&P 500 volatility-managed (`volspy_paper.py`) - account #8
Moreira & Muir (2017): each month hold min(1, 15% / last 21 days' yearly
volatility) in SPY, rest in cash (`anomaly_study2.py` test 9): 2000-2026
+7.8% a year, worst drop -40%, Sharpe 0.60 vs holding SPY 0.49; luck check
98%. A narrow pass in the second half (0.85 vs 0.82). Trades only while the
US market is open.

## Studies
- `anomaly_study.py` / `anomaly_study2.py`: 14 academic anomalies tested with
  the same pass rules (luck check >= 95%, Sharpe above the benchmark in both
  halves, positive after costs). Passed: ETH trend (#7) and volatility-managed
  S&P 500 (#8). Results in `anomaly_study_results.md` and
  `anomaly_study2_results.md`.

## Nasdaq 100 volatility-managed (`volspy_paper.py --asset QQQ`) - account #9
The account #8 rule, unchanged, on QQQ (never used to design it;
`anomaly_study3.py` test 16): 2000-2026 +9.6% a year, worst drop -43%,
Sharpe 0.66 vs holding QQQ 0.42 (worst drop -83%); luck check 97%.

Batch 3 also showed the crypto trend rule does NOT work on smaller coins
(10 other large coins: luck check 34%), so it is used on BTC and ETH only.

## S&P 500 vol-managed + 200-day filter (`volspy_paper.py --asset SPY200`) - account #10
Account #8's rule, plus cash whenever SPY closes below its 200-day average
(checked each trading day; `anomaly_study4.py` test 25): 2000-2026 +6.6% a
year, worst drop -20% (vs -55% holding SPY), Sharpe 0.67 vs 0.49; luck 96%.

## Gold vol-managed (`volspy_paper.py --asset GLD`) - account #11
Account #8's rule on gold, never tuned on gold (`anomaly_study4.py` test 28):
2004-2026 +9.1% a year, worst drop -43%, Sharpe 0.66 vs holding GLD 0.58;
luck 98%.

Across 30 tests about 1-2 false passes are expected by chance at the 95% bar;
the volatility-managed rule passing on SPY, QQQ and gold (but not on EFA or
IWM) makes it more believable than any single pass.
