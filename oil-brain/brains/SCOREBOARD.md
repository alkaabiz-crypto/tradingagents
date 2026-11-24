# Brain tournament scoreboard (2026-11-24)

12 research brains (149 hand-designed rules) plus a swarm of 2,784 generated rules: about
2,930 rules in total, plus 52 in the oil brain. Same engine, splits and costs for all.

## The luck bar
With this many tries, luck alone produces impressive numbers. The swarm measured it directly
(White 2000 / Romano & Wolf 2005, 300 time-shifted copies of all 2,784 rules): the best of
2,784 rules reaches **t = 3.5 by luck on a typical run and 4.2 at the 95% level**. A single
brain's best rule is judged against t >= 3 (Harvey, Liu & Zhu 2016).

## Brains

| brain | rules | best rule | post-2014 Sharpe | t | winners | candidates |
|---|---|---|---|---|---|---|
| calendar | 15 | IEF long in the last 3 trading days of the month | 0.67 | 2.39 | 0 | 1 |
| crypto | 11 | BTC long when its 28-day return > 0, else cash | 1.10 | 4.62 | 2 (+1 false, 7-day) | 1 (ETH 28d) |
| earnings | 7 | SPY only in earnings season | 0.67 | 2.42 | 0 | 0 |
| energy | 13 | backwardation tilt on XLE vs SPY | 0.33 | 1.19 | 0 | 0 |
| global | 11 | fade big US days in an Asian ETF basket | 0.44 | 1.59 | 0 | 0 |
| insiders | 11 | long stocks after insider purchases, SPY-hedged | 0.50 | 1.79 | 0 | 0 |
| liquidity | 15 | USO long/short on HYG-minus-LQD 63-day sign, weekly | 0.62 | 2.24 | 0 | 1 |
| macro | 13 | SPY or IEF by HYG/LQD 21-day sign, monthly | 0.91 | 3.25 | 0 | 0 (static mix equal) |
| ml | 15 | logistic model, USO 5-day | 0.26 | 0.94 | 0 | 0 |
| sectors | 12 | 10-month average per sector, long/flat | 0.77 | 2.78 | 0 | 0 |
| statarb | 11 | sector-adjusted weekly reversal when VIX > 25 | 0.53 | 1.90 | 0 | 0 |
| volatility | 15 | SPY, flat when VIX > VIX3M | 0.79 | 2.84 | 0 | 0 |

## Swarm (`swarm/swarm.py`, 2,784 rules, 24 instruments, 8 families)
Winners above the t = 4.19 luck bar, all positive in OOS and HOLDOUT and above buy-and-hold:
BTC above its 100-day average (t 4.69), BTC 20-day breakout (4.59), BTC 10-day trend (4.44),
BTC 21-day trend (4.42). Next best outside crypto: QQQ/XLK above the 200-day average (t ~3.1),
below the luck bar and not better than holding. No oil rule is near the top.

## What the tournament says
1. **One family survives everything: Bitcoin trend-following** (long when the price is above
   a 10-100 day trend, else cash). Found independently by the crypto brain and the swarm, robust
   across lookbacks, delays and costs. Caveat: after the papers (2022 on) its edge alone is
   t ~1.6; its clearest benefit is smaller crashes (-50% vs -77%).
2. **Candidates** (all gates, t < 3): credit appetite -> USO (liquidity), month-end IEF
   (calendar, chosen after a TLT near miss), ETH 28-day trend (crypto).
3. **Dead after 2014 and costs:** oil signals (52 rules), overnight drift, turn of month,
   pre-holiday, VIX timing, sector rotation, country momentum, short-term reversal, pairs,
   PEAD, earnings premium, insider buying in large caps, ML on daily features.

Next: independent audit of the Bitcoin trend family and the three candidates (phase 3), then
forward paper tests (phase 4). Research, not financial advice.
