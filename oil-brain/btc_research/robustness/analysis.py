import itertools, json, math
import numpy as np, pandas as pd
from scipy.stats import norm, skew, kurtosis
from engine import *

D = Data(load())
BASE = dict(N=20, K=2.0, M=4, L=200, H=30)
P_NEW = ('2019-01-01', None)
P_OLD = ('2015-01-01', '2018-12-31')
cache = {}


def run(**kw):
    cfg = {**BASE, **kw}
    cfg['K'] = float(cfg['K'])
    key = tuple(sorted((k, str(v)) for k, v in cfg.items()))
    if key not in cache:
        tr, dp = backtest(D, daily=True, **cfg)
        cache[key] = (cfg, tr, dp)
    return cache[key]


def row(**kw):
    cfg, tr, _ = run(**kw)
    a = stats(period(tr, *P_NEW).R); b = stats(period(tr, *P_OLD).R)
    return dict(**{k: cfg[k] for k in ['N', 'K', 'M', 'L', 'H']},
                n_new=a['n'], avgR_new=a['avgR'], t_new=a['t'], n_old=b['n'], avgR_old=b['avgR'], t_old=b['t'])


out = {}
# ---------- 1. replication
cfg, tr, _ = run()
p = period(tr, *P_NEW)
out['base_new'] = stats(p.R); out['base_new_closed'] = stats(p[p.reason != 'open'].R)
out['base_old'] = stats(period(tr, *P_OLD).R)
out['base_by_year'] = p.groupby(p.entry_date.dt.year).R.agg(['count', 'mean', 'sum']).round(2).reset_index().values.tolist()
conv = []
for tag, kw, end in [('as built', {}, None), ('no re-entry on exit day', dict(reenter_exit_day=False), None),
                     ('as built, end 2025-12-31', {}, '2025-12-31'), ('H=29 (exit one bar earlier)', dict(H=29), None),
                     ('H=31', dict(H=31), None), ('zero cost', dict(cost=0.0), None)]:
    t2 = backtest(D, **{**BASE, **kw}); s = stats(period(t2, '2019-01-01', end).R)
    conv.append([tag, s['n'], round(s['avgR'], 3), round(s['t'], 2)])
out['conventions'] = conv

# ---------- 2. one/two at a time
Ms = [2, 3, 4, 6, 8, 'trail']
oat = {}
oat['N'] = [row(N=n) for n in [10, 15, 20, 30, 40, 55, 80, 100]]
oat['K'] = [row(K=k) for k in [1, 1.5, 2, 2.5, 3, 4]]
oat['M'] = [row(M=m) for m in Ms] + [row(M='trail', H=None)]
oat['L'] = [row(L=l) for l in [None, 50, 100, 150, 200, 300]]
oat['H'] = [row(H=h) for h in [10, 20, 30, 60, None]]
oat['LxH'] = [row(L=l, H=h) for l in [None, 50, 100, 150, 200, 300] for h in [10, 20, 30, 60, None]]
oat['NxL'] = [row(N=n, L=l) for n in [10, 15, 20, 30, 40, 55, 80, 100] for l in [None, 50, 100, 150, 200, 300]]
grid = [row(N=n, K=k, M=m) for n in [10, 15, 20, 30, 40, 55, 80, 100] for k in [1, 1.5, 2, 2.5, 3, 4] for m in Ms]
g = pd.DataFrame(grid)
out['oat'] = {k: pd.DataFrame(v).round(3).to_dict('records') for k, v in oat.items()}
g.round(3).to_csv(os.path.join(HERE, 'grid_NxKxM.csv'), index=False)
pos_both = ((g.avgR_new > 0) & (g.avgR_old > 0)).mean()
out['grid'] = dict(n=len(g), pos_new=(g.avgR_new > 0).mean(), pos_old=(g.avgR_old > 0).mean(), pos_both=pos_both,
                   t2_new=(g.t_new > 2).mean(), t2_old=(g.t_old > 2).mean(), t2_both=((g.t_new > 2) & (g.t_old > 2)).mean(),
                   med_avgR_new=g.avgR_new.median(), med_avgR_old=g.avgR_old.median(),
                   corr_new_old=g.avgR_new.corr(g.avgR_old),
                   base_rank_new=int((g.avgR_new > g.query('N==20 and K==2 and M==4').avgR_new.iloc[0]).sum()) + 1)
