# Candlestick patterns and close-location features: evidence review

Compiled 2026-11-25 from web sources (abstracts, publisher and RePEc pages, secondary summaries, and two full texts I read: Caginalp & Laurent 1998 and Jiang, Kelly & Xiu 2023).
Confidence tags:
- [V] means I checked it against the abstract or full text.
- [S] means it comes from a secondary summary (for example CXO Advisory).
- [M] means it comes from my prior knowledge and I could not re-verify it in this session. Check [M] items before citing them.

## 1. Classic candlestick pattern studies

| Study | Market / sample | Method | Result | Costs / snooping |
|---|---|---|---|---|
| Caginalp & Laurent 1998, *Appl. Math. Finance* 5:181-205 [V, full text] | All S&P 500 stocks, 1992-96, daily OHLC | 8 three-day reversal patterns (TWS, TBC, 3-inside/outside up/down, morning/evening star) with **no body-size conditions**. Trend = the 3-day SMA of closes falls (or rises) on each of the prior 6 days, with at most one violation. The test is whether P(t+3) < mean(close t+4..t+6). | Hit rate 63-75% vs a 45-53% base rate (z up to 36). Buy signals averaged about 0.86% gross per trade over about 2 days, and short signals 0.27%. | Authors estimate 0.56-0.76% per trade after a 0.1-0.3% spread. Their "out of sample" just means the definitions came from Morris (1992). There was no snooping correction and no split by time period. The exit uses the **average of 3 future closes**, which smooths the result and is not a tradeable fill. |
| Marshall, Young & Rose 2006, *JBF* 30:2303 [S] | 30 DJIA stocks, 1992-2002 (the same years as C&L) | 28 single-day and multi-day signals. Entry at the close the day after the signal, 10-day hold. Bootstrap on simulated **OHLC** series. | Bullish signals were positive less than half the time. The bootstrap found **no signal with predictive power**. The result held with next-open entry and in sub-periods. | Fails even before costs. |
| Marshall, Young & Cahan 2008, *RQFA* 31:191 [M] | Large Japanese stocks, about 1975-2004 | Same OHLC bootstrap | Candlesticks do not add value. Some weak bullish evidence in the early sub-period, for large stocks only. | Not robust. |
| Fock, Klein & Zwergel 2005, *J. Derivatives* 13(1):28 [V meta / M results] | DAX and Bund futures, intraday, 2002-03 | Precise definitions of basic patterns, tested alone and combined with momentum/MA filters | No significant predictive power. Combining with filters did not rescue it. | Negative. |
| Goo, Chen & Chang 2007, *IMFI* 4(4) [V meta] | 25 Taiwan 50 / Mid-Cap 100 stocks, 1997-2006 | Holding periods of 1-10 days, t-tests, stop-loss variants | Some patterns, mostly bullish ones held longer, looked profitable. Stop-loss helped. | t-tests only, no snooping correction. Weak evidence. |
| Horton 2009, *QREF* 49:283 [V] | 349 US stocks | Stars, crows and doji | "Little value" for stock selection; supports weak-form EMH. | Negative. |
| Lu, Shiu & Liu 2012, *Rev. Fin. Econ.* 21:63 [V] | Taiwan 50 stocks, 2002-08 | Bootstrap plus out-of-sample test | 3 bullish reversal patterns profitable | Short sample from a single market. |
| Lu & Shiu 2012, *EMFT* 48 [V meta] | Taiwan 50, 2002-09 | Two-day patterns | Some profitable; they conclude the market is inefficient | Same data family. |
| Lu 2014, *PBFJ* 26:65 [V] | Taiwan, 1992-2009 | "Four-price-level" classification of all one-day candles. Bootstrap, OOS and sub-sample tests. | 4 one-day patterns profitable after costs (1 bullish, 3 bearish) | Survived costs in-paper. Selected from a large family. |
| Lu & Shiu 2016, *Appl. Econ.* 48:3345 [V] | 30 DJIA stocks, 1974-2009 | All possible one-day candles plus bootstrap | Predictive power rose after 1992; "several" patterns profitable | Bootstrap only; the family-wise error rate is unclear. |
| Duvinage, Mazza & Petitjean 2013, *Quant. Finance* 13:1059 [S] | 30 DJIA stocks, 5-minute bars, Apr 2010 to Apr 2011 | 83 rules, 50-minute horizon, 0.05% one-way cost. Bonferroni, then SSPA (stepwise SPA). | 26/83 significant gross. **5/83 net** (3 on Sharpe). Under SSPA, **0/83 beat buy-and-hold net**. Of 2,047 combined systems, **0 survived**. | The cleanest multiple-testing result: nothing survives. |
| Lu, Chen & Hsu 2015, *JBF* 61:172 [V] | DJIA stocks | 3 trend definitions × 4 holding rules, with a data-snooping correction | **8 three-day reversal patterns profitable under the C&L holding rule** (any trend definition) at 0.5% cost and with 0.1% cost; holds in 3 sub-periods. **None profitable under the MYR fixed-10-day rule.** Stronger in volatile markets. | The best "pro" result. It shows the effect is a **short-horizon (2-3 day) reversal**, so the holding rule matters more than the pattern. |
| Tharavanij, Siraprapasiri & Rajchamaha 2017, *SAGE Open* 7(4) [V] | SET50, 2006-16 | 1/3/5/10-day holds, MYR and C&L exits, skewness-adjusted t-test and binomial test, %D/RSI/MFI filters | Most patterns have returns not different from zero, and the significant ones are high-variance. Patterns cannot reliably predict direction. Filters do not help. | Negative. |
| Chen, Bao & Zhou 2016, *Physica A* 457:148 [V] (the query's "Chen, Bao & Sun"; the third author is Zhou) | Chinese A-shares | 4 pairs of two-day bull/bear patterns, Step-SPA | 3 of 8 patterns forecast at short and longer horizons, 2 only very short-term, 3 inconsistent across size groups | Survives Step-SPA for some patterns. Costs and the short-sale ban in China limit usability. |
| Deng et al. 2022, *SAGE Open* [V] | SSE50, 2000-18 | One-day and multi-day patterns | Some bullish patterns (Long White, Bullish Gap) significant over some holding periods; **no bearish pattern works** | No strong snooping correction. |
| Atri, Zhu & Yegen 2016, *PBFJ* [V meta] | Shanghai/Shenzhen, 1999-2008 | 5 reversal patterns | Profitability depends on liquidity and size | Mixed. |
| Jamaloodeen et al. 2018 [V meta] | S&P 500 | Single-candle patterns | Largely descriptive. | n/a |

### Crypto
- Cohen 2021, *RQFA* 57 [V abstract]: Bitcoin, 2012 to mid-2020, automated systems built on classic patterns. **Only engulfing** reliably anticipated trend shifts. A "reversed kicker" had 74% profitable longs. Harami failed. Patterns were optimised on the same data, so overfitting is likely.
- "Do Candlestick Patterns Work in Cryptocurrency Trading?" (IEEE BigData 2021) [V abstract]: 68 patterns across the top 23 coins. **Most are of little use** and generate false signals.
- Day et al. 2022, *Appl. Econ. Letters* [V abstract]: Bitcoin futures, runs of consecutive 1-minute candles, with mean reversion after the runs. This is an intraday microstructure effect.
- IJQRM 2023 (BTC/ETH) [V abstract]: only engulfing anticipated changes.

### FX
- I found no peer-reviewed hourly-FX candlestick study with a proper snooping correction. An Iranian thesis reported hourly and 4-hour profits but rejected the main hypothesis.
- Technical-rule literature with snooping controls, which bounds what candlesticks could plausibly deliver:
  - Qi & Wu 2006 [M]: some significance before 1990s.
  - Hsu, Taylor & Wang 2016 [M]: stepwise SPA; genuine but declining predictability, concentrated in emerging markets.
  - Wang (Cardiff) [V meta]: emerging-market FX technical profits are "illusory" after snooping.
  - Sullivan, Timmermann & White 2006 [V meta]: weaker in recent periods.
  - Zarrabi, Snaith & Coakley 2016 [V meta]: **none survive costs plus snooping**.

### Commodities and oil
- I found **no peer-reviewed candlestick study on crude oil futures**. The only hits were an MBA thesis (DBS 2016) and a study of oil-company stocks (IJEEP 2017).
- Related evidence:
  - Marshall, Cahan & Cahan 2008, *JBF* 32:1810 [V meta / M result]: about 7,000 technical rules on 15 commodity futures, with White's Reality Check and Romano-Wolf stepwise tests. **No rules profitable after snooping**.
  - Park & Irwin 2010 [M]: US futures 1985-2004, WRC and SPA. Profits not significant after the late 1980s.
  - Szakmary et al. 2010 [V meta]: trend-following in commodities works at **multi-month** horizons, not candlestick horizons.

## 2. Machine learning and image approaches
- **Jiang, Kelly & Xiu 2023, *J. Finance* 78(6):3193-3249** [V full text]:
  - Inputs: CNN on black-and-white OHLC bar images with moving-average and volume, over the past 5, 20 or 60 days. US stocks 1993-2019, with out-of-sample tests.
  - Weekly I5/R5 decile spread: gross annualised Sharpe of **7.2 equal-weight and 1.7 value-weight**, against WSTR (weekly reversal) at 2.8 / 0.8 and TREND at 2.9 / 0.7.
  - Monthly: Sharpe 2.4; quarterly: 1.3. Days 6-20 alone give Sharpe 1.2.
  - Weekly turnover is about the same as WSTR. The authors say the strategy is "mostly accessible to investors who behave as market makers". Profits stay significant after standard cost adjustments at lower rebalance frequencies.
  - It transfers to 26 international markets and to other time scales.
  - **Interpretation:** the largest logistic-approximation coefficients imply a signal of about **½(High+Low) − Close** for the previous day, scaled by the image. In other words, **future returns are high when the close is at the low end of the recent high-low range**. Rising volume also predicts positive returns. So the CNN's main legible feature is a **close-location reversal** (an IBS-like effect), not any named pattern.
  - Caveats: this is a **cross-sectional** stock result, and much of the edge sits in small, illiquid names (equal-weight Sharpe is about 4x value-weight). It does not show time-series predictability for an ETF.
- Follow-ups [M]:
  - Various "image vs. time series" replications find that a 1D-CNN or a simple model on scaled OHLC matches the image CNN, so the image format itself is not the source of the edge.
  - Chinese-market replications report strong A-share results; the short-sale ban and limit moves both apply.
  - Murray, Xia & Xiao, "Charting by machines" (JFE 2024): similar conclusions with simpler networks.

## 3. Wick, shadow and close-location features
- **IBS = (C−L)/(H−L)**:
  - Pagonidis 2013/14 [S, via Kinlay]: across equity index ETFs since about 1993, mean next-day return is **+0.35% when IBS<0.2 and −0.13% when IBS>0.8**.
  - The effect is stronger:
    - after wide-range days;
    - on high-volume days (US);
    - Monday to Tuesday;
    - slightly in bear regimes.
  - Positive skew after low IBS.
  - Kinlay's SPY test, 1999-2016 (buy at close when IBS<0.2, exit at the close when IBS>0.8 or next close): about 13% gross CAGR. It **decayed and was negative in 2015-16**, but stayed within 99% bootstrap bounds. Commissions and slippage cut returns materially.
  - Pandey & Joshi 2023 (arXiv 2306.12434) [V abstract]: confirms it on a country-ETF basket; time in market is low.
- **Shadows as predictors**:
  - Meng, Ma, Qiao & Xie 2021, *J. Sys. Sci. Complexity* 34:657 [V abstract]: US market-index shadows predict returns statistically and economically, with a "Halloween effect" in the shadow.
  - Dai et al. 2025, *Financial Innovation* [V abstract]: (upper − lower) shadow of the **VIX** candle predicts S&P returns negatively.
  - I did not find a peer-reviewed English cross-sectional A-share "upper shadow factor" paper. Chinese broker factor research (上下影线 factors) is widespread but not peer-reviewed [M].
- **Related microstructure** [M]:
  - Lou, Polk & Skouras 2019 (JFE), "A tug of war": momentum accrues overnight and reversal intraday.
  - Gao, Han, Li & Zhou 2018 (JFE), market intraday momentum: the first half-hour return predicts the last half-hour.
  - Daily high-low range is a better volatility estimator than close-to-close (Parkinson; Alizadeh-Brandt-Diebold); shadows mainly carry **volatility information**.

## 4. Gaps
- There is no strong peer-reviewed evidence that "gaps fill" in an exploitable way.
- Fill-rate tables (for example thetrading.tools, SPY 1993 onward: 78% of 0.1-0.25% up-gaps fill the same day) are mostly arithmetic. Small gaps fill almost automatically and fill probability falls with gap size.
- Caporale & Plastun (2017-2019, gaps in US stocks and crypto) [M]: some anomalous post-gap drift or reversal that is generally not profitable after costs.
- Turku thesis 2011-24 [V]: overnight-to-intraday reversal is strongest in small, illiquid stocks and is "structural", not exploitable.

## 5. Multiple-testing frameworks and their effect
- **White Reality Check (2000)** and **Sullivan, Timmermann & White 1999**: the best of about 8,000 DJIA rules was significant in 1897-1986 and **not after 1987**.
- **Hansen SPA (2005)** and **Hsu-Hsu-Kuan stepwise SPA (2010)**:
  - Duvinage et al. 2013: candlesticks go from 26/83 gross to 0/83 net.
  - Chen, Bao & Zhou 2016: a few Chinese patterns survive.
- **Romano-Wolf StepM (2005)**: used by Marshall, Cahan & Cahan 2008 on commodities; nothing survives.
- **FDR (Bajgrowicz & Scaillet 2012, JFE)**: DJIA technical rules show no persistent out-of-sample performance after costs.
- **Bailey & López de Prado Deflated Sharpe Ratio (2014)** and the **Probability of Backtest Overfitting (2017)**: I found no candlestick paper that applies them. We should apply DSR ourselves, with the number of trials set to every rule × parameter × asset we try.
- Pattern: the more honest the correction, the fewer candlestick rules survive. The positive papers mostly use a simple bootstrap, a single market (Taiwan, China), or the C&L averaged-exit construction.

## 6. Conclusions
### (a) Most credible features
1. **Close location within the day's range (IBS / ½(H+L) − C)** as a 1-5 day **reversal** signal. Three lines of evidence support it:
   - practitioner work on index ETFs;
   - JKX's CNN, whose main interpretable feature it is;
   - the short-term reversal literature.
   It is strongest after wide-range days. It has decayed since about 2013 in SPY.
2. **Range or shadow size as a volatility and conditioning variable**. It predicts volatility well; use it to size positions or to amplify (1).
3. **Three-day reversal patterns with a defined prior trend, held 2-3 days** (C&L family; Lu, Chen & Hsu 2015 is the best "pro" paper). These are largely short-term reversal in disguise.
4. **Engulfing** is the one named pattern that recurs across studies, including crypto. The evidence is weak.

### (b) Best described as myths, at least as standalone signals with 5-10 day holds
- Doji (indecision) and stars (morning/evening star, shooting star).
- Hammer and hanging man as single-bar reversals.
- Harami.
- Three black crows as a bearish predictor, and bearish patterns generally on upward-drifting assets.
- "Gaps always fill" as an edge.
- Oscillator filters (RSI/%D/MFI) "confirming" candles (Tharavanij 2017).
- Any of the 50-100 Nison/Morris patterns tested in bulk; essentially none survive SSPA after costs.

### (c) Testable rules
For each rule:
- Compute signals on bar t (close known).
- Run two entry variants: **E1 = buy at the close of t** (assumes a market-on-close (MOC) order) and **E2 = buy at the open of t+1**. Exit at the close of t+N.
- Costs: 2-5 bp per side for SPY/QQQ/IWM/GLD/TLT/XLE, 5-10 bp for USO/BNO, 10-25 bp for BTC.
- Report each rule as one family for DSR.
- Notation:
  - IBS = (C−L)/(H−L), set to NaN if H=L.
  - Range R = H−L. ATR14 = 14-day ATR.
  - Body = |C−O|.
  - Upper shadow US = H−max(O,C); lower shadow LS = min(O,C)−L.
  - Trend uses the C&L definition: SMA3 of closes falling on at least 5 of the 6 days t−6..t, or the simpler C < SMA10 variant.

| # | Rule | Exit |
|---|---|---|
| 1 | **IBS long:** IBS_t < 0.20 | Close t+1. Variant: first close with IBS > 0.8, max 5 days. |
| 2 | **IBS short / flat:** IBS_t > 0.80 → short (or go to cash) | Close t+1 |
| 3 | **IBS + wide range:** IBS < 0.20 and R_t > 1.25 × ATR14 | Close t+1, t+3 |
| 4 | **IBS + trend filter:** IBS < 0.20 and C > SMA200 | Close t+1, t+5 |
| 5 | **Continuous close location:** go long z = (½(H+L) − C)/R (the JKX approximator) | Sign or position ∝ z, held 1 and 5 days |
| 6 | **Long lower shadow (hammer, precise):** LS ≥ 2×Body, US ≤ 0.25×R, R > ATR14, C < SMA10 | Close t+1, t+3, t+5 |
| 7 | **Long upper shadow (shooting star):** US ≥ 2×Body, LS ≤ 0.25×R, R > ATR14, C > SMA10 → short or flat | Close t+1, t+3 |
| 8 | **Bullish engulfing:** C_{t−1}<O_{t−1}, C_t>O_t, O_t ≤ C_{t−1}, C_t ≥ O_{t−1}, plus downtrend (C&L) | Close t+2 and t+3 (C&L style), and t+10 (MYR style) |
| 9 | **Bearish engulfing:** the mirror of 8 with uptrend → short or flat | t+2, t+3, t+10 |
| 10 | **Three inside up (C&L):** downtrend; black day; white day inside the prior body; day 3 closes above day-1 open | t+3 and t+5 |
| 11 | **Three white soldiers / three black crows (C&L, no size filter):** 3 consecutive white (black) days with rising (falling) closes, each opening inside the prior body, preceded by a down (up) trend | t+3, t+5, t+10. Expect bullish weak and bearish ≈ 0. |
| 12 | **Gap-down reversal:** O_t ≤ L_{t−1} − 0.25×ATR14 and C_t > O_t (gap fades intraday); buy at the close | Close t+1, t+3 |
| 13 | **Gap fill intraday (E2 only):** O_{t+1} < C_t × (1−0.5%) → buy at the open | Exit at the close the same day; check whether H ≥ C_t (fill rate vs base rate) |
| 14 | **Doji null test:** Body ≤ 0.1×R and R > ATR14 | Next 1/3/5-day return and absolute return. Expect only a volatility effect. |
| 15 | **Inside-bar / NR7 volatility test:** R_t = min of the last 7 ranges and H_t ≤ H_{t−1}, L_t ≥ L_{t−1} | Next 5-day absolute return (breakout volatility), not direction |

- Asset notes:
  - Expect IBS rules (1-5) to work best on SPY/QQQ/IWM, which are mean-reverting indexes, and worse on GLD/TLT/USO/BNO/BTC.
  - In commodities and BTC, short-horizon returns tend to carry momentum, so try the **inverted** sign there too. Count that as an extra trial in DSR.
  - USO/BNO roll and contango create structural drift, so compare against a drift-adjusted null.
- Pipeline:
  - Use a block-bootstrap of OHLC as the null (MYR-style).
  - Run stepwise SPA or Romano-Wolf across the full family (15 rules × variants × 9 assets).
  - Apply DSR to the chosen rule.
  - Run a time-split OOS (for example pre-2015 / post-2015) because the IBS effect is decaying.

### (d) Honest base rate
- Of the roughly 15-20 academic candlestick studies, about 40% report some profitable pattern. Those positives are concentrated in Taiwan, China, the C&L exit construction, or simple bootstrap tests.
- Under strict multiple-testing corrections with realistic costs, survival is **about 0-10% of patterns**:
  - Duvinage et al.: 0/83 net under SSPA; 5/83 under the looser test.
  - Marshall et al. (US and Japan): 0 on bootstrap.
  - Lu, Chen & Hsu: 8 three-day patterns, but only with a 2-3 day averaged exit.
- Expect any classic named pattern to fail after costs on liquid US ETFs. The best prior is a small, decaying edge from **close-location reversal (IBS) on equity-index ETFs**: roughly 0.1-0.3% gross per trade at t+1, versus a cost of about 2-5 bp per side. That likely leaves a positive but modest net edge, with Sharpe below 1 after 2013, and it needs MOC execution (entry at the close). Entering at the next open loses a large part of the edge, because some of the reversal happens overnight.
- Park & Irwin (2007, J. Econ. Surveys) [M]: about 56 of 95 modern technical-analysis studies were positive, but most lacked snooping or cost controls. The pattern is the same: positive results shrink sharply once tests are honest.

## Sources (main)
- Caginalp & Laurent 1998 full text: https://c.mql5.com/forextsd/forum/210/The%20Predictive%20Power%20of%20Price%20Patterns.pdf
- MYR 2006 summary: https://www.cxoadvisory.com/technical-trading/candlesticks-fiddlesticks/ ; https://ideas.repec.org/a/eee/jbfina/v30y2006i8p2303-2323.html
- MYC 2008: https://ideas.repec.org/a/kap/rqfnac/v31y2008i2p191-207.html
- Horton 2009: https://ideas.repec.org/a/eee/quaeco/v49y2009i2p283-294.html
- Fock et al. 2005: https://opus.bibliothek.uni-augsburg.de/opus4/frontdoor/index/index/year/2017/docId/35176
- Goo et al. 2007: https://businessperspectives.org/publishing-policies2/the-application-of-japanese-candlestick-trading-strategies-in-taiwan
- Lu et al. 2012: https://ideas.repec.org/a/eee/revfin/v21y2012i2p63-68.html ; Lu 2014: https://ideas.repec.org/a/eee/pacfin/v26y2014icp65-78.html ; Lu & Shiu 2016: https://ideas.repec.org/a/taf/applec/v48y2016i35p3345-3354.html
- Lu, Chen & Hsu 2015: https://ideas.repec.org/a/eee/jbfina/v61y2015icp172-183.html
- Duvinage et al. 2013: https://ideas.repec.org/a/taf/quantf/v13y2013i7p1059-1070.html ; https://cxoadvisory.com/technical-trading/testing-japanese-candlesticks-intraday-on-liquid-stocks
- Tharavanij et al. 2017: https://ideas.repec.org/a/sae/sagope/v7y2017i4p2158244017736799.html
- Chen, Bao & Zhou 2016: https://econpapers.repec.org/RePEc:eee:phsmap:v:457:y:2016:i:c:p:148-165
- Deng et al. 2022: https://doaj.org/article/1c545d4ddf834eb2a8ca41bbfb6bf695
- Cohen 2021 (BTC): https://ideas.repec.org/a/kap/rqfnac/v57y2021i3d10.1007_s11156-021-00973-6.html ; IEEE crypto: https://ieeexplore.ieee.org/document/9671826
- JKX 2023: https://economics.yale.edu/research/re-imagining-price-trends
- IBS: https://jonathankinlay.com/?p=2199 ; https://arxiv.org/abs/2306.12434
- Shadows: https://sysmath.cjoe.ac.cn/jssc/EN/10.1007/s11424-020-9126-8 ; https://doaj.org/article/42a0cc343e9b4813b542a9f3b0dfec2d
- Commodities: https://ideas.repec.org/a/eee/jbfina/v32y2008i9p1810-1819.html
- Gaps: https://www.thetrading.tools/gap-analysis ; https://www.utupub.fi/bitstreams/88057d2a-1ee8-4c05-9592-c535a21b502c/download
