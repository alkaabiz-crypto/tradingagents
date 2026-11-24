# BTC breakout rule: out-of-sample replication on 13 other coins

**Bottom line:** The edge partly replicates, and only on the long side. On 12 of 13 alts the average trade is positive, and pooled across all 931 alt trades the average is +0.31R (t 5.1 per trade, 2.5 after clustering by month). That is about 40% of BTC's +0.79R. ETH is the only alt that comes close to BTC. Almost all of the result comes from long trades, and most of it from the 2019-2021 bull market. The short side does not replicate (+0.06R, t 0.8). As a portfolio, the rule gives a smoother ride than holding the coins: Sharpe 1.10 against 0.95, and a much smaller drawdown. Before you trust it, assume a lot of shrinkage: per trade, expect about +0.2 to +0.3R on longs and nothing on shorts.

Scripts: `replicate.py` (main), `fallen.py` (survivorship check). Outputs: `per_coin.csv`, `pooled.csv`, `basket.csv`, `yearly.csv`, `trades.csv`, `fallen_coins.csv`, `misc.json`. The data is Yahoo daily OHLC, downloaded on 2026-11-24 to `data/`.

## Method (parameters unchanged from BTC)

- **Trend filter:** compare the close with its 200-day SMA. Above means only longs are allowed; below means only shorts.
- **Signals:** go long when the close is above the 20-day high (previous 20 days, excluding today). Go short when the close is below the 20-day low.
- **Entry:** at the next day's open.
- **Stop and target:** the stop is entry ∓ 2×ATR20, where ATR20 is the simple average of true range on the signal day. The target is 4R. A trade still open after 30 bars is closed at the close of the 30th bar. If one bar touches both stop and target, I count the stop. A stop that gaps through fills at the open; the target fills at its own price.
- **Positions:** at most one per coin. A new signal is allowed from the close of the exit bar onward.
- **Costs:** 10 bp per side. R = (signed move − costs) / stop distance.
- **Window:** signals from 2019-01-01, and only after a coin has at least 300 daily bars. SOL, DOT and AVAX therefore start in 2021. The split is 2019-2021 against 2022 to 2026-11.
- **BTC check:** my code reproduces the reference result exactly: 74 trades, +0.79R, t 3.28.
- **Placebo:** for each coin, 300 runs. Each run takes the same number of entries on random eligible days, trades in the trend direction, and uses the same exits. The p-value is the share of runs whose mean R is at least the actual mean R. This tests whether the breakout timing adds anything beyond "trade with the 200-day trend and use this exit".

## 1. Per coin (2019 to 2026-11)

| Coin | Yahoo data starts | First eligible signal | Trades | Win | Avg R | t | Total R | Max DD (R) | 2019-21: n / avg | 2022+: n / avg | Placebo p |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **BTC (in-sample)** | 2014-09-17 | 2019-01-01 | 74 | 47% | +0.79 | 3.28 | +58.5 | 6.2 | 32 / +0.86 | 42 / +0.74 | 0.003 |
| ETH | 2017-11-09 | 2019-01-01 | 70 | 49% | +0.74 | 2.98 | +51.6 | 4.1 | 30 / +0.95 | 40 / +0.58 | 0.010 |
| SOL | 2020-04-10 | 2021-02-04 | 57 | 37% | +0.39 | 1.46 | +22.3 | 9.2 | 8 / +1.75 | 49 / +0.17 | 0.166 |
| XRP | 2017-11-09 | 2019-01-01 | 76 | 34% | +0.12 | 0.61 | +9.5 | 13.2 | 27 / +0.14 | 49 / +0.12 | 0.070 |
| LTC | 2014-09-17 | 2019-01-01 | 73 | 40% | +0.24 | 1.12 | +17.9 | 16.0 | 24 / +0.99 | 49 / −0.12 | 0.150 |
| BNB | 2017-11-09 | 2019-01-01 | 85 | 38% | +0.53 | 2.27 | +44.7 | 10.4 | 33 / +0.80 | 52 / +0.35 | 0.007 |
| ADA | 2017-11-09 | 2019-01-01 | 80 | 41% | +0.38 | 1.78 | +30.2 | 5.9 | 32 / +0.60 | 48 / +0.23 | 0.076 |
| DOGE | 2017-11-09 | 2019-01-01 | 81 | 38% | +0.20 | 1.03 | +16.3 | 15.0 | 31 / +0.62 | 50 / −0.06 | 0.130 |
| BCH | 2017-11-09 | 2019-01-01 | 81 | 33% | −0.08 | −0.47 | −6.6 | 12.7 | 29 / −0.31 | 52 / +0.05 | 0.591 |
| LINK | 2017-11-09 | 2019-01-01 | 77 | 47% | +0.45 | 2.10 | +34.5 | 12.3 | 30 / +0.88 | 47 / +0.17 | 0.053 |
| DOT | 2020-08-20 | 2021-06-16 | 52 | 46% | +0.26 | 1.18 | +13.6 | 5.1 | 6 / −0.14 | 46 / +0.31 | 0.286 |
| AVAX | 2020-07-13 | 2021-07-17 | 49 | 41% | +0.27 | 1.07 | +13.3 | 6.3 | 6 / +0.77 | 43 / +0.20 | 0.189 |
| TRX | 2017-11-09 | 2019-01-01 | 78 | 33% | +0.20 | 0.92 | +15.3 | 7.2 | 31 / +0.28 | 47 / +0.14 | 0.674 |
| XLM | 2017-11-09 | 2019-01-01 | 72 | 44% | +0.41 | 1.87 | +29.5 | 6.0 | 27 / +0.38 | 45 / +0.43 | 0.010 |

