"""Study 1 (pre-registered 2026-11-24, before running): classic short-term reversal, paper parameters.
Universe: 110 large US stocks listed since before 2005 (fetch.py; survivorship bias stated).
Weights: linear contrarian (Lehmann 1990 / Lo-MacKinlay 1990): w_i proportional to -(r_i - mean r),
dollar neutral, $1 long / $1 short. Positions at close t, earn t->t+1. Cost 5 bp per unit of
turnover (sum |dw|); 10 bp stress = the engine's 2x-cost gate. Benchmark: SPY buy-and-hold
(strict for a market-neutral book). Placebo: 500 circular time shifts of the whole weight matrix.
Counted from 2005-07-01. No parameter is chosen from data; all come from the papers.
 R1 weekly reversal: at each week's last close, signal = -(5-day return), held one week.
 R2 daily reversal: each close, signal = -(1-day return), held one day.
 R3 industry-adjusted weekly reversal (Da, Liu & Schaumburg 2014): like R1, but the 5-day return
    is demeaned within the stock's sector (11 GICS sectors), so the book is sector-neutral.
Expectation (literature): gross positive, strongest pre-2010; daily rule likely eaten by costs;
industry-adjusted stronger than raw.
"""
from lib import *
we = week_ends(px.index)
r5 = px.pct_change(5, fill_method=None)
R1 = hold(neutral(-r5), we)
R2 = neutral(-ret)
R3 = hold(neutral(-r5, SECT), we)
# check: placebo machinery with zero shift equals port()
rows = []; series = {}
for k, w in {"R1 weekly reversal": R1, "R2 daily reversal": R2, "R3 weekly industry-adj reversal": R3}.items():
    o, r = evaluate_w(k, w); rows.append(o); series[k] = r
df = show(rows)
df.to_csv("study1_results.csv")
for k, r in series.items():
    p = r.loc["2005-07":]
    print(k, "net % by year:", (p.groupby(p.index.year).sum() * 100).round(1).to_dict())
