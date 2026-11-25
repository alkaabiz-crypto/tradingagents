# CANDLES.md — the candle brain

Built 2026-11-25 at the user's request: everything the lab knows about candles and wicks, what they mean, and what
really tells whether price will rise or fall. **Read this before any study or ticket that uses candles.**
Sources: `REF_anatomy.md` (what candles represent, with links), `REF_evidence.md` (academic studies),
`candle_study.py` (our own test of 1,248 systems), `harami_neighbours.py`, `../smallwins/` (IBS), `../MISTAKES.md`.
Tags: **[FACT]** mechanics, **[ACADEMIC]** peer-reviewed support, **[LORE]** trader belief, **[OURS]** this lab's test.

---

## 1. What a candle is

A candle is four prices for one time slot: **open, high, low, close (OHLC)**.

```
        |   <- upper wick (shadow): high down to the top of the body
      ┌─┴─┐
      │   │ <- body: open to close (green/white = close above open, red/black = close below open)
      └─┬─┘
        |   <- lower wick: bottom of the body down to the low
```
- **Body** = |close − open|: who won the slot, buyers (green) or sellers (red). [FACT]
- **Range** = high − low: how far price travelled, i.e. how volatile the slot was. [FACT]
- **Upper wick** = high − max(open, close): price went up there but **could not stay**. [FACT]
- **Lower wick** = min(open, close) − low: price went down there but **could not stay**. [FACT]
- **Close location (IBS)** = (close − low) / (high − low): 0 = closed at the low, 1 = closed at the high. [FACT]

What a candle does NOT show [FACT]: which came first, the high or the low; how long price spent at each level;
how much was traded at each price. Two very different days can make the same candle.

**The same day makes different candles on different charts** [FACT]:
- ETFs (USO, SPY, QQQ): the 9:30-16:00 New York session (6:30 pm - 1:00 am Abu Dhabi). Overnight moves show as
  GAPS between one close and the next open.
- Futures (WTI CL, S&P ES): the almost-24-hour day, 6 pm - 5 pm New York. WTI's official settlement is set
  14:28-14:30 New York and can differ from the last trade.
- CFDs (Exness USOIL, USTEC, US500): the broker's server midnight cuts the candle; MetaTrader charts plot the BID
  only, so a stop can fill at the ask without any wick on the chart showing it; spreads widen around 5 pm New York.
- So an Exness USOIL daily candle is NOT the same candle as USO's daily candle. Always test on the chart you trade.

## 2. What wicks mean

- A wick proves only that price traded there and was pushed back before the close. [FACT]
- **Why it happens** (explanations): orders waiting at that level absorbed the move; stop-loss orders were triggered
  and then filled; the move ran out of buyers or sellers. Real FX order data shows take-profit orders bunch at round
  numbers (these cause reversals) and stop-losses just beyond them (these cause fast breakouts) — Osler 2003. [ACADEMIC]
  "Liquidity grabs", "stop hunts" and Market-Profile "excess" are the trader versions of this story. [LORE]
- Daily highs and lows bunch near the open and the close. That happens even in a pure random walk, so on its own
  it is NOT a signal. [ACADEMIC]
- **The best-proven use of wicks is measuring volatility**: estimators that use the high and low (Parkinson 1980,
  Garman-Klass 1980, Rogers-Satchell 1991, Yang-Zhang 2000) are ~5-8x more efficient than close-to-close.
  Big wicks = a jumpy market = use smaller size and wider stops. [ACADEMIC]
- **Do long wicks predict the next day?** [OURS] On 12 markets since 2014, next-day returns by wick size moved only
  a few bp with no steady pattern. A long lower wick did NOT mean "up tomorrow" (it was slightly negative on
  average); a long upper wick did NOT mean "down tomorrow". **Wicks alone do not predict direction.**

## 3. What really predicts a rise or a fall (ranked by evidence)

