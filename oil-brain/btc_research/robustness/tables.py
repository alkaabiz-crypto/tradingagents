import pandas as pd
def md(df, index=True):
    df = df.reset_index() if index else df
    cols = [str(c) for c in df.columns]
    s = '| ' + ' | '.join(cols) + ' |\n|' + '---|' * len(cols) + '\n'
    for r in df.itertuples(index=False):
        s += '| ' + ' | '.join('' if pd.isna(v) else (f'{v:.2f}' if isinstance(v, float) else str(v)) for v in r) + ' |\n'
    return s
g = pd.read_csv('grid_NxKxM.csv')
d = pd.read_csv('one_at_a_time.csv').fillna({'L': 'none', 'H': 'none'})
o = []
for v in ['avgR_new', 'avgR_old', 't_new', 't_old']:
    for a, b in [('N', 'K'), ('N', 'M'), ('K', 'M')]:
        o.append(f'### {v}: {a} x {b} (mean over the third axis)\n\n' + md(g.pivot_table(index=a, columns=b, values=v)))
o.append('### grid describe\n\n' + md(g[['n_new','avgR_new','t_new','n_old','avgR_old','t_old']].describe()))
o.append('### worst 5 (2019+)\n\n' + md(g.sort_values('avgR_new').head(5), False))
o.append('### best 5 (2019+)\n\n' + md(g.sort_values('avgR_new').tail(5), False))
for b in ['N', 'K', 'M', 'L', 'H']:
    o.append(f'### vary {b}\n\n' + md(d[d.block == b][['N','K','M','L','H','n_new','avgR_new','t_new','n_old','avgR_old','t_old']], False))
x = d[d.block == 'LxH']; y = d[d.block == 'NxL']
for v in ['avgR_new', 'avgR_old']:
    o.append(f'### L x H {v}\n\n' + md(x.pivot_table(index='L', columns='H', values=v, aggfunc='first')))
    o.append(f'### N x L {v}\n\n' + md(y.pivot_table(index='N', columns='L', values=v, aggfunc='first')))
o.append(f"LxH both>0: {((x.avgR_new>0)&(x.avgR_old>0)).mean():.2f} min new {x.avgR_new.min():.2f} min old {x.avgR_old.min():.2f}; NxL both>0: {((y.avgR_new>0)&(y.avgR_old>0)).mean():.2f} min new {y.avgR_new.min():.2f} min old {y.avgR_old.min():.2f}; grid min t_new {g.t_new.min():.2f} min t_old {g.t_old.min():.2f}")
open('tables_out.md', 'w').write('\n'.join(o))
