"""Shared machinery for the insiders brain.

Event -> portfolio:
  * event = (stock, signal date). Entry at the CLOSE of the first trading day strictly after the
    Form 4 FILING_DATE (conservative 1-day delay: filings can arrive up to 10 pm).
  * held for `hold` trading days. Book = equal weight over active stocks, long each stock,
    short the same total in SPY (beta-1 hedge). Weight vector known at close t earns t->t+1.
  * cost 10 bp per unit of turnover on every leg (stocks and SPY).
Evaluation:
  * engine.evaluate (unchanged) is fed ret = book return per unit of gross long (net of the
    stock-level costs computed here), pos = 1 when the book holds anything, cost_bps=0,
    bench = the same-universe passive book (equal weight of all universe stocks minus SPY).
    That benchmark absorbs most of the survivorship bias of a today's-large-caps universe.
  * engine's own placebo (circular shift of a mostly-constant pos) and its 2x-cost gate are
    degenerate for a stock book, so gates 4 and 5 are replaced:
      gate 4: placebo = every event's date shifted by an independent random offset of
              +/- 60..750 trading days (same stock, same count, same hold) -> 500 books;
              p = share of placebo post-2014 Sharpes >= real.
      gate 5: post-2014 sum of returns at 20 bp per side > 0.
"""
import os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.abspath(os.path.join(HERE, "..", "..")))
import engine  # noqa: E402

COST = 10.0
POOL = 756  # control pool: names with a purchase event in the trailing ~3 years


def load_prices():
    px = pd.read_csv(os.path.join(HERE, "data", "prices.csv.gz"), index_col=0, parse_dates=True)
    return px


def load_universe():
    """today's largest SEC filers that are Section 16 issuers (have Form 4 P/S rows) and have
    Yahoo prices; first 500 by SEC size order."""
    c = pd.read_csv(os.path.join(HERE, "data", "candidates.csv"))
    c["yt"] = c.ticker.str.replace(".", "-", regex=False)
    t = load_trades()
    px = load_prices()
    c = c[c.cik.isin(set(t.ISSUERCIK)) & c.yt.isin(px.columns)]
    return c.head(500).reset_index(drop=True)


_T = None


def load_trades():
    global _T
    if _T is None:
        t = pd.read_csv(os.path.join(HERE, "data", "trades.csv.gz"), low_memory=False)
        t["FILING_DATE"] = pd.to_datetime(t.FILING_DATE, format="%d-%b-%Y", errors="coerce")
        t["TRANS_DATE"] = pd.to_datetime(t.TRANS_DATE, format="%d-%b-%Y", errors="coerce")
        for k in ["TRANS_SHARES", "TRANS_PRICEPERSHARE"]:
            t[k] = pd.to_numeric(t[k], errors="coerce")
        t["value"] = t.TRANS_SHARES * t.TRANS_PRICEPERSHARE
        rel = t.RPTOWNER_RELATIONSHIP.fillna("")
        t["is_off_dir"] = rel.str.contains("Officer|Director")
        t = t.drop_duplicates()
        _T = t
    return _T


def filings(code):
    """one row per Form 4 filing (accession) with open-market code P (acquired) or S (disposed),
    officer or director owners only."""
    t = load_trades()
    ad = "A" if code == "P" else "D"
    t = t[(t.TRANS_CODE == code) & (t.TRANS_ACQUIRED_DISP_CD == ad) & t.is_off_dir]
    g = t.groupby("ACCESSION_NUMBER").agg(cik=("ISSUERCIK", "first"), fdate=("FILING_DATE", "first"),
                                          tdate=("TRANS_DATE", "min"), owner=("RPTOWNERCIK", "first"),
                                          title=("RPTOWNER_TITLE", "first"),
                                          rel=("RPTOWNER_RELATIONSHIP", "first"),
                                          value=("value", "sum"))
    return g.dropna(subset=["fdate"]).reset_index()


