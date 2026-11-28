"""Energy stocks vs oil: does the oil-hedged "residual" snap back or keep going? (pre-registered 2026-11-28, before
any run; idea queue item 5 in BRAIN.md, "energy equities vs oil, beta-hedged", aimed at small frequent trades).
Why: oil stocks move with crude; when a stock moves much more or less than oil explains, the gap may close in 1-3
days (liquidity / overreaction, Lehmann 1990, Lo & MacKinlay 1990 short-term reversal; pairs trading, Gatev, Goetzmann
& Rouwenhorst 2006) or keep going (slow diffusion of firm news, residual momentum, Blitz, Huij & Martens 2011).
Markets: XOM, CVX, COP, OXY, XLE, XOP (6). Hedge: USO. Adjusted daily closes (dividends included).
Residual: e_t = r_stock - beta * r_USO, beta = 60-day rolling OLS from PAST days only; z = e / 60-day sd of e.
Trade = the hedged pair (long stock + short beta*USO, or the mirror), entered AT the signal close, held H closes.
Rules (5) x sides (2: long the residual after a fall / short it after a rise for R1-R2; follow the sign for M1) :
  R1 1-day reversal:  z_t < -2 -> long residual (mirror: z_t > +2 -> short), hold 1 day
  R2 1-day reversal:  same signal, hold 3 days
  R3 5-day reversal:  5-day summed residual / (sd*sqrt5) < -1.5 -> long (mirror > +1.5), hold 1 day
  R4 5-day reversal:  same, hold 3 days
  M1 20-day residual momentum: sum of 20-day residual > 0 -> long residual (mirror < 0 -> short), hold 5 days,
     re-entered every 5 days (non-overlapping)
  10 rules-with-side x 6 markets = 60 systems. Luck bar: Sidak 1% for 60.
Costs per trade: stock CFD round trip (costs.py STOCK_CFD, 10 bp) + beta x USOIL round trip (5 bp); swap-free.
Periods by entry: IS < 2014, OOS 2014-2019, HOLDOUT 2020+.
PASS (fixed): mean net > 0 in OOS AND HOLDOUT; > 0 at 2x cost post-2014; post-2014 t >= Sidak bar (non-overlapping
trades only: a new entry only after the previous one exits); random-entry placebo (same number of entries post-2014,
random days, same hold, 1000 runs, seed 128) p <= 0.01; then a neighbour check (z 1.5/2.5, beta window 40/90:
>= 70% of neighbours also pass the basic gates) before any paper sleeve. Report the deflated Sharpe (E6).
Research, not financial advice.      python3 oil-brain/smallwins/energy_residual.py
"""
import os, sys, math
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); OB = os.path.dirname(HERE)
sys.path.insert(0, OB)
import costs

MARKETS = ["XOM", "CVX", "COP", "OXY", "XLE", "XOP"]
RULES = ["R1", "R2", "R3", "R4", "M1"]


def sidak_t(m, alpha=0.01):
    p = 1 - (1 - alpha) ** (1 / m); lo, hi = 0.0, 10.0
    for _ in range(60):
        mid = (lo + hi) / 2; lo, hi = (mid, hi) if math.erfc(mid / math.sqrt(2)) > p else (lo, mid)
    return hi


def tstat(x):
    x = np.asarray(x); return x.mean() / (x.std(ddof=1) / np.sqrt(len(x))) if len(x) > 2 else np.nan


_cache = {}
def closes(sym):
    if sym not in _cache:
        import yfinance as yf
        c = yf.Ticker(sym).history(period="max", auto_adjust=True).Close.dropna()
        c.index = c.index.tz_localize(None).normalize(); _cache[sym] = c[~c.index.duplicated()]
    return _cache[sym]


def frame(sym, win=60):
    s, u = closes(sym), closes("USO"); df = pd.concat([s, u], axis=1, keys=["s", "u"]).dropna()
    r = df.pct_change().dropna()
    beta = (r.s.rolling(win).cov(r.u) / r.u.rolling(win).var()).shift(1)        # past days only
    e = r.s - beta * r.u; sd = e.rolling(win).std().shift(1)
    f = pd.DataFrame({"rs": r.s, "ru": r.u, "beta": beta, "e": e, "z": e / sd,
                      "z5": e.rolling(5).sum() / (sd * np.sqrt(5)), "m20": e.rolling(20).sum()}).dropna()
    return f


