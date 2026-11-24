"""Bitcoin breakout ticket for an Exness demo account (MT5 symbol BTCUSD; 1 lot = 1 BTC).

    python3 oil-brain/combo/btc_ticket.py [--balance 2000] [--risk 0.01]
    python3 oil-brain/combo/btc_ticket.py record <BUY|SELL> <lots> <fill> <stop> <tp> [note]   # log your demo fill
    python3 oil-brain/combo/btc_ticket.py close <fill> [note]                                    # log your demo exit

The rule (combo lab survivor, BTC R2 D1 T2; unchanged): at the 00:00 UTC daily close,
  trend = BTC above its 200-day average -> longs only; below -> shorts only.
  LONG  if the close is above the highest high of the previous 20 days (and trend up).
  SHORT if the close is below the lowest low of the previous 20 days (and trend down).
  Enter at once (the next day's open). Stop = 2 x ATR(20) from entry. Take profit = 4 x that distance (4R).
  Close at market after 30 days if neither is hit. Risk 1% of the balance per trade.
Backtest 2019-2026: 74 trades, 47% winners, average +0.79R, t 3.28; still t 2.5 with 30%/yr swaps.
Demo account only. Not financial advice.
"""
import os, sys, csv, datetime as dt
import numpy as np, pandas as pd, yfinance as yf
HERE = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(HERE, "btc_demo_log.csv")


def arg(name, default):
    return float(sys.argv[sys.argv.index(name) + 1]) if name in sys.argv else default


def ticket():
    bal, risk = arg("--balance", 2000.0), arg("--risk", 0.005)  # 0.5%: btc_research/BTC_REPORT.md
    b = yf.Ticker("BTC-USD").history(period="1y")[["Open", "High", "Low", "Close"]]
    b.index = b.index.tz_localize(None).normalize()
    today = pd.Timestamp.now(tz="UTC").tz_localize(None).normalize()
    done = b[b.index < today]                       # finished daily candles only
    c = done.Close
    tr = pd.concat([done.High - done.Low, (done.High - c.shift()).abs(), (done.Low - c.shift()).abs()], axis=1).max(axis=1)
    atr = tr.rolling(20).mean().iloc[-1]
    sma200 = c.rolling(200).mean().iloc[-1]
    hi20 = done.High.iloc[-21:-1].max(); lo20 = done.Low.iloc[-21:-1].min()
    last = c.iloc[-1]; day = done.index[-1].date()
    trend = "UP (longs only)" if last > sma200 else "DOWN (shorts only)"
    side = 1 if (last > hi20 and last > sma200) else -1 if (last < lo20 and last < sma200) else 0
    print(f"BTC breakout check, candle closed {day} 24:00 UTC: close ${last:,.0f}, 200-day avg ${sma200:,.0f} -> trend {trend}")
    print(f"20-day range before it: high ${hi20:,.0f}, low ${lo20:,.0f}.  ATR(20) ${atr:,.0f}")
    live = b[b.index >= today]
    px = float(live.Open.iloc[0]) if len(live) else last
    if side == 0:
        nxt = (f"a daily close above ${max(hi20, done.High.iloc[-20:].max()):,.0f} with the trend up" if last > sma200
               else f"a daily close below ${min(lo20, done.Low.iloc[-20:].min()):,.0f} (trend down -> SHORT)")
        print(f"NO TRADE. Next signal needs {nxt}.")
        return
    stop_d = 2 * atr; lots = round(bal * risk / stop_d, 3)
    stop = px - side * stop_d; tp = px + side * 4 * stop_d
    print(f"SIGNAL: {'BUY' if side > 0 else 'SELL'} BTCUSD at market now (open ~${px:,.0f})")
    if side < 0:
        lots = round(lots / 2, 3)
        print("  NOTE: research found no edge in shorts (+0.06R on 13 coins). Optional: take it at HALF size (shown) or skip.")
    print(f"  Volume {lots} lots (risk {risk:.0%} of ${bal:,.0f} = ${bal*risk:,.0f}; stop distance ${stop_d:,.0f})")
    print(f"  Stop loss ${stop:,.0f}   Take profit ${tp:,.0f} (4R)   Close by {(today + pd.Timedelta(days=30)).date()} if neither hits")
    print("  MT5: New Order > BTCUSD > Market Execution > enter Volume, Stop Loss, Take Profit > Sell/Buy.")
    print("  Then log it: python3 oil-brain/combo/btc_ticket.py record <BUY|SELL> <lots> <fill> <stop> <tp>")


def record():
    a = sys.argv[2:]
    new = not os.path.exists(LOG)
    with open(LOG, "a", newline="") as f:
        w = csv.writer(f)
        if new: w.writerow(["time_utc", "event", "side", "lots", "price", "stop", "tp", "note"])
        if sys.argv[1] == "record":
            w.writerow([dt.datetime.utcnow().isoformat(timespec="minutes"), "open", a[0], a[1], a[2], a[3], a[4], " ".join(a[5:])])
        else:
            w.writerow([dt.datetime.utcnow().isoformat(timespec="minutes"), "close", "", "", a[0], "", "", " ".join(a[1:])])
    print("Logged to", LOG)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ("record", "close"):
        record()
    else:
        ticket()
