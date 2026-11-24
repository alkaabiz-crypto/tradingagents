"""TradingAgents verdicts -> paper book (registered 2026-11-24, before any verdict).

Each US trading day after the close, run the real TradingAgents multi-agent analysis on ONE ticker
(a fixed weekday rotation, so each ticker gets a fresh verdict once a week and the API cost stays at
one run a day), read its 5-tier rating, and paper-trade it until that ticker's next verdict.

    python3 oil-brain/live/ta_sleeve.py          # after the close: run today's verdict, then mark the book
    python3 oil-brain/live/ta_sleeve.py --mark   # only mark the book (no API call)
    python3 oil-brain/live/ta_sleeve.py --dry Buy  # plumbing test with a fake rating (not saved)

Rotation: Mon SPY, Tue QQQ, Wed NVDA, Thu XLE (oil), Fri GLD.
Rating -> target exposure on that ticker's $1,000 slot:
    Buy +1.0   Overweight +0.5   Hold = keep the previous exposure   Underweight -0.5   Sell -1.0
Two books are scored on the same verdicts: LONG-ONLY (negative targets become cash) and LONG/SHORT.
Positions are taken at the close of the verdict day (5 bp per unit traded) and marked at each close.
Benchmark: equal-weight buy-and-hold of the five tickers over the same days.
Pass bar (fixed): >= 13 weeks, the long-only book beats the benchmark net of costs, and verdicts
beat a coin flip (next-week direction hit rate) at p < 0.05 over >= 60 verdicts.

Needs ANTHROPIC_API_KEY in the environment (environment settings -> variable). Without it the sleeve
stays in cash and says so. Models: claude-sonnet-5 (deep) and claude-haiku-4-5 (quick); about one run
a day. ANTHROPIC_BASE_URL is removed for the run so the key is used with the public API.
Paper money only. Research, not financial advice.
"""
import os, sys, json, csv, datetime as dt
import pandas as pd, yfinance as yf

HERE = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(HERE, "ta_state.json")
LOG = os.path.join(HERE, "ta_verdicts.csv")
ROTATION = {0: "SPY", 1: "QQQ", 2: "NVDA", 3: "XLE", 4: "GLD"}
TICKERS = list(ROTATION.values())
TARGET = {"Buy": 1.0, "Overweight": 0.5, "Underweight": -0.5, "Sell": -1.0}
SLOT = 1000.0
COST = 5e-4


def closes():
    df = yf.download(TICKERS, period="3mo", auto_adjust=True, progress=False)["Close"]
    df.index = pd.to_datetime(df.index).tz_localize(None).normalize()
    ny = pd.Timestamp.now(tz="America/New_York")
    today = ny.tz_localize(None).normalize() + (pd.Timedelta(days=1) if ny.hour * 60 + ny.minute >= 16 * 60 + 10 else pd.Timedelta(0))
    return df[df.index < today].dropna(how="all")


def load():
    if os.path.exists(STATE):
        return json.load(open(STATE))
    return {"start": None, "last_mark": None,
            "books": {b: {"cash": SLOT * len(TICKERS), "units": {t: 0.0 for t in TICKERS}} for b in ("long_only", "long_short")},
            "target": {t: 0.0 for t in TICKERS}, "bench_units": None, "history": []}


def run_verdict(ticker, day):
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        return None, "ANTHROPIC_API_KEY is not set: add it in the environment settings, then start a new session"
    os.environ.pop("ANTHROPIC_BASE_URL", None)
    sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))
    from tradingagents.default_config import DEFAULT_CONFIG
    from tradingagents.graph.trading_graph import TradingAgentsGraph
    cfg = DEFAULT_CONFIG.copy()
    cfg.update(llm_provider="anthropic", deep_think_llm="claude-sonnet-5", quick_think_llm="claude-haiku-4-5",
               max_debate_rounds=1, max_risk_discuss_rounds=1,
               results_dir=os.path.join(HERE, "ta_reports"))
    graph = TradingAgentsGraph(debug=False, config=cfg)
    _, rating = graph.propagate(ticker, day)
    return rating, "ok"


def trade(st, px, day):
    for name, book in st["books"].items():
        for t in TICKERS:
            if pd.isna(px.get(t)):
                continue
            tgt = st["target"][t]
            if name == "long_only":
                tgt = max(tgt, 0.0)
            want = tgt * SLOT / px[t]
            delta = want - book["units"][t]
            if abs(delta) * px[t] > 1:
                book["cash"] -= delta * px[t] + abs(delta) * px[t] * COST
                book["units"][t] = want


def mark(st, px, day):
    eq = {n: round(b["cash"] + sum(b["units"][t] * px[t] for t in TICKERS if not pd.isna(px.get(t))), 2)
          for n, b in st["books"].items()}
    if st["bench_units"] is None:
        st["bench_units"] = {t: SLOT / px[t] for t in TICKERS}
    eq["benchmark"] = round(sum(st["bench_units"][t] * px[t] for t in TICKERS), 2)
    st["history"] = [h for h in st["history"] if h["date"] != day] + [dict(date=day, **eq)]
    st["last_mark"] = day
    return eq


def main():
    dry = sys.argv[sys.argv.index("--dry") + 1] if "--dry" in sys.argv else None
    st = load(); df = closes(); day = df.index[-1]; d = str(day.date()); px = df.iloc[-1]
    st["start"] = st["start"] or d
    msg = ""
    if "--mark" not in sys.argv:
        ticker = ROTATION.get(day.weekday())
        done = os.path.exists(LOG) and any(r["date"] == d for r in csv.DictReader(open(LOG)))
        if ticker and not done:
            rating, info = (dry, "dry run") if dry else run_verdict(ticker, d)
            if rating:
                if rating in TARGET:
                    st["target"][ticker] = TARGET[rating]
                msg = f"TradingAgents verdict on {ticker} for {d}: {rating} -> target {st['target'][ticker]:+.1f} x ${SLOT:,.0f}"
                if not dry:
                    new = not os.path.exists(LOG)
                    with open(LOG, "a", newline="") as f:
                        w = csv.writer(f)
                        if new: w.writerow(["date", "ticker", "rating", "target", "close"])
                        w.writerow([d, ticker, rating, st["target"][ticker], round(float(px[ticker]), 4)])
            else:
                msg = f"No verdict today ({ticker}): {info}. The sleeve stays as it is."
    trade(st, px, d)
    eq = mark(st, px, d)
    if not dry:
        json.dump(st, open(STATE, "w"), indent=1)
    start_cap = SLOT * len(TICKERS)
    print(msg or "Marked only.")
    print(f"TradingAgents sleeve since {st['start']}: long-only ${eq['long_only']:,.2f} ({eq['long_only']/start_cap-1:+.2%}), "
          f"long/short ${eq['long_short']:,.2f} ({eq['long_short']/start_cap-1:+.2%}), "
          f"buy-and-hold ${eq['benchmark']:,.2f} ({eq['benchmark']/start_cap-1:+.2%})")
    print("Targets:", {t: v for t, v in st["target"].items()})


if __name__ == "__main__":
    main()
