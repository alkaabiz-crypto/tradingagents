import numpy as np, pandas as pd, bt
HERE = bt.HERE + '/risk'
pd.set_option('display.width', 200)
df = bt.load()
allt = bt.backtest(df)
allt.to_csv(f'{HERE}/trades_2015_now.csv', index=False)
openT = allt[allt.reason == 'open']
tr = allt[allt.reason != 'open'].copy()
tr['ed'] = pd.to_datetime(tr.entry_date); tr['xd'] = pd.to_datetime(tr.exit_date); tr['yr'] = tr.ed.dt.year

def row(s, name):
    r = s.R.values; n = len(r)
    if n == 0: return dict(group=name, n=0)
    t = r.mean() / r.std(ddof=1) * np.sqrt(n) if n > 1 else np.nan
    return dict(group=name, n=n, avgR=round(r.mean(), 2), medR=round(np.median(r), 2), t=round(t, 2),
                win=f'{(r>0).mean()*100:.0f}%', totR=round(r.sum(), 1),
                stop=f'{(s.reason=="stop").mean()*100:.0f}%', tgt=f'{(s.reason=="target").mean()*100:.0f}%',
                time=f'{(s.reason=="time").mean()*100:.0f}%')
def table(rows):
    d = pd.DataFrame(rows).fillna('')
    out = ['| ' + ' | '.join(map(str, d.columns)) + ' |', '|' + '---|' * len(d.columns)]
    out += ['| ' + ' | '.join(map(str, r)) + ' |' for r in d.values]
    return '\n'.join(out)

print('## OPEN TRADE\n', openT.to_string())
print('\n## HEADLINE')
print(table([row(tr, 'all closed 2015-now'), row(tr[tr.ed >= '2019'], '2019-now'),
             row(tr[(tr.ed >= '2019') & (tr.ed < '2026')], '2019-2025 (claim window?)')]))

# yearly BTC return -> bull/bear
yc = df.Close.resample('YE').last(); yret = yc.pct_change()
yret.iloc[0] = yc.iloc[0] / df.Close.iloc[0] - 1
yret.index = yret.index.year
tr['regime'] = tr.yr.map(lambda y: 'bull' if yret[y] > 0 else 'bear')
print('\n## YEAR RETURNS', {k: f'{v*100:.0f}%' for k, v in yret.items()})
print('\n## SIDE')
rows = []
for per, s in [('2015-now', tr), ('2019-now', tr[tr.ed >= '2019'])]:
    for side in ['LONG', 'SHORT']: rows.append(row(s[s.side == side], f'{per} {side}'))
print(table(rows))
print('\n## REGIME (calendar-year BTC return sign)')
rows = []
for reg in ['bull', 'bear']:
    s = tr[tr.regime == reg]; rows.append(row(s, f'{reg} years ({sorted(s.yr.unique())})'))
    for side in ['LONG', 'SHORT']: rows.append(row(s[s.side == side], f'  {reg} {side}'))
print(table(rows))
print('\n## PERIOD')
pers = [('2015-2018', '2015', '2019'), ('2019-2021', '2019', '2022'), ('2022-now', '2022', '2100')]
rows = []
for nm, a, b in pers:
    s = tr[(tr.ed >= a) & (tr.ed < b)]; rows.append(row(s, nm))
    for side in ['LONG', 'SHORT']: rows.append(row(s[s.side == side], f'  {nm} {side}'))
print(table(rows))
print('\n## BY YEAR')
print(table([row(tr[tr.yr == y], str(y)) | {'BTC yr': f'{yret[y]*100:.0f}%'} for y in sorted(tr.yr.unique())]))
print('\n## EXIT REASONS')
rows = []
for per, s in [('2015-now', tr), ('2019-now', tr[tr.ed >= '2019']), ('2022-now', tr[tr.ed >= '2022'])]:
    for rs in ['stop', 'target', 'time']:
        x = s[s.reason == rs]
        rows.append(dict(period=per, exit=rs, n=len(x), share=f'{len(x)/len(s)*100:.0f}%', avgR=round(x.R.mean(), 2),
                         avg_days=round(x.days.mean(), 1)))
print(table(rows))
# time-exit breakdown
te = tr[tr.reason == 'time']
print('time exits: positive', (te.R > 0).sum(), 'negative', (te.R <= 0).sum(), 'min', te.R.min(), 'max', te.R.max())
# concentration
r19 = tr[tr.ed >= '2019'].R.sort_values(ascending=False).values
print('\n## CONCENTRATION 2019+: total', r19.sum().round(1), 'top5', r19[:5].sum().round(1), 'top10', r19[:10].sum().round(1),
      'avg ex top5', r19[5:].mean().round(3), 'avg ex top10', r19[10:].mean().round(3))
print('worst R', tr.R.min(), tr.loc[tr.R.idxmin(), ['entry_date', 'side', 'R']].to_dict())