out['grid_pivots'] = {}
for col in ['avgR_new', 'avgR_old', 't_new', 't_old']:
    out['grid_pivots'][col + '_NxK'] = g.pivot_table(index='N', columns='K', values=col, aggfunc='mean').round(2).to_dict()
    out['grid_pivots'][col + '_NxM'] = g.pivot_table(index='N', columns='M', values=col, aggfunc='mean').round(2).to_dict()
    out['grid_pivots'][col + '_KxM'] = g.pivot_table(index='K', columns='M', values=col, aggfunc='mean').round(2).to_dict()
# full-period subsets for the grid (all configs)

# ---------- 3. walk forward
menu = [dict(N=n, K=k, M=m) for n in [20, 55] for k in [2.0, 3.0] for m in [3, 4, 'trail']]
wf_trades = []; wf_log = []
last_exit = pd.Timestamp('1900-01-01')
for Y in range(2018, 2027):
    t0, t1 = pd.Timestamp(f'{Y-4}-01-01'), pd.Timestamp(f'{Y}-01-01')
    best = None
    for m in menu:
        _, tr, _ = run(**m)
        trn = tr[(tr.entry_date >= t0) & (tr.exit_date < t1)]
        if len(trn) >= 15 and (best is None or trn.R.mean() > best[1]):
            best = (m, trn.R.mean(), len(trn))
    chosen = best[0] if best else dict(N=20, K=2.0, M=4)
    _, tr, _ = run(**chosen)
    yt = tr[(tr.entry_date.dt.year == Y) & (tr.signal > last_exit - pd.Timedelta(days=0))]
    yt = yt[yt.entry_date > last_exit]
    if len(yt): last_exit = yt.exit_date.max()
    wf_trades.append(yt.assign(year=Y))
    _, btr, _ = run()
    by = btr[btr.entry_date.dt.year == Y]
    s = stats(yt.R); sb = stats(by.R)
    wf_log.append(dict(year=Y, chosen=f"N{chosen['N']} K{chosen['K']} M{chosen['M']}",
                       train_avgR=None if not best else round(best[1], 2), train_n=None if not best else best[2],
                       oos_n=s['n'], oos_avgR=round(s['avgR'], 2) if s['n'] else None, oos_sumR=round(s['totR'], 1),
                       base_n=sb['n'], base_avgR=round(sb['avgR'], 2), base_sumR=round(sb['totR'], 1)))
wf = pd.concat(wf_trades)
out['wf_log'] = wf_log
out['wf_total'] = stats(wf.R)
out['wf_base_same_span'] = stats(period(run()[1], '2018-01-01').R)
out['wf_from2019'] = stats(wf[wf.entry_date >= '2019-01-01'].R)

# ---------- 4. DSR and PBO
# trial set = every distinct config evaluated above (incl. walk-forward menu)
keys = list(cache.keys())
def trade_sr(tr, s, e=None):
    r = period(tr, s, e).R.values
    return r.mean() / r.std(ddof=1) if len(r) > 2 and r.std() > 0 else np.nan
srs = np.array([trade_sr(cache[k][1], *P_NEW) for k in keys]); srs = srs[~np.isnan(srs)]
Rb = period(run()[1], *P_NEW).R.values
sr = Rb.mean() / Rb.std(ddof=1); T = len(Rb); g3 = skew(Rb); g4 = kurtosis(Rb, fisher=False)
EG = 0.5772156649
def sr0(Ntr, var):
    return math.sqrt(var) * ((1 - EG) * norm.ppf(1 - 1 / Ntr) + EG * norm.ppf(1 - 1 / (Ntr * math.e)))
