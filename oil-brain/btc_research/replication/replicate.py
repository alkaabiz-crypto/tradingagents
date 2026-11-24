"""Out-of-sample replication of the BTC 20-day breakout rule on other coins.
Rule (unchanged): trend = close vs SMA200; long if close > max(high, prev 20d) & trend up;
short if close < min(low, prev 20d) & trend down. Enter next open. Stop 2xATR20 (SMA of TR at
signal day), target 4R, time exit at close of the 30th bar held, stop wins on a both-touch bar.
One position per coin. 10 bp per side. R = (signed move - costs)/stop distance.
Fills: stop at the worse of stop/open (gap), target at target price.
"""
import json, sys
import numpy as np, pandas as pd

D = sys.argv[1] if len(sys.argv) > 1 else '.'
COINS = 'BTC ETH SOL XRP LTC BNB ADA DOGE BCH LINK DOT AVAX TRX XLM'.split()
WIN0 = pd.Timestamp('2019-01-01')
SPLIT = pd.Timestamp('2022-01-01')
COST = 0.001; N_PLACEBO = 300; WARM = 300
rng = np.random.default_rng(7)


def load(c):
    d = pd.read_csv(f'{D}/data/{c}-USD.csv', index_col=0, parse_dates=True).dropna()
    d = d[(d[['Open', 'High', 'Low', 'Close']] > 0).all(axis=1)]
    pc = d.Close.shift()
    tr = pd.concat([d.High - d.Low, (d.High - pc).abs(), (d.Low - pc).abs()], axis=1).max(axis=1)
    d['atr'] = tr.rolling(20).mean()
    d['sma'] = d.Close.rolling(200).mean()
    d['hh'] = d.High.shift().rolling(20).max()
    d['ll'] = d.Low.shift().rolling(20).min()
    return d


def simulate(d, i, direction):
    """signal at bar i, entry at open i+1. returns dict or None."""
    O, H, L, C = d.Open.values, d.High.values, d.Low.values, d.Close.values
    if i + 1 >= len(d):
        return None
    e = O[i + 1]; sd = 2 * d.atr.values[i]
    stop = e - direction * sd; tgt = e + direction * 4 * sd
    last = min(i + 30, len(d) - 1)
    for j in range(i + 1, last + 1):
        if direction == 1:
            hit_s = L[j] <= stop; hit_t = H[j] >= tgt
            if hit_s:
                x = min(stop, O[j]); why = 'stop'; break
            if hit_t:
                x = tgt; why = 'target'; break
        else:
            hit_s = H[j] >= stop; hit_t = L[j] <= tgt
            if hit_s:
                x = max(stop, O[j]); why = 'stop'; break
            if hit_t:
                x = tgt; why = 'target'; break
    else:
        j = last; x = C[j]; why = 'time' if last == i + 30 else 'open'
    r = (direction * (x - e) - COST * (e + x)) / sd
    return dict(sig=d.index[i], entry_i=i + 1, exit_i=j, entry=e, exit=x, sd=sd, dir=direction, R=r, why=why)


def run_rule(d, first_i):
    C = d.Close.values; up = (C > d.sma.values); dn = (C < d.sma.values)
    lng = (C > d.hh.values) & up; sht = (C < d.ll.values) & dn
    trades = []; i = first_i
    while i < len(d) - 1:
        s = 1 if lng[i] else (-1 if sht[i] else 0)
        if s:
            t = simulate(d, i, s)
            if t['why'] == 'open':  # still open at data end: drop
                break
            trades.append(t); i = t['exit_i']  # may signal again at close of exit bar
        i += 1
    return trades


def stats(R):
    R = np.asarray(R); n = len(R)
    if n == 0:
        return dict(n=0)
    cum = np.cumsum(R); dd = (np.maximum.accumulate(np.r_[0, cum])[1:] - cum).max()
    sdv = R.std(ddof=1) if n > 1 else np.nan
    return dict(n=n, win=(R > 0).mean(), avg=R.mean(), t=R.mean() / sdv * np.sqrt(n) if n > 1 else np.nan,
                tot=R.sum(), mdd=dd)


