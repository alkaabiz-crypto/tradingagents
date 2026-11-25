"""QQQ IBS dip on Exness USTEC-style candles (pre-registered 2026-11-25, before any run; the user asked to test the
IBS rule on Exness USTEC candles).

Exness gives no downloadable USTEC history; USTEC is a CFD on the Nasdaq-100 futures (NQ), so candles are rebuilt
from Yahoo NQ=F (front-month continuous futures):
  A  EXNESS DAILY candles: hourly NQ bars grouped by UTC date (Exness MT5 server time is GMT+0); candles with
     fewer than 6 hourly bars (the Sunday-evening stub, holidays) are dropped. 1h history: ~2024-07 to now.
  B  US-SESSION candles on the CFD price: hourly NQ bars starting 09:00-15:00 New York (≈ the cash session,
     6:30 pm-1:00 am Abu Dhabi in winter); entry/exit at the last bar's close (≈ 16:00 New York) — what the
     pre-close alert does. Same 1h history.
  C  NQ=F DAILY bars (CME Globex day, 18:00-17:00 New York), 2000-2026, for a long history on the futures price.
  Q  QQQ daily (the original), over the same dates as A/B, for comparison.
Rule (unchanged from ibs_live.py): IBS = (close - low) / (high - low) < 0.2 -> buy at that candle's close; sell at
the first candle close with IBS > 0.5, or at the 5th candle. One position at a time.
Exness-style costs: spread 1 bp a side (USTEC ~1.5-2 points on ~25,000) + overnight swap 1.7 bp per CALENDAR
night held (≈ 6% a year financing; weekends count 3 nights). Stress: 2x spread and 2x swap.
Futures roll: continuous NQ=F jumps at the quarterly roll (Mar/Jun/Sep/Dec); results are also shown excluding
entries on days 8-16 of those months.
Scored: trades, trades a year, win rate, average net bp, t; placebo = random entry candles, same exit, 500 runs,
seed 11. Judgement (fixed): A or B CONFIRM the QQQ result if the average net trade > 0 and t >= 1.5 over the short
1h window (low power, ~2.4 years); C must pass the smallwins gates (OOS 2014-19 > 0, HOLDOUT 2020+ > 0, post-2014
t >= 2, > 0 at 2x costs, placebo p <= 0.01). Research, not financial advice.
"""
import os, sys
import numpy as np, pandas as pd, yfinance as yf

HERE = os.path.dirname(os.path.abspath(__file__))
SPREAD, SWAP = 1e-4, 1.7e-4


def nq_hourly():
    h = yf.Ticker("NQ=F").history(period="730d", interval="1h")[["Open", "High", "Low", "Close"]].dropna()
    return h


def candles_utc(h):
    x = h.copy(); x.index = x.index.tz_convert("UTC")
    g = x.groupby(x.index.date)
    c = pd.DataFrame({"Open": g.Open.first(), "High": g.High.max(), "Low": g.Low.min(), "Close": g.Close.last(), "n": g.Close.size()})
    c.index = pd.to_datetime(c.index)
    return c[c.n >= 6].drop(columns="n")


def candles_session(h):
    x = h.copy(); x.index = x.index.tz_convert("America/New_York")
    x = x[(x.index.hour >= 9) & (x.index.hour <= 15)]
    g = x.groupby(x.index.date)
    c = pd.DataFrame({"Open": g.Open.first(), "High": g.High.max(), "Low": g.Low.min(), "Close": g.Close.last(), "n": g.Close.size()})
    c.index = pd.to_datetime(c.index)
    return c[c.n >= 5].drop(columns="n")


def daily(sym, start=None):
    d = yf.Ticker(sym).history(period="max", interval="1d")[["Open", "High", "Low", "Close"]].dropna()
    d.index = d.index.tz_localize(None).normalize(); d = d[~d.index.duplicated()]
    ny = pd.Timestamp.now(tz="America/New_York").tz_localize(None).normalize()
    d = d[d.index < ny]  # finished candles only
    return d[d.index >= start] if start is not None else d


