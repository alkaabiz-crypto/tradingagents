# BTC paper trader

Paper money only: no real orders are placed. Starting balance: $300.

A scheduled task runs `python3 paper/btc_paper.py` every day at 08:45 Gulf time
(UAE). It reads BTC/USD daily candles and the live price from Gemini's public
API, applies the rules below, then commits the updated `ledger.json` and
`journal.md`.

## Rules (spot only, no leverage)
- **Buy** only when, on the last daily close:
  - the price is above its 20-day average,
  - the 20-day average is above the 50-day average,
  - RSI(14) is between 40 and 65,
  - and the price is no more than 3% above the 20-day average.
- **Size:** half the account (about $150).
- **Stop-loss:** 4% below entry, so one loss costs about 2% of the account.
- **Take profit:** sell half at +7%, then move the stop up to the entry price.
- **Exit the rest** on a daily close below the 20-day average.
- **Brakes:**
  - after 2 losing trades in a row, no buys for a day;
  - if the account is down $20 in a week, no buys until next Monday.
- **Fees:** 0.4% is charged on every paper fill.

## Statuses
- `WAIT`: the trend is down; stay in cash.
- `GET READY`: price is back near or above the 20-day average.
- `BUY SIGNAL`: all checks pass; a paper buy is made.
- `HOLD`: a paper position is open.

## Files
- `journal.md`: one line per day.
- `ledger.json`: cash, position and every trade.