Yahoo's history for most alts only starts on 2017-11-09, so data before 2019 is thin. BTC also has 41 trades before 2019, averaging +1.30R; LTC has 43, averaging +0.19R.

**Scorecard across the 13 alts:**

- 12 of 13 have a positive average R.
- 3 have t ≥ 2: ETH, BNB and LINK. XLM and ADA are close, at about 1.8.
- 3 have placebo p < 0.05: ETH, BNB and XLM. 6 have p < 0.10. With 13 tests you would expect about 0.65 at p < 0.05 by chance.
- 11 of 13 show a lower average in 2022+ than in 2019-21. The exceptions are DOT, BCH and XLM.

## 2. Pooled alts (BTC excluded)

| Subset | Trades | Win | Avg R | t (per trade) | t (month-clustered) | Total R |
|---|---|---|---|---|---|---|
| All 13 alts | 931 | 40% | **+0.31** | 5.14 | 2.53 | +292 |
| Longs | 496 | 37% | **+0.54** | 5.56 | 2.64 | +267 |
| Shorts | 435 | 43% | **+0.06** | 0.83 | 0.37 | +24 |
| 2019-2021 | 314 | 45% | +0.56 | 4.96 | 2.71 | +175 |
| 2022-now | 617 | 37% | +0.19 | 2.64 | 1.20 | +117 |
| Longs 2022+ | 284 | 31% | +0.34 | 2.71 | 1.14 | +96 |
| Shorts 2022+ | 333 | 43% | +0.06 | 0.79 | 0.34 | +21 |
| Excluding longs signalled Oct-2020 to Dec-2021 | 814 | 39% | +0.23 | 3.66 | 1.72 | +186 |
| BTC (reference) | 74 | 47% | +0.79 | 3.28 | 3.10 | +58 |

The month-clustered t-stat sums R by signal month and then tests across the 95 months. It is the honest figure to use, because coin results move together: the average pairwise correlation of monthly R between coins is 0.24.

**R by year, all alt trades:**

| Year | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|---|---|
| Avg R | +0.43 | +0.74 | +0.49 | +0.05 | +0.09 | +0.43 | −0.04 | +0.46 |

The result does not rest on a few outliers. The top 20 trades out of 931 make up 80R of the 292R total, and the other 911 trades still average +0.23R. Exits split as 57% stop, 28% time and 15% target.

## 3. Basket (all 14 coins, from 2019-01-01, daily mark-to-market)

Each trade risks a fixed fraction of equity, measured as stop distance. Coins join the basket once they are eligible. Sharpe uses 365-day annualization.

| Portfolio | Sharpe | CAGR | Max DD | Ann. vol | Final multiple | Max gross exposure |
|---|---|---|---|---|---|---|
| Breakout, 1% risk per trade | **1.10** | 43.8% | 48.4% | 40% | 17.6× | 1.9× |
| Breakout, 0.5% risk per trade | 1.10 | 22.3% | 26.8% | 20% | 4.9× | 0.95× |
| Breakout, 1%, alts only | 1.00 | 35.2% | 50.6% | 37% | 10.8× | 1.9× |
| Breakout, 1%, longs only | 1.30 | 42.2% | 33.8% | 31% | 16.1× | 1.9× |
| Breakout, 1%, shorts only | 0.16 | 0.7% | 57.8% | 28% | 1.06× | 1.6× |
| Equal-weight buy & hold (daily rebalance) | 0.95 | 53.4% | 79.7% | 74% | 29.3× | 1.0× |
| BTC buy & hold | 0.89 | 42.4% | 76.6% | 60% | 16.4× | 1.0× |