def trades(f, rule, side, zk=None):
    """Entry flags (bool array) and hold. side +1 = long residual after a fall / follow up-momentum."""
    if rule in ("R1", "R2"):
        k = zk or 2.0; sig = (f.z < -k) if side > 0 else (f.z > k); hold = 1 if rule == "R1" else 3
    elif rule in ("R3", "R4"):
        k = zk or 1.5; sig = (f.z5 < -k) if side > 0 else (f.z5 > k); hold = 1 if rule == "R3" else 3
    else:
        sig = (f.m20 > 0) if side > 0 else (f.m20 < 0); hold = 5
    return sig.values, hold


def run(f, flags, hold, side, cost_mult=1.0):
    """Non-overlapping trades: pair return over the next `hold` days with beta fixed at entry."""
    rs, ru, b = f.rs.values, f.ru.values, f.beta.values; out, idx, i, n = [], [], 0, len(f)
    while i < n - hold:
        if flags[i]:
            g = np.prod(1 + rs[i + 1:i + 1 + hold]) - 1 - b[i] * (np.prod(1 + ru[i + 1:i + 1 + hold]) - 1)
            c = cost_mult * (costs.SPREAD_BP["STOCK_CFD"] + abs(b[i]) * costs.SPREAD_BP["USOIL"]) / 1e4
            out.append(side * g - c); idx.append(f.index[i]); i += hold
        else:
            i += 1
    return pd.Series(out, index=pd.DatetimeIndex(idx), dtype=float)


def evaluate(f, rule, side, zk=None):
    flags, hold = trades(f, rule, side, zk)
    r = run(f, flags, hold, side); r2 = run(f, flags, hold, side, 2.0); post = r[r.index >= "2014-01-01"]
    seg = lambda a, b: r[(r.index >= a) & (r.index < b)].mean() * 1e4 if len(r[(r.index >= a) & (r.index < b)]) else np.nan
    row = dict(n_post=len(post), per_year=len(post) / 12.9, IS_bp=seg("1900", "2014-01-01"), OOS_bp=seg("2014-01-01", "2020-01-01"),
               HO_bp=seg("2020-01-01", "2100"), post_bp=post.mean() * 1e4 if len(post) else np.nan,
               post2x_bp=r2[r2.index >= "2014-01-01"].mean() * 1e4 if len(post) else np.nan,
               t=tstat(post), win=float((post > 0).mean()) if len(post) else np.nan)
    row["basic"] = bool(row["OOS_bp"] > 0 and row["HO_bp"] > 0 and row["post2x_bp"] > 0)
    return row, post, hold


def main():
    N = len(MARKETS) * len(RULES) * 2; bar = sidak_t(N); rng = np.random.default_rng(128); rows = []
    print(f"{N} systems (5 rules x 2 sides x 6 markets), luck bar t >= {bar:.2f}")
    for sym in MARKETS:
        f = frame(sym); fp = f[f.index >= "2014-01-01"]
        for rule in RULES:
            for side in (1, -1):
                row, post, hold = evaluate(f, rule, side); row.update(sym=sym, rule=rule, side="long" if side > 0 else "short",
                                                                     placebo_p=np.nan, neighbours=np.nan)
                if row["basic"] and row["t"] >= bar and len(post) > 10:
                    sims = []
                    for _ in range(1000):
                        fl = np.zeros(len(fp), bool); fl[rng.choice(len(fp) - hold, size=len(post), replace=False)] = True
                        sims.append(run(fp, fl, hold, side).mean())
                    row["placebo_p"] = float((np.array(sims) >= post.mean()).mean())
                    nb = []
                    for zk, win in ([(None, 40), (None, 90)] + ([(1.5 if rule in "R1R2" else 1.0, 60), (2.5 if rule in "R1R2" else 2.0, 60)] if rule != "M1" else [])):
                        nb.append(evaluate(frame(sym, win), rule, side, zk)[0]["basic"])
                    row["neighbours"] = float(np.mean(nb))
                rows.append(row)
    df = pd.DataFrame(rows)
    df["PASS"] = df.basic & (df.t >= bar) & (df.placebo_p <= 0.01) & (df.neighbours >= 0.7)
    df.to_csv(os.path.join(HERE, "energy_residual_results.csv"), index=False)
    pd.set_option("display.width", 220)
    cols = ["sym", "rule", "side", "n_post", "per_year", "IS_bp", "OOS_bp", "HO_bp", "post_bp", "post2x_bp", "t", "win",
            "basic", "placebo_p", "neighbours", "PASS"]
    print(df.sort_values("t", ascending=False)[cols].head(20).round(2).to_string(index=False))
    print(f"\nbasic gates passed: {int(df.basic.sum())} of {N}; t >= bar: {int((df.t >= bar).sum())}")
    print("PASS:", df[df.PASS][["sym", "rule", "side"]].values.tolist() or "none")


if __name__ == "__main__":
    main()