1. **Where the close sits in the day's range (IBS), in US stock indexes, for 1-5 days.** [ACADEMIC + OURS]
   Closing near the LOW tends to be followed by a bounce; near the HIGH by a small give-back.
   Pagonidis: +0.35% next day after IBS < 0.2, −0.13% after IBS > 0.8 (index ETFs); the CNN image study
   (Jiang, Kelly & Xiu 2023) found its model mainly learned this same close-location effect.
   OURS: QQQ IBS < 0.2 -> sell at the first close with IBS > 0.5: 34 trades a year, 65% wins, +31 bp a trade
   net, passed the placebo and the neighbour check (73%). It FAILED on SPY (13%), IWM and DIA (0%), and it is
   weakening since ~2013-2015 in the literature. **Needs entry at the close**; at the next open half the edge is gone.
   -> live paper sleeve `../smallwins/ibs_live.py` + the 00:44 Abu Dhabi pre-close alert.
2. **Short-term reversal after a sharp drop, in stock indexes** (RSI(2) dip, 3 down closes, bullish harami).
   [ACADEMIC + OURS] Same family as (1). Bullish harami pointed the right way in 100% of its 54 settings on SPY,
   QQQ and DIA, but it is rare (~3 a year) and did not reach significance (neighbour check: FAIL).
3. **Range as a volatility gauge** for sizing and stops. [ACADEMIC] (Not direction.)
4. Everything else below has no reliable edge.

**In OIL, nothing candle-based worked.** [OURS] Every oil candle pattern and every small-win dip setup failed
(USO, BNO, XLE, XOP); there is no peer-reviewed study showing oil candlestick profits either. Oil gaps 20-50% in a
day sometimes (2020), which wrecks small-win systems.

## 4. The named patterns: definitions and verdicts

Definitions as coded in `candle_study.py` (Nison / Bulkowski style). "Down/up" = the close before the pattern is
below/above the close 5 days earlier. Result = post-2014, 12 markets, entry at the next open, 1-day hold, excess
over the market's normal drift. Bulkowski numbers are from his encyclopedia (not peer-reviewed).

| Pattern | What it looks like | Said to mean | OURS: markets right (of 12), median excess | Verdict |
|---|---|---|---|---|
| **Bullish harami** | down; big red day, then a small green body inside it | selling is drying up | **10/12, +16 bp** (oil +17) | best pattern, but rare; not proven |
| Bearish harami | up; big green, then small red inside | buying drying up | 9/12, +7 bp | weak |
| Inverted hammer | down; long upper wick, tiny lower wick | buyers testing | 9/12, +6 bp | weak |
| Bullish marubozu | big green, almost no wicks | strong buyers | 8/12, +3 bp | noise |
| Gravestone doji | open=close at the low, long upper wick | top | 8/12, +3 bp (as short) | noise |
| Hanging man | up; long lower wick, small body at the top | top | 7/12, +3 bp | noise (Bulkowski: acts as continuation) |
| Shooting star | up; long upper wick, small body at the bottom | top | 7/12, +3 bp | noise (Bulkowski 59%, rank 55) |
| Piercing line | down; red, then opens below its low, closes above its midpoint | bottom | 7/12, +6 bp | too rare to judge |
| Inside bar | high and low inside yesterday's | pause | 7/12, +1 bp | noise (useful only as low volatility) |
| Three white soldiers / black crows | 3 strong candles in a row | trend continues | 6/12, ~+1-3 bp | noise; oil −17/−20 bp |
| Hammer | down; long lower wick, small body at the top | bottom | 6/12, −0.4 bp | **myth** (oil +34 bp but few events) |
| Tweezer bottom / top | two equal lows / highs | reversal | 6/12, ~0 bp | myth |
| Doji | open ≈ close | indecision / reversal | 5/12, −5 bp | **myth** |
| Morning star / evening star | 3-candle reversal | reversal | 5/12, −3 bp / −23 bp | **myth** (evening star is wrong way) |
| Dark cloud cover | up; green, then opens above its high, closes below its midpoint | top | 5/12, −4 bp | myth |
| Long lower wick / dragonfly doji | lower wick ≥ 60-70% of range | "buyers rejected the low" | 4/12, −1 / −4 bp | **myth** |
| Outside up / down | engulfs yesterday's whole range | reversal / momentum | 3-4/12, −2 / −3 bp | myth |
| **Bullish engulfing** | down; red, then a bigger green body swallowing it | strong reversal up | **1/12, −12 bp** | **myth — it points the WRONG way** |
| **Bearish engulfing** | up; green, then a bigger red body | strong reversal down | **1/12, −11 bp** | **myth — wrong way** (Bulkowski 63%, rank 84) |

