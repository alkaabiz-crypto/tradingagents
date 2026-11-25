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


## 4b. The "John Wick" candle and BTC wicks (2026-11-25)

**What traders mean** [LORE] (notes: `REF_johnwick_btc.md`): crypto slang, no official definition. An unusually
LARGE wick that pokes through an obvious recent high/low (a "stop hunt" / "liquidity grab") and closes back inside.
It mixes three older ideas: the **pin bar** (tail >= 2/3 of the range), the **swing failure pattern (SFP)** (sweep a
prior swing high/low, close back inside) and **Turtle Soup** (Linda Raschke: new 20-day low while the old one is
>= 4 days old, buy back above it). Wyckoff calls the same thing a **spring** (at a range low) / **upthrust** (high).
Typical numbers: wick >= 60-67% of the range, >= 2-3x the body, range >= 1-2x ATR(14), sweep of the 10-20-candle
low/high, stop beyond the wick tip, target 1.5-3R, out in 1-5 candles.
Why big BTC wicks happen [FACT]: forced liquidations of leveraged perpetual-futures positions (e.g. the 10 Oct 2025
cascade, > $19B liquidated in 24 hours) push price through levels, then it snaps back. Wicks differ between venues,
so an Exness BTCUSD wick is not the same as a Binance or Coinbase wick.
Evidence [ACADEMIC]: no rigorous cost-aware test of John Wick / SFP / Turtle Soup on BTC exists; the famous claims
are anecdotes. BTC leans to MOMENTUM (Liu & Tsyvinski 2018: a big up day predicts a small further rise), not to
reversal; short-term reversal shows up mainly in small altcoins. Hour-of-day and weekday return effects did not
persist (Baur et al. 2019).
**OURS** (`btc_wicks.py`, `btc_wicks2.py`; 276 systems: John Wick, John Wick + sweep, SFP, Turtle Soup, with the trend,
small-candle control, liquidation wick (>= 2 x ATR and biggest in 50 candles), pin bar, confirmed sweep; long and
short; daily 2014-2026, 4-hour and 1-hour 2024-2026; 10 bp a side): **0 pass.** Best t 1.4 (the luck bar is ~3.5).
- Buying big lower wicks: up some years, down others — no edge. The John Wick is rare (~2 a year on daily candles).
- SHORTING big upper wicks LOST in almost every version (BTC tends to keep going up after them = momentum).
- Hourly: costs (~0.1% a side) are bigger than any wick edge; 0 of 30 hourly long versions made money.
- The "liquidity grab" sweep and a confirmation entry did not fix it.
**Verdict:** on BTC the John Wick candle is a story, not a tradable edge. The lab's only BTC edge is TREND:
the 20-day breakout in the 200-day trend's direction, long side only (btc_research/BTC_REPORT.md; +0.3-0.5R a
trade, fading) — the existing demo ticket (combo/btc_ticket.py, 4:07 am Abu Dhabi).

## 4c. ALL 61 famous patterns (TA-Lib library, 2026-11-25, `talib_study.py`)

TA-Lib is the standard pattern library (definitions after Nison / Morris / Bulkowski; body and wick sizes are judged
against the last 10 candles). Test: 61 patterns x bullish/bearish x 12 markets x holds 1/3/5/10 days = 5,856
systems, entry at the next open, excess over each market's normal drift, 5 bp a side (BTC 10 bp).
**Result: 0 pass.** With 1,988 systems that had enough events, the fair luck bar is t >= 4.56; nothing came close.
Consistency check [OURS]: 18 pattern/hold groups were "right" in >= 9 of 12 markets, but luck alone gives ~13, and
the markets move together, so that is noise. 27 groups were WRONG in >= 9 of 12 markets, vs ~17 by luck: famous
patterns are more often wrong than right. **Engulfing is wrong-way in BOTH our own coding and TA-Lib's** (bearish
engulfing right in only 1-3 of 12 markets): a replicated result. Three Outside (engulfing + confirmation) is the
worst of all (bearish: right in 0-2 of 12 markets).
"Markets right" = markets (of those with >= 5 events) where the pattern beat the normal drift in its direction.

