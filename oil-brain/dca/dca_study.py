"""Oil DCA study (pre-registered 2026-11-25, before any run; the user asked for plain DCA on oil with entry
conditions and exits, tried every way).

QUESTION: does any entry condition or exit beat PLAIN weekly DCA into oil, out of sample, by more than luck?

Instruments (daily bars in oil-brain/data):
  USO  - the oil fund (rolls front-month WTI futures; this is roughly what a long USOIL CFD costs too)
  XLE  - US energy stocks (dividends included via adjusted closes where Yahoo has them)
  BNO  - Brent oil fund (from 2010)
DCA mechanics: $100 is added every week (first trading day of the week). Plain DCA buys it at that day's close.
  A variant with an ENTRY CONDITION keeps the week's $100 (and any cash piled up) in cash when the condition is
  false, and invests ALL its cash on the first weekly check where the condition is true. Cash earns 0 (conservative:
  T-bills would add a little to the cash-heavy variants).
  An EXIT sells the whole holding at the close when it triggers; the cash then waits for the entry condition again.
  Costs: 5 bp per buy and per sell.
Entry conditions (checked on the weekly day, data as of that close; EIA/COT only after their release dates):
  E0 always (PLAIN DCA)                       E1 close below its 200-day average (buy weakness)
  E2 close above its 200-day average (trend)  E3 at least 20% below the 52-week high (buy the dip)
  E4 RSI(14) < 35                             E5 12-month return > 0 (time-series momentum)
  E6 curve: USO 63-day return minus USL 63-day return > 0 (front month stronger = backwardation-ish)
  E7 US crude stocks below the 5-year same-week normal (tight market)
  E8 managed money net long in the bottom 25% of its 3 years (crowd is out; contrarian)
  E9 close more than 1 standard deviation below its 1-year average (deep value)
Exits:
  X0 never sell (hold)             X1 close below the 200-day average
  X2 take profit: holding up 50% on its average cost
  X3 trailing stop: holding value 25% below its peak since the last buy-in from cash
  X4 12-month return < 0
Systems: 10 entries x 5 exits x 3 instruments = 150 (E0+X0 = plain DCA is the benchmark in each).
Periods (each starts fresh with $0): IS 2006-2013 (BNO 2010-2013), OOS 2014-2019, HOLDOUT 2020-2026-11.
Score per period: money multiple = final value / total added (and the gap to plain DCA in points).
PASS (fixed): beats plain DCA on the same instrument in OOS AND HOLDOUT, AND a placebo test over 2014-2026:
  the same exit with the entry condition replaced by random weeks with the same share of "true" weeks
  (200 runs, blocks of 4 weeks to keep clustering); placebo p <= 0.01 (with 150 systems, ~1-2 can pass
  p <= 0.01 by luck, so a pass is only a candidate for paper trading).
Research, not financial advice.
"""
import os, sys
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); OB = os.path.dirname(HERE)
sys.path.insert(0, OB)
import brain_v2 as B

COST = 5e-4
WEEKLY = 100.0
PERIODS = {"IS": ("2006-01-01", "2013-12-31"), "OOS": ("2014-01-01", "2019-12-31"), "HOLDOUT": ("2020-01-01", "2026-12-31")}
ENTRIES = ["E0", "E1", "E2", "E3", "E4", "E5", "E6", "E7", "E8", "E9"]
EXITS = ["X0", "X1", "X2", "X3", "X4"]
NAMES = {"E0": "plain (always)", "E1": "below 200d avg", "E2": "above 200d avg", "E3": "20% off 52w high",
         "E4": "RSI14<35", "E5": "12m return>0", "E6": "curve backwardation", "E7": "stocks below normal",
         "E8": "funds out (bottom 25%)", "E9": "1 sd below 1y avg",
         "X0": "hold", "X1": "sell below 200d", "X2": "take profit +50%", "X3": "trailing 25%", "X4": "sell 12m<0"}


def px(sym):
    df = pd.read_csv(os.path.join(OB, "data", f"{sym}.csv"), index_col=0, parse_dates=True)
    df.index = pd.to_datetime(df.index).tz_localize(None).normalize()
    return df[~df.index.duplicated()].Close.dropna()


def rsi(x, n=14):
    d = x.diff(); up = d.clip(lower=0).ewm(alpha=1 / n).mean(); dn = (-d.clip(upper=0)).ewm(alpha=1 / n).mean()
    return 100 - 100 / (1 + up / dn)


def conditions(c, f):
    f = f.reindex(c.index, method="ffill")
    sma200 = c.rolling(200).mean()
    e = pd.DataFrame(index=c.index)
    e["E0"] = True
    e["E1"] = c < sma200
    e["E2"] = c > sma200
    e["E3"] = c <= 0.8 * c.rolling(252).max()
    e["E4"] = rsi(c) < 35
    e["E5"] = c.pct_change(252) > 0
    e["E6"] = f["curve63"] > 0
    e["E7"] = f["stocks_dev"] < 0
    e["E8"] = f["mm_pct3y"] < 0.25
    e["E9"] = c < c.rolling(252).mean() - c.rolling(252).std()
    x = pd.DataFrame(index=c.index)
    x["X1"] = c < sma200
    x["X4"] = c.pct_change(252) < 0
    return e.fillna(False).astype(bool), x.fillna(False).astype(bool)


