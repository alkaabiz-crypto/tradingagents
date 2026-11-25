# Candle Brain: what a price candle and its parts represent

Reference for a retail trader in WTI crude (USOIL CFD / CL futures / USO-type ETFs), US index CFDs (US500, US100, US30) and index ETFs (SPY, QQQ, DIA), on daily and intraday charts.

Compiled 2026-11-25 from web sources. Every claim is tagged:

- **[MECH]** mechanical fact: true by construction, by exchange rules or by mathematics.
- **[ACAD]** academically supported: peer-reviewed, or a working paper by academics. The tag says whether results are mixed.
- **[LORE]** practitioner lore: books, blogs, vendors. Bulkowski's statistics count as practitioner research because they are large-sample but not peer-reviewed.

Where a fact comes from a secondary source rather than the primary text, the entry says so.

---

## 0. TL;DR for the agent

1. A candle summarises four prices from one time bucket: open, high, low and close. It throws away the path, the volume at each price and the order of the high and low. **[MECH]**
2. The bucket boundaries are arbitrary. Change the timeframe, the session definition (24h CFD vs 9:30-16:00 cash vs CME Globex) or the broker's server time zone and you get a different candle. **[MECH]**
3. A wick proves only that some trade or quote printed at that price and the bar closed elsewhere. "Rejection", "stop hunt" or "absorption" are interpretations. Osler (2003) gives partial academic support for clustered stop and take-profit orders. **[MECH + ACAD + LORE]**
4. The high-low range is a statistically efficient volatility measure, 5-8x more efficient than close-to-close (Parkinson, Garman-Klass, Rogers-Satchell, Yang-Zhang). This is the most academically robust use of candle anatomy. **[ACAD]**
5. Where the close sits in the range (IBS / CLV) has documented next-day mean reversion in equity index ETFs. The effect is not peer-reviewed in its original form, and it decays and is cost-sensitive. **[ACAD-mixed / LORE]**
6. Named candlestick patterns have weak and mixed academic support. Most peer-reviewed tests on US large caps and on DAX/Bund futures find no edge after costs. A few find narrow effects that depend on holding rules (Lu, Chen and Hsu 2015). Bulkowski's own tests show many famous patterns are near-random (about 50-60%). **[ACAD-mixed]**
7. Even under a pure random walk, a day's high and low cluster near the open and close (arcsine law). "The low was made in the first hour" is not by itself evidence of anything. **[MECH (math) + ACAD]**

---

## 1. Anatomy

### 1.1 The four prices and derived parts **[MECH]**

| Part | Definition | What it literally represents |
|---|---|---|
| Open (O) | First traded price (or first quote, on CFDs) in the bucket | Where the bucket started. For a daily bar this depends on where "day" starts. |
| High (H) | Maximum price in the bucket | The furthest buyers lifted price during the bucket. A sampled extreme: true continuous-time high is at least this, and for bid-only charts the ask high is higher. |
| Low (L) | Minimum price in the bucket | The furthest sellers pushed price. |
| Close (C) | Last price in the bucket. On futures the **daily settlement** can differ from the last trade. | Where the bucket ended: the price at which the period's positions were marked. |
| Range | H − L | Realised extent of movement, a volatility proxy (see section 2.4). |
| Body (real body) | abs(C − O) | Net displacement within the bucket. |
| Upper wick / shadow | H − max(O, C) | Price traded above both open and close and did not hold there by the close. |
| Lower wick / shadow | min(O, C) − L | Price traded below both open and close and did not hold there by the close. |
| Colour | C > O: white/green (bullish). C < O: black/red (bearish). | Only the sign of C − O **within the bucket**. It says nothing about C vs the prior close: a red candle can be an up day if it gapped up. |
| Body/range ratio | abs(C − O)/(H − L) | ~1 means a trend bar (marubozu); ~0 means a doji. |
| Close location (IBS) | (C − L)/(H − L), from 0 to 1 | Where in its range the bar closed. See section 3. |

