"""Live paper sleeve: QQQ IBS dip (registered 2026-11-25 after smallwins.py + neighbours.py; before any forward day).

Rule (fixed, from the study): at the close, if QQQ's internal bar strength IBS = (close - low) / (high - low) is
below 0.2 and QQQ has 200 days of history, BUY at that close. SELL at the first close where IBS > 0.5, or at the
5th close. One position at a time. Cost 5 bp a side. Paper sleeve $2,000, fully invested per trade (no leverage).
Backtest 2014-2026: 436 trades (~34 a year), win rate 65%, +31 bp a trade net (t 3.4), placebo p 0.000;
neighbours: 73% of 15 settings pass at 2x cost. Entry at the NEXT OPEN halves the edge (+16 bp, t 2.1), so the
real-life version must be placed in the last minutes before the US close (00:45-00:55 Abu Dhabi time in winter).
Also scores SPY as a second, weaker sleeve for comparison (SPY did NOT hold its neighbour check).

    python3 oil-brain/smallwins/ibs_live.py            # after the US close: settle today, then today's signal
    python3 oil-brain/smallwins/ibs_live.py --preclose # ~15 minutes before the close: what the signal will likely be

Paper money only; it never sends orders. Research, not financial advice.
"""
import os, sys, json
import pandas as pd, yfinance as yf

HERE = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(HERE, "ibs_state.json")
SLEEVES = {"QQQ_IBS": dict(sym="QQQ", start=2000.0), "SPY_IBS_COMPARE": dict(sym="SPY", start=2000.0),
           # Forward-only comparison sleeves, registered 2026-11-25 after ibs_improve.py (same QQQ signals):
           #  VOLSIZED: invest min(1, 1% / (ATR14/close)) of the sleeve; cut drawdowns in 2000-13 AND 2014-26.
           #  UPCLOSE: exit at the first up close (or 5 days); better after 2014 but worse before -> hypothesis only.
           "QQQ_IBS_VOLSIZED": dict(sym="QQQ", start=2000.0, size="vol"),
           "QQQ_IBS_UPCLOSE": dict(sym="QQQ", start=2000.0, exit="upclose")}
COST = 5e-4


def bars(sym, final=True):
    b = yf.Ticker(sym).history(period="1y", auto_adjust=True)[["Open", "High", "Low", "Close"]]
    b.index = b.index.tz_localize(None).normalize(); b = b[~b.index.duplicated()].dropna()
    if final:
        ny = pd.Timestamp.now(tz="America/New_York")
        today = ny.tz_localize(None).normalize() + (pd.Timedelta(days=1) if ny.hour * 60 + ny.minute >= 16 * 60 + 10 else pd.Timedelta(0))
        b = b[b.index < today]
    return b


def ibs(row):
    rng = row.High - row.Low
    return 0.5 if rng <= 0 else float((row.Close - row.Low) / rng)


def main():
    if "--preclose" in sys.argv:
        for name, s in SLEEVES.items():
            b = bars(s["sym"], final=False); r = b.iloc[-1]; v = ibs(r)
            st = json.load(open(STATE)) if os.path.exists(STATE) else {}
            held = st.get(name, {}).get("open")
            if held:
                act = "SELL at the close (IBS > 0.5)" if v > 0.5 else (
                    "SELL at the close (5th day)" if held["days"] >= 4 else "keep holding")
            else:
                act = "BUY at the close (IBS < 0.2)" if v < 0.2 else "no trade"
            print(f"{name}: {s['sym']} now {r.Close:.2f} (day low {r.Low:.2f}, high {r.High:.2f}) IBS {v:.2f} -> likely {act}")
        return
    st = json.load(open(STATE)) if os.path.exists(STATE) else {}
    for name, s in SLEEVES.items():
        S = st.setdefault(name, dict(cash=s["start"], open=None, trades=[], last_day=None))
        b = bars(s["sym"])
        if S["last_day"] is None:
            S["last_day"] = str(b.index[-2].date())  # start trading from the latest finished day
        for d in b.index[b.index > pd.Timestamp(S["last_day"])]:
            row = b.loc[d]; v = ibs(row); px = float(row.Close); o = S["open"]
            prev = b.Close[b.index < d]
            if o:
                o["days"] += 1
                done = (px > float(prev.iloc[-1])) if s.get("exit") == "upclose" else (v > 0.5)
                if done or o["days"] >= 5:
                    pnl = o["qty"] * (px - o["entry"]) - COST * o["qty"] * (o["entry"] + px)
                    S["cash"] += o["qty"] * o["entry"] + pnl
                    S["trades"].append(dict(opened=o["opened"], closed=str(d.date()), entry=round(o["entry"], 2), exit=round(px, 2),
                                            days=o["days"], pnl=round(pnl, 2), pct=round(pnl / (o["qty"] * o["entry"]), 5),
                                            why=("up close" if s.get("exit") == "upclose" else "IBS > 0.5") if done else "5 days"))
                    S["open"] = None
            elif v < 0.2:
                w = 1.0
                if s.get("size") == "vol":
                    h = b[b.index <= d]; tr = pd.concat([h.High - h.Low, (h.High - h.Close.shift()).abs(),
                                                         (h.Low - h.Close.shift()).abs()], axis=1).max(axis=1)
                    w = min(1.0, 0.01 / (float(tr.rolling(14).mean().iloc[-1]) / px))
                qty = w * S["cash"] / px
                S["open"] = dict(entry=px, qty=qty, opened=str(d.date()), days=0, weight=round(w, 3)); S["cash"] -= qty * px
            S["last_day"] = str(d.date())
        last = float(b.Close.iloc[-1]); o = S["open"]
        S["equity"] = round(S["cash"] + (o["qty"] * last if o else 0), 2)
        t = S["trades"]; wins = sum(1 for x in t if x["pnl"] > 0)
        print(f"{name} ({s['sym']}): ${S['equity']:,.2f} (start ${s['start']:,.0f}); {len(t)} trades, "
              f"{wins} wins" + (f", avg {sum(x['pct'] for x in t) / len(t):+.2%} a trade" if t else "")
              + (f" | HOLDING from {o['entry']:.2f} ({o['days']} days)" if o else " | flat"))
    json.dump(st, open(STATE, "w"), indent=1)


if __name__ == "__main__":
    main()
