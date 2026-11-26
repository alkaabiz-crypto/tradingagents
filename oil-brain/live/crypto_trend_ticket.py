"""Crypto trend DEMO ticket + AI forward check (registered 2026-11-26; the user said "ok sure" to running the plain
rule as a daily demo ticket, with the TradingAgents AI logged next to it). FROZEN RULE, never change it:
  Each UTC day, for BTCUSD and ETHUSD (half the balance each):
    direction = LONG if yesterday's close > its 50-day average, else SHORT
    entry at the UTC open (00:00 UTC = 4:00 am Abu Dhabi), stop 0.5 x ATR14 (a 0.35 ATR stop is logged as a shadow),
    size = half the balance x min(1, 2% / ATR%), no target, close at the UTC close (midnight UTC).
  Costs (paper P&L): costs.py, Exness Standard swap-free = spread + stop slippage, no commission, no swap.
Commands:
  python3 oil-brain/live/crypto_trend_ticket.py ticket [--balance 3400]   # score past days + today's ticket (00:07 UTC)
  python3 oil-brain/live/crypto_trend_ticket.py ai                        # AI verdict for TOMORROW (run ~18:07 UTC)
  python3 oil-brain/live/crypto_trend_ticket.py score                     # paper record + AI agree/disagree split
AI check (pre-registered): after >= 60 scored coin-days, compare the rule's P&L on days the AI AGREED with the
direction vs days it DISAGREED. The AI "helps" only if agree-days beat disagree-days with a shuffle p < 0.05 AND
skipping disagree-days raises the Sharpe. Until then the AI changes nothing. Demo/paper only. Not financial advice.
"""
import os, sys, csv, argparse, datetime as dt
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); OB = os.path.dirname(HERE)
sys.path.insert(0, HERE); sys.path.insert(0, OB)
import costs

COINS = {"BTC-USD": "BTCUSD", "ETH-USD": "ETHUSD"}
LOG = os.path.join(HERE, "crypto_trend_log.csv"); AILOG = os.path.join(HERE, "crypto_trend_ai.csv")
FIELDS = ["day", "coin", "side", "atr", "weight", "notional", "open", "stop", "close", "result", "pnl", "pnl_shadow035"]


def daily(sym):
    import yfinance as yf
    d = yf.Ticker(sym).history(period="1y")[["Open", "High", "Low", "Close"]].dropna()
    d.index = d.index.tz_localize(None).normalize(); return d[~d.index.duplicated()]


def plan(d, day):
    """Ticket for UTC day `day` from bars strictly before it."""
    p = d[d.index < day]
    tr = pd.concat([p.High - p.Low, (p.High - p.Close.shift()).abs(), (p.Low - p.Close.shift()).abs()], axis=1).max(axis=1)
    atr = float(tr.rolling(14).mean().iloc[-1]); c = float(p.Close.iloc[-1]); sma = float(p.Close.rolling(50).mean().iloc[-1])
    return (1 if c > sma else -1), atr, min(1.0, 0.02 / (atr / c)), c, sma


def result(bar, s, atr, k, sym):
    o = float(bar.Open); st = o - s * k * atr
    hit = (bar.Low <= st) if s > 0 else (bar.High >= st)
    x = st if hit else float(bar.Close); g = s * (x / o - 1)
    return x, ("stop" if hit else "close"), g - costs.round_trip(sym, bool(hit)), o, st


def read(path):
    return list(csv.DictReader(open(path))) if os.path.exists(path) else []


def write(rows):
    with open(LOG, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS); w.writeheader(); w.writerows(rows)


