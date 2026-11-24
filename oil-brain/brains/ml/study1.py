"""ML study 1 (pre-registered 2026-11-24, written BEFORE any run).

Question: can a machine-learning model combine many weak daily signals into a real 1-5 day edge
on USO, XLE or SPY? (Gu, Kelly & Xiu 2020 RFS: ML helps for the stock cross-section, mostly via
nonlinear interactions of momentum/liquidity/volatility; López de Prado 2018: backtest overfitting,
purging and embargo of overlapping labels.)

Features (all known at the close of day t; ~40 columns):
  - log returns over 1, 5, 21, 63 days of USO, XLE, SPY, TLT, GLD, DXY (DXY lagged 1 extra day
    because Yahoo's index close may be stamped after 16:00 ET)
  - log VIX and log OVX levels, and their 5-day log changes
  - carry: USO minus USL 21-day log return (curve-shape proxy)
  - CFTC: weekly change in commercials' net/OI (legacy) and managed-money net/OI (disagg),
    Tuesday data used only from the first trading day after the Friday release (study 8 rule)
  - volume z-scores of USO, XLE, SPY (log volume vs its trailing 63-day mean/sd)
  - day of week (one-hot, Mon..Fri)
Targets: y = 1 if the instrument's forward return over h days (close t -> close t+h) > 0, h in {1, 5}.
Instruments: USO, XLE, SPY.
Models (hyperparameters fixed a priori, never tuned):
  - LOGIT: StandardScaler + L2 logistic regression, C = 0.05.
  - GBM:   HistGradientBoostingClassifier(max_iter=150, learning_rate=0.03, max_depth=3,
           min_samples_leaf=100, l2_regularization=1.0, early_stopping=False, random_state=0).
Walk-forward: expanding window, refit once a year on Jan 1 using only rows whose label is fully
  observed before Dec 31 of the previous year (purge h days) plus a 5-trading-day embargo.
  Data start ~2008-04 (USL/OVX history); first predicted year 2011. Engine start = 2011-01-01, so
  "IS" in the table = 2011-2013 genuine walk-forward predictions; OOS/HOLDOUT never used to choose
  anything.
Position at close t: +1 if p - 0.5 >= 0.02, -1 if p - 0.5 <= -0.02, else 0. Updated daily
  (for h = 5 the 5-day label is still re-predicted each day; position is the daily sign).
Costs 5 bp per turnover. Benchmark: buy and hold of the same instrument.
Rules counted: 2 models x 3 instruments x 2 horizons = 12. Shuffled-label control (labels
  randomly permuted within each training window, same pipeline) for every config with 1 seed,
  plus a 20-seed distribution for LOGIT/GBM on h=5: these are controls, not tradable rules, but are
  conservatively charged as 3 rules -> 15 total. No further rules in this brain.
Expectation (prior): ~0 edge. A daily, single-asset time series has far less data than the
  Gu-Kelly-Xiu cross-section; most single features already failed in BRAIN.md.
Reporting: engine.evaluate table, out-of-sample AUC / accuracy, logit mean standardized
  coefficients, GBM permutation importance (final model, on its own training data).
"""
import os, sys, json, warnings
import numpy as np, pandas as pd
warnings.filterwarnings("ignore")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..")))
from engine import load, evaluate, table, D
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score
from sklearn.inspection import permutation_importance

idx = load("SPY").index
idx = idx[idx >= "2008-01-01"]
C = {s: load(s).reindex(idx).ffill() for s in ["USO", "USL", "XLE", "SPY", "TLT", "GLD", "VIX", "OVX"]}
C["DXY"] = load("DX-Y.NYB").reindex(idx, method="ffill").shift(1)
V = {s: load(s, "Volume").reindex(idx) for s in ["USO", "XLE", "SPY"]}

