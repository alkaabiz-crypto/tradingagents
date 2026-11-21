# BTC paper trader

Paper money only: no real orders are placed. There are three separate paper
accounts, each starting with $300:

| Mode | Candles | Stop-loss | Take half profit at | Files |
|---|---|---|---|---|
| `2h` (intraday) | 2-hour | 1.5% below entry | +3% | `ledger_2h.json`, `journal_2h.md` |
| `daily` (swing) | daily | 4% below entry | +7% | `ledger.json`, `journal.md` |
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