def ticket(balance):
    today = pd.Timestamp(dt.datetime.now(dt.timezone.utc).date()); rows = read(LOG); have = {(r["day"], r["coin"]) for r in rows}
    for sym, ex in COINS.items():
        d = daily(sym)
        for r in rows:                                   # score finished days
            if r["coin"] == ex and r["result"] == "open" and pd.Timestamp(r["day"]) < today and pd.Timestamp(r["day"]) in d.index:
                b = d.loc[pd.Timestamp(r["day"])]; s = 1 if r["side"] == "LONG" else -1
                x, res, net, o, st = result(b, s, float(r["atr"]), 0.5, sym); _, _, net35, _, _ = result(b, s, float(r["atr"]), 0.35, sym)
                r.update(open=round(o, 2), stop=round(st, 2), close=round(x, 2), result=res,
                         pnl=round(float(r["notional"]) * net, 2), pnl_shadow035=round(float(r["notional"]) * net35, 2))
        if (str(today.date()), ex) not in have:
            s, atr, w, c, sma = plan(d, today); notional = balance / 2 * w
            rows.append(dict(day=str(today.date()), coin=ex, side="LONG" if s > 0 else "SHORT", atr=round(atr, 2),
                             weight=round(w, 3), notional=round(notional, 2), open="", stop="", close="", result="open",
                             pnl="", pnl_shadow035=""))
            print(f"{ex}: {'BUY' if s > 0 else 'SELL'} at market now (~{c:,.2f}); {c:,.2f} vs 50-day avg {sma:,.2f}; "
                  f"size ${notional:,.0f} ({w:.0%} of ${balance / 2:,.0f}); stop {c - s * 0.5 * atr:,.2f} "
                  f"(0.5 ATR = {0.5 * atr:,.2f} from the open); no target; close at midnight UTC (4:00 am Abu Dhabi)")
            # Exness: min volume 0.01 lot (user, 2026-11-26); contract size assumed 1 coin per lot (check Specification)
            raw = notional / c; lots = max(0.01, round(raw, 2)); real = lots * c
            note = "" if raw >= 0.005 else f"  <- BELOW the 0.01 minimum: 0.01 lot = ${real:,.0f}, {real / notional:.1f}x the rule's size"
            print(f"   volume {lots:.2f} lot (~${real:,.0f}); loss if stopped ~${lots * 0.5 * atr:,.2f}{note}")
    write(rows); score(short=True)


def ai():
    import day_ticket as T
    tomorrow = str(dt.datetime.now(dt.timezone.utc).date() + dt.timedelta(days=1)); done = {(r["for_day"], r["coin"]) for r in read(AILOG)}
    today = str(dt.datetime.now(dt.timezone.utc).date())
    for sym, ex in COINS.items():
        if (tomorrow, ex) in done: continue
        rating, model, _ = T.verdict(sym, today)
        side = {"Buy": "LONG", "Overweight": "LONG", "Sell": "SHORT", "Underweight": "SHORT"}.get(rating, "NONE")
        new = not os.path.exists(AILOG)
        with open(AILOG, "a", newline="") as f:
            w = csv.writer(f)
            if new: w.writerow(["made", "for_day", "coin", "rating", "ai_side", "model"])
            w.writerow([today, tomorrow, ex, rating or "error", side, model])
        print(f"AI {ex} for {tomorrow}: {rating} -> {side} ({model})")


def score(short=False):
    L = pd.DataFrame(read(LOG))
    if L.empty: print("No tickets yet."); return
    D = L[L.result != "open"].copy()
    if D.empty: print("Crypto trend demo: no finished days yet."); return
    D["pnl"] = D.pnl.astype(float); D["pnl_shadow035"] = D.pnl_shadow035.astype(float)
    print(f"Crypto trend demo record: {len(D)} coin-days, P&L ${D.pnl.sum():+,.2f} (0.35 ATR shadow ${D.pnl_shadow035.sum():+,.2f}), "
          f"win {np.mean(D.pnl > 0):.0%}; last day: " + ", ".join(f"{r.coin} {r.side} {r.result} ${float(r.pnl):+.2f}" for r in D[D.day == D.day.max()].itertuples()))
    A = pd.DataFrame(read(AILOG))
    if short or A.empty: return
    M = D.merge(A.rename(columns={"for_day": "day"}), on=["day", "coin"]); M = M[M.ai_side.isin(["LONG", "SHORT"])]
    agree, dis = M[M.ai_side == M.side].pnl, M[M.ai_side != M.side].pnl
    print(f"AI check: {len(M)} days with an AI call (needs >= 60): agree {len(agree)} days ${agree.sum():+,.2f}, "
          f"disagree {len(dis)} days ${dis.sum():+,.2f}")
    if len(M) >= 60 and len(agree) and len(dis):
        rng = np.random.default_rng(91); x = M.pnl.values; k = len(agree)
        sims = [rng.permutation(x)[:k].mean() - rng.permutation(x)[k:].mean() for _ in range(2000)]
        p = float(np.mean(np.array(sims) >= agree.mean() - dis.mean())); print(f"  agree-minus-disagree shuffle p {p:.3f}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("cmd", choices=["ticket", "ai", "score"]); ap.add_argument("--balance", type=float, default=3400)
    a = ap.parse_args(); {"ticket": lambda: ticket(a.balance), "ai": ai, "score": score}[a.cmd]()