F = pd.DataFrame(index=idx)
for s in ["USO", "XLE", "SPY", "TLT", "GLD", "DXY"]:
    lp = np.log(C[s])
    for h in [1, 5, 21, 63]:
        F[f"{s}_r{h}"] = lp.diff(h)
for s in ["VIX", "OVX"]:
    F[f"{s}_lvl"] = np.log(C[s]); F[f"{s}_d5"] = np.log(C[s]).diff(5)
F["carry21"] = np.log(C["USO"]).diff(21) - np.log(C["USL"]).diff(21)
L = pd.read_csv(os.path.join(D, "COT_legacy_WTI.csv"), index_col=0, parse_dates=True)
G = pd.read_csv(os.path.join(D, "COT_disagg_WTI.csv"), index_col=0, parse_dates=True)
def usable(sig):
    out = pd.Series(np.nan, index=idx)
    for d, v in sig.dropna().items():
        nxt = idx[idx > d + pd.Timedelta(days=3)]
        if len(nxt): out[nxt[0]] = v
    return out.ffill()
F["cot_comm_d1"] = usable(((L.comm_positions_long_all - L.comm_positions_short_all) / L.open_interest_all).diff())
F["cot_mm_d1"] = usable(((G.m_money_positions_long_all - G.m_money_positions_short_all) / G.open_interest_all).diff())
for s in ["USO", "XLE", "SPY"]:
    lv = np.log(V[s].replace(0, np.nan))
    F[f"{s}_volz"] = (lv - lv.rolling(63).mean()) / lv.rolling(63).std()
for k, d in enumerate(["Mon", "Tue", "Wed", "Thu", "Fri"]):
    F[f"dow_{d}"] = (idx.dayofweek == k).astype(float)
F = F.dropna()
FEATS = list(F.columns)
print(f"features: {len(FEATS)}, rows {len(F)}, {F.index[0].date()} .. {F.index[-1].date()}")


def make_model(kind):
    if kind == "LOGIT":
        return make_pipeline(StandardScaler(), LogisticRegression(C=0.05, max_iter=2000))
    return HistGradientBoostingClassifier(max_iter=150, learning_rate=0.03, max_depth=3, min_samples_leaf=100,
                                          l2_regularization=1.0, early_stopping=False, random_state=0)


def walk_forward(kind, sym, h, shuffle_seed=None, keep=False):
    px = C[sym]
    fwd = np.log(px).shift(-h) - np.log(px)        # label of row t uses t..t+h
    y = (fwd > 0).astype(float).where(fwd.notna())
    X = F; yy = y.reindex(X.index)
    p = pd.Series(np.nan, index=X.index); coefs = []; last = None
    for yr in range(2011, X.index[-1].year + 1):
        cut = pd.Timestamp(f"{yr-1}-12-31")
        pos_cut = X.index.searchsorted(cut, side="right")      # rows < pos_cut are <= cut
        tr_end = pos_cut - h - 5                                # purge h + embargo 5
        Xtr, ytr = X.iloc[:tr_end], yy.iloc[:tr_end]
        ok = ytr.notna(); Xtr, ytr = Xtr[ok], ytr[ok].values
        if shuffle_seed is not None:
            ytr = np.random.default_rng(shuffle_seed * 1000 + yr).permutation(ytr)
        m = make_model(kind).fit(Xtr.values, ytr)
        te = (X.index.year == yr)
        p[te] = m.predict_proba(X[te].values)[:, 1]
        if kind == "LOGIT":
            coefs.append(m[-1].coef_[0])
        last = (m, Xtr, ytr)
    pos = pd.Series(0.0, index=p.index)
    pos[p - 0.5 >= 0.02] = 1.0; pos[p - 0.5 <= -0.02] = -1.0
    pos[p.isna()] = 0.0
    return p, pos, yy, (np.mean(coefs, axis=0) if coefs else None), (last if keep else None)


