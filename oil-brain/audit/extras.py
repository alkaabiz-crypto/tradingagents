"""Extra checks: alpha vs buy&hold, D per-day-rank returns, C 2026 detail. Run: python extras.py > extras.txt"""
import numpy as np, pandas as pd
from audit import load, pnl, ret_n, build_C, month_end_pos, metrics

def alpha(r, b, ann):
    df = pd.concat([r, b], axis=1).dropna(); y, x = df.iloc[:, 0].values, df.iloc[:, 1].values
    X = np.c_[np.ones(len(x)), x]; beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    e = y - X @ beta; s2 = e @ e / (len(y) - 2); cov = s2 * np.linalg.inv(X.T @ X)
    return f"alpha {beta[0]*ann*100:6.1f}%/yr  t {beta[0]/np.sqrt(cov[0,0]):5.2f}  beta {beta[1]:.2f}"

for sym, sig, lab in [("BTC-USD", lambda p: (ret_n(p,28)>0)|(p>p.rolling(100).mean()), "A"), ("ETH-USD", lambda p: ret_n(p,28)>0, "B")]:
    px = load(sym); ret = px.pct_change().dropna(); first = px.index[100]
    r = pnl(sig(px).astype(float), ret, 10).loc[first:]; b = ret.loc[first:]
    for nm, a, z in [("full", None, None), ("2014-19", None, "2019"), ("2020+", "2020", None), ("2022+", "2022", None)]:
        print(lab, nm, alpha(r.loc[a:z], b.loc[a:z], 365))
    # vol-matched B&H: hold exposure-fraction of B&H
    e = sig(px).astype(float).loc[first:].mean()
    print(f"{lab} exposure {e:.2f}; vol of rule {r.std()*np.sqrt(365):.2f} vs B&H {b.std()*np.sqrt(365):.2f}")

hyg, lqd, uso = load("HYG"), load("LQD"), load("USO"); ret = uso.pct_change().dropna()
pos = build_C(hyg, lqd, ret.index).fillna(0); first = pos[pos != 0].index[0]
r = pnl(pos, ret, 5).loc[first:]; b = ret.loc[first:]
for nm, a, z in [("full", None, None), ("2014-19", "2014", "2019"), ("2020+", "2020", None), ("ex 2020 & 2026", None, None)]:
    if nm.startswith("ex"):
        m = ~r.index.year.isin([2020, 2026]); print("C", nm, alpha(r[m], b[m], 252), "Sh %.2f t %.2f" % (metrics(r[m],252)["sh"], metrics(r[m],252)["t"]))
    else:
        print("C", nm, alpha(r.loc[a:z], b.loc[a:z], 252))
print("C 2026 by month rule/USO %:", "  ".join(f"{m}:{(1+g).prod()*100-100:.0f}/{(1+b.loc[g.index]).prod()*100-100:.0f}" for m, g in r.loc["2026"].groupby(r.loc["2026"].index.month)))
print("C position during Mar-Apr 2026:", pos.loc["2026-02-20":"2026-05-01"].resample("W-FRI").last().to_dict())
m = r.index.year.isin(range(2010, 2020)); print("C 2010-2019 only:", metrics(r[m], 252))

ief = load("IEF"); ret = ief.pct_change().dropna()
per = ret.index.to_period("M"); s = ret.index.to_series()
rk_end = s.groupby(per).rank(method="first", ascending=False).values  # 1 = last trading day
rk_st = s.groupby(per).rank(method="first").values
print("\nD IEF mean return (bp) on day by rank-from-month-end (1=last day of month), by period")
for nm, a, z in [("2002-13", "2002", "2013"), ("2014-19", "2014", "2019"), ("2020+", "2020", None)]:
    rr = ret.loc[a:z]; k = pd.Series(rk_end, index=ret.index).loc[a:z]; k2 = pd.Series(rk_st, index=ret.index).loc[a:z]
    row = {f"E{i}": rr[k == i].mean()*1e4 for i in range(5, 0, -1)}
    row.update({f"S{i}": rr[k2 == i].mean()*1e4 for i in range(1, 3)}); row["all"] = rr.mean()*1e4
    print(" ", nm, "  ".join(f"{k}:{v:5.2f}" for k, v in row.items()))
p = month_end_pos(ret.index, 3)
g = pnl(p, ret, 0)
print("D gross (0 cost):", {k: round(v, 3) for k, v in metrics(g, 252).items()})
print("D breakeven cost per side (bp): %.1f" % (g[g != 0].sum() / (p.diff().abs().sum()) * 1e4))
print("D alpha vs IEF B&H:", alpha(pnl(p, ret, 5), ret, 252))
shy = load("SHY").pct_change().dropna(); ps = month_end_pos(shy.index, 3)
print("SHY k3 gross:", {k: round(v, 3) for k, v in metrics(pnl(ps, shy, 0), 252).items()})
