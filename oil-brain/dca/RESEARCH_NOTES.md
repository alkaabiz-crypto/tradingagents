# Oil DCA research notes: plain DCA vs conditioned DCA, entries and exits (WTI, USO, CFD, XLE)

Compiled 2026-11-25. Method: web search plus abstracts and summaries. **[V]** = checked against an abstract, the paper or a reliable summary in this session. **[M]** = from memory or secondary sources only, so verify before citing exact numbers.

---

## 1. DCA vs lump sum (LS)

| Claim | Effect / sample | Replication |
|---|---|---|
| Constantinides (1979), "A Note on the Suboptimality of Dollar-Cost Averaging", JFQA. A fixed DCA schedule is dominated by any plan that reacts to new information. [V-secondary] | Theoretical | Not disputed. DCA's case is behavioral, not mean-variance. |
| Rozeff (1994), "Lump-Sum Investing versus Dollar-Averaging", JPM. LS beats DCA. [V-secondary] | LS 1-4% higher over 12 months; LS won in 40 of 65 S&P years | Confirmed by every later study |
| Williams & Bacon (1993), JFP. LS beats DCA about 2/3 of the time, S&P 1926-91. [M] | about 2/3 win rate | Confirmed |
| Leggio & Lien (2003), JFP. LS beats DCA across asset classes on Sortino and Sharpe. [M] | Small-cap, large-cap, bonds | Consistent |
| Vanguard (2012), "Dollar-cost averaging just means taking risk later". [V] | LS won about 67% (US, UK, AU, 1926-2011) | Replicated by Vanguard (2023, Finlay & Zorn): LS won 68%, 1976-2022, median edge 1.2-2.2%/yr. https://corporate.vanguard.com/content/dam/corp/research/pdf/cost_averaging_invest_now_or_temporarily_hold_your_cash.pdf |
| Hayley (2014), Cass WP, "Dollar Cost Averaging: the role of cognitive error". DCA is mean-variance inefficient; its appeal rests on a cognitive error. [V] | Theoretical and empirical | https://openaccess.city.ac.uk/id/eprint/6227/1/Dollar%20Cost%20Averaging%2028012015.pdf |
| **Value averaging (VA)**: Edleson (book 1991/1993, Wiley 2006); Marshall (2000), JFSD 13(1). VA has a higher IRR than DCA. [V] | Reports a higher IRR | **Refuted on measurement:** Hayley (2014/15), "Value Averaging and the Automated Bias of Performance Measures". The IRR advantage is a bias in the measure; there is no higher expected terminal wealth. VA also needs an unbounded cash reserve. https://openaccess.city.ac.uk/id/eprint/6298/1/VALUE%20AVERAGING%207%20October%202014.pdf |

**What applies to oil.** The DCA-vs-LS logic is simple. LS wins when the asset has a positive expected excess return. Rolled WTI futures had roughly zero or negative excess return after 2008, so DCA's relative performance will look *better* than in equities. That is not because DCA is good. It is because the asset lost money: any slow deployment beats immediate deployment into a falling asset. I found no peer-reviewed study of DCA specifically into oil or commodities. Treat every "DCA into oil" claim as untested.

