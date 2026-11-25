# MISTAKES.md — the lab's mistake log (read this before every new study)

The user asked (2026-11-25) for the lab to keep knowing what its mistakes are and to fix them. Every entry:
what went wrong, how it was found, the fix, and the rule that now prevents it. Add new entries at the bottom.

## A. Testing mistakes (they make luck look like skill)

| # | Mistake | How it showed up | Fix / standing rule |
|---|---|---|---|
| A1 | **Trusting a high win rate** | Oil "buy the dip, small target" won 71% of trades but lost 18 bp a trade (smallwins, 2026-11-25) | Judge the AVERAGE trade after costs, the worst trade and the t-stat; win rate is reported, never used as a pass |
| A2 | **Best-of-many = lucky** | 1 of 147 DCA timing rules passed the placebo; its neighbours failed (24% beat plain DCA) | Count every system tried; placebo p <= 0.01; neighbour check (>= 70% of nearby settings) before any paper sleeve |
| A3 | **Testing on the same data you tuned on** | — (prevented) | Pre-register the rules, the grids and the pass bar in the docstring and COMMIT IT before running |
| A4 | **One market can be a fluke** | QQQ IBS passed; SPY 13%, IWM 0%, DIA 0% of neighbours | Always test unseen sister markets; a rule that works on one market only is labelled "market-specific, may fade" |
| A5 | **Wrong benchmark** | Beating 0 is easy for long-only rules in a rising market | Compare with plain buy-and-hold / plain DCA AND random-entry placebos with the same exit |
| A6 | **Fill-price fantasy** | QQQ IBS: entry at the close +31 bp; at the next open only +16 bp | Test the realistic fill; if the edge needs the close, the live version must be placed before the close |
| A7 | **Daily bars hide the order of high and low** | Stop and target hit on the same day | If a bar touches both, count the STOP; gaps through a stop fill at the open (worse) |
| A8 | **Regime dependence** | Oil DCA lost 2006-2019, doubled 2020-2026; oil brain worked 2014-19, failed since 2020 | Always split IS / OOS (2014-19) / HOLDOUT (2020+) and require both later periods |

## B. AI (TradingAgents) mistakes

| # | Mistake | How it showed up | Fix / standing rule |
|---|---|---|---|
| B1 | **The AI says "Buy" too often** | 6 of 7 day tickets on 2026-11-24 were Buy | The day-ticket score compares the AI with ALWAYS-LONG and a COIN-FLIP direction on the same days |
| B2 | **The AI contradicts itself** | XOM "Sell" plan talked of a short squeeze and put the stop on the wrong side | Only the AI's direction is used; stops/targets come from a fixed ATR rule |
| B3 | **Horizon mismatch** | AI gave 6-12 month plans when the user wanted daily trades | Day tickets pass a next-session mandate through the portfolio context |
| B4 | **Free-model limits** | Gemini daily quota gone after 1-2 runs; Groq 8k tokens/min too small; Mistral Small/Medium 0 requests | Mistral Codestral (deep) + Ministral 14B (quick), throttled per model, Gemini fallback |
| B5 | **Agents run blind when data fails** | Yahoo 429 -> fundamentals analyst had no data | Say so in the report; prefer free SEC EDGAR fundamentals; add Alpha Vantage if the user gets a key |

## C. Engineering mistakes

| # | Mistake | How it showed up | Fix / standing rule |
|---|---|---|---|
| C1 | **A failed download overwrote good data** | EIA_weekly.csv became empty (xlrd missing) -> oil brain crashed | fetch_eia.py refuses to write a partial download; pip install xlrd in every run |
| C2 | **A failed AI run blocked its retry** | GLD ticket logged as "error" and then skipped | day_ticket.py replaces failed rows and retries |
| C3 | **Two jobs sharing one rate limit** | Ticket batch and the evening verdict both on Codestral -> 429 | Run Codestral jobs one after another; per-model throttle |
| C4 | **Non-reproducible placebo seeds** | smallwins.py seeds the placebo with Python's hash(), which changes per process | New studies use fixed integer seeds (to fix in smallwins.py's next version) |

## D. Market-knowledge mistakes to avoid

- Oil ETFs (USO, BNO) and long USOIL CFDs lose to the spot price through contango roll / swaps; spot WTI is not investable.
- Oil can gap 20-50% in a day (2020): small-target systems on oil carry hidden crash risk.
- "Buy the dip" in oil has failed in every test here (DCA, smallwins, swarm); in tech indexes it worked 2014-2026.

## E. Added 2026-11-25
| # | Mistake | How it showed up | Fix / standing rule |
|---|---|---|---|
| E1 | **Wrong system count in a pre-registration** | btc_wicks2.py said 48 systems, it ran 96 (forgot the 2 sides) | Count = rules x sides x exits x timeframes x markets; the script prints the real count and the luck bar uses the real cumulative count (276 for BTC wicks) |
| E2 | **Trusting crypto-Twitter backtests** | "20 of 22 weekly BTC SFPs worked" had no costs, no stops, no out-of-sample | Treat social-media pattern claims as LORE until our own pre-registered test |
| E3 | **Fading strength in a momentum market** | Shorting BTC's big upper wicks lost in almost every version | Check whether the market trends (BTC, oil) or mean-reverts (US indexes) before using a reversal candle |
