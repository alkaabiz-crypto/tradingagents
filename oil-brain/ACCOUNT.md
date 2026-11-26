# ACCOUNT.md — the user's trading account (read before EVERY study and every ticket)

Set 2026-11-26 by the user: "put in mind the costs for each trade and the swap free so u know for the future".

- Broker: **Exness**, MT5, server time GMT+0 (daily candle = UTC day; for US indexes the US-session candle differs).
- Account type: **Standard**: **no commission**, the only trade cost is the **spread** (paid once, at entry, as the
  buy-sell gap). Market stops can fill worse than the stop price (slippage) in fast moves.
- **Swap-free**: no overnight swap, so holding overnight or for several days costs no financing.
  (Check in the Exness app that each symbol traded is covered; brokers can exclude some symbols or change the terms.)
- Money: demo / paper only in this lab. Never place real orders.

## Cost rule for all studies (use oil-brain/costs.py)
- Round-trip cost = the symbol's spread as a % of price (+ slippage on stop exits), NO commission, NO swap.
- Until the user gives real spreads from the app, use the estimates in costs.py and ALSO report results at
  0 / 2 / 5 / 10 bp round trip, so the real account can be read off (MISTAKES.md E8).
- US ETFs / stocks tested on Yahoo data map to Exness CFDs (QQQ -> USTEC, SPY -> US500, XLE/USO -> USOIL, GLD -> XAUUSD,
  BTC-USD -> BTCUSD); stock CFD spreads are wider than index spreads.
- Swap-free means multi-day holds (e.g. QQQ IBS, up to 5 days) carry no extra cost, an advantage over normal accounts.
- Crypto trend demo ticket: the user set **$700 total** ($350 per coin, BTCUSD + ETHUSD) on 2026-11-26.
- Exness minimum volume: **0.01 lot** (user, 2026-11-26). Contract size assumed 1 coin per lot for BTCUSD / ETHUSD until checked.
