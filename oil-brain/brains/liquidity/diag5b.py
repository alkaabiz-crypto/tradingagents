"""Diagnostic for F3b (study 5), not a new rule: crash dependence, overlap with USO 63d momentum, by year."""
import numpy as np
from lib import ld, sharpe, tstat
from engine import pnl
uso = ld("USO"); ru = uso.pct_change()
def at(sig, idx, freq="W"):
    sig = sig.reindex(idx).ffill(); ends = idx.to_series().groupby(idx.to_period(freq)).last().values
    return sig.loc[ends].reindex(idx).ffill()
c = ld("HYG").pct_change(63) - ld("LQD").pct_change(63)
p = at(np.sign(c).where(c.notna()), ru.index).loc["2007-06-01":].fillna(0)
m = at(np.sign(uso.pct_change(63)), ru.index).loc["2007-06-01":].fillna(0)
r = pnl(p, ru.loc["2007-06-01":], 5); rm = pnl(m, ru.loc["2007-06-01":], 5)
crash = ((r.index >= "2014-07-01") & (r.index <= "2016-02-29")) | ((r.index >= "2020-01-15") & (r.index <= "2020-06-30"))
pc = r[~crash].loc["2014":]
print("F3b post Sharpe %.2f, no-crash %.2f (t %.2f); long leg %.2f short leg %.2f" % (sharpe(r.loc["2014":]), sharpe(pc), tstat(pc),
      sharpe((p.shift(1).clip(lower=0) * ru).loc["2014":]), sharpe((p.shift(1).clip(upper=0) * ru).loc["2014":])))
print("agreement with USO 63d momentum sign: %.0f%%; corr of daily pnl with momentum-63d pnl post: %.2f; momentum-63d weekly post Sharpe %.2f"
      % (100 * (p == m).mean(), r.loc["2014":].corr(rm.loc["2014":]), sharpe(rm.loc["2014":])))
ag = (p == m).shift(1).fillna(False).astype(bool)
print("disagree days post: Sharpe %.2f t %.2f n %d" % (sharpe(r[~ag].loc["2014":]), tstat(r[~ag].loc["2014":]), (~ag).loc["2014":].sum()))
print("by year %:", (r.groupby(r.index.year).sum() * 100).round(1).to_dict())
print("current F3b position:", p.iloc[-1], "HYG-LQD 63d %+.4f" % c.dropna().iloc[-1])
