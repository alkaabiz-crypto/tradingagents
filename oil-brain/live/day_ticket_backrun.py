"""Back-run of the day tickets (pre-registered 2026-11-26, before any run; the user asked to back-run the day tickets
and test them fully). Two parts:

PART 1 — the ticket RULE without the AI, 2014-2026, all 17 markets (free):
  The same fixed levels as day_ticket.py (entry at the next open, stop 0.5 x ATR14, target 1 x ATR14, out at the
  close; both touched = stop; 5 bp a side), with simple directions: ALWAYS LONG, ALWAYS SHORT, COIN FLIP (seed 51),
  YESTERDAY (same side as the last day's move), TREND (long above the 50-day average, short below).
  This is the bar the AI has to beat.

PART 2 — the AI back-run (TradingAgents with the day mandate, as live):
  Dates: 16 trading days drawn at random (seed 52) from 2026-01-05 .. 2026-11-20, i.e. AFTER the models' training
  data (Codestral 2508, Ministral 14B 2512), so the AI cannot remember the outcome. Markets: XOM, USO, SPY, QQQ, NVDA
  (oil + index + tech). 16 x 5 = 80 tickets, ~5-8 minutes each on the free Mistral models (~7-10 hours).
  Look-ahead safety: price data are cut at the date; the news tools keep only articles published before it (Yahoo
  keeps few old articles, so the news analyst is mostly blind in a back-run — the back-run is HARDER than live).
  Logged to live/day_tickets_backrun.csv (never mixed with the live log). Resumable: done (date, ticker) pairs are skipped.
PASS for the AI (fixed): over the 80 back-run tickets plus the live ones, mean R > 0 with t >= 2 AND it beats
  ALWAYS LONG and the COIN FLIP on the same ticker-days (coin-flip shuffle p < 0.05). With 80 tickets this has
  little power: a pass would be a hint, a fail is not proof the AI is useless.
    python3 oil-brain/live/day_ticket_backrun.py rule      # part 1
    python3 oil-brain/live/day_ticket_backrun.py ai        # part 2 (long; resumable)
    python3 oil-brain/live/day_ticket_backrun.py score     # score part 2
Research, not financial advice.
"""
import os, sys, csv
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import day_ticket as T

LOG = os.path.join(HERE, "day_tickets_backrun.csv")
ALL17 = "XOM CVX COP OXY XLE USO SPY QQQ IWM GLD SLV LLY NVDA AAPL MSFT AMZN TSLA".split()
AI5 = ["XOM", "USO", "SPY", "QQQ", "NVDA"]


def full_bars(sym):
    import yfinance as yf
    d = yf.Ticker(sym).history(period="max", auto_adjust=False)[["Open", "High", "Low", "Close"]].dropna()
    d.index = d.index.tz_localize(None).normalize(); d = d[~d.index.duplicated()]
    return d[d.index < pd.Timestamp.now().normalize()]


def atr(d):
    tr = pd.concat([d.High - d.Low, (d.High - d.Close.shift()).abs(), (d.Low - d.Close.shift()).abs()], axis=1).max(axis=1)
    return tr.rolling(14).mean()


def part1():
    rng = np.random.default_rng(51); rows = []
    for sym in ALL17:
        d = full_bars(sym); a = atr(d); sma = d.Close.rolling(50).mean()
        d = d[d.index >= "2013-06-01"]
        dirs = {"ALWAYS LONG": lambda i: 1, "ALWAYS SHORT": lambda i: -1,
                "COIN FLIP": lambda i: 1 if rng.random() < 0.5 else -1,
                "YESTERDAY": lambda i: 1 if d.Close.iloc[i] > d.Close.iloc[i - 1] else -1,
                "TREND": lambda i: 1 if d.Close.iloc[i] > sma.loc[d.index[i]] else -1}
        for name, f in dirs.items():
            R = []
            for i in range(1, len(d) - 1):
                if d.index[i] < pd.Timestamp("2014-01-01") or np.isnan(a.loc[d.index[i]]):
                    continue
                R.append(T.outcome(d.iloc[i + 1], float(a.loc[d.index[i]]), f(i))[6])
            R = np.array(R); rows.append(dict(sym=sym, direction=name, n=len(R), mean_R=R.mean(), win=(R > 0).mean(),
                                              t=R.mean() / (R.std(ddof=1) / np.sqrt(len(R)))))
    df = pd.DataFrame(rows); df.to_csv(os.path.join(HERE, "day_ticket_rule_backtest.csv"), index=False)
    g = df.groupby("direction").agg(markets=("sym", "size"), mean_R=("mean_R", "mean"), win=("win", "mean"),
                                    markets_positive=("mean_R", lambda x: int((x > 0).sum())), median_t=("t", "median"))
    pd.set_option("display.width", 200)
    print("Ticket RULE 2014-2026, 17 markets, every day (no AI):"); print(g.round(3).to_string())
    print("\nBest market per direction:"); print(df.sort_values("t", ascending=False).groupby("direction").head(2).round(3).to_string(index=False))


