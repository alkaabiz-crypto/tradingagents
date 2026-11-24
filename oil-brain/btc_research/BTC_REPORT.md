# Bitcoin breakout: deep research report (2026-11-24)

Four independent agents each rebuilt the rule from its description only and attacked one side of it.
Details: `replication/REPLICATION.md`, `robustness/ROBUSTNESS.md`, `risk/RISK.md`, `execution/EXECUTION.md`.
Research, not financial advice.

**The rule:** at the 00:00 UTC daily close, trend = BTC vs its 200-day average (above: longs only; below:
shorts only). Long on a close above the 20-day high, short on a close below the 20-day low. Enter at once.
Stop 2 x ATR(20), target 4 x that distance, out after 30 days. Risk a fixed % of the account per trade.

## Verdict: real, smaller than the headline, long side only

| question | answer |
|---|---|
| Does it reproduce? | Yes, all four rebuilds: +0.70 to +0.81R per trade, t 3.0-3.4 (2019-2026) |
| Is it curve-fit? | No. All 288 neighbouring settings are positive in both periods; 75% have t > 2. Deflated Sharpe 0.90-0.94; probability of overfitting 0.20-0.39 |
| Would honest re-tuning have worked? | Yes: re-picked every January from past data only, +0.65R, t 2.47, positive 8 of 9 years |
| Is it just being long a rising coin? | Partly. Random entries with the same trend filter and exits earn +0.19R since 2019; the breakout timing adds about +0.4 to +0.6R |
| Longs or shorts? | **Longs**: +1.20R (t 5.1) since 2015. **Shorts**: +0.23R (t 0.8), lose money in bull years |
| Other coins? | Partly. 12 of 13 positive; ETH matches BTC (+0.74R, t 3.0); 13 coins' longs +0.54R, shorts +0.06R; shorts lose even on coins that collapsed 90% |
| Is it fading? | Yes. 2015-18 +1.17R, 2019-21 +1.03R, 2022-now +0.57R (t 1.9); last 30 trades +0.36R (t 0.97) |
| Depends on the 00:00 UTC close? | No. All 6 close times positive (+0.71 to +0.87R) |
| Execution on an Exness CFD? | Works. Enter within 1-4 hours (costs <= 0.03R). No gaps on 24/7 BTC. $10-40 spread ~0.02R. Each 10%/yr of swap ~0.065R. Mid case ($20 spread, 20% swap, 10 bp slippage) +0.68R, t 2.89; bad case +0.58R, t 2.46 |
| Weekends? | Take weekend signals; removing weekends hurts (+0.65R) and adds gap risk |

## What to expect if you trade it

- **Expectancy:** plan on **+0.3 to +0.5R per trade** after costs, not +0.8R.
- **Frequency:** about 10 trades a year, one a month on average; median hold 11 days; ~48% winners;
  winners average +2.8R, losers -1R. Months with no trade are normal.
- **Risk per trade:** **0.5%** on demo and for the first 20 real trades, then 1%; 2% is a hard cap.
  At 1%: median 3-year drawdown 5%, 95th percentile 9%; 1 losing year in 6 (1 in 3 if the recent,
  weaker edge persists). At 1% the position is about 14% of the account: no leverage needed.
- **Version to trade:** **longs only** (or shorts at half size). The original long/short rule keeps
  running on paper unchanged for comparison.
- **Stop trading it if:** the average of the last 20 trades turns negative, or the account draws down
  more than 15%.

## Live setup from 2026-11-24
- `combo/combo_live.py`: BTC_BREAKOUT (original, long/short, paper, unchanged) and **BTC_BREAKOUT_LONG**
  (long-only, 0.5% risk, registered today, forward test).
- `combo/btc_ticket.py`: Exness demo tickets at 00:07 UTC daily, now at 0.5% risk, with shorts marked
  optional at half size.
