"""Study 5 (pre-registered 2026-11-24, after study 4, before running): is F3 (USO long/short on HY-IG credit
21d) robust, and is it just oil momentum in disguise? F3 failed OOS (0.10) and t (1.97), so it cannot win;
this asks only whether it deserves a forward test.
 F3a same rule with a 10-day credit lookback; F3b with 63 days (neighbours fixed a priori, both counted as rules).
Diagnostics (not rules): agreement of F3's sign with sign(USO 21d return); F3 Sharpe on the days the two
disagree (the part not explained by oil's own trend); F3 without the two crash windows used in study 3
(2014-07..2016-02, 2020-01-15..2020-06).
"""
import numpy as np, pandas as pd
from lib import ld, evaluate, table, sharpe, tstat
from engine import pnl
uso = ld("USO"); ru = uso.pct_change()
def at(sig, idx, freq="W"):
    sig = sig.reindex(idx).ffill(); ends = idx.to_series().groupby(idx.to_period(freq)).last().values
    return sig.loc[ends].reindex(idx).ffill()
def cred(k): return ld("HYG").pct_change(k) - ld("LQD").pct_change(k)
rows = []
for k, nm in [(10, "F3a"), (63, "F3b")]:
    c = cred(k); rows.append(evaluate(f"{nm} USO long/short on HY-IG credit {k}d, weekly", at(np.sign(c).where(c.notna()), ru.index), ru, start="2007-06-01"))
print(table(rows))
c = cred(21); p = at(np.sign(c).where(c.notna()), ru.index).loc["2007-06-01":].fillna(0)
m = at(np.sign(uso.pct_change(21)), ru.index).loc["2007-06-01":].fillna(0)
r = pnl(p, ru.loc["2007-06-01":], 5)
agree = (p == m)
print("F3 agrees with USO 21d momentum sign on %.0f%% of days" % (100 * agree.mean()))
dis = r[~agree.shift(1).fillna(True).astype(bool)]
for nm, x in [("disagree days", dis), ("agree days", r[agree.shift(1).fillna(False).astype(bool)])]:
    for per, a, b in [("IS", None, "2013"), ("post", "2014", None)]:
        y = x.loc[a:b]; print(f"F3 on {nm} {per}: Sharpe {sharpe(y):.2f}, t {tstat(y):.2f}, n {len(y)}")
crash = ((r.index >= "2014-07-01") & (r.index <= "2016-02-29")) | ((r.index >= "2020-01-15") & (r.index <= "2020-06-30"))
post = r.loc["2014":]; pc = r[~crash].loc["2014":]
print("F3 post-2014 Sharpe %.2f; without crash windows %.2f (t %.2f)" % (sharpe(post), sharpe(pc), tstat(pc)))
print("F3 by year %:", (r.groupby(r.index.year).sum() * 100).round(1).to_dict())
