# US crude oil (WTI, Exness "USOIL"): how it works

The brain's reference manual. Facts carry a source; numbers come from our own data
(`history.py`, `study12.py`, `episodes.csv`, `indicator_buckets.csv`) unless stated.
Research, not financial advice.

## 1. What you are trading

- **WTI crude** is light, sweet US oil priced at **Cushing, Oklahoma**, the delivery hub of the NYMEX
  futures contract (CL, 1,000 barrels). Exness USOIL and most CFDs track the front futures month and
  **roll** to the next month before expiry, so the CFD price jumps at each roll; the broker adjusts or
  charges for it. USO (the ETF used in our tests) holds the front month and loses money on every roll
  in contango.
- **Brent** (North Sea, ICE) is the world benchmark; WTI usually trades a few dollars below it.
- **Trading hours:** futures trade almost 24 hours (Sun 18:00 to Fri 17:00 New York, 1-hour daily break).
  Most volume is 09:00-14:30 New York; the **settlement price** is the average of 14:28-14:30.
- **Daily range:** typically 2-3%; on news days 5-10%. In April 2020 the expiring contract went to
  -$37 because nobody could store the oil.

## 2. What moves the price

**Supply**
- **OPEC+** (Saudi Arabia, Russia and allies) sets production quotas at meetings (usually twice a year,
  plus surprise calls). Surprise cuts jump the price ~3% on the day; the effect fades (IMF 2022).
- **US shale** (Permian, Bakken): US output went from 5.0m barrels/day (2008) to **14.0m (Nov 2026)**.
  Shale reacts to price with a 6-12 month lag, which caps long rallies.
- **Disruptions:** wars, sanctions (Iran, Russia, Venezuela), hurricanes in the Gulf of Mexico,
  pipeline outages. A supply shock lifts oil and hurts stocks; a demand shock moves both the same way
  (Ready 2018).
- **SPR:** the US Strategic Petroleum Reserve (276m barrels now) is released in crises and refilled when
  cheap.

**Demand**
- The world economy: recessions crash oil (2008: -72%; 2020: -70% then the negative print).
- China's imports, US driving (summer), heating oil (winter), jet fuel.
- **Refineries** turn crude into gasoline and diesel. Their margin (the **crack spread**) pulls crude
  demand; in spring and autumn they shut for maintenance and crude piles up.

**Money and markets**
- **Dollar:** oil is priced in dollars. Since 2008, a rising dollar has gone with weaker oil: after the
  dollar index rose >3% in 3 months, USO averaged **-2.7%** over the next 4 weeks; after it fell >3%,
  **+1.7%** (table 5). The link weakened after the US became a net exporter (ECB 2024).
- **Positioning:** hedge funds ("managed money" in the CFTC report) amplify moves and get crowded.
- **Curve shape:** when near-month oil is dearer than later months (**backwardation**) the market is
  tight; when cheaper (**contango**) oil is plentiful and storage pays. Deep contango was followed by
  weaker USO returns (-1.1% over 4 weeks), deep backwardation by stronger ones (+1.4%).

## 3. The weekly calendar (New York time)

| when | what | why it matters |
|---|---|---|
| Tue 16:30 | API inventory estimate | first look at the week's stocks; moves after-hours prices |
| **Wed 10:30** | **EIA Weekly Petroleum Status Report** | official stocks, production, refinery runs; biggest weekly volatility spike |
| Thu 10:30 | EIA natural gas storage | moves gas, sometimes oil |
| Fri 13:00 | Baker Hughes rig count | drilling activity, a slow supply signal |
| Fri 15:30 | CFTC Commitments of Traders | who holds what (as of Tuesday) |
| monthly | OPEC and IEA oil market reports; US CPI and jobs; Fed meetings | demand outlook, dollar |

Holiday weeks shift the EIA report (Thanksgiving week: Wednesday as usual; markets closed Thursday,
early close Friday). Liquidity is thin around holidays.

## 4. Indicators and what history says (USO, 2008-2026, next 4 weeks)

Full-sample descriptive averages (not a trading test; buckets overlap in time):