# ---------- decay ----------
print('\n## DECAY')
tr = tr.reset_index(drop=True)
tr['roll20'] = tr.R.rolling(20).mean()
snap = tr[tr.roll20.notna()][['exit_date', 'roll20']]
step = snap.iloc[::5]
print(table([dict(after_trade_ending=str(a), roll20_avgR=round(b, 2)) for a, b in step.values] +
            [dict(after_trade_ending=str(snap.iloc[-1, 0]), roll20_avgR=round(snap.iloc[-1, 1], 2))]))
print('roll20 min/max/last', snap.roll20.min().round(2), snap.roll20.max().round(2), snap.roll20.iloc[-1].round(2),
      'share of windows <0:', (snap.roll20 < 0).mean().round(2))
x = np.arange(len(tr)); b = np.polyfit(x, tr.R.values, 1)
res = tr.R.values - np.polyval(b, x); se = np.sqrt(res.var(ddof=2) / ((x - x.mean())**2).sum())
print('OLS R on trade#: slope/trade', b[0].round(4), 't', (b[0] / se).round(2), 'implied R first->last', np.polyval(b, [0, len(x)-1]).round(2))
for nm, s in [('first half', tr.iloc[:len(tr)//2]), ('second half', tr.iloc[len(tr)//2:]), ('last 30', tr.iloc[-30:]), ('last 20', tr.iloc[-20:])]:
    print(nm, row(s, nm))
tr.to_csv(f'{HERE}/trades_closed_with_roll20.csv', index=False)

# ---------- live experience ----------
print('\n## LIVE')
s19 = tr[tr.ed >= '2019']
span_yrs = (df.index[-1] - pd.Timestamp('2019-01-01')).days / 365.25
print('2019+ trades/yr', round(len(s19) / span_yrs, 1), ' 2015+ trades/yr', round(len(tr) / ((df.index[-1] - tr.ed.iloc[0]).days / 365.25), 1))
print('per year counts', tr.groupby('yr').size().to_dict())
gaps = tr.ed.diff().dt.days.dropna(); flat = (tr.ed.values[1:] - tr.xd.values[:-1]).astype('timedelta64[D]').astype(int)
print('days between entries: mean', gaps.mean().round(1), 'median', gaps.median(), 'max', gaps.max())
print('flat days between exit and next entry: mean', flat.mean().round(1), 'median', np.median(flat), 'p90', np.percentile(flat, 90), 'max', flat.max())
# in-market days, flat months
inm = pd.Series(False, index=df.index)
for _, t in allt.iterrows(): inm[str(t.entry_date):str(t.exit_date)] = True
inm = inm['2019':]
print('time in market 2019+', f'{inm.mean()*100:.0f}%')
m = inm.resample('ME').max()
mf = (~m).groupby(m.index.year).sum()
newm = s19.groupby(s19.ed.dt.to_period('M')).size()
allm = pd.period_range('2019-01', df.index[-1].to_period('M'), freq='M')
nonew = pd.Series([0 if p in newm.index else 1 for p in allm], index=allm)
print('fully flat months per year (no position any day):', mf.to_dict(), 'avg', round(mf.mean(), 1))
print('months with no NEW trade per year:', nonew.groupby(nonew.index.year).sum().to_dict(), 'avg', round(nonew.groupby(nonew.index.year).sum().mean(), 1))
w = s19[s19.R > 0].R; L = s19[s19.R <= 0].R
print('winners n', len(w), 'mean', w.mean().round(2), 'median', w.median().round(2), '| losers n', len(L), 'mean', L.mean().round(2), 'median', L.median().round(2))
print('R buckets 2019+:', pd.cut(s19.R, [-9, -0.9, -0.25, 0, 1, 2, 3.5, 9]).value_counts().sort_index().to_dict())
print('stop distance % of price 2019+: median', s19.stop_pct.median(), 'range', s19.stop_pct.min(), s19.stop_pct.max())
print('days held median', s19.days.median(), 'mean', s19.days.mean().round(1))
# historical streaks
ls = cur = 0
for r in s19.R:
    cur = cur + 1 if r <= 0 else 0; ls = max(ls, cur)
print('historical longest losing streak 2019+', ls)
ls = cur = 0
for r in tr.R:
    cur = cur + 1 if r <= 0 else 0; ls = max(ls, cur)
print('historical longest losing streak 2015+', ls)
# historical equity DD at each risk
for rk in [0.005, 0.01, 0.02, 0.03]:
    eq = np.cumprod(1 + rk * s19.R.values); dd = 1 - eq / np.maximum.accumulate(np.r_[1, eq])[1:]
    print(f'hist 2019+ risk {rk}: final x{eq[-1]:.2f} CAGR {(eq[-1]**(1/span_yrs)-1)*100:.0f}% maxDD {dd.max()*100:.0f}%')
np.save(f'{HERE}/r2019.npy', s19.R.values)
