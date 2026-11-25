"""Next-day paper tickets from TradingAgents (registered 2026-11-24, before any ticket).

The user asked for something for daily trades. TradingAgents reads daily bars, so it is asked for ONE
next-session call per ticker; the ticket levels come from a fixed rule, so every ticket is scored the same way.

    python3 oil-brain/live/day_ticket.py XOM CVX     # after the close: tickets for the next session
    python3 oil-brain/live/day_ticket.py --score     # score every open ticket whose session has closed

Direction: TradingAgents' rating on the last close, with a mandate (via the portfolio context) that the caller
is a paper day trader holding for the next session only.  Buy/Overweight -> LONG, Sell/Underweight -> SHORT,
Hold -> NO TRADE.
Levels (fixed): entry = next session's open; stop = 0.5 x ATR(14) from the entry; target = 1.0 x ATR(14);
exit at that session's close if neither is hit. If the daily bar touches both, count the STOP (worst case).
Cost 5 bp a side. Result in R (1R = the stop distance) and in % of the entry.
Pass bar (fixed): >= 60 tickets, mean R > 0 net of costs with t >= 2, AND better than the same tickets with a
coin-flip direction (1000 shuffles, p < 0.05). Until then it is a paper experiment, not a reason to trade.
Model: free Mistral Codestral (2 requests/minute; ~8 min a ticker), Gemini fallback, as in ta_sleeve.py.
Changed 2026-11-25 at the user's request (after 6 tickets, none scored yet): Codestral for the deep roles and
Ministral 14B for the quick roles (Mistral limits are per model, so this is about twice as fast); then Ministral
14B alone; then Gemini. The ticket rule and the pass bar are unchanged; the log's "model" column says which ran.
Paper money only. Research, not financial advice.
"""
import os, sys, csv, datetime as dt
import numpy as np, pandas as pd, yfinance as yf

HERE = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(HERE, "day_tickets.csv")
FIELDS = ["made", "session", "ticker", "rating", "side", "atr", "entry", "stop", "target", "exit", "result", "R", "pct", "model"]
COST = 5e-4
MANDATE = ("Portfolio context: the caller is a PAPER DAY TRADER. Judge ONLY the next US trading session after the "
           "analysis date: should they be long, short or flat from that session's open to its close? Ignore multi-month "
           "views. Buy/Overweight = go long tomorrow, Sell/Underweight = go short tomorrow, Hold = no trade tomorrow. "
           "Choose Hold unless the short-term evidence (momentum, levels, news due tomorrow) is clear. "
           "Set time_horizon to '1 day'.")


class DayMandate:
    def render(self, ticker):
        return MANDATE


def bars(ticker, period="6mo"):
    df = yf.download(ticker, period=period, auto_adjust=False, progress=False, threads=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df.index = pd.to_datetime(df.index).tz_localize(None).normalize()
    ny = pd.Timestamp.now(tz="America/New_York")
    if ny.hour * 60 + ny.minute < 16 * 60 + 10:  # today's bar is not final yet
        df = df[df.index < ny.tz_localize(None).normalize()]
    return df.dropna()


def atr14(df):
    tr = pd.concat([df.High - df.Low, (df.High - df.Close.shift()).abs(), (df.Low - df.Close.shift()).abs()], axis=1).max(axis=1)
    return float(tr.rolling(14).mean().iloc[-1])


def verdict(ticker, day):
    sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))
    sys.path.insert(0, HERE)
    from ta_sleeve import _throttle_openai_calls, MISTRAL_ATTEMPTS
    from tradingagents.default_config import DEFAULT_CONFIG
    from tradingagents.graph.trading_graph import TradingAgentsGraph
    os.environ.pop("ANTHROPIC_BASE_URL", None)
    base = DEFAULT_CONFIG.copy()
    base.update(max_debate_rounds=1, max_risk_discuss_rounds=1, results_dir=os.path.join(HERE, "ta_reports"))
    errors = []
    for label, extra in MISTRAL_ATTEMPTS + [("gemini", dict(llm_provider="google", deep_think_llm="gemini-3.5-flash",
                                                             quick_think_llm="gemini-3.5-flash-lite"))]:
        if label.startswith("mistral"):
            os.environ.setdefault("MISTRAL_API_KEY", "proxy-injected"); _throttle_openai_calls(31.0)
        else:
            real = os.environ.get("GOOGLE_API_KEY") or os.environ.get("api_key") or os.environ.get("GEMINI_API_KEY")
            os.environ["GOOGLE_API_KEY"] = real or "placeholder-the-proxy-adds-the-real-key"
        cfg = base.copy(); cfg.update(extra)
        try:
            state, rating = TradingAgentsGraph(debug=False, config=cfg).propagate(ticker, day, portfolio=DayMandate())
            return rating, label, str(state.get("final_trade_decision", ""))
        except Exception as e:
            errors.append(f"{label}: {type(e).__name__}: {str(e)[:100]}")
    return None, "none", " | ".join(errors)


def read_log():
    return list(csv.DictReader(open(LOG))) if os.path.exists(LOG) else []


def write_log(rows):
    with open(LOG, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS); w.writeheader(); w.writerows(rows)


