# Exness swap-free strategy lab (Nov 2026)

This folder holds rule-based backtests run alongside TradingAgents. They price the rules for a small Exness Standard,
UAE Extended Swap-Free account, which charges no commission and no swap, so the spread is the only cost. Nothing here
changes the TradingAgents package itself.

## Survivors

| Plan | Market and size | Rule | 2024-now (real lot $) | Worst drop |
|---|---|---|---|---|
| BTC NR4 breakout | BTCUSD, 0.01 lot | After a UTC day whose range is the smallest of the last 4: buy-stop at its high and sell-stop at its low. The other level is the stop. Close at the daily close. | +$599 | -$145 |
| USTEC overnight hold | USTEC, 0.05 lot (needs ~$1,000) | Buy at 15:55 NY only if the price is above the 200-day SMA. Sell at the next open (09:00-09:30 NY). | +$426 | -$128 |
| Both together | | Correlation ~0; a trade is open in both on only 8-11% of days | +$1,026 | -$123 |

**BTC NR4**
- It made money in every year from 2014 to 2026 (`batch23_nr4_yearly.py`).
- A walk-forward search over 270 settings found nothing better than the base rule out of sample (`batch24_nr4_walkforward.py`).
- Since 2021 its edge has been far smaller than it was in 2014-20.

**USTEC overnight**
- It made money in each of 2000-13, 2014-19, 2020-23 and 2024-now (`batch15_overnight_variants.py`).
- Crash-period drops at 0.05 lot were between $89 and $248 (`batch10_stress.py`).

## What failed

About 600 rule/market tests were run. These failed:
- Famous swing rules, beyond the leads above: RSI(2), IBS at the next open, golden cross, and Turtle.
- Candle and oil studies.
- Every day-trade rule tested with a stop-loss and take-profit on USTEC, US500 and gold, on daily, hourly and 5-minute bars: opening-range breakouts, Williams breakout with stops, trend-day entries, pivot bounce, Turtle Soup, 80-20, Crabel stretch, RSI, Bollinger, EMA cross, VWAP and Supertrend + VWAP.
- The same day-trade rules on oil.

Breakouts only work on BTC (`batch26_breakouts.py`).

## Method

- Rules were written down before each run, with nothing tuned on the test period.
- The periods are 2014-19, 2020-23 and 2024-now. The PASS bar is Sharpe > 0.3 in all three, plus t >= 2.
- Checks: neighbouring parameters, a block bootstrap, a 2x cost check, and walk-forward tests.
- When a bar touches both the stop and the target, the stop counts (worst case).
- Data: Yahoo daily and hourly bars, plus Binance 1-minute BTC bars run on the user's PC. Index CFDs use proxies: USTEC ≈ QQQ x 41 and US500 ≈ SPY x 10.

## Files

- `scripts/`: one script per batch (`batch3` ... `batch27`), plus:
  - `famous2_lib.py`: shared helpers.
  - `path_sim.py`: an OHLC path simulator.
  - `fetch_intraday.py`: Yahoo intraday download.
  - `nr4_paper.py`: the daily paper ledger for BTC NR4.
- `results/`: result CSVs, plus `signals.csv`, the daily signal and P&L series of both survivors from 1999 to 2026-11-24.
- The price CSVs are not committed. Rebuild them from Yahoo into `data/` (daily) and `intraday/` (hourly and 5m), then run scripts from the lab root.

These are backtests, not guarantees, and not financial advice. Demo first.
