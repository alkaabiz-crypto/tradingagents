"""Study 2 (macro brain), pre-registered 2026-11-24 after study 1 (0 PASS of 9), BEFORE running.

Part A (descriptive, no rule): yearly correlation of daily DXY and USO returns, to check the
ECB 2024 claim that the oil-dollar link weakened / changed sign as the US became a net exporter.

Part B (descriptive, IS ONLY 2007-06..2013): monthly predictive regressions of next-month
USO, XLE, SPY return on this month's return of GLD, DBB, DXY, TLT, HYG-LQD, SPY, USO
(21 pairs; Hong-Torous-Valkanov / Rapach-Strauss-Zhou lead-lag idea). Rule M10 = the pair with
the largest IS |t|, traded long/short on the target with the IS sign, monthly. This is a
selection over 21 pairs, so its result is discounted accordingly (counted as 1 rule, flagged).

M11 Credit risk switch: hold SPY if HYG/LQD 21d relative return > 0, else IEF (benchmark SPY).
M12 Neighbour of M5: HYG/LQD 63d up -> long USO else flat.
M13 Credit -> energy equities: HYG/LQD 21d up -> long XLE else flat (energy is the largest
    high-yield sector, so credit stress should hit XLE). Benchmark XLE.
Costs 5 bp. Running total after this study: 13 rules.
"""
import numpy as np, pandas as pd
from common import engine, px, ret, monthly

START = "2007-06-01"
spy = ret("SPY"); idx = spy.dropna().index
R = {s: ret(s).reindex(idx) for s in ["USO", "XLE", "SPY", "GLD", "DBB", "TLT", "HYG", "LQD", "IEF"]}
R["DXY"] = px("DX-Y.NYB").reindex(idx).ffill().pct_change()

# (bug fix before any rule ran: dict.get default was evaluated eagerly)
# Part A
a = pd.concat([R["DXY"], R["USO"]], axis=1).dropna().loc["2007":]
print("A. yearly corr(DXY, USO) daily:")
print(a.groupby(a.index.year).apply(lambda d: round(d.iloc[:, 0].corr(d.iloc[:, 1]), 2)).to_string())

# Part B (IS only)
m = pd.DataFrame({k: (1 + v.fillna(0)).groupby(idx.to_period("M")).prod() - 1 for k, v in R.items()})
m["CREDIT"] = m["HYG"] - m["LQD"]
m = m.loc["2007-07":]
mis = m.loc[:"2013-12"]
res = []
for tgt in ["USO", "XLE", "SPY"]:
    for p in ["GLD", "DBB", "DXY", "TLT", "CREDIT", "SPY", "USO"]:
        y, x = mis[tgt].shift(-1).iloc[:-1], mis[p].iloc[:-1]
        b = np.polyfit(x, y, 1)[0]
        e = y - (b * x + (y.mean() - b * x.mean()))
        se = e.std() / (x.std() * np.sqrt(len(x)))
        res.append((tgt, p, b, b / se))
res = pd.DataFrame(res, columns=["target", "predictor", "beta", "t_IS"])
print("\nB. IS lead-lag (next-month target on this-month predictor):")
print(res.round(2).to_string(index=False))
best = res.iloc[res.t_IS.abs().idxmax()]
print("selected:", best.target, "<-", best.predictor, "sign", np.sign(best.beta))

rows = []
def ev(name, sig, r, bench=None):
    rows.append(engine.evaluate(name, monthly(sig, idx).fillna(0), r, 5, bench, START))

pmap = {"CREDIT": lambda: np.log(px("HYG") / px("LQD")), "DXY": lambda: np.log(px("DX-Y.NYB"))}
lvl = pmap[best.predictor]() if best.predictor in pmap else np.log(px(best.predictor))
lvl = lvl.reindex(idx).ffill()
# month-end to month-end change of the predictor, known at the month-end close
me = lvl.groupby(idx.to_period("M")).tail(1)
sigm = np.sign(best.beta) * np.sign(me.diff())
ev(f"M10 IS-selected {best.target}<-{best.predictor} L/S", sigm.reindex(idx), R[best.target])

credit = np.log(px("HYG") / px("LQD")).reindex(idx).ffill()
on = (credit.diff(21) > 0).astype(float)
onm = monthly(on, idx).fillna(0)
sw = onm.shift(1) * R["SPY"] + (1 - onm.shift(1)) * R["IEF"].fillna(0)
# switch evaluated as a "position 1" on the switched return stream; costs approximated by
# passing the switch path as the position on SPY would undercount IEF legs, so add costs manually:
turn = onm.diff().abs().fillna(0) * 2  # sell one, buy the other
sw_net = sw - turn.shift(1).fillna(0) * 5 / 1e4
rows.append(engine.evaluate("M11 credit switch SPY/IEF", pd.Series(1.0, index=idx),
                            sw_net.fillna(0), 0, R["SPY"], START))
ev("M12 HYG/LQD 63d up -> USO L/F", (credit.diff(63) > 0).astype(float), R["USO"])
ev("M13 HYG/LQD 21d up -> XLE L/F", on, R["XLE"])
print(); print(engine.table(rows))
pd.DataFrame(rows).to_csv("study2_results.csv", index=False)