| indicator | bucket | avg next 4 weeks | up % |
|---|---|---|---|
| Crude stocks vs 5-year same-week average | below by >20m barrels | +1.5% | 51% |
| | above by >20m barrels | +1.2% | 57% |
| Curve (USO minus USL, 63 days) | deep contango | -1.1% | 51% |
| | deep backwardation | +1.4% | 51% |
| Funds' net long, 3-year percentile | below 20% | -0.4% | 55% |
| | above 80% | +0.8% | 54% |
| 6-month trend | below -20% | -1.0% | 55% |
| | above +20% | +2.0% | 58% |
| Dollar, 3-month change | below -3% | +1.7% | 60% |
| | above +3% | **-2.7%** | 46% |
| Refinery utilization | below 85% | +1.3% | 60% |

- **Seasonality** (USO average month): Feb +2.2%, Mar +1.5%, Apr +1.3%, Jun +2.4% strong;
  **Nov -4.2%**, Aug -1.4% weak. Published work finds it too noisy to trade (CXO; JP Morgan 2015).
- **Weekday:** Monday weakest (-17 bp a day on average), Thursday strongest (+12 bp); not significant
  after volatility (Auer 2014).

## 5. Big rallies and crashes (WTI, 25% swings, 2000-2026)

38 swings of 25%+ since 2008 (`episodes.csv`). What the indicators said **at the start** (hindsight
dating, so this describes turning points; it does not time them):

| at the start of | count | funds' net long percentile (median) | funds crowded (>70%) | backwardation | brain v2 (median) |
|---|---|---|---|---|---|
| a RALLY | 19 | **0.22** (11 of 19 below 25%) | **0 of 19** | 2 of 19 | **-0.43** (bearish) |
| a CRASH | 19 | 0.47 | **7 of 19** | **10 of 19** | 0.00 |

- **Rallies start when hedge funds have given up** (low net long) and the fundamental picture still
  looks bad. Not one of 19 rallies started with funds crowded long.
- **Crashes often start from tightness** (backwardation) and crowded longs: 2011, 2012, 2013-15,
  2015, 2018, 2019, 2023.
- **The brain's trend-and-fundamentals view is bearish at bottoms** (median -0.43): it confirms moves
  late. That is why it cannot time turns.
- Recent swings: Dec 2025 - Apr 2026 **+104%** ($55 -> $113), Apr 2026 -26%, Apr-May +30%,
  May-Jul -37%, Jul-Sep **+54%** ($69 -> $106), then down since September.

## 6. What our tests say (63 oil rules + the brain, all with costs)

- **Nothing short-term works after costs:** EIA-day reactions, overnight gaps, intraday momentum,
  fading or following big days, RSI/MACD/Bollinger and 400 other indicator rules, Brent-WTI,
  crack spreads, CFTC positioning changes, OPEC (too few events).
- **Slow trend-following on oil makes money mainly in crashes** (2014-16, 2020): positive but
  t < 2 outside crashes.
- **Brain v2 (study 12):** the 7-vote brain worked in 2014-2019 (Sharpe 0.83) and failed from 2020
  (Sharpe -0.07; it lost 73% in 2020 by reading tight inventories as bullish into the COVID crash).
  Inventory draws alone: Sharpe 1.03 to 2013, 0.86 in 2014-2019, **-0.38 since 2020**. Since COVID,
  US oil has traded on macro, OPEC+ and geopolitics more than on weekly US inventories.
- **So the brain is a map of the market, not a signal.** Use it to know what the market is pricing,
  where the risks are, and when positioning is stretched; size small and use stops.

## 7. Risk rules for trading USOIL

- Daily moves of 2-3% are normal: a 1% stop is noise. Size so that a 3% move costs no more than you
  accept losing.
- Avoid opening trades in the 10 minutes around Wednesday 10:30 and OPEC+ headlines; spreads widen.
- Know the CFD's roll date and overnight swap; holding through a roll costs money in contango.
- Weekend gaps: geopolitics often hits on weekends; a stop does not protect against a gap.