class Book:
    def __init__(self, uni, px):
        self.uni = uni
        self.px = px[list(uni.yt) + ["SPY"]].loc["2005-12-01":]
        self.ret = self.px.pct_change()
        self.dates = self.ret.index
        self.R = self.ret[list(uni.yt)].values  # T x N
        self.spy = self.ret["SPY"].fillna(0).values
        self.col = {cik: i for i, cik in enumerate(uni.cik)}
        self.alive = self.px[list(uni.yt)].notna().values
        Rn = np.nan_to_num(self.R)
        self.ew = np.where(self.alive.sum(1) > 0, (Rn * self.alive).sum(1) / np.maximum(self.alive.sum(1), 1), 0.0)
        self.hedge = "spy"

    def entry_idx(self, dates):
        # first trading day strictly after filing date
        return np.searchsorted(self.dates.values, np.asarray(dates, dtype="datetime64[ns]"), side="right")

    def weights(self, ev_i, ev_j, hold):
        """ev_i: entry day index, ev_j: stock column. Returns T x N indicator (held), positions
        known at close of day t."""
        T, N = self.R.shape
        A = np.zeros((T + hold + 2, N))
        ok = (ev_i >= 0) & (ev_i < T)
        np.add.at(A, (ev_i[ok], ev_j[ok]), 1)
        np.add.at(A, (np.minimum(ev_i[ok] + hold, T + hold), ev_j[ok]), -1)
        H = (np.cumsum(A, axis=0)[:T] > 0) & self.alive
        return H

    def book(self, H, cost=COST, P=None):
        n = H.sum(1)
        w = np.where(n[:, None] > 0, H / np.maximum(n, 1)[:, None], 0.0)  # long weights at close t
        Rn = np.nan_to_num(self.R)
        gross = np.zeros(len(n))
        if P is not None:  # hedge = equal-weight control pool P (fallback: whole universe)
            Pm = np.where(P.sum(1)[:, None] > 0, P, self.alive).astype(float)
            wh = -w.sum(1)[:, None] * Pm / np.maximum(Pm.sum(1), 1)[:, None]
            W = w + wh
            gross[1:] = (W[:-1] * Rn[1:]).sum(1)
            turn = np.abs(np.diff(w, axis=0, prepend=0)).sum(1) + np.abs(np.diff(wh, axis=0, prepend=0)).sum(1)
            c = np.zeros(len(n)); c[1:] = turn[:-1] * cost / 1e4
            return pd.Series(gross - c, self.dates), pd.Series(gross - 2 * c, self.dates), pd.Series(n, self.dates)
        ws = -w.sum(1)  # SPY hedge
        hr = self.spy if self.hedge == "spy" else self.ew
        gross[1:] = (w[:-1] * Rn[1:]).sum(1) + ws[:-1] * hr[1:]
        turn = np.abs(np.diff(w, axis=0, prepend=0)).sum(1) + np.abs(np.diff(ws, prepend=0))
        c = np.zeros(len(n)); c[1:] = turn[:-1] * cost / 1e4
        return pd.Series(gross - c, self.dates), pd.Series(gross - 2 * c, self.dates), pd.Series(n, self.dates)

    def bench(self):
        H = self.alive.copy()
        r, _, _ = self.book(H, cost=0)
        return r


def evaluate(name, bk, ev_i, ev_j, hold, n_placebo=500, seed=11, start="2006-01-03"):
    H = bk.weights(ev_i, ev_j, hold)
    pool = (lambda ei, Hx: bk.weights(ei, ev_j, POOL) & ~Hx) if bk.hedge == "pool" else (lambda ei, Hx: None)
    r, r2, n = bk.book(H, P=pool(ev_i, H))
    pos = pd.Series((n > 0).astype(float), bk.dates)
    out = engine.evaluate(name, pos, r, cost_bps=0, bench=bk.bench(), start=start, n_placebo=20)
    post = r.loc["2014-01-01":]
    real = engine.sharpe(post)
    rng = np.random.default_rng(seed)
    T = len(bk.dates)
    ps = []
    for _ in range(n_placebo):
        sh = rng.integers(60, 751, len(ev_i)) * rng.choice([-1, 1], len(ev_i))
        ei = ev_i + sh
        # reflect out-of-range dates back inside the sample
        ei = np.where(ei < 0, -ei, ei); ei = np.where(ei >= T, 2 * (T - 1) - ei, ei)
        Hp = bk.weights(ei, ev_j, hold)
        rp, _, _ = bk.book(Hp, P=pool(ei, Hp))
        ps.append(engine.sharpe(rp.loc["2014-01-01":]))
    ps = np.array(ps)
    pp = float(np.mean(ps >= real))
    out.update(placebo_p=pp, placebo_mean=float(np.nanmean(ps)), x2cost_post=float(r2.loc["2014-01-01":].sum()),
               events=int(len(ev_i)), events_post=int((bk.dates[np.clip(ev_i, 0, T - 1)] >= "2014-01-01").sum()),
               exposure_post=float(pos.loc["2014-01-01":].mean()),
               avg_names_post=float(n.loc["2014-01-01":][n.loc["2014-01-01":] > 0].mean()))
    # trades per year = event entries per year
    out["trades_per_year"] = float(len(ev_i) / (len(r.loc[start:]) / 252))
    gates = [out["OOS"] > 0.3, out["HOLDOUT"] > 0.3, out["post"] > out["bench_post"],
             out["t_post"] >= 2.0, pp <= 0.05, out["x2cost_post"] > 0]
    out["verdict"] = "PASS" if all(gates) else f"FAIL ({6 - sum(gates)} of 6 gates)"
    if bk.hedge in ("ew", "pool"):  # survivorship-neutral book: its passive benchmark is exactly zero
        out["bench_post"] = 0.0
        gates[2] = out["post"] > 0
        out["verdict"] = "PASS" if all(gates) else f"FAIL ({6 - sum(gates)} of 6 gates)"
    out["winner"] = bool(all(gates) and out["t_post"] >= 3.0)
    return out, r


def show(rows):
    df = pd.DataFrame(rows).set_index("rule")
    cols = ["IS", "OOS", "HOLDOUT", "post", "bench_post", "t_post", "placebo_p", "placebo_mean",
            "cagr_post", "events", "events_post", "exposure_post", "avg_names_post", "verdict"]
    with pd.option_context("display.width", 250, "display.max_columns", 30):
        return df[cols].round(3).to_string()