Academic agreement [ACADEMIC]: Marshall, Young & Rose 2006 (DJIA), Marshall, Young & Cahan 2008 (Japan), Fock,
Klein & Zwergel 2005 (DAX/Bund intraday, closest to CFDs), Horton 2009, Tharavanij et al. 2017: no value after costs.
Duvinage et al. 2013: 0 of 2,047 systems survive a proper multiple-testing test. Positive papers (Caginalp & Laurent
1998; Lu, Chen & Hsu 2015; some Taiwan/China studies) only work with 2-3 day exits, which is the short-term
reversal effect of section 3, not the patterns themselves. Base rate: ~0-10% of patterns survive strict tests.

## 5. How price rises and falls (what the evidence supports)

- Over days, US stock indexes **mean-revert**: sharp down closes are followed by small bounces (section 3).
- Over months, many markets **trend** (time-series momentum), but the effect weakened after 2009; slow signals
  (12-month) held up better than fast ones (see ../dca/RESEARCH_NOTES.md).
- Oil is driven by **inventories, the futures curve (backwardation/contango), OPEC and the dollar**, not by
  candle shapes (see ../KNOWLEDGE.md, ../BRAIN.md). Even those signals failed in the lab after 2020.
- Gaps: "gaps always fill" is mostly arithmetic (small gaps fill by chance); a 1928-2018 US index study found
  gaps tend to CONTINUE in their direction. [ACADEMIC]
- Volume: in CFDs "volume" is usually a tick count, not real contracts. [FACT]

## 6. Rules for the bot (standing)

1. Never trade a named candlestick pattern on its own. The only candle feature the lab trades is IBS on QQQ.
2. Never trust a pattern because it "looks right" on a chart (hindsight): only coded, pre-registered, tested rules.
3. Always use the candle of the market and session you actually trade (USO ≠ USOIL ≠ CL).
4. Use the range (ATR, Yang-Zhang) for size and stops, not for direction.
5. In oil, do not use candle signals; use the oil brain's fundamentals as background only.
6. In strong trends, reversal candles fail again and again; context beats shape.
7. A new candle idea must pass: pre-registration, OOS 2014-19 and HOLDOUT 2020+, 2x cost, placebo p ≤ 0.01,
   the family-wise luck bar (best of N; ~t 4.0 for 1,248 systems), and the neighbour check.
8. Log every candle mistake in ../MISTAKES.md.

## 7. Open questions (next tests)

- IBS with a wide-range-day filter and a volume filter (stronger in the literature); Monday-into-Tuesday effect.
- IBS on the actual Exness USTEC / US500 CFD session candles (server midnight), and with real CFD spreads/swaps.
- Intraday candles (1h/5m) on USOIL around the EIA report (Wed 10:30 New York = 7:30 pm Abu Dhabi).
- Deflated Sharpe (Bailey & López de Prado) on every candle family.
- Reverse-sign (momentum) versions on USO, BNO, GLD and BTC, counted as extra trials.

## 8. Change log
- 2026-11-25: created from the two research files, candle_study.py (1,248 systems) and the harami neighbour check.