Sources: [StockCharts ChartSchool, candlestick dictionary](https://chartschool.stockcharts.com/table-of-contents/chart-analysis/candlestick-charts/candlestick-pattern-dictionary); [StockCharts, intro to candlesticks](https://chartschool.stockcharts.com/table-of-contents/chart-analysis/candlestick-charts/introduction-to-candlesticks); Nison, *Japanese Candlestick Charting Techniques* (NYIF 1991; 2nd ed. 2001).

**What a candle does not tell you [MECH]:**
- Whether the high or the low came first. A hammer could be "dumped then rallied" or "rallied, dumped, rallied".
- How long price spent at each level. Market Profile and volume profile show this; the candle does not.
- How much volume traded at the wick extreme. A wick can be one print.
- On CFDs, whether a real exchange trade occurred at that price (see section 1.4).

### 1.2 Timeframes: the same move, different candles **[MECH]**

- A daily candle equals the aggregation of its intraday candles: O = first intraday open, H = max of highs, L = min of lows, C = last close. A daily hammer can be a clean V on the 1h chart, or a 3-day-style range compressed into one session.
- A daily "doji" can be a strong trend down in the morning followed by a strong trend up in the afternoon. Each lower-timeframe candle is unambiguous; the daily summary hides it.
- Pattern labels are **timeframe-relative**. A 5-minute bullish engulfing inside a daily downtrend is a different object from a daily bullish engulfing. Pattern statistics (Bulkowski) are from **daily** US stock data and do not transfer automatically to 5-minute CFDs. **[LORE caveat]**
- Weekly and monthly candles depend on the week start (Sunday open vs Monday open).

### 1.3 Session boundaries: futures vs ETFs vs CFDs **[MECH]**

| Instrument | Session | Effect on the daily candle |
|---|---|---|
| CME WTI crude (CL) | CME Globex Sun-Fri 6:00 pm to 5:00 pm ET, 60-minute daily break 5-6 pm ET ([CME WTI overview](https://www.cmegroup.com/education/courses/introduction-to-energy/introduction-to-crude-oil/wti-overview.html); [Schwab CL specs](https://www.schwab.com/node/21011)) | The "daily" bar on most futures platforms runs 6 pm ET to 5 pm ET, so the Asian and London sessions belong to the *next* day's bar. |
| CL **settlement** | First six months settle on Globex trades between **14:28:00 and 14:30:00 ET**, via a VWAP/spread methodology ([CME SER-4867](https://cmegroup.com/tools-information/lookups/advisories/market-regulation/SER-4867.html); [CME settlement procedures](https://www.cmegroup.com/market-data/cme-group-settlement-procedures.html)) | Exchange "daily close" (settlement) ≠ last trade at 5 pm. Data vendors differ on whether the daily C is settlement or last. This makes a real difference to IBS/CLV and to close-based patterns. |
| CME E-mini S&P (ES) | Sun-Fri 6:00 pm to 5:00 pm ET, 5-6 pm ET maintenance break (Schwab; older sources cite a 4:15-4:30 pm halt that pre-dates the 2021 schedule change) ([Schwab ES](https://www.schwab.com/futures/sp-500-emini); [StoneX](https://futures.stonex.com/blog/what-are-emini-sp-500-futures)) | Overnight moves are inside the bar, so no opening gap at 9:30. |
| SPY / QQQ / USO (ETFs) | Regular session 9:30 to 16:00 ET, plus thin pre/post-market (standard NYSE/Nasdaq hours; not re-verified in this search) | Overnight news appears as an **opening gap**, and pre/post-market prints usually do not count in the daily OHLC. |
| Index and oil CFDs (US500, USOIL) | Usually ~23h/day, following the underlying future. Daily candle cut at the broker's **server midnight**, often GMT+2/+3 so that midnight = 5 pm New York ([BabyPips forum](https://forums.babypips.com/t/candle-close-times/59584); [TitanFX glossary](https://research.titanfx.com/glossary/what-is-daily-chart); [IC Markets DST note](https://icmarkets.eu/blog/?p=23626)) | Same market, different candles by broker. A GMT-midnight broker creates a small **Sunday candle** and six daily bars a week, which distorts patterns, ATR and moving averages. |

**Key consequences:**
- The **same day** can be a hammer on SPY (cash session), a plain red candle on ES (Globex day) and something else again on a US500 CFD cut at a different hour. **[MECH]**
- Gaps are mostly a **cash-session/ETF phenomenon**. On 23h futures and CFDs the overnight move is *inside* the candle as a wick or body, except Sunday-open gaps and the daily break. **[MECH]**
- Oil-specific intraday landmarks: the EIA Weekly Petroleum Status Report comes out Wednesdays at 10:30 am ET, with holiday shifts ([EIA schedule](https://www.eia.gov/petroleum/supply/weekly/schedule.php)). The 14:28-14:30 ET settlement window, and expiry/roll days for CL, also produce characteristic spikes and wicks. **[MECH (schedule)]**. "Spike-and-reverse on EIA" is **[LORE]**.

### 1.4 CFD-specific mechanics **[MECH]**

- MetaTrader-type platforms plot **bid** prices. Buy stops and short stop-losses fill at the **ask**, so a stop can trigger at a price the chart's wick never shows. Spreads widen around the daily rollover (about 5 pm ET), which produces apparent "stop-hunt" wicks that are really spread artefacts. ([MQL5 forum: charts are bid](https://mql5.com/en/forum/152920); [MQL5: high/low vs bid/ask](https://www.mql5.com/en/forum/311603); [MQL5 blog on spread widening](https://www.mql5.com/en/blogs/post/779382))
- CFD OHLC comes from the broker's quote stream, not the exchange tape. Highs and lows can differ by a few ticks across brokers, and from the futures or ETF.
- An oil CFD is typically priced off a specific CL contract month, or a rolling/"cash" construct. At **rolls**, the price series may jump, or be back-adjusted, creating artificial gaps or bodies. Check the broker's contract specs. *(General broker practice; verify for the specific broker.)*

---

## 2. What wicks (and ranges) mean mechanically

### 2.1 The mechanical minimum **[MECH]**

A wick means price **traded (or was quoted) at the extreme, and by the end of the bucket price had moved back**. Nothing more is implied by the data. The "story" layers below are interpretations.

### 2.2 Order-flow / microstructure interpretations

| Interpretation | Mechanism | Status |
|---|---|---|
| **Stop runs / liquidity sweeps** | Stop orders cluster just beyond obvious levels (round numbers, prior highs/lows). Price reaching them triggers a burst of market orders that extends the move briefly. If no new initiative flow follows, price returns, leaving a wick. | **[ACAD, partial]** Osler (2003, *J. Finance* 58(5):1791-1819) used ~9,700 actual FX orders: **take-profit orders cluster at round numbers**, which helps explain reversals at support/resistance, and **stop-loss orders cluster just beyond round numbers**, which helps explain fast moves after levels break ([IDEAS](https://ideas.repec.org/a/bla/jfinan/v58y2003i5p1791-1819.html); [NY Fed SR125](https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr125.pdf)). Osler's later work models **stop-loss price cascades** ([NY Fed SR150](https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr150.pdf)). Evidence is from FX; applying it to oil and index CFDs is plausible but untested here. "Smart-money liquidity grabs" (ICT/SMC terminology) is **[LORE]**. |
| **Limit-order absorption** | Large resting limit orders (or iceberg orders) absorb aggressive market orders at a level. Price cannot progress and snaps back once the aggressors exhaust. | Mechanically true of limit order books **[MECH]**. Reading it off a candle, without depth-of-market or footprint data, is **[LORE]**. |
| **Auction market theory / Market Profile "excess"** | Markets auction up to find sellers and down to find buyers. A fast move to a price that attracts strong opposite activity, with little time spent there, leaves **single prints / a tail** ("excess"). Profile traders treat this as rejection of unfair price. Value area is conventionally ~70% of time/volume around the point of control. | **[LORE]**. Developed by J. Peter Steidlmayer at the CBOT in the 1980s; codified by Dalton, *Mind Over Markets*. The 70% figure is a convention, not a fitted statistic ([Wikipedia: Market profile](https://en.wikipedia.org/wiki/Market_profile); [LuxAlgo: Excess](https://www.luxalgo.com/library/concept/excess/); [LuxAlgo: TPO](https://www.luxalgo.com/library/concept/tpo-profile.md)). A candle wick is a *coarse* proxy for a profile tail; a profile also shows time-at-price. |
| **VWAP** | VWAP = Σ(price·volume)/Σvolume since the anchor (usually the session open). Institutions benchmark execution to it, so price far from VWAP means recent buyers or sellers are at a large gain or loss. | Definition **[MECH]**; VWAP is an execution benchmark in the academic execution-cost literature. "Price reverts to VWAP" or "wicks through VWAP are rejections" is **[LORE]**. For 23h CFDs, the anchor choice changes VWAP materially. |
| **News spike** | A discrete information shock (EIA, CPI, FOMC) moves price past where liquidity rebuilds, then it partially retraces. | Mechanically common. The retracement fraction is not a law. |
| **Spread/quote artefact** | Thin liquidity (rollover, Sunday open) prints a stray quote. | **[MECH]** on CFDs (section 1.4). |

### 2.3 When in the day highs and lows form; intraday volume shape

- **Arcsine law [MECH: mathematics].** For a driftless random walk (Brownian motion), the time at which the maximum (or minimum) occurs over an interval follows the arcsine distribution. That distribution is **U-shaped**: extremes are most likely at the start and end of the interval *even with zero information*. Acar, Lequeux and Ritz used this as their benchmark ("Timing the highs and lows of the day", LIFFE Equity Products Review, Q2 1996; FT-SE 100 futures, 1992-1995) ([PDF](https://www.financnik.cz/forum/uploads/monthly_2010_11/acar-emmanuel-timing-the-highs-and-lows-of-the-day.pdf)).
- **Empirical [practitioner-academic, FT-SE futures].** About 32% of highs and 33% of lows fell in the first ~38-minute bar, which is **more** clustering at the open than a random walk predicts. The time between the day's two extremes was typically longer than the random walk implies (mode ~7.5h vs ~4.5h): if one extreme prints at the open, the other tends to come late. The authors attribute this to high open/close volume and volatility, with causality unresolved. **[ACAD-ish / industry research]**
- **E-mini S&P [LORE].** Practitioner counts: the high or low of day forms in the first hour on ~71% of days; daily highs fall in the first or last hour ~75% of the time ([TradingMarkets](https://tradingmarkets.com/?p=653319); [mypivots](https://mypivots.com/articles/articles.aspx?artnum=20)). Small samples, no out-of-sample testing.
- **Random-walk tests [ACAD].** Mok, Lam and Li (2000, *Rev. Quant. Fin. & Acct.*) used high/low timing to test intraday random walk in Hang Seng index futures. A later revisit (Liu 2016, working paper) found the earlier inefficiency no longer persisted ([PolyU WP](https://weblib.cpce-polyu.edu.hk/apps/wps/assets/pdf/w20160505.pdf)).
- **U-shaped intraday volume and volatility [ACAD].** Volume, volatility and returns are higher near the open and close: Wood, McInish and Ord (1985, *J. Finance*), Harris (1986), Jain and Joh (1988, *JFQA*), with hourly NYSE volume differing significantly across hours ([EconPapers: Jain & Joh](https://econpapers.repec.org/RePEc:cup:jfinqa:v:23:y:1988:i:03:p:269-283_01)). Theory: Admati and Pfleiderer (1988, *RFS*), "A Theory of Intraday Patterns", where discretionary liquidity traders bunch together. Heston, Korajczyk and Sadka (2010, *J. Finance*) find intraday return patterns that are not purely an open/close artefact ([paper](https://www.bauer.uh.edu/departments/finance/documents/Heston_Korajczyk_Sadka_paper_UH.pdf); [arXiv](https://arxiv.org/pdf/1005.3535.pdf)).
- **Practical meaning:** the first and last hours of the *cash* session (and for oil, the 9:00-14:30 ET pit-era core hours, EIA and settlement) are where most wicks and range get built. Overnight CFD candles are thin, and their wicks are less informative. **[LORE, consistent with ACAD volume patterns]**

### 2.4 What the high-low range tells us: range-based volatility **[ACAD]**

The range carries more information about volatility than the close-to-close change, because it uses the path's extremes.

| Estimator | Formula (per bar, log prices; h = ln H/O, l = ln L/O, c = ln C/O) | Properties | Source |
|---|---|---|---|
| Close-to-close | (ln Cₜ/Cₜ₋₁)² | Efficiency 1 (baseline) | - |
| **Parkinson (1980)** | σ² = (ln H/L)² / (4 ln 2) | Uses the range only. ~5x as efficient as close-to-close (Parkinson claimed 2.5-5x; sources quote 4.9-5.2). Assumes zero drift and continuous trading, so it is biased low when trading is discrete or there are opening gaps. | Parkinson, "The extreme value method for estimating the variance of the rate of return", *J. Business* 53 (1980); [bookdown OHLC table](https://bookdown.org/jarneric/financial_econometrics/5.1-ohlc-measures.html) |
| **Garman-Klass (1980)** | σ² = 0.5(ln H/L)² − (2 ln 2 − 1)c² | Efficiency ~7.4. Assumes zero drift and no opening jump. | Garman & Klass, *J. Business* 53 (1980); [Meilijson, "GK revisited"](https://arxiv.org/pdf/0807.3492) |
| **Rogers-Satchell (1991)** | σ² = h(h − c) + l(l − c) | **Unbiased for any drift**. Ignores opening jumps. | Rogers & Satchell, *Ann. Appl. Prob.* 1(4):504-512 ([Project Euclid](https://projecteuclid.org/euclid.aoap/1177005835)) |
| **Yang-Zhang (2000)** | σ² = σ²_overnight + k·σ²_open-to-close + (1−k)·σ²_RS, with k = 0.34/(1.34 + (n+1)/(n−1)) | Drift-independent and **handles opening jumps (gaps)**. Minimum variance in its class. Uses multiple bars. | Yang & Zhang, *J. Business* 73(3):477-491 ([EconPapers](https://econpapers.repec.org/RePEc:ucp:jnlbus:v:73:y:2000:i:3:p:477-91); [qf-lib implementation note](https://qf-lib.readthedocs.io/en/stable/_autosummary/qf_lib.common.utils.volatility.drift_independent_volatility.DriftIndependentVolatility.html)) |
| **Alizadeh-Brandt-Diebold (2002)** | log range as a volatility proxy | Log range is ~Gaussian and robust to microstructure noise, so it works well in stochastic-volatility models. | *J. Finance* 57(3):1047-1091 ([EconPapers](https://econpapers.repec.org/RePEc:bla:jfinan:v:57:y:2002:i:3:p:1047-1091)) |

**Implications for candle reading:**
- A large range means high realised volatility for that bar, which is mostly **noise** about direction. Volatility clusters, so a big-range bar predicts more big-range bars (GARCH-type persistence) better than it predicts direction. **[ACAD]**
- Use Yang-Zhang for ETFs and cash indexes (which have gaps). For 23h CFDs and futures, gaps are small, so Garman-Klass or Rogers-Satchell are adequate. **[ACAD → applied]**
- Normalise every "long body", "long wick" or "tall candle" judgment by recent range or ATR. A 1% WTI candle is small; a 1% SPY candle is large. **[MECH/LORE]**

---

## 3. Close location, IBS, Williams %R, A/D, gaps

### 3.1 Formulas **[MECH]**

- **IBS (Internal Bar Strength)** = (C − L)/(H − L), from 0 to 1 ([Kinlay](https://jonathankinlay.com/?p=2199)).
- **CLV / Money Flow Multiplier (Chaikin)** = [(C − L) − (H − C)]/(H − L) = 2·IBS − 1, from −1 to +1. A/D line = cumulative Σ(CLV × volume). **It ignores gaps**: a gap-down day that closes in the upper half of its range adds to A/D ([StockCharts A/D](https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/accumulation-distribution-line)).
- **Williams %R (Larry Williams)** = (HighestHigh_n − C)/(HighestHigh_n − LowestLow_n) × −100, with n = 14 by default. 0 to −20 is overbought and −80 to −100 oversold; in strong trends it stays pinned in one zone ([StockCharts %R](https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/williams-r)). %R with n = 1 is IBS rescaled.

### 3.2 Evidence on IBS / short-term reversal

- **Pagonidis (2013/2014), "The IBS Effect: Mean Reversion in Equity ETFs"** (NAAIM paper; original PDF not retrieved, findings via Kinlay's summary) **[LORE / industry research]**:
  - Equity index ETFs since the early 1990s: average next-day return +0.35% when IBS < 0.2, and −0.13% when IBS > 0.8.
  - Stronger after high-range days and in high volatility.
  - For US index ETFs the effect appeared only on **high-volume** days.
  - Similar in bull and bear markets, and stronger in the direction of the larger trend.
  ([Kinlay summary](https://jonathankinlay.com/?p=2199))
- **Kinlay (c. 2016)**: SPY and EWS IBS strategy returns turned negative in 2015-16. The SPY equity curve broke below the 95% Monte Carlo band (inside 99%), which is possible decay. Commissions substantially cut the returns. **[LORE, quant-blog analysis]**
- **Pandey and Joshi (2023), arXiv:2306.12434**: replicates IBS-threshold mean reversion on a basket of country ETFs over 10 years, with a long-lowest-IBS / short-highest-IBS strategy. Not peer-reviewed ([arXiv](https://arxiv.org/abs/2306.12434v1)). **[ACAD-preprint]**
- Broader **short-term reversal in equity ETFs/indexes** after extreme days has academic support, e.g. a study of short-term overreaction in US equity ETFs after extreme one-day returns ([SciELO](https://new.scielo.br/j/rcf/a/dN4R3PXxcJcC7B9fvSV58kC/?lang=en)) and Quantpedia's reversal-effect summaries ([Quantpedia](https://quantpedia.com/strategies/mean-reversion-effect-in-country-equity-indexes)). **[ACAD-mixed]**
- **Not established for WTI.** Crude oil has different microstructure (trend/momentum effects in commodity futures are better documented than daily reversal). No IBS-on-oil evidence was found in this search. Treat it as untested. **[gap]**
- **Data caveat [MECH]:** IBS on a 23h CFD bar or a Globex bar is not the same quantity as IBS on the SPY cash bar studied by Pagonidis. Futures settlement vs last-trade close also changes it.

### 3.3 Gaps and gap fills

- **Definition [MECH]:** gap = today's open ≠ yesterday's close. A "full gap" (open beyond the prior high or low) is the stricter version. Gaps exist mainly in session-based instruments (ETFs, cash indexes). On 23h CFDs and futures they appear mostly at the Sunday open and after the daily break.
- **Plastun, Sibande, Gupta and Wohar (2020, *N. Am. J. Econ. & Finance* 52:101177):** Dow, S&P 500 and NASDAQ 1928-2018. They find abnormal price moves **in the direction of the gap** on gap days (momentum), exploitable but temporary, with no seasonality. **Results are contrary to the popular belief that "gaps get filled."** ([UP repository](https://repository.up.ac.za/handle/2263/78336)) **[ACAD]**
- **Caporale and Plastun (2017, *Investment Analysts Journal*):** stocks, FX and commodities 2000-2015. Gap behaviour was mostly consistent with efficiency, with the exception of FX ([Brunel](https://bura.brunel.ac.uk/handle/2438/14372)). **[ACAD]**
- **Yuan (2015):** significant intraday reversals in US stock index futures after large opening moves (cited in the Plastun papers). **[ACAD]**
- Bottom line: "gaps always fill" is **[LORE]**. Evidence is mixed and points to gap-direction momentum on the day in US indexes. Many small gaps do get revisited eventually, simply because price oscillates.

---

## 4. Named patterns: definitions and Bulkowski statistics

### 4.1 How the sources define things

- **Nison** (*Japanese Candlestick Charting Techniques*, 1991/2001) introduced the patterns to the West. His definitions are mostly **qualitative with a few ratios** (e.g. a hammer's lower shadow is at least 2x the real body) and always require **trend context**: a hammer is only a hammer after a decline. He stresses confirmation and Western support/resistance. *(Nison's text was not retrieved directly; definitions below are as widely quoted from it via StockCharts and other secondary sources.)*
- **Bulkowski** (*Encyclopedia of Candlestick Charts*, Wiley 2008; [ThePatternSite](https://www.thepatternsite.com/CandlePerformers.html)) tested 103 patterns on ~4.7 million daily candle lines, mostly US stocks.
  - **Prior trend** = the intermediate-term (3-6 month) price trend leading to the pattern.
  - **Overall performance rank** = a ranked sum of % price changes 1, 3, 5 and 10 days after the breakout, across bull/bear markets × up/down breakouts. 1 = best of 103.
  - **"Reversal/continuation %"** = how often the breakout (a close above the pattern high or below its low) went in the reversal or continuation direction. 50% is coin-flip.
  - "Tall" and "short" are judged against the **median** of recent candles. The exact lookback is not stated on the web pages.
  ([Glossary](https://www.thepatternsite.com/glossary.html))
  - **Caveat: Bulkowski's numbers are self-published, not peer-reviewed.** They cover daily US stock data from a specific period, ignore costs, and the ranks can shift as he updates samples (e.g. bearish three-line strike n = 85).
- **TA-Lib defaults** (the de facto software standard): Doji body ≤ 10% of the average high-low range of the last 10 bars. "Long body" > average body of last 10. "Very long body" > 3x average. "Long shadow" > body. "Very long shadow" > 2x body ([ta-lib.org candle settings](https://ta-lib.org/api/candle-settings/)). **[MECH: software convention]**

### 4.2 Single-candle patterns

| Pattern | Definition (common/Nison-style numeric) | Context required | Bulkowski tested result | Overall rank /103 |
|---|---|---|---|---|
| **Doji** | O ≈ C. Body ≤ ~5-10% of range (TA-Lib: ≤10% of avg range). Bulkowski: "a few pennies" apart. Variants: **long-legged** (long both shadows), **dragonfly** (O = C at the high, long lower shadow), **gravestone** (O = C at the low, long upper shadow). | Nison: most significant after a tall candle in a mature trend, especially at tops. | Southern doji (in downtrend): bullish reversal 52%, "near random" ([page](https://thepatternsite.com/SouthernDoji.html)) | 78 |
| **Spinning top** | Small body, upper and lower shadows each longer than the body | None (indecision) | Reversal 50% ([white](https://thepatternsite.com/SpinTopWhite.html)) | 69 |
| **Marubozu** | Body is ~the whole range: no shadows (white/black). Opening/closing variants lack one shadow. | None | White: continuation 56% ([page](https://thepatternsite.com/WhiteMarubozu.html)) | 71 |
| **Hammer** | Small body at the top of the range. Lower shadow ≥ 2x (ideally 2-3x) body. Little or no upper shadow. Colour unimportant. | **After a decline** | Bullish reversal ~60% ([page](https://www.thepatternsite.com/Hammer.html)) | 65 |
| **Hanging man** | Same shape as the hammer | **After an advance**. Nison wants bearish confirmation next session. | Tested as **bullish continuation 59%**, i.e. fails as a reversal ([page](https://www.thepatternsite.com/HangingMan.html)) | 87 |
| **Inverted hammer** | Small body at the bottom of the range. Upper shadow ≥ 2x body. Little or no lower shadow. Bulkowski's version: 2 lines, a tall black candle then the inverted hammer opening below the prior close, not a doji. | After a decline | Tested as **bearish continuation 65%** (not a reversal), yet strong post-breakout moves ([page](https://thepatternsite.com/HammerInv.html)) | **6** |
| **Shooting star** | Small body near the low. Upper shadow ≥ 2x body. Little or no lower shadow. Not a doji. Nison: ideally gaps up from the prior body. | After an advance | Bearish reversal 59%, "near random" ([page](https://www.thepatternsite.com/ShootingStar.html)) | 55 |
| **Pin bar** ("Pinocchio bar", term usually credited to Martin Pring) | Long tail (commonly ≥ 2/3 of range, or ≥ 2-3x body) protruding beyond nearby bars, small body at the other end. No consensus threshold. | At support/resistance, as a false breakout | No Bulkowski entry; **[LORE]** ([LuxAlgo](https://www.luxalgo.com/library/concept/pin-bar/)) | - |

### 4.3 Two-candle patterns

| Pattern | Definition | Context | Bulkowski result | Rank |
|---|---|---|---|---|
| **Bullish engulfing** | Black body, then a taller white body that engulfs it (bodies only; shadows ignored) | Downtrend | Bullish reversal 63% ([page](https://thepatternsite.com/BullEngulfing.html)) | 84 |
| **Bearish engulfing** | White body, then a taller black body that engulfs it | Uptrend | Bearish reversal 79%, but short-lived follow-through ([page](https://www.thepatternsite.com/BearEngulfing.html)) | 91 |
| **Bullish harami** | Tall black candle, then a small white body inside the prior *body* (Nison: "pregnant"). Harami cross = doji second day. | Downtrend | Reversal 53% (≈ random) ([page](https://www.thepatternsite.com/HaramiBull.html)) | 38 |
| **Piercing line** | Black candle. White candle opens **below the prior low** (Nison/Bulkowski; many modern sources relax this to below the prior close) and closes **above the midpoint** of the black body, but below its open. | Downtrend | Bullish reversal 64% ([page](https://thepatternsite.com/Piercing.html)) | 13 |
| **Dark cloud cover** | Tall white candle. Black candle opens **above the prior high** and closes **below the midpoint** of the white body, but above its open. Closing below the open makes it a bearish engulfing. | Uptrend | Bearish reversal 60% ([page](https://www.thepatternsite.com/DarkCloudCover.html)) | 22 |
| **Tweezer top / bottom** | Two adjacent candles with the same (or nearly the same) high (top) or low (bottom) | Uptrend / downtrend | Tweezers top: *bullish continuation* 56%, near random ([page](https://thepatternsite.com/TweezersTop.html)) | 81 (top) |
| **Inside bar** | Hₜ < Hₜ₋₁ and Lₜ > Lₜ₋₁ (range inside the prior range; harami uses bodies, the inside bar uses the full range) | Any; read as volatility contraction | **[LORE]** (price-action traders). Mechanically a lower range, so expect a range expansion later. | - |
| **Outside bar** | Hₜ > Hₜ₋₁ and Lₜ < Lₜ₋₁ (range engulfs the prior range) | Any | **[LORE]**. Mechanically both sides' stops were run in one bar. | - |

### 4.4 Three- and four-candle patterns

| Pattern | Definition | Context | Bulkowski result | Rank |
|---|---|---|---|---|
| **Morning star** | Tall black candle. A small body (any colour) gapping below it. A tall white candle closing at least halfway into the first body. (Doji middle = morning doji star.) | Downtrend | Bullish reversal 78% ([page](https://www.thepatternsite.com/MorningStar.html)) | 12 |
| **Evening star** | Tall white candle. A small body gapping above. A tall black candle opening below the middle candle and closing at least midway down the first body. | Uptrend | Bearish reversal 72% ([page](https://www.thepatternsite.com/EveningStar.html)) | **4** |
| **Three white soldiers** | Three tall white candles, each opening within the prior body, each closing near its high and higher than the last | Downtrend (reversal) | Bullish reversal 82% ([page](https://www.thepatternsite.com/ThreeWhiteSoldiers.html)) | 32 |
| **Three black crows** | Three tall black candles, each opening within the prior body, each closing near its low at new lows | Uptrend | Bearish reversal 78% ([page](https://thepatternsite.com/ThreeBlackCrows.html)) | **3** |
| **Three-line strike, bearish** | Three black candles with lower lows, then a tall white candle opening below the prior close and closing above the first candle's open | Downtrend | Theory says bearish continuation; **tested as bullish reversal 84%**. n = 85 only ([page](https://www.thepatternsite.com/ThreeLineStrikeBear.html)). | **1** |
| **Three-line strike, bullish** | Three white candles with higher highs, then a tall black candle wiping them out | Uptrend | Tested as bearish reversal 65% ([top-10 page](https://www.thepatternsite.com/CandlePerformers.html)) | **2** |

Bulkowski's top 10 overall ([page](https://www.thepatternsite.com/CandlePerformers.html)):
1. three-line strike bearish
2. three-line strike bullish
3. three black crows
4. evening star
5. upside tasuki gap
6. inverted hammer
7. matching low
8. bullish abandoned baby
9. two black gapping
10. bearish breakaway

Note how the most famous single-candle patterns (hammer, shooting star, doji, engulfing, hanging man) rank mid-to-low. Several "reversal" patterns actually test as **continuation**. **[LORE: Bulkowski's own data]**

### 4.5 Academic evidence on candlestick patterns **[ACAD-mixed]**

| Study | Data | Finding |
|---|---|---|
| Caginalp & Laurent (1998), *Appl. Math. Finance* 5:181-205 | S&P 500 stocks 1992-96, daily, 3-day reversal patterns | Strong out-of-sample significance, ~1% profit over a 2-day hold. One of the few positive results ([EconPapers](https://econpapers.repec.org/RePEc:taf:apmtfi:v:5:y:1998:i:3-4:p:181-205)). |
| Fock, Klein & Zwergel (2005), *J. Derivatives* 13(1):28-40 | **Intraday DAX and Bund futures** | "No evidence of predictive ability from candlestick patterns alone", even combined with momentum filters ([summary](https://improbable.com/2015/06/28/fock-performance-of-candlestick-analysis); [Kassel record](https://forschung.uni-kassel.de/converis/portal/detail/Publication/2462413?lang=en_GB)). Most relevant to intraday index CFDs. |
| Marshall, Young & Rose (2006), *J. Banking & Finance* 30(8):2303-2323 | DJIA stocks | Candlestick strategies do not add value; companion 2007 paper: not profitable on large US stocks ([EconPapers](https://econpapers.repec.org/RePEc:eee:jbfina:v:30:y:2006:i:8:p:2303-2323); [2007 PDF](https://c.mql5.com/forextsd/forum/211/Market%20Timing%20with%20Candlestick%20Technical%20Analysis.pdf)). |
| Horton (2009), *QREF* 49(2):283-294, "Stars, crows, and doji" | 349 stocks | Generally little value (abstract-level) ([IDEAS](https://ideas.repec.org/a/eee/quaeco/v49y2009i2p283-294.html)). |
| Lu, Chen & Hsu (2015), *J. Banking & Finance* 61:172-183 | DJIA components | Eight 3-day reversal patterns **are** profitable after 0.5% costs and data-snooping control **with Caginalp-Laurent holding rules**, but not with Marshall-Young-Rose rules. Stronger in volatile markets. Profitability depends on exit rules more than on the trend definition ([IDEAS](https://ideas.repec.org/a/eee/jbfina/v61y2015icp172-183.html)). |
| Thai, South African replications | Emerging markets | Mostly insignificant; only isolated patterns (e.g. three outside down on the JSE) ([UCT](https://open.uct.ac.za/bitstreams/85e5328d-4d5e-4fcd-83fe-4c6416aeb231/download)) |

**Takeaway:** treat named patterns as *descriptions of what happened*, not standalone signals. The evidence is weakest for intraday futures, the closest analogue to index and oil CFDs.

---

## 5. Volume, trend vs range, context

- **Volume [MECH + LORE].**
  - Exchange volume exists for CL, ES and ETFs. **CFD "volume" is usually tick count** (number of quote updates), not traded contracts. It is a rough activity proxy only.
  - A wick on high volume means many contracts traded at extreme prices and still failed to hold. Practitioners read that as more meaningful than a low-volume wick.
  - Pagonidis's finding that US ETF IBS works only on high-volume days is consistent with this **[LORE/industry research]**. Jain & Joh (1988) document contemporaneous volume-return links **[ACAD]**.
  - Mizrach & Weerts (2009, *Appl. Fin. Econ.*): turnover rises at n-day highs and lows, and rises with n ([IDEAS](https://ideas.repec.org/a/taf/apfiec/v19y2009i10p767-777.html)) **[ACAD]**.
- **Strong trends [LORE, partly MECH].**
  - In persistent trends, candles have large bodies, short wicks on the trend side, and closes near the extreme (IBS near 1 in uptrends). Williams %R and IBS stay pinned.
  - "Reversal" candles (shooting star, bearish engulfing, doji) appear repeatedly and fail. Bulkowski's data shows hanging man and tweezers top testing as *continuation*.
  - Counter-trend wicks in a trend usually mark pullback lows/highs, not reversals.
- **Ranges [LORE].** Wicks at range boundaries plus small bodies are the "natural" habitat of rejection patterns and of IBS mean reversion. The equity-index IBS evidence is effectively a range/short-horizon effect.
- **Support/resistance [ACAD-partial via Osler + LORE].** A wick into a prior high/low or round number is consistent with take-profit absorption (reversal) or a stop cascade (breakout), per Osler (2003). The *close* relative to the level is what practitioners use to separate the two.
- **Volatility regime [ACAD + LORE].**
  - Normalise all body and wick sizes to ATR or range-based volatility.
  - In high-volatility regimes, wicks are larger and more frequent mechanically.
  - Lu, Chen & Hsu (2015) and Pagonidis both report pattern/IBS effects as **stronger in volatile conditions**.
- **Oil-specific context [MECH/LORE].** OPEC+ meeting days, EIA Wednesdays, API Tuesdays (after the cash close), CL expiry/roll and settlement windows. Candles on those days embed scheduled-information shocks, and their wicks reflect news, not "technical rejection".

---

## 6. Common retail mistakes

| Mistake | Why it's wrong | Tag |
|---|---|---|
| **Reading the live candle as final** | Until the bucket closes, the "hammer" can become a marubozu down. Bulkowski measures from the *breakout after completion*. | MECH |
| **Hindsight/selection bias** | Textbook examples are cherry-picked successes. Bulkowski's base rates for famous patterns are 50-65%, many near random. | LORE (data) / ACAD |
| **Ignoring trend context** | Hammer vs hanging man is *the same shape*: the label depends entirely on the prior trend. Bulkowski uses a 3-6 month trend; intraday traders often use 5 bars. | MECH (definition) |
| **Timeframe mismatch** | Trading a 5-minute pattern against a daily trend, or applying daily-stock statistics to 1-minute CFDs | MECH / ACAD (Fock et al.) |
| **CFD session/server-time differences** | Daily candles differ by broker cut-off. A Sunday candle exists on GMT-midnight servers. CFD highs and lows are bid-only and broker-specific. Futures settlement ≠ last trade. | MECH |
| **Treating spread spikes as stop hunts** | Rollover spread widening triggers stops at ask prices not drawn on bid charts | MECH |
| **Unnormalised sizes** | "Long wick" without reference to ATR or recent range | MECH |
| **Assuming gaps fill** | US index evidence shows gap-direction momentum, not fill (Plastun et al. 2020) | ACAD |
| **Confirmation bias / narrative overlay** | Calling every wick a "liquidity grab" after the fact. The same wick is called absorption if price reverses and a stop run if it breaks out: the story is unfalsifiable. | LORE critique |
| **Ignoring costs** | IBS and pattern edges are small, a fraction of a percent per trade. CFD spreads, overnight financing and commissions erase them (Kinlay; Lu, Chen & Hsu use 0.1-0.5% costs). | ACAD / LORE |
| **Using the open/close clustering of extremes as a signal** | It arises even under a random walk (arcsine law) | MECH (math) |
| **Confusing colour with direction** | A red candle after a gap up can be an up day vs the prior close | MECH |

---

## 7. Practical encoding hints (for an agent)

- Compute per bar: `range = H - L`, `body = abs(C - O)`, `upper = H - max(O,C)`, `lower = min(O,C) - L`, `ibs = (C - L)/range`, `body_pct = body/range`, `range_atr = range/ATR(14)`, `gap = O - C_prev`. Guard against range = 0.
- Label using TA-Lib-style relative thresholds (average of the last 10 bars), not fixed constants. Require trend context, e.g. close below/above the 20-bar SMA, or the slope of 10-bar returns.
- Always record **which session/cut-off** produced the bar (CFD server time, Globex day or cash session) and whether close = settlement or last trade.
- For volatility, use Yang-Zhang on ETF/cash bars (gaps) and Garman-Klass/Rogers-Satchell on 23h CFD/futures bars.
- Present pattern outputs as context, with base rates (e.g. "hammer: Bulkowski ~60% reversal, rank 65/103, not peer-reviewed"), never as standalone buy/sell signals.

---

## Source list (primary or most authoritative first)

- Nison, S. *Japanese Candlestick Charting Techniques*, NYIF 1991 / 2nd ed. 2001 (book; definitions via secondary sources here).
- Bulkowski, T. *Encyclopedia of Candlestick Charts*, Wiley 2008; ThePatternSite: https://www.thepatternsite.com/CandlePerformers.html , glossary https://www.thepatternsite.com/glossary.html
- StockCharts ChartSchool, candlestick dictionary / A-D line / Williams %R.
- TA-Lib candle settings: https://ta-lib.org/api/candle-settings/
- Parkinson (1980) *J. Business* 53:61-65; Garman & Klass (1980) *J. Business* 53:67-78; Rogers & Satchell (1991) *Ann. Appl. Prob.* 1:504-512; Yang & Zhang (2000) *J. Business* 73:477-491; Alizadeh, Brandt & Diebold (2002) *J. Finance* 57:1047-1091.
- Osler (2003) *J. Finance* 58:1791-1819; Osler (2005) NY Fed SR150.
- Acar, Lequeux & Ritz (1996) LIFFE Equity Products Review; Mok, Lam & Li (2000) RQFA; Jain & Joh (1988) JFQA; Admati & Pfleiderer (1988) RFS; Wood, McInish & Ord (1985) J. Finance; Heston, Korajczyk & Sadka (2010) J. Finance.
- Pagonidis (2013/14) NAAIM, via Kinlay https://jonathankinlay.com/?p=2199 ; Pandey & Joshi (2023) arXiv:2306.12434.
- Plastun, Sibande, Gupta & Wohar (2020) NAJEF 52:101177; Caporale & Plastun (2017) IAJ.
- Caginalp & Laurent (1998); Fock, Klein & Zwergel (2005); Marshall, Young & Rose (2006); Horton (2009); Lu, Chen & Hsu (2015).
- CME: WTI hours/settlement (SER-4867, settlement procedures); EIA WPSR schedule.
- Broker/MT4 mechanics: MQL5 forum threads, BabyPips forum, IC Markets, TitanFX (practitioner sources for mechanics; verify per broker).

**Items not verified in this pass:** Nison's exact wording (only secondary quotes seen); Bulkowski's exact lookback for "tall/short" median; full text of Marshall-Young-Rose 2006 and Horton 2009 (abstract-level only); the original Pagonidis PDF; current SPY session hours (standard knowledge, not re-fetched).
