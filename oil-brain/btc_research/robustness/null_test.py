"""Null: same trend filter + same exits, but entries on random days instead of breakouts."""
import numpy as np, pandas as pd, json, os
from engine import *
D = Data(load()); c = D.c
s = D.sma(200); hh, ll = D.hh(20)
valid = ~np.isnan(s) & ~np.isnan(D.atr) & ~np.isnan(hh)
up = valid & (c > s); dn = valid & (c < s)
base = backtest(D)
res = {}
for tag, (a, b) in {'2019+': ('2019-01-01', None), '2015-18': ('2015-01-01', '2018-12-31')}.items():
    pb = period(base, a, b)
    res[tag] = dict(base=stats(pb.R), base_long=stats(pb[pb.side == 1].R), base_short=stats(pb[pb.side == -1].R))
rng = np.random.default_rng(7)
out = {k: [] for k in res}
for p in [0.06]:
    for i in range(1000):
        m = rng.random(len(c)) < p
        tr = backtest(D, sig_override=(m & up, m & dn))
        for tag, (a, b) in {'2019+': ('2019-01-01', None), '2015-18': ('2015-01-01', '2018-12-31')}.items():
            r = period(tr, a, b).R
            out[tag].append((len(r), r.mean()))
for tag in res:
    arr = np.array(out[tag])
    res[tag]['null_n_median'] = float(np.median(arr[:, 0]))
    res[tag]['null_avgR_median'] = float(np.median(arr[:, 1]))
    res[tag]['null_avgR_p95'] = float(np.percentile(arr[:, 1], 95))
    res[tag]['p_null_ge_base'] = float((arr[:, 1] >= res[tag]['base']['avgR']).mean())
# buy-and-hold-in-trend reference: always long above SMA200 / short below, same exits (enter every eligible day)
tr = backtest(D, sig_override=(up, dn))
for tag, (a, b) in {'2019+': ('2019-01-01', None), '2015-18': ('2015-01-01', '2018-12-31')}.items():
    res[tag]['every_day_in_trend'] = stats(period(tr, a, b).R)
json.dump(res, open(os.path.join(HERE, 'null_results.json'), 'w'), indent=1, default=float)
print(json.dumps(res, indent=1, default=float))