def dsr(Ntr, var):
    s0 = sr0(Ntr, var)
    return norm.cdf((sr - s0) * math.sqrt(T - 1) / math.sqrt(1 - g3 * sr + (g4 - 1) / 4 * sr ** 2)), s0
psr0 = norm.cdf(sr * math.sqrt(T - 1) / math.sqrt(1 - g3 * sr + (g4 - 1) / 4 * sr ** 2))
# effective number of independent trials from daily-pnl correlation
dps = np.array([cache[k][2] for k in keys])
mask = D.idx >= '2019-01-01'
C = np.corrcoef(dps[:, mask]); rho = C[np.triu_indices_from(C, 1)].mean()
Neff = rho + (1 - rho) * len(keys)
var = srs.var(ddof=1)
out['dsr'] = dict(SR_per_trade=sr, T=T, skew=g3, kurt=g4, PSR_vs0=psr0, n_trials=len(keys), var_SR=var,
                  mean_SR_trials=srs.mean(), max_SR_trials=srs.max(), avg_corr=rho, N_eff=Neff,
                  table=[[n, round(sr0(n, var), 3), round(dsr(n, var)[0], 3)] for n in [10, 50, 100, int(round(Neff)), len(keys)]])
# CSCV / PBO on the NxKxM grid, daily R-pnl, Sharpe metric
def pbo(M, S=16):
    Tn = M.shape[1] // S * S; M = M[:, -Tn:]
    blocks = np.array_split(np.arange(Tn), S)
    s1 = np.stack([M[:, b].sum(1) for b in blocks], 1); s2 = np.stack([(M[:, b] ** 2).sum(1) for b in blocks], 1)
    cnt = np.array([len(b) for b in blocks])
    def shp(ix):
        n = cnt[ix].sum(); m = s1[:, ix].sum(1) / n; v = s2[:, ix].sum(1) / n - m ** 2
        return np.where(v > 1e-12, m / np.sqrt(np.maximum(v, 1e-12)), -np.inf)
    lam = []; oos_best = []
    for comb in itertools.combinations(range(S), S // 2):
        isx = list(comb); oos = [i for i in range(S) if i not in comb]
        a, b = shp(isx), shp(oos)
        n = np.argmax(a)
        w = (np.argsort(np.argsort(b))[n] + 1) / (len(b) + 1)
        lam.append(math.log(w / (1 - w))); oos_best.append(b[n])
    lam = np.array(lam); oos_best = np.array(oos_best)
    return dict(PBO=(lam <= 0).mean(), median_logit=float(np.median(lam)), n_splits=len(lam),
                oos_daily_sharpe_of_IS_best_median=float(np.median(oos_best)) * math.sqrt(365),
                frac_oos_best_positive=float((oos_best > 0).mean()))
gkeys = [k for k in keys if dict(k)['L'] == '200' and dict(k)['H'] == '30']
G = np.array([cache[k][2] for k in gkeys])
start = np.argmax(D.idx >= '2015-06-01')
out['pbo_full'] = pbo(G[:, start:]); out['pbo_full']['n_configs'] = len(gkeys)
out['pbo_2019'] = pbo(G[:, mask])
Aall = np.array([cache[k][2] for k in keys])
start300 = np.argmax(D.idx >= '2015-11-01')
out['pbo_all_trials_full'] = pbo(Aall[:, start300:]); out['pbo_all_trials_full']['n_configs'] = len(keys)

json.dump(out, open(os.path.join(HERE, 'results.json'), 'w'), indent=1, default=lambda o: o.item() if hasattr(o, 'item') else str(o))
pd.concat([pd.DataFrame(v).assign(block=k) for k, v in oat.items()]).round(3).to_csv(os.path.join(HERE, 'one_at_a_time.csv'), index=False)
wf.to_csv(os.path.join(HERE, 'walkforward_trades.csv'), index=False)
print(json.dumps({k: out[k] for k in ['base_new', 'base_new_closed', 'base_old', 'grid', 'wf_total', 'wf_base_same_span', 'wf_from2019', 'dsr', 'pbo_full', 'pbo_2019', 'pbo_all_trials_full']}, indent=1, default=str))
