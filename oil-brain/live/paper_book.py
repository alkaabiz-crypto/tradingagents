"""Live paper book: every surviving strategy trading paper money from 2026-11-24.

Run after each US close (and any time to see the current marks):
    python3 oil-brain/live/paper_book.py
It downloads fresh Yahoo closes, marks open positions, applies each strategy's rule at the
latest close, books trades with costs, and writes:
    live/state.json   cash, positions, equity per sleeve, full trade log, today's orders
    live/equity.csv   daily equity per sleeve and total
Rules are the audited ones (oil-brain/audit/AUDIT.md) and do not change. Paper money only.

Sleeves (start $10,000 total):
  IEF_MONTH_END  $3,000  long IEF over the last 3 NYSE trading days of each month, else cash. 2 bp/side.
  BTC_TREND      $2,500  long BTC-USD when its 28-day return > 0, else cash. 10 bp/side.
  ETH_TREND      $1,500  long ETH-USD when its 28-day return > 0, else cash. 10 bp/side.
  USO_FOLLOW     $3,000  after a USO day beyond +/-2.5 x its 20-day sd, same direction for 5 days. 5 bp/side.
"""
import json, os, datetime as dt
import numpy as np, pandas as pd, yfinance as yf

HERE = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(HERE, "state.json")
START = "2026-11-24"
SLEEVES = {"IEF_MONTH_END": ("IEF", 3000, 2), "BTC_TREND": ("BTC-USD", 2500, 10),
           "ETH_TREND": ("ETH-USD", 1500, 10), "USO_FOLLOW": ("USO", 3000, 5)}
NYSE_HOLIDAYS = pd.to_datetime([
    "2026-01-01", "2026-01-19", "2026-02-16", "2026-04-03", "2026-05-25", "2026-06-19", "2026-07-03",
    "2026-09-07", "2026-11-26", "2026-12-25", "2027-01-01", "2027-01-18", "2027-02-15", "2027-03-26",
    "2027-05-31", "2027-06-18", "2027-07-05", "2027-09-06", "2027-11-25", "2027-12-24"])
BDAY = pd.offsets.CustomBusinessDay(holidays=NYSE_HOLIDAYS)


def closes(sym):
    s = yf.Ticker(sym).history(period="1y", auto_adjust=True)["Close"]
    s.index = s.index.tz_localize(None).normalize()
    return s[~s.index.duplicated()].dropna()


def target(name, px):
    """Target exposure (-1..1) at the latest close, and a one-line reason."""
    last = px.index[-1]
    if name == "IEF_MONTH_END":
        left = len(pd.date_range(last, last + pd.offsets.MonthEnd(0), freq=BDAY)) - 1
        on = 0 < left <= 3
        return (1.0 if on else 0.0), f"{left} NYSE trading days left in the month after {last.date()}"
    if name in ("BTC_TREND", "ETH_TREND"):
        r28 = px.iloc[-1] / px.iloc[-29] - 1
        return (1.0 if r28 > 0 else 0.0), f"28-day return {r28:+.1%}"
    if name == "USO_FOLLOW":
        r = px.pct_change(); z = r / r.rolling(20).std().shift(1)
        hits = z[z.abs() > 2.5]
        hits = hits[hits.index >= px.index[-5]]  # signals in the last 5 sessions still hold
        if len(hits):
            return float(np.sign(hits.iloc[-1])), f"big day {hits.index[-1].date()} (z {hits.iloc[-1]:+.2f}), hold 5 days"
        return 0.0, f"no big day in the last 5 sessions (today z {z.iloc[-1]:+.2f})"


def main():
    st = json.load(open(STATE)) if os.path.exists(STATE) else {
        "start": START, "sleeves": {k: {"cash": v[1], "qty": 0.0, "symbol": v[0]} for k, v in SLEEVES.items()},
        "trades": [], "history": []}
    marks, orders = {}, []
    for name, (sym, alloc, cost_bp) in SLEEVES.items():
        px = closes(sym)
        s = st["sleeves"][name]
        price, day = float(px.iloc[-1]), px.index[-1].date().isoformat()
        tgt, why = target(name, px)
        equity = s["cash"] + s["qty"] * price
        want_qty = tgt * equity / price
        if abs(want_qty - s["qty"]) * price > 1:  # trade only real changes
            trade_qty = want_qty - s["qty"]
            fee = abs(trade_qty) * price * cost_bp / 1e4
            s["cash"] -= trade_qty * price + fee
            s["qty"] = want_qty
            st["trades"].append(dict(date=day, sleeve=name, symbol=sym, side="BUY" if trade_qty > 0 else "SELL",
                                     qty=round(trade_qty, 6), price=round(price, 4), fee=round(fee, 2), reason=why))
        equity = s["cash"] + s["qty"] * price
        s.update(last_price=price, last_date=day, equity=round(equity, 2), target=tgt, reason=why)
        marks[name] = round(equity, 2)
        side = "LONG" if tgt > 0 else "SHORT" if tgt < 0 else "FLAT (cash)"
        orders.append(f"{name}: {side} {sym}" + (f" ~${abs(tgt) * equity:,.0f}" if tgt else "") + f"  [{why}]")
    total = round(sum(marks.values()), 2)
    today = dt.date.today().isoformat()
    st["history"] = [h for h in st["history"] if h["date"] != today] + [dict(date=today, total=total, **marks)]
    st.update(updated=dt.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"), total=total, orders=orders,
              pnl=round(total - sum(v[1] for v in SLEEVES.values()), 2))
    json.dump(st, open(STATE, "w"), indent=1)
    pd.DataFrame(st["history"]).to_csv(os.path.join(HERE, "equity.csv"), index=False)
    print(f"Paper book {st['updated']}: total ${total:,.2f} (P&L ${st['pnl']:+,.2f} since {st['start']})")
    for o in orders:
        print("  " + o)


if __name__ == "__main__":
    main()