**Correlations:**

- Monthly R between coins averages 0.24 across all pairs and 0.23 between alts. BTC's average correlation with each alt is 0.27.
- The daily returns of the breakout basket have a correlation of only 0.04 with the equal-weight buy-and-hold.

**Calendar-year returns:**

| Year | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 YTD |
|---|---|---|---|---|---|---|---|---|
| Breakout, 1% risk | +56% | +103% | +87% | +19% | +5% | +71% | −5% | +47% |
| EW buy & hold | +34% | +251% | +840% | −70% | +144% | +109% | −27% | −40% |

**How to read the basket results:**

- The rule beats buy-and-hold on Sharpe only modestly (1.10 against 0.95). Its real advantage is a much shallower drawdown and returns that are uncorrelated with holding the coins.
- Even so, a 48% drawdown at 1% risk is large, because correlated stop-outs across 14 coins hit at the same time. At 0.5% risk the drawdown falls to 27%.
- Adding shorts lowers the Sharpe, from 1.30 for longs only to 1.10 for both sides.
- The 0.5% and 1% versions show the same Sharpe because the rule ignores leverage costs. Funding costs are not modelled; at 1.9× gross exposure, real perpetual funding would cost something.

## 4. Survivorship bias, and whether the short side holds up

**The bias:** all 13 alts are still in the top tier in 2026. Picking them with hindsight selects coins that had big sustained rallies, which is exactly the setting where a long breakout and trend rule earns money. It also leaves out coins that collapsed: LUNA, FTT, EOS, BSV, WAVES and others. Longs on those coins would have been stopped out repeatedly, while shorts on them would have done well. So the bias pushes the **long-side results up and the short-side results down**.

**The short side on the survivors does not hold up:**

- Pooled across alts it averages +0.06R (clustered t 0.37). The 2022+ figure is the same, +0.06R.
- Only 2 alts have short t > 1: ETH at +0.43R and DOT at +0.29R.
- On BTC itself the short side was weak too: +0.46R, t 1.1.
- The shorts-only basket has a Sharpe of 0.16.

**Check on fallen or faded coins:** I ran `fallen.py`, with the same rule and window, on EOS, ETC, XTZ, BSV, FTT, ZEC, DASH, NEO, XMR and WAVES. LUNA and MIOTA are not available on Yahoo. Most of these lost 55-97% from their first eligible date.

| Set | Trades | Avg R | t |
|---|---|---|---|
| 10 fallen or faded coins, all trades | 772 | +0.17 | 2.66 |
| Longs | 343 | **+0.48** | 4.16 |
| Shorts | 429 | **−0.09** | −1.43 |

What this shows:

- The short side loses money even on coins that went down 90% or more (EOS, BSV, FTT, WAVES). That is strong evidence the short leg has no edge. Short breakouts in crypto bear markets are hit by violent rallies, and a 2×ATR stop is too tight to survive them.
- Survivorship does **not** explain the long edge away: longs on the fallen coins still average +0.48R. This is close to the survivors' +0.54R, though it is still driven by those coins' 2019-2021 rallies.

## Verdict

1. **Does it replicate beyond BTC? Partly, and only on the long side.**
   - The direction of the result is consistent: 12 of 13 survivors are positive, and the 10 fallen coins are positive on longs too.
   - The size is about 40% of BTC's, +0.31R against +0.79R, so BTC's figure was close to the best case and in-sample.
   - Only ETH, and to a lesser degree BNB, match BTC.
   - The placebo test supports the breakout timing as better than random trend-following entries on only 3 of 13 coins at p < 0.05.
2. **The short side does not replicate.** It is +0.06R on survivors and −0.09R on fallen coins. Drop it, or treat it as unproven.
3. **The edge is decaying.** The alt average was +0.56R in 2019-21 and +0.19R in 2022+. After clustering, the 2022+ result is not significant (t 1.2), and longs alone in 2022+ also have a clustered t of 1.1.
4. **As a portfolio,** a longs-only basket at about 0.5% risk per trade looks worth paper-trading. On 2019-2026 data it had a Sharpe of about 1.3, a drawdown far smaller than buy-and-hold, and near-zero correlation with buy-and-hold. Plan on a per-trade edge of about +0.2 to +0.3R, not +0.8R.