**Backtest caution.** For a fair comparison, give every variant the same capital-flow schedule. Undeployed cash earns T-bills. Report terminal wealth and time-weighted metrics, not only IRR (Hayley's bias applies to any conditional-buy rule, ours included).

---

## 2. Why USO, rolled futures and CFDs lag spot WTI

| Claim | Effect / sample | Status |
|---|---|---|
| Gorton & Rouwenhorst (2006), "Facts and Fantasies about Commodity Futures", FAJ 62(2). An equal-weight collateralized commodity futures index earned an equity-like premium with negative correlation to stocks, 1959-2004. [V] | About 5%/yr excess, Sharpe similar to equities | Bhardwaj, Gorton & Rouwenhorst (2015), "Facts and Fantasies ... Ten Years Later" (NBER w21243), say the premium "largely holds" out of sample (diversified index). For **crude alone after 2008 it does not hold**. https://nber.org/papers/w10595, https://nber.org/papers/w21243 |
| Erb & Harvey (2006), "The Strategic and Tactical Value of Commodity Futures", FAJ 62(2). The average single-commodity excess return is about zero. Index returns come from rebalancing and term structure (roll yield). [V] | Roll return explains most of the cross-section of long-run returns | Confirmed by Szymanowska et al., Koijen et al. https://people.duke.edu/~charvey/Research/Published_Papers/P91_The_strategic_and.pdf |
| Szymanowska, de Roon, Nijman & van den Goorbergh (2014), "An Anatomy of Commodity Futures Risk Premia", JF 69(1). Splits returns into a spot premium and a term premium; the basis is the key sort. [V] | Spot premia 5-14%/yr, term premia 1-3%/yr (long-short sorts) | Cross-sectional, so it does not translate directly to single-asset oil timing. https://ideas.repec.org/a/bla/jfinan/v69y2014i1p453-482.html |
| Koijen, Moskowitz, Pedersen & Vrugt (2018), "Carry", JFE. Carry (the slope) predicts returns in every asset class, commodities included. [M] | Commodity carry Sharpe about 0.5-0.6 (cross-sectional) | Held up out of sample. Single-asset time-series carry is weaker. |
| USO vs spot, 2009-2020: prolonged contango and a steep curve explain the underperformance (Applied Economics Letters, 2022). [V-abstract] | Large; USO lost about 98% from peak to 2020 trough | https://informahealthcare.com/doi/abs/10.1080/13504851.2022.2082363 |
| The roll costs are concentrated in contango episodes: 2009-10, 2015-16 and 2020 (super-contango). [V] | Practitioner estimate: USO lagged front-month WTI by about half since 2014 | 24/7 Wall St (2026), secondary source |
| **April 2020.** The May WTI contract settled at -$37.63 on 20 Apr 2020. USO moved to multi-month holdings (27 Apr 2020 filing) and did a 1:8 reverse split. [V] | Breaks any USO price series that is not adjusted for splits | Adjust for the split and expect a structural change in USO's roll method from May 2020. |
| **CFD (Exness USOIL).** The swap is a financing charge, not a true roll, and some brokers also include roll adjustments. Exness offers swap-free accounts for some clients. Triple-swap day for energies is unclear (sources conflict). [V] | Not public in a stable form; get the live contract spec | https://www.exness.com/commodities/usoil. Model the swap as a parameter (for example -3 to -8%/yr on notional for longs) and run sensitivity tests. |
| Spot WTI is **not investable**. A backtest on spot (DCOILWTICO) overstates returns compared with any instrument you can actually hold. | | Backtest on the continuous back-adjusted front contract, or on USO total return. Spot is a benchmark only. |

**Implication.** The instrument choice may matter more than the timing rule. Since 2006, buy-and-hold USO is deeply negative, while XLE gained about 6%/yr including dividends (about 220% cumulative, June 2006 to January 2026; PortfoliosLab, secondary). XLE's max drawdown was about -71%, against about -98% for USO.

---

## 3. Entry-timing signals for oil

### 3a. Term structure, basis, backwardation (strongest academic support)
- Gorton, Hayashi & Rouwenhorst (2013), "The Fundamentals of Commodity Futures Returns", Review of Finance 17(1). Low inventories go with backwardation and high risk premia. The basis, prior 12-month returns and volatility all reflect the state of inventories and predict premia. **Positions (hedging pressure) do NOT predict premia.** Sample 1969/71-2006/10. [V] https://www.nber.org/papers/w13249
- Levine, Ooi, Richardson & Sasseville (2018), "Commodities for the Long Run", FAJ. Uses 1877-2015 data. Average excess returns were much higher in backwardation than in contango, and higher when the trend was up. [M] This is the most direct long-sample support for a "buy only in backwardation" rule.
- Fuertes, Miffre & Rallis (2010), JBF, "Tactical allocation in commodity futures markets: combining momentum and term structure signals". Double-sorted long-short earned about 21%/yr in 1979-2007. [M] Quantpedia's term-structure strategy cites about 11.7%/yr in 1979-2004 with a max drawdown of -78%. There is evidence of weaker results in financialized markets. https://quantpedia.com/strategies/term-structure-effect-in-commodities
- Bessembinder, Coughenour, Seguin & Smoller (1995), JF 50(1). The curve implies mean reversion: about 44% of a spot oil shock is expected to reverse within 8 months. [V] This is the expected path priced by the curve, not an excess return you can earn.

**Decay.** Most of the evidence is *cross-sectional* (long-short across 20-30 commodities). The *time-series* version for a single asset (oil long only when backwardated) has less direct out-of-sample evidence after 2008. Mechanically, it avoids the worst roll bleed (2009-10, 2015-17, 2020). It also misses the start of rallies: the curve flips to backwardation late, after the price has already recovered (2016-17, 2021).

### 3b. Momentum, trend, time-series momentum (TSMOM)
- Moskowitz, Ooi & Pedersen (2012), "Time Series Momentum", JFE. Uses 58 futures from 1985-2009, crude included. A 12-month lookback held for 1 month gives significant returns in every asset class. [V]
- Hurst, Ooi & Pedersen (2017), "A Century of Evidence on Trend-Following". Positive in every decade, 1880-2016. [V-partial]
- **Decay.** Georgopoulou & Wang (2016) find TSMOM's risk-adjusted returns diminishing after 2009, "particularly in commodities" [V-secondary]. Kurth, Eisler, Rej & Bouchaud (2026, arXiv 2607.01550) find a sharp break in trend profitability around 2008/9 across 101 futures (1995-2025). Fast trend Sharpe (EWM 5/20) fell from 0.84 to 0.12. Slow trend Sharpe (EWM 50/200) fell from 0.70 to 0.40. Commodities held up comparatively well as an asset class, with no energy-specific numbers. [V] **Use slow signals (6-12 months, 200 days), not fast ones.**
- Psaradellis, Laws, Pantelous & Sermpinis (2016), summarised by CXO Advisory. Tested 7,846 technical rules on WTI futures and USO, 2006-2015. After correcting for data snooping and costs, the out-of-sample net Sharpe ranged from -0.93 to +0.37. "Technical trading rules do not work for crude oil futures or USO on a net out-of-sample basis." [V] https://www.cxoadvisory.com/commodity-futures/performance-of-technical-trading-rules-for-crude-oil-futures/ **This is the key base rate.**
- Faber (2007/2013), 10-month SMA on GSCI within GTAA. The rule mainly cuts drawdowns and adds little return. [V-secondary]

### 3c. Mean reversion, buying drawdowns
- Over long horizons, real oil prices mean-revert slowly (Pindyck 1999, Energy Journal, "The long-run evolution of energy prices") [M]. The half-life is years and the long-run mean itself shifts.
- Alquist, Kilian & Vigfusson (2013), Handbook chapter. No approach reliably beats the no-change forecast for the nominal oil price. Futures do worse than no-change at long horizons. [V] There is no reliable, publicly documented edge in level-based buy-the-dip timing.
- In practice, buying the dip in rolled oil after 2008 meant catching falling knives: 2008-09, 2014-16 and 2020. Each ended up higher only for buyers who survived the roll cost or held spot, which you cannot hold.

### 3d. Inventories (EIA, Cushing)
- Inventory surprises move prices on the announcement day. A build of +1 mb versus consensus lowers the futures return. The effect lasts no longer than the day (EIA 2017 presentation; Ye & Karali 2016, Energy Economics). [V] The *level* of inventories works through the basis, which is already captured in 3a. A weekly-frequency edge is mostly not tradeable for a DCA investor.
- Proxy: use the 5-year range of Cushing stocks or total US commercial stocks (EIA weekly, from 2004). Weak support. It mostly duplicates the backwardation signal.

### 3e. Positioning, hedging pressure (CFTC COT)
- de Roon, Nijman & Veld (2000), JF. Hedging pressure affects futures returns. [M]
- Basu & Miffre (2013), JBF 37(7). Long-short hedging-pressure portfolios earn significant premia (cross-sectional). [V]
- Against: Gorton, Hayashi & Rouwenhorst (2013) and Rouwenhorst & Tang (2012) find **no predictive power** from positions. [V] Mixed evidence. A single-asset COT oil timing rule is low priority. Use it as a robustness test only.

### 3f. Dollar
- The oil-USD correlation flipped from negative to positive around the early 2010s, after the shale boom and the move to US net exporter status in 2019-20. BIS WP 1083 (Rees) treats this as partly structural. The ECB (2024) says it is mostly a mix of shocks. [V] **The relationship is unstable, so do not use the dollar as a signal.**

### 3g. Seasonality
- Practitioner claims: refiner buying from December to May, and strength from May to September (StoneX, Barchart). I found no rigorous academic support, and the timing has shifted over time. [V] Low priority. It is an obvious data-mining risk.

### 3h. Oil and equities
- Driesprong, Jacobsen & Maat (2008), "Striking Oil: Another Puzzle?", JFE 89(2). Rising oil prices predict lower stock-market returns (a lagged effect). [V] Industry-level US follow-ups support it. This says nothing about timing oil itself. For an XLE investor, XLE follows oil with a lag and an equity beta.
- Practical point: DCA into XLE (with dividends) removes roll bleed and has historically dominated USO. Its drawdowns were still about -70% (2008, 2020).

---

## 4. Exits and risk control

| Method | Evidence | Status |
|---|---|---|
| Stop-losses: Kaminski & Lo (2014), "When Do Stop-Loss Rules Stop Losses?", JFM 18. Under a random walk, a stop-loss always lowers expected return. With momentum or regime switching it can add value. Monthly 1950-2004: +50-100 bp/month during stop-out periods (equity to bonds). [V] https://dspace.mit.edu/handle/1721.1/114876 | Depends on the series being autocorrelated | Oil's trend profits after 2009 are weak, so expect little benefit beyond lower volatility. |
| Han, Zhou & Zhu (2016), "Taming Momentum Crashes: A Simple Stop-Loss Strategy". A stop-loss helps momentum portfolios. [M] | Equity momentum | Not tested on oil |
| 200-day or 10-month trend filter exit (Faber; Hurst et al.) | Large drawdown cuts in GTAA, about the same return | Fast signals decayed after 2009 (Kurth et al. 2026). Slow signals held up better. |
| Volatility targeting: Harvey et al. (2018), "The Impact of Volatility Targeting", JPM 45(1). Uses 60 assets, 1926-2017. Sharpe gains for equities and credit (leverage effect). **For commodities the Sharpe gain is negligible, but tail risk and extreme returns fall.** [V] https://people.duke.edu/~charvey/Research/Published_Papers/P135_The_impact_of.pdf | | Bongaerts, Kang & van Dijk raise a look-ahead critique. Useful for capping drawdowns, not for adding return. |
| Take-profit, trailing stop | No academic support specific to oil. With no autocorrelation, a take-profit cuts the right tail. Oil's returns are positively skewed in spikes (2008, 2022). | Test only as robustness. Expect it to hurt. |
| Psaradellis et al. (2016) | Filter, channel and breakout exits fail out of sample net of costs | Base rate |

---

## 5. Practitioner and web evidence
- **Quantpedia:** commodity term-structure and momentum strategies (cross-sectional); there is evidence of weaker results in financialized markets.
- **CXO Advisory:** technical rules on WTI and USO fail out of sample (2006-2015 sample).
- **Alpha Architect:** volatility targeting improves risk-adjusted returns mainly for equities. Its trend-following articles back slow trend filters as drawdown control.
- **EIA:** inventory shocks have only an announcement-day effect.
- **CME:** "Demystifying time-series momentum" education piece.
- **No credible study was found of DCA into oil or USO.** Mechanical expectation: DCA into USO since 2006 would show a large negative IRR, since each tranche suffers its own roll bleed. DCA into the WTI front contract (back-adjusted) would also show a negative excess return. DCA into XLE would show a positive return.

---

## 6. Ranked rules to test (daily data, 2006 onward)

Shared setup, applied to all variants:
- Contribution C every week (Monday close) into a cash account that earns T-bills.
- Rules decide whether and how much of the accumulated cash to deploy.
- Instruments: (a) back-adjusted CL1 with roll at front-contract expiry minus 5 trading days, (b) USO total return, split-adjusted, (c) XLE total return, (d) CFD = spot minus a swap parameter.
- Benchmarks: plain weekly DCA, and lump sum at t0 (where a lump sum applies).
- Costs: 2-5 bp per trade on futures and ETFs, plus the CFD spread and swap.

1. **Backwardation gate.** Buy the weekly amount (plus any cash that has piled up) only when F2/F1 - 1 < 0, i.e. the 2nd-month contract is below the front month. Otherwise hold the cash. Variant: use F12/F1 - 1 < 0, the 1-year slope, which is less noisy. Highest academic support (Gorton, Hayashi & Rouwenhorst 2013; Szymanowska et al. 2014; Levine et al. 2018).
2. **Trend gate, 12-month TSMOM.** Buy only when the 252-day total return of the instrument is > 0. Variant: exit all holdings to cash when it turns ≤ 0 and redeploy when it turns > 0 (Moskowitz, Ooi & Pedersen 2012; Hurst, Ooi & Pedersen 2017).
3. **200-day SMA filter (buy and hold-exit).** Buy only when close > SMA200. Sell everything when close < SMA200 for 3 consecutive closes, a buffer against whipsaw. Re-enter when it closes above.
4. **Combined carry and trend.** Buy only when both rule 1 and rule 2 are true. Exit when both are false (Fuertes, Miffre & Rallis 2010 logic).
5. **Volatility-scaled DCA.** Weekly buy amount = C × min(2, σ_target / σ_63d), with σ_target = 35% a year (roughly oil's long-run volatility) and σ measured over 63 days. Any shortfall stays in cash. This deploys more in calm markets and less in turbulence. Harvey et al.: expect lower tail risk and no Sharpe gain.
6. **Drawdown-accelerated DCA (the "buy the dip" test).** Weekly amount = C × (1 + k × DD), where DD is the instrument's drawdown from its 252-day high and k = 2, capped at 3C, paid from accumulated cash. Expect this to *lose* against plain DCA on USO and CL1 because of 2008, 2014-16 and 2020, and possibly to win on XLE. Run it as the counter-hypothesis.
7. **Slow-trend and carry exit overlay on plain DCA.** Buy every week regardless. Sell all holdings when SMA50 < SMA200 *and* the 1st-2nd month spread is in contango. Buy back on the first week when either condition clears.
8. **Kaminski-Lo style stop-loss.** Hold plain DCA. Exit to cash when the trailing 63-day cumulative return is < -20%. Re-enter when the trailing 21-day return is > 0. Test thresholds -10%, -20% and -30% and report them all to avoid cherry-picking.
9. **Contango-depth deferral (roll-cost avoider).** Buy only when the annualised roll yield, (F1/F2 - 1) × 12, is above -10%/yr. This skips only steep contango, such as 2009, 2015 and 2020. It is a softer version of rule 1.
10. **Inventory gate.** Buy only when EIA US commercial crude stocks, excluding the SPR, are below their 5-year seasonal average for that week. Use the Wednesday release, applied on Thursday or later to avoid look-ahead. Expected to duplicate rule 1, so treat it as a robustness check.
11. **Instrument switch (not a timing rule).** Run the same plain DCA into XLE instead of USO. Likely the single biggest effect.
12. **COT hedging-pressure gate (low prior).** Buy only when the commercial net short as a share of open interest is above its 3-year median, i.e. hedgers are more short. Use Tuesday COT data applied the following Monday. Mixed evidence (Basu & Miffre vs Gorton, Hayashi & Rouwenhorst).

Do NOT prioritise the dollar filter, seasonality, take-profit or fast moving-average crossovers.

### Honest base rates and expectations
- Lump sum vs DCA: LS wins about 2/3 of the time in positive-premium assets. In oil futures after 2008 the premium was about zero or negative, so DCA and cash-heavy rules will look good partly by construction. Compare against a "never buy, hold T-bills" baseline as well.
- Technical rules on WTI and USO: out of sample after costs, **fewer than 2% of rolling best-rule portfolios beat the median rule** (Psaradellis et al. 2016, sample 2006-15). Expect most of your 12 rules to fail significance after a data-snooping correction (use White's Reality Check, SPA or a Deflated Sharpe).
- Trend following after 2009: Sharpe for fast signals fell about 85%, for slow signals about 40% (Kurth et al. 2026). After 2014, oil-specific trend was dominated by a few regimes: the 2014-15 collapse, 2020 and 2022. Gains depend heavily on those episodes. Report results with each one excluded.
- Oil price forecastability: the no-change forecast is rarely beaten (Alquist, Kilian & Vigfusson 2013).
- A realistic hope: rules 1, 2, 3, 4 and 7 cut max drawdown from about -90% to about -40 to -60% on USO and CL1, and cut roll bleed. Terminal wealth may still be below a T-bill baseline. The sample has only about 4-5 independent oil regimes since 2006, so treat any Sharpe gap below about 0.3 as noise.
- Data hygiene: USO 1:8 reverse split (April 2020); USO roll-method change (May 2020); the negative CL1 print on 20 April 2020 (log returns break, so use arithmetic P&L on back-adjusted prices); CFD swap rates change over time.