def dates():
    import yfinance as yf
    cal = yf.Ticker("SPY").history(start="2026-01-05", end="2026-11-21").index.tz_localize(None).normalize()
    rng = np.random.default_rng(52)
    return sorted(str(x.date()) for x in rng.choice(cal, size=16, replace=False))


def part2():
    done = set()
    if os.path.exists(LOG):
        done = {(r["made"], r["ticker"]) for r in csv.DictReader(open(LOG)) if r["rating"] != "error"}
    for day in dates():
        for t in AI5:
            if (day, t) in done:
                continue
            d = full_bars(t); d = d[d.index <= day]; a = float(atr(d).iloc[-1])
            rating, model, _ = T.verdict(t, day)
            side = {"Buy": "LONG", "Overweight": "LONG", "Sell": "SHORT", "Underweight": "SHORT"}.get(rating, "NONE")
            new = not os.path.exists(LOG)
            with open(LOG, "a", newline="") as f:
                w = csv.writer(f)
                if new: w.writerow(["made", "ticker", "rating", "side", "atr", "model"])
                w.writerow([day, t, rating or "error", side, round(a, 4), model])
            print(f"{day} {t}: {rating} -> {side} ({model})", flush=True)


def score():
    if not os.path.exists(LOG):
        print("No back-run tickets yet."); return
    L = pd.read_csv(LOG); L = L[L.side.isin(["LONG", "SHORT"])]
    cache = {}; ai, lo, sh = [], [], []
    for _, r in L.iterrows():
        if r.ticker not in cache: cache[r.ticker] = full_bars(r.ticker)
        nx = cache[r.ticker][cache[r.ticker].index > pd.Timestamp(r.made)]
        if nx.empty: continue
        b = nx.iloc[0]; s = 1 if r.side == "LONG" else -1
        ai.append(T.outcome(b, r.atr, s)[6]); lo.append(T.outcome(b, r.atr, 1)[6]); sh.append(T.outcome(b, r.atr, -1)[6])
    ai, lo, sh = map(np.array, (ai, lo, sh))
    rng = np.random.default_rng(53); flips = np.array([np.where(rng.random(len(ai)) < .5, lo, sh).mean() for _ in range(2000)])
    t = ai.mean() / (ai.std(ddof=1) / np.sqrt(len(ai))) if len(ai) > 2 else np.nan
    allrows = pd.read_csv(LOG)
    print(f"Back-run tickets: {len(allrows)} made ({(allrows.side == 'NONE').sum()} no-trade), {len(ai)} traded and scored")
    print(f"AI mean {ai.mean():+.3f}R (t {t:.2f}, win {np.mean(ai > 0):.0%}) | always-long {lo.mean():+.3f}R | coin flip "
          f"{flips.mean():+.3f}R, AI beats it in {(flips < ai.mean()).mean():.0%} of shuffles (p {(flips >= ai.mean()).mean():.2f})")
    print("Long calls:", int((L.side == 'LONG').sum()), " short calls:", int((L.side == 'SHORT').sum()))


if __name__ == "__main__":
    {"rule": part1, "ai": part2, "score": score}[sys.argv[1] if len(sys.argv) > 1 else "score"]()
