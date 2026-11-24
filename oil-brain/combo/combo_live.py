"""Live paper trader for the combo-lab systems (registered 2026-11-24, before any forward data).
Run after each US close:  python3 oil-brain/combo/combo_live.py
For each system it: fills yesterday's pending entry at today's open, manages open trades bar by bar
(stop, target, trailing stop, max hold) with today's high/low/close, then checks today's close for a new
signal and writes the ticket for tomorrow's open. Sizing as trader-budget: risk 1% of the sleeve per trade.
Trader-risk checks: one trade per system, stop on the right side, risk >= 0.05% of price, size <= sleeve.
Paper money only; it never sends orders.

Systems (from combo_daily.py; the only survivors, plus the best oil system as a forward-only candidate):
  BTC_BREAKOUT  BTC-USD: 20-day breakout in the 200-day trend's direction; stop 2 x ATR20, target 4R, max 30 days. $2,000.
  GLD_PULLBACK  GLD: above its 200-day average and RSI(2) < 10 -> long; stop 2 x ATR20, trailing 3 x ATR20. $2,000.
  USO_TURTLE    USO: 55-day breakout in the 200-day trend's direction; stop 2 x ATR20, trailing 3 x ATR20. $2,000
                (did NOT pass: t 1.5; forward test only).
"""
import os, json, datetime as dt
import numpy as np, pandas as pd, yfinance as yf
HERE = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(HERE, "combo_state.json")
SYS = {
    "BTC_BREAKOUT": dict(sym="BTC-USD", start=2000, entry="d1", regime="r2", stop=2, trail=None, target=4, maxh=30, cost=10),
    "GLD_PULLBACK": dict(sym="GLD", start=2000, entry="rsi2", regime="r2l", stop=2, trail=3, target=None, maxh=10**6, cost=5),
    "USO_TURTLE": dict(sym="USO", start=2000, entry="d2", regime="r2", stop=2, trail=3, target=None, maxh=10**6, cost=5),
    # Registered 2026-11-24 after the deep research (btc_research/BTC_REPORT.md): long-only, 0.5% risk.
    "BTC_BREAKOUT_LONG": dict(sym="BTC-USD", start=2000, entry="d1", regime="r2", stop=2, trail=None, target=4, maxh=30,
                              cost=10, long_only=True, risk=0.005),
}


def bars(sym):
    b = yf.Ticker(sym).history(period="2y", auto_adjust=True)[["Open", "High", "Low", "Close"]]
    b.index = b.index.tz_localize(None).normalize()
    b = b[~b.index.duplicated()].dropna()
    # Only finished days: crypto's daily bar closes at 00:00 UTC; US ETFs at 16:00 New York.
    if sym.endswith("-USD"):
        today = pd.Timestamp.now(tz="UTC").tz_localize(None).normalize()
    else:
        ny = pd.Timestamp.now(tz="America/New_York")
        today = ny.tz_localize(None).normalize() + (pd.Timedelta(days=1) if ny.hour * 60 + ny.minute >= 16 * 60 + 10 else pd.Timedelta(0))
    return b[b.index < today]


def signal(b, s):
    c = b.Close
    tr = pd.concat([b.High - b.Low, (b.High - c.shift()).abs(), (b.Low - c.shift()).abs()], axis=1).max(axis=1)
    atr = tr.rolling(20).mean()
    trend = np.sign(c - c.rolling(200).mean())
    if s["entry"] == "d1":
        raw = np.where(c > b.High.rolling(20).max().shift(1), 1, np.where(c < b.Low.rolling(20).min().shift(1), -1, 0))
    elif s["entry"] == "d2":
        raw = np.where(c > b.High.rolling(55).max().shift(1), 1, np.where(c < b.Low.rolling(55).min().shift(1), -1, 0))
    else:
        d = c.diff(); up = d.clip(lower=0).ewm(alpha=.5).mean(); dn = (-d.clip(upper=0)).ewm(alpha=.5).mean()
        r2 = 100 - 100 / (1 + up / dn); raw = np.where(r2 < 10, 1, 0)
    raw = pd.Series(raw, index=b.index)
    ok = (raw == trend) if s["regime"] == "r2" else ((raw > 0) & (trend > 0))
    sig = raw.where(ok, 0)
    if s.get("long_only"): sig = sig.clip(lower=0)
    return sig, atr