def make(tickers):
    rows = read_log()
    for t in tickers:
        df = bars(t); day = str(df.index[-1].date()); a = atr14(df)
        if any(r["made"] == day and r["ticker"] == t and r["rating"] != "error" for r in rows):
            print(f"{t}: ticket for after {day} already made"); continue
        rows = [r for r in rows if not (r["made"] == day and r["ticker"] == t)]  # retry a failed one
        rating, model, text = verdict(t, day)
        side = {"Buy": "LONG", "Overweight": "LONG", "Sell": "SHORT", "Underweight": "SHORT"}.get(rating, "NONE")
        rows.append(dict(made=day, session="", ticker=t, rating=rating or "error", side=side, atr=round(a, 4),
                         entry="", stop="", target="", exit="", result="open" if side != "NONE" else "no trade",
                         R="", pct="", model=model))
        write_log(rows)
        last = float(df.Close.iloc[-1])
        print(f"\n=== {t} (close {day}: ${last:,.2f}, ATR14 ${a:,.2f}) -> {rating} -> {side}")
        if side != "NONE":
            sgn = 1 if side == "LONG" else -1
            print(f"Ticket for the next session: {'BUY' if sgn > 0 else 'SELL SHORT'} at the open; "
                  f"stop {0.5 * a:,.2f} {'below' if sgn > 0 else 'above'} the open (~${last - sgn * 0.5 * a:,.2f}), "
                  f"target {a:,.2f} {'above' if sgn > 0 else 'below'} (~${last + sgn * a:,.2f}); out at the close.")
        print(text[:700] if rating else f"TradingAgents could not run: {text}")


def outcome(b, a, sgn):
    """The fixed rule on one daily bar: (exit, result, pct net of costs, R)."""
    e = float(b.Open); stop = e - sgn * 0.5 * a; tgt = e + sgn * a
    hit_stop = (b.Low <= stop) if sgn > 0 else (b.High >= stop)
    hit_tgt = (b.High >= tgt) if sgn > 0 else (b.Low <= tgt)
    x, res = (stop, "stop") if hit_stop else (tgt, "target") if hit_tgt else (float(b.Close), "close")
    pct = sgn * (x / e - 1) - 2 * COST
    return e, stop, tgt, x, res, pct, pct * e / (0.5 * a)


def score():
    rows = read_log(); done = []; cache = {}

    def session_bar(r):
        if r["ticker"] not in cache:
            cache[r["ticker"]] = bars(r["ticker"], "1y")
        nxt = cache[r["ticker"]][cache[r["ticker"]].index > pd.Timestamp(r["made"])]
        return None if nxt.empty else (nxt.index[0], nxt.iloc[0])

    for r in rows:
        if r["result"] != "open":
            continue
        sb = session_bar(r)
        if sb is None:
            continue
        day, b = sb; sgn = 1 if r["side"] == "LONG" else -1
        e, stop, tgt, x, res, pct, R = outcome(b, float(r["atr"]), sgn)
        r.update(session=str(day.date()), entry=round(e, 4), stop=round(stop, 4), target=round(tgt, 4),
                 exit=round(x, 4), result=res, R=round(R, 3), pct=round(pct, 5))
        done.append(r)
    write_log(rows)
    for r in done:
        print(f"{r['session']} {r['ticker']} {r['side']}: {r['result']} -> {float(r['R']):+.2f}R ({float(r['pct']):+.2%})")
    closed = [r for r in rows if r["R"] not in ("", None)]
    if not closed:
        print("No closed tickets yet.")
        return
    ai = np.array([float(r["R"]) for r in closed])
    # Fair comparisons on the SAME ticker-days (added 2026-11-25 at the user's request; the rule is unchanged):
    # ALWAYS LONG = the same ticket but always a buy; COIN FLIP = the AI's sides shuffled at random.
    longR, shortR = [], []
    for r in closed:
        b = session_bar(r)[1]; a = float(r["atr"])
        longR.append(outcome(b, a, 1)[6]); shortR.append(outcome(b, a, -1)[6])
    longR, shortR = np.array(longR), np.array(shortR)
    rng = np.random.default_rng(0)
    flips = np.array([np.where(rng.random(len(ai)) < 0.5, longR, shortR).mean() for _ in range(1000)])
    p = float((flips >= ai.mean()).mean())
    s = ai.std(ddof=1) if len(ai) > 1 else float("nan")
    t = ai.mean() / (s / np.sqrt(len(ai))) if len(ai) > 1 and s > 0 else float("nan")
    print(f"All closed tickets: {len(ai)}, AI mean {ai.mean():+.2f}R (t {t:.2f}, win rate {np.mean(ai > 0):.0%}) | "
          f"always-long {longR.mean():+.2f}R | coin flip {flips.mean():+.2f}R, AI beats it in {1 - p:.0%} of shuffles (p {p:.2f})")
    print("Pass bar: >= 60 tickets, t >= 2, coin-flip p < 0.05. Also watch: does the AI beat always-long?")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if "--score" in sys.argv:
        score()
    else:
        make([a.upper() for a in args] or ["XOM", "CVX"])