| Pattern | What it looks like | Said to mean | Side | Events (post-2014, 12 mkts) | Markets right 1d / 5d | Median excess 5d | Verdict |
|---|---|---|---|---|---|---|---|
| Two Crows | up; long green, then a gap-up red, then a red that opens inside it and closes into the green body | top | bear | 10 | 2/2 / 2/2 | +128 bp | too rare to judge |
| Three Inside Up/Down | a harami followed by a candle that confirms the reversal | reversal | bull | 353 | 7/12 / 5/12 | -21 bp | **wrong way** |
| Three Inside Up/Down | a harami followed by a candle that confirms the reversal | reversal | bear | 301 | 3/12 / 5/12 | -24 bp | **wrong way** |
| Three-Line Strike | three candles one way, then one big candle that wipes them all out | Bulkowski's #1 (but rare) | bull | 6 | 0/1 / 0/1 | -136 bp | too rare to judge |
| Three-Line Strike | three candles one way, then one big candle that wipes them all out | Bulkowski's #1 (but rare) | bear | 10 | 0/1 / 1/1 | +86 bp | too rare to judge |
| Three Outside Up/Down | an engulfing candle followed by a confirming candle | reversal | bull | 564 | 5/12 / 5/12 | -10 bp | no edge |
| Three Outside Up/Down | an engulfing candle followed by a confirming candle | reversal | bear | 602 | 1/12 / 0/12 | -39 bp | **wrong way** |
| Advance Block | three green candles with shrinking bodies and growing upper wicks | uptrend tiring | bear | 130 | 6/9 / 4/9 | -16 bp | no edge |
| Belt Hold | a long candle opening at its extreme (no wick on the open side) | reversal | bull | 3235 | 7/12 / 8/12 | +7 bp | weak, mostly consistent (within luck) |
| Belt Hold | a long candle opening at its extreme (no wick on the open side) | reversal | bear | 3104 | 7/12 / 7/12 | +9 bp | no edge |
| Closing Marubozu | long body with no wick on the close side | strength in its direction | bull | 3195 | 7/12 / 2/12 | -6 bp | **wrong way** |
| Closing Marubozu | long body with no wick on the close side | strength in its direction | bear | 2288 | 5/12 / 4/12 | -26 bp | **wrong way** |
| Counterattack | two opposite candles closing at the same price | reversal | bull | 37 | 4/6 / 0/6 | -180 bp | no edge |
| Counterattack | two opposite candles closing at the same price | reversal | bear | 5 | 0/1 / 0/1 | -92 bp | too rare to judge |
| Dark Cloud Cover | green, then a red opening above its high and closing below its midpoint | top | bear | 164 | 3/11 / 6/11 | +7 bp | **wrong way** |
| Doji | open = close | indecision | bull | 5321 | 4/12 / 6/12 | +2 bp | no edge |
| Doji Star | a doji gapping away from a long candle | reversal warning | bull | 417 | 5/12 / 7/12 | +8 bp | no edge |
| Doji Star | a doji gapping away from a long candle | reversal warning | bear | 536 | 5/12 / 4/12 | -9 bp | **wrong way** |
| Dragonfly Doji | open = close at the high, long lower wick | bottom | bull | 595 | 6/12 / 5/12 | -5 bp | no edge |
| Engulfing | a body that swallows the previous opposite body | strong reversal | bull | 1213 | 3/12 / 3/12 | -6 bp | **wrong way** |
| Engulfing | a body that swallows the previous opposite body | strong reversal | bear | 1416 | 3/12 / 3/12 | -35 bp | **wrong way** |
| Evening Doji Star | evening star with a doji in the middle | top | bear | 72 | 4/9 / 6/9 | +32 bp | no edge |
| Evening Star | long green, small star, long red | top | bear | 238 | 8/12 / 9/12 | +47 bp | weak, mostly consistent (within luck) |
| Up/Down-gap Side-by-side White Lines | a gap then two similar green candles | continuation | bull | 80 | 3/9 / 1/9 | -53 bp | no edge |
| Gravestone Doji | open = close at the low, long upper wick | top | bull | 490 | 6/12 / 5/12 | -14 bp | **wrong way** |
| Hammer | down; small body at the top, long lower wick | bottom | bull | 875 | 7/12 / 5/12 | -7 bp | no edge |
| Hanging Man | up; small body at the top, long lower wick | top | bear | 960 | 8/12 / 8/12 | +19 bp | weak, mostly consistent (within luck) |
| Harami | a small body inside the previous long body | trend pausing / reversal | bull | 1511 | 5/12 / 7/12 | +15 bp | no edge |
| Harami | a small body inside the previous long body | trend pausing / reversal | bear | 1360 | 6/12 / 6/12 | -0 bp | no edge |
| Harami Cross | a doji inside the previous long body | reversal | bull | 461 | 8/12 / 6/12 | -10 bp | no edge |
| Harami Cross | a doji inside the previous long body | reversal | bear | 435 | 8/12 / 9/12 | +19 bp | weak, mostly consistent (within luck) |
| High-Wave | small body with very long wicks both sides | confusion | bull | 2517 | 5/12 / 8/12 | +9 bp | no edge |
| High-Wave | small body with very long wicks both sides | confusion | bear | 2351 | 7/12 / 9/12 | +8 bp | weak, mostly consistent (within luck) |
| Hikkake | an inside bar, then a false breakout of it | trap, trade the other way | bull | 1955 | 6/12 / 7/12 | +3 bp | no edge |
| Hikkake | an inside bar, then a false breakout of it | trap, trade the other way | bear | 2394 | 5/12 / 6/12 | -1 bp | no edge |
| Modified Hikkake | hikkake after a close near the inside bar's extreme | trap | bull | 5 | 0/1 / 1/1 | +23 bp | too rare to judge |
| Modified Hikkake | hikkake after a close near the inside bar's extreme | trap | bear | 8 | 0/1 / 0/1 | -136 bp | too rare to judge |
| Homing Pigeon | two red candles, the second inside the first | bottom | bull | 555 | 6/11 / 5/11 | -3 bp | no edge |
| Identical Three Crows | three crows each opening at the prior close | panic selling | bear | 7 | 1/1 / 1/1 | +709 bp | too rare to judge |
| In-Neck | down; red, then a green closing just inside its close | continuation down | bear | 38 | 4/5 / 4/5 | +37 bp | no edge |
| Inverted Hammer | down; small body at the bottom, long upper wick | bottom | bull | 553 | 9/12 / 8/12 | +25 bp | weak, mostly consistent (within luck) |
| Ladder Bottom | three reds, a red with an upper wick, then a gap-up green | bottom | bull | 52 | 4/7 / 6/7 | +34 bp | no edge |
| Long-Legged Doji | doji with long wicks both sides | indecision | bull | 5318 | 4/12 / 6/12 | +2 bp | no edge |
| Long Line | a long-bodied candle | strength in its direction | bull | 4318 | 6/12 / 7/12 | +1 bp | no edge |
| Long Line | a long-bodied candle | strength in its direction | bear | 3433 | 6/12 / 5/12 | -7 bp | **wrong way** |
| Marubozu | long body, no wicks | strength in its direction | bull | 1138 | 8/12 / 7/12 | +2 bp | no edge |
| Marubozu | long body, no wicks | strength in its direction | bear | 733 | 5/12 / 4/12 | -22 bp | **wrong way** |
| Matching Low | two reds closing at the same low | bottom | bull | 497 | 7/12 / 8/12 | +14 bp | no edge |
| Morning Doji Star | morning star with a doji in the middle | bottom | bull | 54 | 5/8 / 2/8 | -37 bp | no edge |
| Morning Star | long red, small star, long green | bottom | bull | 206 | 9/12 / 6/12 | +1 bp | weak, mostly consistent (within luck) |
| On-Neck | down; red, then a green closing at its low | continuation down | bear | 102 | 5/11 / 4/11 | -17 bp | no edge |
| Piercing | red, then a green opening below its low and closing above its midpoint | bottom | bull | 166 | 3/11 / 10/11 | +63 bp | **wrong way** |
| Rickshaw Man | long-legged doji with the body in the middle | indecision | bull | 4005 | 2/12 / 8/12 | +6 bp | **wrong way** |
| Separating Lines | opposite candles opening at the same price | continuation | bull | 87 | 7/10 / 8/10 | +59 bp | no edge |
| Separating Lines | opposite candles opening at the same price | continuation | bear | 98 | 3/12 / 5/12 | -26 bp | **wrong way** |
| Shooting Star | up; small body at the bottom, long upper wick | top | bear | 644 | 4/12 / 8/12 | +9 bp | weak, mostly consistent (within luck) |
| Short Line | a short-bodied candle | indecision | bull | 2928 | 5/12 / 4/12 | -6 bp | **wrong way** |
| Short Line | a short-bodied candle | indecision | bear | 2216 | 3/12 / 3/12 | -13 bp | **wrong way** |
| Spinning Top | small body, wicks both sides | indecision | bull | 4207 | 5/12 / 9/12 | +8 bp | weak, mostly consistent (within luck) |
| Spinning Top | small body, wicks both sides | indecision | bear | 3987 | 4/12 / 8/12 | +1 bp | no edge |
| Stalled Pattern | three greens, the last small (stalling) | uptrend tiring | bear | 71 | 4/8 / 4/8 | +7 bp | no edge |
| Stick Sandwich | red, green, red with the two reds closing equal | bottom | bull | 25 | 2/4 / 3/4 | +20 bp | too rare to judge |
| Takuri | dragonfly doji with a very long lower wick | bottom | bull | 578 | 6/12 / 6/12 | -0 bp | no edge |
| Tasuki Gap | a gap, then a candle that partly fills it | continuation | bull | 156 | 7/11 / 6/11 | +29 bp | no edge |
| Tasuki Gap | a gap, then a candle that partly fills it | continuation | bear | 104 | 4/11 / 8/11 | +20 bp | no edge |
| Thrusting | down; red, then a green closing just below its midpoint | continuation down | bear | 288 | 8/12 / 3/12 | -20 bp | **wrong way** |
| Tri-Star | three dojis, the middle one gapped | reversal | bear | 5 | 1/1 / 1/1 | +42 bp | too rare to judge |
| Unique Three River | a rare three-candle bottom | bottom | bull | 45 | 4/7 / 4/7 | +28 bp | no edge |
| Upside Gap Two Crows | up; gap-up red, then a bigger red | top | bear | 5 | 0/1 / 0/1 | -17 bp | too rare to judge |
| Upside/Downside Gap Three Methods | a gap, then a candle that closes it | continuation | bull | 102 | 5/10 / 7/10 | +20 bp | no edge |
| Upside/Downside Gap Three Methods | a gap, then a candle that closes it | continuation | bear | 109 | 2/8 / 5/8 | +12 bp | no edge |

