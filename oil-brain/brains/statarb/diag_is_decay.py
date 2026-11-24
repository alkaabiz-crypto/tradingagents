"""IS-only diagnostic (data up to 2013-12-31 only; not a rule): how the gross residual-reversal
edge (R8 signal) decays with holding lag, to choose a turnover-reducing parameter for study 5."""
import re
from lib import *
src = open("study4.py").read()
exec(src[src.index('"""', 10) + 3: src.index("we = week_ends")])   # rebuild sig only
we = week_ends(px.index)
base = neutral(sig).where(sig.notna(), 0)
for lag in range(0, 4):
    w = hold(base, we).shift(5 * lag).fillna(0)
    _, g, t = port(w.loc["2006-06-01":IS_END], 0, ret.loc["2006-06-01":IS_END])
    print(f"week {lag+1} after formation: gross IS ann. mean {g.mean()*252*100:.1f}%  Sharpe {sharpe(g):.2f}")
for a in [1.0, 0.5, 0.33]:
    tgt = hold(base, we).loc["2006-06-01":IS_END]
    W = tgt.copy(); prev = tgt.iloc[0] * 0
    wk = set(pd.DatetimeIndex(we))
    vals = []
    for d, row in tgt.iterrows():
        if d in wk: prev = (1 - a) * prev + a * row
        vals.append(prev.values)
    W = pd.DataFrame(vals, index=tgt.index, columns=tgt.columns)
    n5, g, t = port(W, 5, ret.loc["2006-06-01":IS_END])
    print(f"partial adj a={a}: IS gross Sharpe {sharpe(g):.2f} net5 {sharpe(n5):.2f} turnover/yr {t.mean()*252:.0f}")
