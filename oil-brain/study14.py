"""Study 14 (pre-registered 2026-11-24 ~17:00 UTC, before running): independent check of another chat's findings.
Rules exactly as that chat described them; engine.py gates (IS to 2013, OOS 2014-19, HOLDOUT 2020+; crypto
uses its own split: IS 2014-18, OOS 2019-21, HOLDOUT 2022+). 5 bp per unit of turnover (10 bp crypto).
 V1-V3 volatility control: each month-end hold weight = min(1, 15% / realized vol) in QQQ / SPY / GLD, rest cash
       (realized vol = 63-day daily std x sqrt(252)). Benchmark: buy and hold the same fund.
 C1-C2 crypto weekly trend: weight = 0.5 x [price > price 4 weeks ago] + 0.5 x [price > price 8 weeks ago],
       rebalanced weekly; C1b/C2b also x min(1, 60% / realized vol). BTC and ETH. Benchmark: buy and hold.
 P1 Permanent Portfolio 25% SPY/TLT/GLD/SHY, P2 inverse-vol risk parity SPY/TLT/GLD, P3 minimum variance
       SPY/TLT/GLD (long-only, 252-day covariance) -- all monthly; compared with SPY and 60/40 SPY/IEF
       (descriptive: Sharpe, CAGR, max drawdown by period; these are allocations, not timing rules).
 D1 monthly DCA of $100 into SPY, USO and BNO from 2011-01: money in, final value, money-weighted return.
 M1 10-stock momentum: each month-end hold the 10 of ~110 large US stocks with the best 12-1 month return,
       equal weight, 10 bp per side; vs the equal-weight 110 (same survivorship bias) and SPY.
"""
import os, numpy as np, pandas as pd
from engine import load, evaluate, table, sharpe, tstat
B = os.path.dirname(os.path.abspath(__file__))


def px(name, folder="data"):
    p = os.path.join(B, folder, name + ".csv")
    s = pd.read_csv(p, index_col=0, parse_dates=True)["Close"]
    s.index = pd.to_datetime(s.index).tz_localize(None).normalize()
    return s[~s.index.duplicated()]


def month_end_weights(w, idx):
    me = idx.to_series().groupby(idx.to_period("M")).last().values
    return w.reindex(me).reindex(idx).ffill().fillna(0)


rows = []
for sym in ["QQQ", "SPY", "GLD"]:
    p = px(sym); r = p.pct_change(); vol = r.rolling(63).std() * np.sqrt(252)
    w = month_end_weights((0.15 / vol).clip(upper=1), p.index)
    rows.append(evaluate(f"V vol-control 15% {sym}", w, r, start="2005-01-01"))
for sym in ["BTC-USD", "ETH-USD"]:
    p = px(sym, "brains/crypto/data"); r = p.pct_change(); vol = r.rolling(30).std() * np.sqrt(365)
    sig = 0.5 * (p > p.shift(28)).astype(float) + 0.5 * (p > p.shift(56)).astype(float)
    wk = lambda x: x.where(p.index.day_of_week == 6).ffill().fillna(0)
    for tag, w in [("", wk(sig)), (" + vol 60%", wk(sig * (0.6 / vol).clip(upper=1)))]:
        rows.append(evaluate(f"C weekly trend {sym}{tag}", w, r, cost_bps=10, start="2015-01-01"))
print(table(rows))
print("(crypto rows use the engine's fixed periods; see the split below)")
for sym in ["BTC-USD", "ETH-USD"]:
    p = px(sym, "brains/crypto/data"); r = p.pct_change()
    sig = 0.5 * (p > p.shift(28)).astype(float) + 0.5 * (p > p.shift(56)).astype(float)
    w = sig.where(p.index.day_of_week == 6).ffill().fillna(0)
    pl = w.shift(1) * r - w.diff().abs().shift(1).fillna(0) * 10e-4
    for a, z in [("2015", "2018"), ("2019", "2021"), ("2022", "2026")]:
        x, b = pl.loc[a:z], r.loc[a:z]
        dd = lambda s: ((1 + s.fillna(0)).cumprod() / (1 + s.fillna(0)).cumprod().cummax() - 1).min()
        print(f"  {sym} {a}-{z}: trend Sharpe {x.mean()/x.std()*np.sqrt(365):.2f} maxDD {dd(x):.0%} | hold Sharpe {b.mean()/b.std()*np.sqrt(365):.2f} maxDD {dd(b):.0%}")

# Allocations
pr = pd.DataFrame({k: px(k) for k in ["SPY", "TLT", "GLD"]}).join(px("SHY", "brains/macro/data").rename("SHY")).join(
    px("IEF", "brains/macro/data").rename("IEF")).dropna()
R = pr.pct_change().fillna(0)
me = pr.index.to_series().groupby(pr.index.to_period("M")).last().values


