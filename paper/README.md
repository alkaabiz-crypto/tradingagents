# BTC paper trader

Paper money only: no real orders are placed. There are four separate paper
accounts, each starting with $300:

| Mode | Candles | Stop-loss | Take half profit at | Files |
|---|---|---|---|---|
| `2h` (intraday) | 2-hour | 1.5% below entry | +3% | `ledger_2h.json`, `journal_2h.md` |
| `daily` (swing) | daily | 4% below entry | +7% | `ledger.json`, `journal.md` |
| `range2h` (range) | 2-hour | 0.5% below range low | middle of range | `ledger_range2h.json`, `journal_range2h.md` |
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