How to read it: "no edge" = after the pattern, price did what it does on any random day; "wrong way" = price more
often went the OPPOSITE way; "too rare" = fewer than 30 events in 12 markets since 2014 (cannot be judged).

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

**IBS on Exness USTEC (2026-11-25, ../smallwins/ibs_ustec.py)** [OURS]: on NQ futures 2000-2026 with Exness-style
costs it passes (post-2014 +36 bp a trade, t 3.9). Over the last 2.4 years the US-session candle on the USTEC price
gives the same +36 bp as QQQ; the Exness UTC-midnight candle gives only +19 bp. Use the US-session candle.

## 7. Open questions (next tests)

- IBS with a wide-range-day filter and a volume filter (stronger in the literature); Monday-into-Tuesday effect.
- IBS on US500 (SPY failed its neighbour check) and on USTEC with the user's real Exness fills.
- Intraday candles (1h/5m) on USOIL around the EIA report (Wed 10:30 New York = 7:30 pm Abu Dhabi).
- Deflated Sharpe (Bailey & López de Prado) on every candle family.
- Reverse-sign (momentum) versions on USO, BNO, GLD and BTC, counted as extra trials.

## 8. Change log
- 2026-11-25: all 61 TA-Lib patterns tested (5,856 systems, 0 pass); section 4c.
- 2026-11-25: John Wick candle researched and tested on BTC (276 systems, 0 pass); section 4b.
- 2026-11-25: IBS tested on Exness USTEC-style candles (passes on the futures price; use the US-session candle).
- 2026-11-25: created from the two research files, candle_study.py (1,248 systems) and the harami neighbour check.