def placebo(d, first_i, n, actual):
    C = d.Close.values; s = d.sma.values
    elig = np.array([i for i in range(first_i, len(d) - 31) if C[i] != s[i]])
    means = np.empty(N_PLACEBO)
    for k in range(N_PLACEBO):
        idx = rng.choice(elig, n, replace=False)
        means[k] = np.mean([simulate(d, i, 1 if C[i] > s[i] else -1)['R'] for i in idx])
    return (np.sum(means >= actual) + 1) / (N_PLACEBO + 1), means.mean()


data = {c: load(c) for c in COINS}
rows, alltr = [], []
for c in COINS:
    d = data[c]
    first_i = max(WARM, d.index.searchsorted(WIN0))
    tr = run_rule(d, first_i)
    # also full-history (pre-2019) for coins that have it
    tr_full = run_rule(d, WARM)
    pre = [t for t in tr_full if t['sig'] < WIN0]
    for t in tr:
        t['coin'] = c
    alltr += tr
    R = [t['R'] for t in tr]
    st = stats(R)
    a = [t['R'] for t in tr if t['sig'] < SPLIT]; b = [t['R'] for t in tr if t['sig'] >= SPLIT]
    L = [t['R'] for t in tr if t['dir'] == 1]; S = [t['R'] for t in tr if t['dir'] == -1]
    p, pm = placebo(d, first_i, len(R), st['avg'])
    rows.append(dict(coin=c, data_start=str(d.index[0].date()), first_eligible=str(d.index[first_i].date()), **st,
                     n_a=len(a), avg_a=np.mean(a) if a else np.nan, n_b=len(b), avg_b=np.mean(b) if b else np.nan,
                     nL=len(L), avgL=np.mean(L) if L else np.nan, tL=stats(L).get('t', np.nan),
                     nS=len(S), avgS=np.mean(S) if S else np.nan, tS=stats(S).get('t', np.nan),
                     p=p, placebo_avg=pm, n_pre=len(pre), avg_pre=np.mean([t['R'] for t in pre]) if pre else np.nan))
    print(c, {k: (round(v, 3) if isinstance(v, float) else v) for k, v in rows[-1].items()}, flush=True)

res = pd.DataFrame(rows)
tdf = pd.DataFrame(alltr)
tdf.to_csv(f'{D}/trades.csv', index=False)
res.to_csv(f'{D}/per_coin.csv', index=False)

# ---------- pooled stats ----------
alts = tdf[tdf.coin != 'BTC']
pooled = {}
for name, sub in [('all 13 alts', alts), ('alts long', alts[alts.dir == 1]), ('alts short', alts[alts.dir == -1]),
                  ('alts 2019-21', alts[alts.sig < SPLIT]), ('alts 2022+', alts[alts.sig >= SPLIT]),
                  ('alts long 2022+', alts[(alts.dir == 1) & (alts.sig >= SPLIT)]),
                  ('alts short 2022+', alts[(alts.dir == -1) & (alts.sig >= SPLIT)]),
                  ('alts excl. ETH-era-2020-21 long', alts[~((alts.dir == 1) & (alts.sig >= '2020-10-01') & (alts.sig < '2021-12-31'))]),
                  ('BTC', tdf[tdf.coin == 'BTC'])]:
    st = stats(sub.R.values)
    # month-clustered t: sum R by signal month, t over months
    m = sub.groupby(sub.sig.dt.to_period('M')).R.sum()
    allm = pd.period_range('2019-01', '2026-11', freq='M')
    m = m.reindex(allm, fill_value=0.0)
    st['t_month_clustered'] = m.mean() / m.std(ddof=1) * np.sqrt(len(m))
    pooled[name] = st
pooled = pd.DataFrame(pooled).T
print(pooled)
pooled.to_csv(f'{D}/pooled.csv')

# ---------- correlation of trade results (monthly R per coin) ----------
mR = tdf.groupby([tdf.sig.dt.to_period('M'), 'coin']).R.sum().unstack().reindex(
    pd.period_range('2019-01', '2026-11', freq='M')).fillna(0.0)
