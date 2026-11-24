"""Study 4 (pre-registered 2026-11-24, after studies 1-3, before running): residual reversal.
Blitz, Huij, Lansdorp & Verbeek (2013, "Short-term residual reversal"): reversal on factor-model
residuals, scaled by residual volatility, is stronger and less risky than raw reversal.
Factor model here (no FF data offline): each stock on SPY and its own sector's equal-weight return
excluding itself, rolling 252-day OLS (betas from the window ending t-1, so known at close t).
Residual e_t = r_t - a - b_m*SPY_t - b_s*SECT_t.
 R8 weekly residual reversal: at each week's last close, signal = -(sum of last 5 daily residuals)
    / std of residuals over the past 252 days; linear dollar-neutral weights; held one week.
 R9 R8 only when VIX at the rebalance close > 25 (the Nagel regime threshold fixed in study 2
    before results were seen; NOT re-tuned. Caveat: study 2 post-2014 results were already
    seen, so R9 is not independent of R5).
Costs, benchmark (SPY), placebo, start as before.
Expectation: R8 gross IS > R3 gross IS; post-2014 still weak in calm markets per study 2.
"""
from lib import *
m = spy
R = ret
res = pd.DataFrame(index=px.index, columns=px.columns, dtype=float)
for c in px.columns:
    peers = [k for k in px.columns if SECT[k] == SECT[c] and k != c]
    s = R[peers].mean(axis=1)
    y = R[c]
    df = pd.concat([y, m, s], axis=1, keys=["y", "m", "s"]).dropna()
    L = 252
    mu = df.rolling(L).mean()
    cxx = df.rolling(L).cov().unstack()
    vmm, vss, vms = cxx[("m", "m")], cxx[("s", "s")], cxx[("m", "s")]
    vym, vys = cxx[("y", "m")], cxx[("y", "s")]
    det = vmm * vss - vms ** 2
    bm = (vss * vym - vms * vys) / det
    bs = (vmm * vys - vms * vym) / det
    a = mu["y"] - bm * mu["m"] - bs * mu["s"]
    e = df["y"] - (a.shift(1) + bm.shift(1) * df["m"] + bs.shift(1) * df["s"])
    res[c] = e
rv = res.rolling(252, min_periods=200).std()
sig = -(res.rolling(5).sum() / rv)
we = week_ends(px.index)
base = neutral(sig).where(sig.notna(), 0)
R8 = hold(base, we)
R9 = hold(base.mul((vix > 25).astype(float), axis=0), we)
rows = []
for k, w in {"R8 weekly residual reversal": R8, "R9 R8 only if VIX>25": R9}.items():
    o, r = evaluate_w(k, w); rows.append(o)
    p = r.loc[START:]
    print(k, "net % by year:", (p.groupby(p.index.year).sum() * 100).round(1).to_dict())
print("stocks with signal at START:", int(sig.loc[START:].iloc[0].notna().sum()))
show(rows).to_csv("study4_results.csv")
