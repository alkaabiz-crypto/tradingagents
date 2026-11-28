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

## Swing and indicator candidates (Batches 30-35)

These passed the same bar, at minimum lots, 2024-now. They are not yet paper-traded.

| Candidate | 2024-now | Worst drop | Family |
|---|---|---|---|
| IBS < 0.2 at the close, hold 2 days, USTEC 0.05 (0 losing years of 13) | +$421 | -$161 | Index dip-buy |
| IBS < 0.2, hold 2 days, US30 | +$332 | -$128 | Index dip-buy |
| IBS < 0.2, hold 2 days, US500 0.14 | +$263 | -$112 | Index dip-buy |
| %R(10) < -90, hold 2 days, USTEC | +$420 | -$50 | Index dip-buy |
| Connors R3, US500 | +$110 | -$63 | Index dip-buy |
| %R(10) < -90, hold 2 days, US500 | +$206 | -$60 | Index dip-buy |
| 10-day low close, hold 3 days, US500 (4 losing years) | +$284 | -$80 | Index dip-buy |
| BTC TRIX(15) above its signal, 0.01 lot | +$480 | -$208 | Crypto trend |
| ETH close above SMA50, 0.1 ETH | +$256 | -$177 | Crypto trend |
| ETH NR4 breakout (corr 0.68 with BTC NR4) | | | Crypto breakout |
| Gold turn of month, 1 oz (needs ~$2,000+) | +$1,118 | -$387 | Gold calendar |

- Batch 35 swept 41 indicators and candle patterns over 394 tests. Each rule was compared with 500 random-timing copies of itself, with a Benjamini-Hochberg FDR cut.
- Only crypto trend rules beat random timing. The index indicators were just riding the market's rise, and the candle patterns failed.

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

## Candle and oil brains (Batches 47-54, Nov 28)

The repo now has two deterministic "brains" in `tradingagents/analytics/`: `candles.py` (patterns read in context:
trend vs the 200-day, location at a 10/20-day low or high, range vs ATR, plus point-in-time history of what followed
each pattern on that instrument) and `oil.py` (WTI trend, curve/roll-yield estimate, Brent-WTI, 3-2-1 crack, OVX,
oil-CAD link, energy stocks vs oil). The market analyst agent calls them through the `get_candle_patterns` and
`get_oil_context` tools (`tests/test_brains.py`). The lab scripts import the same modules.

About 770 tests, each with 300-2,000 random-timing shifts and a Benjamini-Hochberg cut:
- Candle brain (`batch47`, `batch51`, `batch53`): the only robust edge is the day breakout (inside bar, NR4/NR7) on
  crypto. It holds on most coins, with low correlation between coins (0.1-0.4) and with Plan A.
- Two data artifacts were caught and rejected. Yahoo spot-FX bars made FX reversal rules look great (they vanish on CME
  futures bars). Nikkei index breakouts looked great on ^N225, but fail on the tradable ETF 1321.T and on futures,
  because the cash index opens stale. FTSE/ASX opens are copies of the prior close, and platinum/palladium bars are flat.
- Oil brain (`batch48`): all 20 rules fail (carry, trend, crack, Brent-WTI pair, OVX, EIA Wednesday, seasonality, CAD link).
- Walk-forward ridge "brain score" over candle, indicator and oil features (`batch49`): fails on all 13 markets.

Final list (`batch54_final10.csv`). Only 9 meet every bar; BTC TRIX vol-sized fails the drop bar:

| Candidate | 2024+ %/yr on $3k | Worst drop | Max corr Plan A |
|---|---|---|---|
| ETH ID/NR4 breakout, 0.5 ETH | 8.5 | -$125 | 0.36 |
| XRP Williams breakout, $500 | 8.1 | -$242 | 0.36 |
| ADA NR4 breakout, $500 | 6.5 | -$200 | 0.26 |
| USTEC overnight, 0.05 | 4.4 | -$286 (since 2014) | 0.19 |
| XRP NR7 breakout, $500 | 4.2 | -$150 | 0.18 |
| XLM NR7 breakout, $500 | 3.7 | -$252 | 0.21 |
| DOGE inside-bar breakout, $500 | 2.0 | -$275 | 0.14 |
| Connors R3 US500, 0.14 | 1.7 | -$84 | 0.43 |
| Turnaround Tuesday USTEC, 0.05 | 0.6 | -$120 (since 2014) | 0.21 |

- Six of the nine are one idea (crypto breakouts). Most alt breakouts are slightly negative in 2026.
- Exness lots and spreads for the alt coins are not verified. The tests assume 20 bp; every alt rule stays positive up to 80 bp.
- Paper: `brains_paper.py` (from Nov 28).
