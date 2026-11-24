"""Study 11 (pre-registered 2026-11-24 14:55 UTC, before running): overnight -> daytime in oil.
Sources: Energy Economics 2017 (inventory announcements, intraday CL): the previous night's return
predicts the day's return; Wen et al. (2021, Econ. Modelling) on USO: the overnight component carries
the signal (continuation); INE China (Econ. Modelling 2021): night predicts day NEGATIVELY (reversal).
Daily USO and XLE Open/Close. Signal known at the open of day t: n_t = open_t / close_{t-1} - 1.
 N1 continuation: trade sign(n_t) from open_t to close_t.
 N2 reversal: trade -sign(n_t).
 N3 continuation, only when |n_t| > its 60-day median (big gaps).
Each trade opens and closes the same day: 2 sides x 5 bp (USO/XLE spreads) = 10 bp a day traded.
Gates as engine.py (IS to 2013, OOS 2014-19, HOLDOUT 2020+, t >= 2 post-2014, placebo = circular
shift of the signal, positive at 2x cost); a tournament winner also needs t > 4.19.
"""
import numpy as np, pandas as pd
from engine import load, sharpe, tstat
rows = []
for sym in ("USO", "XLE"):
    df = load(sym, col=None)
    n = df.Open / df.Close.shift(1) - 1; oc = df.Close / df.Open - 1
    big = n.abs() > n.abs().rolling(60).median().shift(1)
    rules = {"N1 continuation": np.sign(n), "N2 reversal": -np.sign(n), "N3 continuation, big gaps": np.sign(n).where(big, 0)}
    rng = np.random.default_rng(11)
    for name, sig in rules.items():
        sig = sig.fillna(0)
        def net(s, c=10): return s * oc - s.abs() * c / 1e4
        r = net(sig); post = r.loc["2014":]
        real = sharpe(post); vals = sig.values; beats = 0
        for _ in range(300):
            k = int(rng.integers(len(vals) // 10, len(vals) - len(vals) // 10))
            beats += sharpe(net(pd.Series(np.roll(vals, k), index=sig.index)).loc["2014":]) < real
        pp = 1 - beats / 300
        g = [sharpe(r.loc["2014":"2019"]) > 0.3, sharpe(r.loc["2020":]) > 0.3, tstat(post) >= 2, pp <= 0.05,
             net(sig, 20).loc["2014":].sum() > 0, real > sharpe(oc.loc["2014":])]
        rows.append(dict(rule=f"{name} {sym}", IS=sharpe(r.loc[:"2013"]), OOS=sharpe(r.loc["2014":"2019"]),
                         HOLDOUT=sharpe(r.loc["2020":]), post=real, gross_post=sharpe((sig * oc).loc["2014":]),
                         t_post=tstat(post), placebo_p=pp, verdict="PASS" if all(g) else f"FAIL ({6 - sum(g)} of 6)"))
print(pd.DataFrame(rows).set_index("rule").round(2).to_string())