def main():
    st = json.load(open(STATE)) if os.path.exists(STATE) else {
        k: dict(cash=v["start"], open=None, pending=None, trades=[]) for k, v in SYS.items()}
    for k, v in SYS.items():  # sleeves registered later start flat with their own cash
        st.setdefault(k, dict(cash=v["start"], open=None, pending=None, trades=[], last_day=str(pd.Timestamp.now().normalize().date() - pd.Timedelta(days=1))))
    tickets = []
    for name, s in SYS.items():
        b = bars(s["sym"]); sig, atr = signal(b, s); S = st[name]; day = b.index[-1]
        last_seen = pd.Timestamp(S.get("last_day", "1900-01-01"))
        for d in b.index[b.index > last_seen]:
            bar = b.loc[d]
            if S["pending"] and S["open"] is None:  # fill at this day's open
                p = S["pending"]; e = float(bar.Open); risk = p["risk_per_unit"]
                if risk >= 0.0005 * e:
                    qty = min(s.get("risk", 0.01) * S["cash"] / risk, S["cash"] / e)
                    S["open"] = dict(side=p["side"], entry=e, qty=qty, stop=e - p["side"] * risk, risk=risk,
                                     target=(e + p["side"] * s["target"] * risk) if s["target"] else None,
                                     opened=str(d.date()), days=0)
                S["pending"] = None
            o = S["open"]
            if o:
                o["days"] += 1; side = o["side"]; px = None
                if side > 0 and bar.Low <= o["stop"]: px, why = min(o["stop"], bar.Open), "stop"
                elif side < 0 and bar.High >= o["stop"]: px, why = max(o["stop"], bar.Open), "stop"
                elif o["target"] and ((side > 0 and bar.High >= o["target"]) or (side < 0 and bar.Low <= o["target"])):
                    px, why = o["target"], "target"
                elif o["days"] >= s["maxh"]: px, why = float(bar.Close), "time"
                if px is not None:
                    pnl = side * (px - o["entry"]) * o["qty"] - 2 * s["cost"] / 1e4 * o["entry"] * o["qty"]
                    S["cash"] += pnl
                    S["trades"].append(dict(opened=o["opened"], closed=str(d.date()), side=side, entry=round(o["entry"], 4),
                                            exit=round(px, 4), why=why, pnl=round(pnl, 2),
                                            R=round(pnl / (o["risk"] * o["qty"]), 2)))
                    S["open"] = None
                elif s["trail"] and not np.isnan(atr.loc[d]):
                    o["stop"] = max(o["stop"], bar.Close - s["trail"] * atr.loc[d]) if side > 0 else min(o["stop"], bar.Close + s["trail"] * atr.loc[d])
            if S["open"] is None and S["pending"] is None and d == day and sig.loc[d] != 0 and not np.isnan(atr.loc[d]):
                S["pending"] = dict(side=int(sig.loc[d]), risk_per_unit=float(s["stop"] * atr.loc[d]), signal_day=str(d.date()))
        S["last_day"] = str(day.date())
        last = float(b.Close.iloc[-1]); o = S["open"]
        eq = S["cash"] + (o["side"] * (last - o["entry"]) * o["qty"] if o else 0)
        S["equity"] = round(eq, 2)
        if S["pending"]:
            p = S["pending"]; side = "BUY" if p["side"] > 0 else "SELL SHORT"
            tickets.append(f"{name}: {side} {s['sym']} at the next open; stop {p['risk_per_unit']:.2f} away "
                           f"(~{p['risk_per_unit']/last:.1%}); risk {s.get("risk",0.01):.1%} of ${S['cash']:,.0f} = ${s.get("risk",0.01)*S['cash']:.0f}"
                           + (f"; target {s['target']}R" if s["target"] else "; trailing stop 3 x ATR"))
        elif o:
            tickets.append(f"{name}: HOLD {'long' if o['side']>0 else 'short'} {s['sym']} from {o['entry']:.2f}, stop now {o['stop']:.2f}"
                           + (f", target {o['target']:.2f}" if o['target'] else ""))
        else:
            tickets.append(f"{name}: no position, no signal ({s['sym']} {last:.2f})")
    json.dump(st, open(STATE, "w"), indent=1, default=float)
    tot = sum(st[k]["equity"] for k in SYS)
    print(f"Combo paper trader {dt.date.today()}: ${tot:,.2f} (start ${sum(v['start'] for v in SYS.values()):,})")
    for t in tickets: print("  " + t)


if __name__ == "__main__":
    main()