def run(c, entry, exitname, xs, start, end, entry_override=None):
    """Simulate one DCA system over [start, end]. Returns (multiple, added, final, max drawdown of account)."""
    s = c.loc[start:end]
    if len(s) < 60:
        return None
    wk = s.index.to_series().dt.isocalendar()
    weekly = ~pd.Series(list(zip(wk.year, wk.week)), index=s.index).duplicated()
    ent = entry_override.reindex(s.index).fillna(False) if entry_override is not None else entry.reindex(s.index)
    cash = units = added = cost_basis = 0.0; peak = 0.0; acct_peak = 0.0; mdd = 0.0
    for d, p in s.items():
        if weekly[d]:
            cash += WEEKLY; added += WEEKLY
            if ent[d] and cash > 0:
                units += cash * (1 - COST) / p; cost_basis += cash; cash = 0.0
        val = units * p
        if units > 0:
            peak = max(peak, val)
            sell = (exitname == "X1" and xs["X1"].get(d, False)) or (exitname == "X4" and xs["X4"].get(d, False)) \
                or (exitname == "X2" and val >= 1.5 * cost_basis) or (exitname == "X3" and val <= 0.75 * peak)
            if sell:
                cash += val * (1 - COST); units = 0.0; cost_basis = 0.0; peak = 0.0
        acct = cash + units * p
        acct_peak = max(acct_peak, acct)
        if acct_peak > 0:
            mdd = min(mdd, acct / acct_peak - 1)
    final = cash + units * s.iloc[-1]
    return final / added, added, final, mdd


def placebo(c, entry, exitname, xs, start, end, n=200, seed=0):
    s = c.loc[start:end]
    wk = s.index.to_series().dt.isocalendar()
    weekly_days = s.index[~pd.Series(list(zip(wk.year, wk.week)), index=s.index).duplicated().values]
    share = float(entry.reindex(weekly_days).mean())
    rng = np.random.default_rng(seed); out = []
    nblk = int(np.ceil(len(weekly_days) / 4))
    for _ in range(n):
        blocks = rng.random(nblk) < share
        flags = pd.Series(np.repeat(blocks, 4)[:len(weekly_days)], index=weekly_days)
        out.append(run(c, None, exitname, xs, start, end, entry_override=flags)[0])
    return np.array(out), share


def main():
    f = B.features()
    rows = []
    for sym in ["USO", "XLE", "BNO"]:
        c = px(sym); e, xs = conditions(c, f)
        for en in ENTRIES:
            for ex in EXITS:
                r = dict(sym=sym, entry=en, exit=ex)
                for per, (a, b) in PERIODS.items():
                    res = run(c, e[en], ex, xs, a, b)
                    r[per] = None if res is None else round(res[0], 3)
                    r[per + "_dd"] = None if res is None else round(res[3], 3)
                rows.append(r)
    df = pd.DataFrame(rows)
    for per in PERIODS:
        base = df[(df.entry == "E0") & (df.exit == "X0")].set_index("sym")[per]
        df[per + "_vs_plain"] = df.apply(lambda r: None if r[per] is None or pd.isna(base[r.sym]) else round(r[per] - base[r.sym], 3), axis=1)
    cand = df[(df.OOS_vs_plain > 0) & (df.HOLDOUT_vs_plain > 0) & ~((df.entry == "E0") & (df.exit == "X0"))].copy()
    ps = []
    for _, r in cand.iterrows():
        c = px(r.sym); e, xs = conditions(c, f)
        real = run(c, e[r.entry], r.exit, xs, "2014-01-01", "2026-12-31")[0]
        pl, share = placebo(c, e[r.entry], r.exit, xs, "2014-01-01", "2026-12-31")
        ps.append(dict(sym=r.sym, entry=r.entry, exit=r.exit, post2014=round(real, 3), share=round(share, 2),
                       placebo_med=round(float(np.median(pl)), 3), p=round(float((pl >= real).mean()), 3)))
    pdf = pd.DataFrame(ps)
    df["name"] = df.entry.map(NAMES) + " / " + df.exit.map(NAMES)
    df.to_csv(os.path.join(HERE, "dca_results.csv"), index=False)
    pdf.to_csv(os.path.join(HERE, "dca_placebo.csv"), index=False)
    pd.set_option("display.width", 250); pd.set_option("display.max_rows", 300)
    print("Systems tested:", len(df))
    print("\nPLAIN DCA (money multiple = final / added):")
    print(df[(df.entry == "E0") & (df.exit == "X0")][["sym", "IS", "OOS", "HOLDOUT", "IS_dd", "OOS_dd", "HOLDOUT_dd"]].to_string(index=False))
    print(f"\nBeat plain DCA in BOTH OOS and HOLDOUT: {len(cand)} of {len(df) - 3}")
    if len(pdf):
        print(pdf.sort_values("p").to_string(index=False))
        print("\nPASS (placebo p <= 0.01):", len(pdf[pdf.p <= 0.01]))
    print("\nTop 15 by HOLDOUT vs plain:")
    print(df.sort_values("HOLDOUT_vs_plain", ascending=False).head(15)[["sym", "name", "IS", "OOS", "HOLDOUT", "OOS_vs_plain", "HOLDOUT_vs_plain", "HOLDOUT_dd"]].to_string(index=False))


if __name__ == "__main__":
    main()