def run_alloc(wfun):
    w = pd.DataFrame(index=pr.index, columns=R.columns, dtype=float)
    for d in me:
        w.loc[d] = wfun(d)
    w = w.ffill().fillna(0)
    turn = w.diff().abs().sum(axis=1)
    return (w.shift(1) * R).sum(axis=1) - turn.shift(1).fillna(0) * 5e-4


three = ["SPY", "TLT", "GLD"]
def ivol(d):
    v = R.loc[:d, three].tail(252).std(); w = (1 / v) / (1 / v).sum(); return w.reindex(R.columns).fillna(0)
def minvar(d):
    C = R.loc[:d, three].tail(252).cov().values
    best, bw = 9, None
    for a in np.arange(0, 1.01, 0.05):
        for b in np.arange(0, 1.01 - a, 0.05):
            x = np.array([a, b, 1 - a - b]); v = x @ C @ x
            if v < best: best, bw = v, x
    return pd.Series(bw, index=three).reindex(R.columns).fillna(0)
A = {"SPY": R.SPY, "60/40 SPY/IEF": run_alloc(lambda d: pd.Series({"SPY": .6, "IEF": .4}).reindex(R.columns).fillna(0)),
     "P1 Permanent 25x4": run_alloc(lambda d: pd.Series({"SPY": .25, "TLT": .25, "GLD": .25, "SHY": .25}).reindex(R.columns).fillna(0)),
     "P2 risk parity SPY/TLT/GLD": run_alloc(ivol), "P3 min variance SPY/TLT/GLD": run_alloc(minvar)}
print("\nAllocations (monthly rebalance, 5 bp):")
for k, x in A.items():
    x = x.loc["2008-01-01":]
    line = []
    for a, z in [("2008", "2013"), ("2014", "2019"), ("2020", "2026"), ("2008", "2026")]:
        s = x.loc[a:z]; eq = (1 + s).cumprod()
        line.append(f"{a}-{z[2:]}: Sh {s.mean()/s.std()*np.sqrt(252):.2f} CAGR {eq.iloc[-1]**(252/len(s))-1:+.1%} DD {(eq/eq.cummax()-1).min():.0%}")
    print(f"  {k:28} " + " | ".join(line))

# DCA
print("\nMonthly DCA of $100 from 2011-01:")
for sym in ["SPY", "USO", "BNO"]:
    p = px(sym).loc["2011-01-01":]; buys = p.groupby(p.index.to_period("M")).head(1)
    units = (100 / buys).sum(); invested = 100 * len(buys); value = units * p.iloc[-1]
    cf = np.array([-100.0] * len(buys)); t = np.array([(d - buys.index[0]).days / 365 for d in buys.index]); T = (p.index[-1] - buys.index[0]).days / 365
    lo, hi = -0.99, 1.0
    for _ in range(100):
        m = (lo + hi) / 2; f = (cf * (1 + m) ** (T - t)).sum() + value
        lo, hi = (lo, m) if f < 0 else (m, hi)
    print(f"  {sym}: invested ${invested:,.0f}, now ${value:,.0f}, money-weighted return {m:+.1%} a year")

# 10-stock momentum
cl = pd.read_csv(os.path.join(B, "brains/statarb/data/close.csv"), index_col=0, parse_dates=True)
cl.index = pd.to_datetime(cl.index).tz_localize(None).normalize()
rr = cl.pct_change(); mom = cl.shift(21) / cl.shift(252) - 1
mends = cl.index.to_series().groupby(cl.index.to_period("M")).last().values
W = pd.DataFrame(0.0, index=cl.index, columns=cl.columns)
for d in mends:
    m = mom.loc[d].dropna()
    if len(m) >= 50: W.loc[d] = 0; W.loc[d, m.nlargest(10).index] = 0.1
W.loc[~W.index.isin(mends)] = np.nan
W = W.ffill().fillna(0)
mpl = (W.shift(1) * rr.fillna(0)).sum(axis=1) - W.diff().abs().sum(axis=1).shift(1).fillna(0) * 10e-4
ew = rr.mean(axis=1); spy = px("SPY").pct_change().reindex(cl.index)
print(f"\n10-stock momentum ({cl.shape[1]} large US stocks, {cl.index[0].date()}-{cl.index[-1].date()}):")
for k, x in [("M1 top-10 momentum", mpl), ("equal-weight universe", ew), ("SPY", spy), ("M1 minus equal-weight", mpl - ew)]:
    s = [f"{a}-{z[2:]}: Sh {x.loc[a:z].mean()/x.loc[a:z].std()*np.sqrt(252):.2f}" for a, z in [("2006", "2013"), ("2014", "2019"), ("2020", "2026")]]
    print(f"  {k:24} " + " | ".join(s) + f" | t post-2014 {tstat(x.loc['2014':]):.2f}")
