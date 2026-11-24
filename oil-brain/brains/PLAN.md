# Brain tournament plan (written 2026-11-24)

Goal: find a trading rule for the US market (oil included) that survives honest testing,
then prove it forward on paper before anyone risks money.

## Phase 1: first 7 brains (running since 10:23 UTC)

| brain | family | horizon |
|---|---|---|
| calendar | overnight vs day, turn of month, pre-holiday, FOMC | 1 day |
| volatility | VIX term structure, fear regimes, OVX | days to weeks |
| liquidity | volume, Amihud illiquidity, credit spreads | days |
| macro | dollar, rates, copper/gold, cross-asset lead-lag | weeks to months |
| sectors | sector ETF momentum, reversal, oil-sensitive sectors | weeks |
| ml | machine learning on many weak signals, with a shuffled-label control | 1-5 days |
| energy | energy stocks vs crude: pairs, catch-up, residual momentum | 1-5 days |

## Phase 2: 5 more brains (different markets and data, no overlap with phase 1)

| brain | family | key papers | horizon |
|---|---|---|---|
| earnings | post-earnings drift and earnings-day effects on large US stocks | Bernard & Thomas 1989; Chordia et al. 2009 (decay) | 1-60 days |
| statarb | short-term reversal and pairs across large US stocks | Lehmann 1990; Lo & MacKinlay 1990; Gatev et al. 2006 | 1-5 days |
| crypto | Bitcoin/Ether momentum, weekend and time-of-week effects | Liu & Tsyvinski 2021; Liu, Tsyvinski & Wu 2022 | days to weeks |
| global | country ETF momentum, value proxies, lead-lag from the US | Asness, Moskowitz & Pedersen 2013; Rapach et al. 2013 | weeks to months |
| insiders | clustered insider buying (SEC Form 4) in large US stocks | Lakonishok & Lee 2001; Cohen, Malloy & Pomorski 2012 | weeks |

Same rules for all (`RULES.md`): same engine and splits, costs, max 15 rules each, every rule
counted, winner needs all 6 gates AND post-2014 t >= 3. Known bias to state: stock lists built
from today's index members carry survivorship bias; long/short and market-neutral rules are less
affected, long-only stock rules must be discounted.

## Phase 3: scoreboard and audit

1. Collect every `scorecard.json` into `SCOREBOARD.md`: rules tried per brain, best rule,
   winners, candidates. Total rules tried across all brains (the multiple-testing count).
2. An independent auditor re-implements each winner and candidate from its description only
   (not its code), checks for look-ahead, survivorship, cost and data errors, runs a
   neighbouring-parameter grid, and scores a 2x-cost and 1-day-delay version.
3. Only rules that survive the audit go on.

## Phase 4: forward paper test

1. Each surviving rule gets a pre-registered forward log (like `oil-brain/forward.py`): only
   dates after registration count.
2. The 2-hour research loop updates the logs daily and reports.
3. Pass bar for real money consideration: at least 3 months and 30 trades forward, net profit
   after costs, t >= 2 forward, drawdown within the backtest's range. Going live is always the
   user's decision; this is research, not financial advice.
