# Plan A Expert Advisor (MT5): setup

`PlanA_EA.mq5` trades the four Plan A legs with the same rules as the lab backtest and the paper ledger.

| Leg | Rule | Default lot |
|---|---|---|
| BTC NR4 | Buy-stop and sell-stop at yesterday's high/low, placed at 00:00 server. The other level is the stop. Closed at the next 00:00. | 0.02 |
| BTC Williams | Today's open ± half of yesterday's range. Same stop and exit. | 0.02 |
| ETH above 50-day | Long while the daily close is above the 50-day average. | 0.2 |
| US500 10-day low | At 15:55 New York, buy when the price is at its 10-day low. Sell at 15:55 three days after the last signal. | 0.28 |

Every leg has its own magic number (51001-51004). There is no martingale, grid or averaging. A kill switch closes everything when the EA's profit since `InpStartDate` reaches minus `InpMaxLossUSD` (default 680). A log is written to `MQL5/Files/PlanA_log.csv`. The EA never needs your login: you log in inside MT5 yourself.

## Logic check
`ea_mirror_check.py` runs the EA's day-by-day logic in Python over 2024-01-01 to 2026-11-27 and compares it with the lab backtest:

| Leg | Days compared | Result |
|---|---|---|
| BTC NR4 | 245 trade days | Same side and P&L on every day |
| BTC Williams | 759 trade days | Same side and P&L on every day |
| ETH | 1,062 days | Same position on every day |
| US500 | 730 days | Same position on every day |

The .mq5 file itself has not been compiled here, because MetaEditor runs only on Windows. Compile it (step 6 below) and run the Strategy Tester (step 11) before using it live.

## Steps (Windows PC, Exness DEMO first)
1. In the Exness Personal Area, open a **demo** MT5 account of the same type as your real one: Standard, swap-free, 1:200. Set the balance to $5,450 (20,000 AED).
2. Download MT5 from the Exness Personal Area.
3. Install MT5 to D:, not C:. In the installer, click Settings and set the folder to `D:\data claude btc\MT5`.
4. Make MT5 keep its data on D: as well:
   - Right-click the MT5 shortcut and choose Properties.
   - At the end of Target, add a space and `/portable`.
   - Always start MT5 with this shortcut.
5. Log in to the demo account: File > Login to Trade Account. Type the login there only; never paste it anywhere else.
6. Add and compile the EA:
   - Copy `PlanA_EA.mq5` into `D:\data claude btc\MT5\MQL5\Experts\`.
   - Press F4 to open MetaEditor, open the file, and press F7. It should report 0 errors.
7. In Market Watch (Ctrl+M), check that BTCUSD, ETHUSD and US500 are shown. If your names have a suffix (for example BTCUSDm), the EA finds it by itself.
8. Turn on algo trading: Tools > Options > Expert Advisors, tick "Allow algorithmic trading", and make sure the Algo Trading button on the toolbar is green.
9. Load enough US500 history:
   - Tools > Options > Charts, set "Max bars in chart" to Unlimited.
   - Open a US500 M1 chart and scroll back about a month.
10. Attach the EA:
    - Open a BTCUSD H1 chart and drag PlanA_EA onto it from the Navigator.
    - In Inputs, set InpStartDate to today and check the lots and InpMaxLossUSD.
    - On the Common tab, tick "Allow Algo Trading".
11. Run the Strategy Tester (Ctrl+R):
    - Expert PlanA_EA, symbol BTCUSD, "Every tick based on real ticks", from 2024.01.01, deposit 5450.
    - The trades should match the lab backtest.
12. Run on demo for 2-4 weeks. Compare the Experts tab and PlanA_log.csv with the paper ledger.

The EA must be running at 00:00 server time (04:00 UAE) and at 15:55 New York (00:55 UAE in winter, 23:55 UAE in summer).

## Keeping it running (VPS)
- **Easiest:** use MetaQuotes' built-in hosting, about $10-15 a month. Right-click the account in the Navigator, choose "Register a Virtual Server", then migrate. The EA and its settings are copied to the server.
- **Exness:** it also offers a VPS in the Personal Area for accounts that meet its deposit or volume conditions. Check the current terms there.
- **Generic:** any small Windows VPS (1 vCPU, 2 GB RAM) works. Repeat steps 2-10 on it.

Not financial advice. These are backtests, and losses are possible. Go live only after the demo matches the paper ledger.
