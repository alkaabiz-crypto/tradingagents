"""Study 3 (pre-registered 2026-11-24, after studies 1-2, before running): distance-method pairs
(Gatev, Goetzmann & Rouwenhorst 2006, their parameters; Do & Faff 2010 report decay after 2002).
Every 21 trading days a new portfolio is formed (6 overlapping portfolios, as GGR):
  formation = past 252 days. Prices = total-return index normalised to 1 at formation start.
  Pairs = the 20 pairs with smallest sum of squared normalised-price differences (SSD).
  sigma = std of the normalised spread over formation.
  trading = next 126 days; prices re-normalised to 1 at trading start; open when
  |spread| > 2 sigma (long the loser, short the winner, 1/20 per leg); close when the spread
  crosses zero; may reopen; all closed at the end of the 126 days.
Final weights = mean of the 6 active portfolios' weights (so gross <= 2). Constant-weight
approximation within a trade (rebalanced daily, cost counted on actual weight changes only).
 R6 GGR pairs, all 110 stocks.
 R7 GGR pairs restricted to same-sector pairs (GGR's industry variant).
Costs 5 bp per unit turnover (10 bp gate), SPY benchmark, 500-shift placebo, from 2005-07-01
(first trades start 2005-06 after one year of formation from 2004-06).
Diagnostic (not a rule): the same weights delayed one day (GGR's "wait one day" check) to see
how much is bid-ask bounce at the close.
Expectation: positive gross IS but small; post-2014 near zero (Do & Faff decay).
"""
from lib import *
P = (1 + ret.fillna(0)).cumprod().values
n, N = P.shape
cols = px.columns
sect = SECT.values
FORM, TRADE, STEP, NP = 252, 126, 21, 20


def run(same_sector):
    W = np.zeros((n, N)); cnt = np.zeros(n)
    for s in range(0, n - FORM, STEP):
        f = P[s:s + FORM] / P[s]
        G = f.T @ f; d = np.diag(G)
        ssd = d[:, None] + d[None, :] - 2 * G
        iu = np.triu_indices(N, 1)
        vals = ssd[iu].copy()
        if same_sector:
            vals[sect[iu[0]] != sect[iu[1]]] = np.inf
        best = np.argsort(vals)[:NP]
        t0, t1 = s + FORM - 1, min(s + FORM - 1 + TRADE, n - 1)   # trading starts at close t0
        cnt[t0:t1] += 1
        for b in best:
            i, j = iu[0][b], iu[1][b]
            sig = np.std(f[:, i] - f[:, j])
            tp = P[t0:t1 + 1] / P[t0]
            spr = tp[:, i] - tp[:, j]
            pos = 0
            for k in range(len(spr) - 1):      # decision at close t0+k, last close forced flat
                x = spr[k]
                if pos == 0 and abs(x) > 2 * sig:
                    pos = -np.sign(x)            # spread high -> short i, long j
                elif pos != 0 and np.sign(x) == pos:   # crossed zero
                    pos = 0
                    if abs(x) > 2 * sig: pos = -np.sign(x)
                if pos:
                    W[t0 + k, i] += pos / NP; W[t0 + k, j] -= pos / NP
    W = W / 6.0
    return pd.DataFrame(W, index=px.index, columns=cols), cnt


rows = []
for name, ss in [("R6 GGR pairs all", False), ("R7 GGR pairs same sector", True)]:
    w, cnt = run(ss)
    o, r = evaluate_w(name, w); rows.append(o)
    od, _ = evaluate_w(name + " [1-day delay diag]", w.shift(1).fillna(0), n_placebo=50); rows.append(od)
    p = r.loc[START:]
    print(name, "avg gross exposure", round(w.loc[START:].abs().sum(1).mean(), 2),
          "net % by year:", (p.groupby(p.index.year).sum() * 100).round(1).to_dict())
show(rows).to_csv("study3_results.csv")
