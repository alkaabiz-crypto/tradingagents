# CryptoTrendDemo — MT5 Expert Advisor (DEMO ONLY)

Places the lab's crypto trend day trade automatically on an Exness **demo** account: BTCUSD + ETHUSD, direction from
yesterday's close vs the 50-day average, stop 0.5 ATR, vol-sized, closed at midnight server time (GMT+0 = 4:00 am
Abu Dhabi). Same frozen rule as `oil-brain/live/crypto_trend_ticket.py`. It refuses to start on a real account.

## Important
- **MT5 on iPhone cannot run Expert Advisors.** You need MT5 on a Windows PC or Mac (or a Windows VPS) that stays on.
- Not compiled or tested here (no MetaEditor in the lab); compile it in MetaEditor and watch the first day on demo.
- Research, not financial advice. Never switch it to real money without a long, good demo record.

## Install (desktop MT5)
1. In MT5: File -> Open Data Folder -> MQL5 -> Experts. Copy `CryptoTrendDemo.mq5` there.
2. Open MetaEditor (F4), open the file, press Compile (F7). It must say 0 errors.
3. In MT5: Navigator -> Expert Advisors -> drag CryptoTrendDemo onto any chart (e.g. BTCUSD, any timeframe).
4. Inputs: `InpSymbols` = your exact symbol names (Exness sometimes adds a suffix, e.g. `BTCUSDm`), `InpTotalBalance` = 3400.
5. Turn on the **Algo Trading** button (green). Tick "Allow Algo Trading" in the EA's Common tab.
6. Keep the computer on and MT5 open. The Experts tab shows each trade it places and any skip or error.

## What it does every day
- Just after 00:00 server time: closes yesterday's trades, then opens today's (one per symbol), with the stop in the order.
- If the rule's size is below the 0.01 minimum lot, it **skips** that symbol that day (it never sizes up).
- Kill switch: if its closed P&L falls more than 15% of $3,400 below its peak, it stops trading and shows an alert.