def oos_stats(p, y):
    m = (p.index >= "2014-01-01") & p.notna() & y.notna()
    pm, ym = p[m], y[m]
    return dict(auc_post=float(roc_auc_score(ym, pm)), acc_post=float(((pm > 0.5) == (ym > 0.5)).mean()),
                base_up=float(ym.mean()), frac_long=float((pm - 0.5 >= 0.02).mean()), frac_short=float((pm - 0.5 <= -0.02).mean()))


if __name__ == "__main__":
    rows, extra, imp = [], {}, {}
    for kind in ["LOGIT", "GBM"]:
        for sym in ["USO", "XLE", "SPY"]:
            ret = C[sym].pct_change()
            for h in [1, 5]:
                name = f"{kind} {sym} h{h}"
                p, pos, y, coef, last = walk_forward(kind, sym, h, keep=(kind == "GBM"))
                rows.append(evaluate(name, pos, ret, 5, start="2011-01-01"))
                extra[name] = oos_stats(p, y)
                if coef is not None:
                    imp[name] = pd.Series(coef, index=FEATS)
                else:
                    m, Xtr, ytr = last
                    pi = permutation_importance(m, Xtr.values, ytr, scoring="roc_auc", n_repeats=3, random_state=0)
                    imp[name] = pd.Series(pi.importances_mean, index=FEATS)
                # shuffled-label control, 1 seed
                ps, poss, _, _, _ = walk_forward(kind, sym, h, shuffle_seed=1)
                rows.append(evaluate("CTRL-shuf " + name, poss, ret, 5, start="2011-01-01"))
                extra["CTRL-shuf " + name] = oos_stats(ps, y)
                print(name, "done", flush=True)
    print(table(rows))
    print(pd.DataFrame(extra).T.round(3).to_string())
    # luck distribution: 20 shuffled seeds, h5, all instruments (post-2014 Sharpe and t)
    dist = []
    for kind in ["LOGIT", "GBM"]:
        for sym in ["USO", "XLE", "SPY"]:
            ret = C[sym].pct_change()
            for s in range(2, 12):
                _, poss, _, _, _ = walk_forward(kind, sym, 5, shuffle_seed=s)
                e = evaluate(f"shuf{s}", poss, ret, 5, start="2011-01-01", n_placebo=1)
                bh = evaluate("bh", pd.Series(1.0, index=ret.index), ret, 5, start="2011-01-01", n_placebo=1)
                dist.append(dict(kind=kind, sym=sym, seed=s, post=e["post"], t=e["t_post"], excess_vs_bh=e["post"] - bh["post"]))
    dist = pd.DataFrame(dist)
    print("\nShuffled-label luck distribution (h5, 10 seeds each):")
    print(dist.groupby(["kind", "sym"])[["post", "t", "excess_vs_bh"]].describe().round(2).to_string())
    print("max t over all shuffles: %.2f, share with t>=2: %.2f" % (dist.t.max(), (dist.t >= 2).mean()))
    I = pd.DataFrame(imp)
    print("\nLOGIT mean standardized coefs (top |coef| per config):")
    for c in [c for c in I if c.startswith("LOGIT")]:
        s = I[c].reindex(I[c].abs().sort_values(ascending=False).index)[:6]
        print(c, "; ".join(f"{k} {v:+.3f}" for k, v in s.items()))
    print("\nGBM permutation importance (AUC drop, final model on its training data):")
    for c in [c for c in I if c.startswith("GBM")]:
        s = I[c].sort_values(ascending=False)[:6]
        print(c, "; ".join(f"{k} {v:.3f}" for k, v in s.items()))
    out = pd.DataFrame(rows).set_index("rule")
    out = out.join(pd.DataFrame(extra).T)
    out.to_csv(os.path.join(HERE, "study1_results.csv"))
    I.to_csv(os.path.join(HERE, "study1_importance.csv"))
    dist.to_csv(os.path.join(HERE, "study1_shuffle_dist.csv"))