cm = mR.corr().values; iu = np.triu_indices_from(cm, 1)
avg_corr_month = np.nanmean(cm[iu])
alt_cols = [c for c in mR.columns if c != 'BTC']
cma = mR[alt_cols].corr().values; iua = np.triu_indices_from(cma, 1)
avg_corr_month_alts = np.nanmean(cma[iua])
btc_corr = mR.corr()['BTC'].drop('BTC').mean()


# ---------- basket equity curve (daily MTM) ----------
def basket(risk):
    idx = pd.date_range(WIN0, max(d.index[-1] for d in data.values()))
    r = pd.Series(0.0, index=idx); gross = pd.Series(0.0, index=idx)
    for t in alltr:
        d = data[t['coin']]; C = d.Close.values
        for j in range(t['entry_i'], t['exit_i'] + 1):
            p0 = t['entry'] if j == t['entry_i'] else C[j - 1]
            p1 = t['exit'] if j == t['exit_i'] else C[j]
            rr = t['dir'] * (p1 - p0) / t['sd']
            if j == t['entry_i']:
                rr -= COST * t['entry'] / t['sd']
            if j == t['exit_i']:
                rr -= COST * t['exit'] / t['sd']
            day = d.index[j]
            r[day] += risk * rr
            gross[day] += risk * C[j] / t['sd'] if j < t['exit_i'] else 0
    return r, gross


def perf(r):
    eq = (1 + r).cumprod(); yrs = len(r) / 365
    return dict(sharpe=r.mean() / r.std() * np.sqrt(365), cagr=eq.iloc[-1] ** (1 / yrs) - 1,
                mdd=(1 - eq / eq.cummax()).max(), final=eq.iloc[-1], vol=r.std() * np.sqrt(365))


bk = {}
for risk in (0.01, 0.005):
    r, g = basket(risk)
    bk[f'breakout {risk:.1%} risk'] = dict(**perf(r), max_gross=g.max(), avg_gross=g.mean())
    if risk == 0.01:
        r1 = r
    # alts-only basket
for risk in (0.01,):
    keep = alltr
    alltr_bak = alltr
    alltr = [t for t in keep if t['coin'] != 'BTC']
    r, g = basket(risk)
    bk['breakout 1% risk, alts only'] = dict(**perf(r), max_gross=g.max(), avg_gross=g.mean())
    alltr = [t for t in keep if t['dir'] == -1]
    r, g = basket(risk)
    bk['breakout 1% risk, shorts only'] = dict(**perf(r), max_gross=g.max(), avg_gross=g.mean())
    alltr = [t for t in keep if t['dir'] == 1]
    r, g = basket(risk)
    bk['breakout 1% risk, longs only'] = dict(**perf(r), max_gross=g.max(), avg_gross=g.mean())
    alltr = alltr_bak

# equal-weight buy & hold: daily rebalanced across coins once each is past its 300-day warm-up
rets = pd.DataFrame({c: data[c].Close.pct_change() for c in COINS})
for c in COINS:
    rets.loc[rets.index < data[c].index[WARM], c] = np.nan
rets = rets[rets.index >= WIN0]
ew = rets.mean(axis=1)
bk['EW buy&hold (daily rebal)'] = perf(ew)
bk['BTC buy&hold'] = perf(rets['BTC'])
# EW buy&hold, no rebalancing (each coin buys in at eligibility with equal $... approximated by start-2019 coins)
bk = pd.DataFrame(bk).T
print(bk)
bk.to_csv(f'{D}/basket.csv')
# yearly basket vs EW
yr = pd.DataFrame({'breakout_1pct': r1.groupby(r1.index.year).apply(lambda x: (1 + x).prod() - 1),
                   'EW_BH': ew.groupby(ew.index.year).apply(lambda x: (1 + x).prod() - 1)})
print(yr)
yr.to_csv(f'{D}/yearly.csv')
corr_eq = np.corrcoef(r1.reindex(ew.index).fillna(0), ew)[0, 1]
json.dump(dict(avg_corr_month=avg_corr_month, avg_corr_month_alts=avg_corr_month_alts, btc_corr_to_alts=btc_corr,
               corr_basket_vs_ew_daily=corr_eq), open(f'{D}/misc.json', 'w'), indent=1)
print(avg_corr_month, avg_corr_month_alts, btc_corr, corr_eq)
