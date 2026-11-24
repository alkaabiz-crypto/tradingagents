"""Study 5 (pre-registered 2026-11-24, after studies 1-4 and the IS-only diagnostic
diag_is_decay.py, before running): turnover reduction for residual reversal.
Study 4: R8 gross post-2014 Sharpe 0.38 but turnover 145x/yr turns it net negative. The IS-only
decay diagnostic shows the edge lasts ~2 weeks (week1 Sharpe 1.10, week2 0.61, week3 <0) and
partial adjustment a=0.5 lifts IS net Sharpe 0.44 -> 0.73 with turnover 150 -> 61. Parameter a=0.5
taken from IS only (0.33 was similar; 0.5 chosen as the simpler round value).
 R10 R8 signal, weekly partial adjustment: w_new = 0.5*w_old + 0.5*target, at each week's close.
 R11 same, target = R8 target x 1(VIX > 25) (Nagel regime; in calm weeks the book decays
     halfway to zero each week). Same caveat as R9: VIX>25 results already seen post-2014.
Costs 5 bp (10 bp gate), SPY benchmark, 500-shift placebo, START as before.
"""
from lib import *
src = open("study4.py").read()
exec(src[src.index('"""', 10) + 3: src.index("we = week_ends")])   # rebuild R8 signal `sig`
we = week_ends(px.index)
base = neutral(sig).where(sig.notna(), 0)


def partial(target_daily, a=0.5):
    tgt = target_daily.loc[we]
    out = []; prev = tgt.iloc[0] * 0
    for d, row in tgt.iterrows():
        prev = (1 - a) * prev + a * row; out.append(prev.values)
    return pd.DataFrame(out, index=tgt.index, columns=tgt.columns).reindex(px.index).ffill().fillna(0)


R10 = partial(base)
R11 = partial(base.mul((vix > 25).astype(float), axis=0))
rows = []; ser = {}
for k, w in {"R10 resid reversal, partial adj 0.5": R10, "R11 R10 with VIX>25 target": R11}.items():
    o, r = evaluate_w(k, w); rows.append(o); ser[k] = r
    p = r.loc[START:]
    print(k, "net % by year:", (p.groupby(p.index.year).sum() * 100).round(1).to_dict())
    od, _ = evaluate_w(k + " [1-day delay diag]", w.shift(1).fillna(0), n_placebo=50); rows.append(od)
show(rows).to_csv("study5_results.csv")