def trades(c, entry_mask=None):
    ibs = ((c.Close - c.Low) / (c.High - c.Low)).fillna(0.5).values
    px = c.Close.values; idx = c.index; n = len(c); out = []; k = 0
    while k < n - 1:
        go = (ibs[k] < 0.2) if entry_mask is None else entry_mask[k]
        if go:
            j = next((j for j in range(k + 1, min(k + 6, n)) if ibs[j] > 0.5), min(k + 5, n - 1))
            nights = (idx[j] - idx[k]).days
            out.append(dict(date=idx[k], gross=px[j] / px[k] - 1, nights=nights))
            k = j
        else:
            k += 1
    return pd.DataFrame(out)


def net(t, mult=1.0):
    return t.gross - mult * (2 * SPREAD + SWAP * t.nights)


def rollmask(t):
    return ~(t.date.dt.month.isin([3, 6, 9, 12]) & t.date.dt.day.between(8, 16))


def summary(label, t, c):
    if t.empty:
        return dict(version=label, trades=0)
    r = net(t); years = max((c.index[-1] - c.index[0]).days / 365.25, 0.1)
    rng = np.random.default_rng(11); pl = []
    for _ in range(500):
        m = np.zeros(len(c), bool); m[rng.choice(len(c) - 1, size=min(len(t), len(c) - 1), replace=False)] = True
        tp = trades(c, m)
        pl.append(net(tp).mean() if len(tp) else np.nan)
    pl = np.array(pl); nr = net(t[rollmask(t)])
    return dict(version=label, start=str(c.index[0].date()), trades=len(t), per_year=round(len(t) / years, 1),
                win=round((r > 0).mean(), 3), avg_net_bp=round(r.mean() * 1e4, 1),
                t=round(r.mean() / (r.std(ddof=1) / np.sqrt(len(r))), 2) if len(r) > 2 else np.nan,
                avg_net_bp_2x=round(net(t, 2).mean() * 1e4, 1), avg_no_roll_bp=round(nr.mean() * 1e4, 1),
                worst_bp=round(r.min() * 1e4), placebo_p=round(float(np.nanmean(pl >= r.mean())), 3))


def main():
    h = nq_hourly(); A = candles_utc(h); Bc = candles_session(h)
    start = min(A.index[0], Bc.index[0]); Q = daily("QQQ", start)
    rows = [summary("A Exness daily (UTC midnight) USTEC", trades(A), A),
            summary("B US-session candle on USTEC price", trades(Bc), Bc),
            summary("Q QQQ daily, same window", trades(Q), Q)]
    C = daily("NQ=F"); tC = trades(C)
    for lab, a, z in [("C NQ futures daily, IS 2000-13", None, "2014-01-01"), ("C NQ futures daily, OOS 2014-19", "2014-01-01", "2020-01-01"),
                      ("C NQ futures daily, HOLDOUT 2020+", "2020-01-01", None), ("C NQ futures daily, POST 2014", "2014-01-01", None)]:
        cc = C.loc[a:z] if (a or z) else C
        rows.append(summary(lab, trades(cc), cc))
    df = pd.DataFrame(rows); df.to_csv(os.path.join(HERE, "ibs_ustec_results.csv"), index=False)
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 20)
    print(df.to_string(index=False))
    a, b = df.iloc[0], df.iloc[1]
    print(f"\nA confirms: {a.avg_net_bp > 0 and a.t >= 1.5};  B confirms: {b.avg_net_bp > 0 and b.t >= 1.5}")
    post = df[df.version.str.contains("POST")].iloc[0]; oos = df[df.version.str.contains("OOS")].iloc[0]; ho = df[df.version.str.contains("HOLDOUT")].iloc[0]
    print(f"C passes: {oos.avg_net_bp > 0 and ho.avg_net_bp > 0 and post.t >= 2 and post.avg_net_bp_2x > 0 and post.placebo_p <= 0.01}")


if __name__ == "__main__":
    main()
