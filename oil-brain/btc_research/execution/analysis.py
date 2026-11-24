"""Execution-realism study for the BTC breakout rule. Writes results/*.csv and results/tables.md."""
import os
import numpy as np
import pandas as pd
import engine as E

OUT = f'{E.DIR}/results'
os.makedirs(OUT, exist_ok=True)
md = []


def to_md(df):
    df = df.astype(object).where(df.notna(), '')
    cols = [str(c) for c in df.columns]
    lines = ['| ' + ' | '.join(cols) + ' |', '|' + '|'.join(['---'] * len(cols)) + '|']
    for _, r in df.iterrows():
        lines.append('| ' + ' | '.join(str(v) for v in r.values) + ' |')
    return '\n'.join(lines)


def table(df, title):
    md.append(f'\n### {title}\n')
    md.append(to_md(df) if isinstance(df, pd.DataFrame) else str(df))
    md.append('')
    print('\n==', title)
    print(df.to_string(index=False) if isinstance(df, pd.DataFrame) else df)


d = E.btc_daily()
h = E.btc_hourly()
o = E.indicators(d)
START = '2019-01-01'
H0 = h.index[0]

# ---------------------------------------------------------------- baseline
base = E.addR(E.sim_daily(o, start=START))
base.to_csv(f'{OUT}/base_trades.csv', index=False)
rows = [E.summ(base.R, 'Yahoo daily 2019-2026, 10 bp/side (this replication)'),
        E.summ(E.addR(E.sim_daily(o, start=START), cost_bp=0).R, 'same, no costs')]
table(pd.DataFrame(rows), 'Baseline replication (claim: 74 trades, +0.79R, t 3.28)')

# daily 200-SMA indexed by its close time (Yahoo date D closes at D+1 00:00 UTC)
sma200 = d['Close'].rolling(200).mean()
sma200.index = sma200.index + pd.Timedelta(days=1)

# ---------------------------------------------------------------- Task 1: close-time dependence
rows, sigsets = [], {}
for H in [0, 4, 8, 12, 16, 20]:
    c = E.candles_from_hourly(h, H)
    smaA = sma200.reindex(c.index, method='ffill')  # latest completed 00:00-close 200d SMA
    oA = E.indicators(c, sma=smaA)
    oB = E.indicators(c, ma_len=100)
    sigsets[H] = oA
    tA = E.addR(E.sim_daily(oA))
    tB = E.addR(E.sim_daily(oB))
    sA, sB = E.summ(tA.R), E.summ(tB.R)
    rows.append(dict(close_utc=f'{H:02d}:00', n_200=sA['n'], avgR_200=sA['avgR'], t_200=sA['t'], totR_200=sA['totR'],
                     n_100=sB['n'], avgR_100=sB['avgR'], t_100=sB['t'], first_sig_100=str(oB[oB.sig != 0].index.min().date())))
t1 = pd.DataFrame(rows)
# reference: Yahoo daily over the same window
ref = E.addR(E.sim_daily(o, start=str((H0 + pd.Timedelta(days=21)).date())))
t1.loc[len(t1)] = dict(close_utc='Yahoo daily 00:00 (ref)', n_200=len(ref), avgR_200=round(ref.R.mean(), 3),
                       t_200=E.summ(ref.R)['t'], totR_200=round(ref.R.sum(), 1))
t1.to_csv(f'{OUT}/t1_close_time.csv', index=False)
table(t1, f'Task 1: avg R by daily close time, {H0.date()} to {h.index[-1].date()} (10 bp/side). '
          '_200 = 200-day SMA from Yahoo daily closes (ffill to the candle close); _100 = 100-candle SMA on the shifted candles (signals only after 100 candles)')

# pooled distribution of the 6 close times
md.append(f"Spread of avg R across the 6 close times (200-SMA): min {t1.avgR_200[:6].min()}, max {t1.avgR_200[:6].max()}, "
          f"mean {t1.avgR_200[:6].mean():.3f}; 00:00 rank among 6: {int(t1.avgR_200[:6].rank(ascending=False)[0])}.\n")

# ---------------------------------------------------------------- Task 2: entry delay
def sigframe(oX, close_time_index=True):
    s = oX[oX.sig != 0][['sig', 'atr']].rename(columns={'sig': 'dir'})
    return s


s00 = sigframe(o)
s00.index = s00.index + pd.Timedelta(days=1)  # signal time = close time
s00 = s00[s00.index >= H0 + pd.Timedelta(hours=1)]
rows = []
hourly_runs = {}
for dl in [0, 1, 4, 24]:
    tr = E.addR(E.sim_hourly(s00, h, delay_h=dl))
    hourly_runs[dl] = tr
    sm = E.summ(tr.R)
    rows.append(dict(sample='00:00 close, hourly path (2y)', delay=f'{dl}h', n=sm['n'], avgR=sm['avgR'], t=sm['t'], totR=sm['totR']))
# pooled over all 6 close times (more trades, correlated)
for dl in [0, 1, 4, 24]:
    allR = []
    for H, oA in sigsets.items():
        s = sigframe(oA)
        allR.append(E.addR(E.sim_hourly(s, h, delay_h=dl)).R)
    sm = E.summ(pd.concat(allR))
    rows.append(dict(sample='pooled 6 close times, hourly path (2y)', delay=f'{dl}h', n=sm['n'], avgR=sm['avgR'], t=sm['t'], totR=sm['totR']))
for db, lab in [(1, 'next open (0h)'), (2, '24h')]:
    tr = E.addR(E.sim_daily(o, start=START, delay_bars=db))
    sm = E.summ(tr.R)
    rows.append(dict(sample='Yahoo daily 2019-2026', delay=lab, n=sm['n'], avgR=sm['avgR'], t=sm['t'], totR=sm['totR']))
t2 = pd.DataFrame(rows)
t2.to_csv(f'{OUT}/t2_entry_delay.csv', index=False)
table(t2, 'Task 2: entry delay after the signal close (stop/target re-anchored to the actual fill; 10 bp/side)')

# entry price drift vs the signal close, per delay
drift = []
for dl in [1, 4, 24]:
    a = hourly_runs[0].set_index('sig_time')
    b = hourly_runs[dl].set_index('sig_time')
    j = a.join(b, rsuffix='_d', how='inner')
    adv = j['dir'] * (j['entry_d'] - j['entry']) / j['risk']
    drift.append(dict(delay=f'{dl}h', matched=len(j), mean_adverse_entry_R=round(adv.mean(), 3), median=round(adv.median(), 3),
                      pct_worse=round((adv > 0).mean(), 2)))
table(pd.DataFrame(drift), 'Task 2b: how far price moved against the entry during the delay, in R (positive = worse fill), 00:00 signals')

# ---------------------------------------------------------------- Task 3: intrabar order
both_full = int(base.both.sum())
both_rows = [dict(sample='Yahoo daily 2019-2026', trades=len(base), stop_exits=int((base.reason == 'stop').sum()),
                  bars_with_both_touched=both_full)]
for H, oA in sigsets.items():
    t = E.sim_daily(oA)
    both_rows.append(dict(sample=f'2y candles closing {H:02d}:00', trades=len(t), stop_exits=int((t.reason == 'stop').sum()),
                          bars_with_both_touched=int(t.both.sum())))
# hourly cross-check: compare daily-bar sim and hourly-path sim on the same 00:00 signals
dsim = E.addR(E.sim_daily(o, start=str(H0.date())))
dsim = dsim[dsim.entry_time >= H0]
hs = hourly_runs[0]
j = dsim.set_index('sig_time').join(hs.set_index(hs.sig_time - pd.Timedelta(days=1)), rsuffix='_h', how='inner')
agree = (j.reason == j.reason_h).mean()
both_rows.append(dict(sample='hourly bars inside the 2y trades (same-hour both touched)', trades=len(hs), stop_exits=int((hs.reason == 'stop').sum()),
                      bars_with_both_touched=0))
t3 = pd.DataFrame(both_rows)
table(t3, 'Task 3: how often a bar touched both stop and target')
# loose test: assume target first when both touched -> identical if zero
cmp = pd.DataFrame([dict(matched_trades=len(j), same_exit_reason=round(agree, 2),
                         avgR_dailybars=round(j.R.mean(), 3), avgR_hourlypath=round(j.R_h.mean(), 3),
                         mean_abs_R_diff=round((j.R - j.R_h).abs().mean(), 3))])
table(cmp, 'Task 3b: daily-bar simulation vs hourly-path simulation of the same 2y signals (entry at the 00:00 open)')
mism = j[j.reason != j.reason_h][['dir', 'reason', 'R', 'reason_h', 'R_h']]
md.append('Mismatched trades (daily vs hourly):\n\n' + (to_md(mism.round(2).reset_index()) if len(mism) else 'none') + '\n')

# ---------------------------------------------------------------- Task 4: gaps and slippage
st = base[base.reason == 'stop']
g = dict(stop_exits=len(st), gapped_open_beyond_stop=int((st.gap > 0).sum()), mean_gap_bp=round(st.gap.mean() * 1e4, 1),
         max_gap_bp=round(st.gap.max() * 1e4, 1))
# daily: overshoot of the stop-hit day's extreme beyond the stop, and close of that day vs stop
ov, cl = [], []
for _, r in st.iterrows():
    bar = d.loc[r.exit_time]
    ext = bar.Low if r.dir == 1 else bar.High
    ov.append(r.dir * (r.stop - ext) / r.stop)
    cl.append(r.dir * (r.stop - bar.Close) / r.stop)
g2 = pd.DataFrame([dict(sample='Yahoo daily 2019-2026 (stop exits)', **g, median_day_extreme_beyond_stop_bp=round(np.median(ov) * 1e4),
                        median_day_close_beyond_stop_bp=round(np.median(cl) * 1e4))])
hst = pd.concat([E.sim_hourly(sigframe(oA), h, delay_h=1) for oA in sigsets.values()])
hst = hst[hst.reason == 'stop']
g3 = pd.DataFrame([dict(sample='hourly, pooled 6 close times, 2y (stop exits)', stop_exits=len(hst),
                        hour_open_gapped_beyond_stop=int((hst.gap > 0).sum()), mean_gap_bp=round(hst.gap.mean() * 1e4, 1),
                        max_gap_bp=round(hst.gap.max() * 1e4, 1),
                        median_hour_extreme_beyond_stop_bp=round(hst.worst.median() * 1e4, 1),
                        p90_hour_extreme_bp=round(hst.worst.quantile(.9) * 1e4, 1),
                        median_hour_close_beyond_stop_bp=round(hst.after.median() * 1e4, 1),
                        p90_hour_close_bp=round(hst.after.quantile(.9) * 1e4, 1))])
table(g2, 'Task 4a: daily stop exits — gap at the open and how far the stop day traded beyond the stop')
table(g3, 'Task 4b: hourly stop exits — gap at the hourly open, extreme of the touching hour, close of the touching hour (bp beyond stop)')
rows = []
for se in [0, 10, 25, 50]:
    r = dict(slip_bp=se)
    for ss in [0, 10, 25, 50]:
        r[f'stop_slip_{ss}'] = round(E.addR(base, slip_entry_bp=se, slip_stop_bp=ss).R.mean(), 3)
    rows.append(r)
t4 = pd.DataFrame(rows).rename(columns={'slip_bp': 'entry_slip_bp'})
t4.to_csv(f'{OUT}/t4_slippage.csv', index=False)
table(t4, 'Task 4c: avg R, 2019-2026, 10 bp/side plus slippage on entries (rows) and stop exits (columns)')
md.append(f"Median stop distance = {base.risk.div(base.entry).median()*1e4:.0f} bp of price, so 10 bp of slippage costs about "
          f"{10/(base.risk.div(base.entry).median()*1e4):.3f}R per occurrence.\n")

# ---------------------------------------------------------------- Task 5: weekends
base['wd'] = base.sig_time.dt.weekday
base['wk'] = np.where(base.wd >= 5, 'Sat/Sun candle', 'Mon-Fri candle')
rows = [E.summ(base[base.wk == k].R, k) for k in ['Mon-Fri candle', 'Sat/Sun candle']]
allh = E.addR(E.sim_daily(o, start='2015-06-01'))
allh['wk'] = np.where(allh.sig_time.dt.weekday >= 5, 'Sat/Sun', 'Mon-Fri')
rows += [E.summ(allh[allh.wk == k].R, f'{k} candle, 2015-2026') for k in ['Mon-Fri', 'Sat/Sun']]
rows.append(E.summ(E.addR(E.sim_daily(o, start=START, allow_weekday={0, 1, 2, 3, 4})).R, 'rule taking weekday signals only, 2019-2026'))
# weekday-only BTC series (ETF-like: weekend candles removed, Monday opens with the weekend gap)
dw = d[d.index.weekday < 5]
ow = E.indicators(dw)
tw = E.addR(E.sim_daily(ow, start=START))
rows.append(E.summ(tw.R, 'BTC with weekend candles deleted (ETF-like), 2019-2026, 30-bar exit'))
tw21 = E.addR(E.sim_daily(ow, start=START, max_bars=21))
rows.append(E.summ(tw21.R, 'same, 21-bar (~30 calendar days) exit'))
t5 = pd.DataFrame(rows)
table(t5, 'Task 5a: weekend vs weekday breakouts (Yahoo daily; candle dated Sat/Sun = signal at the Sun/Mon 00:00 UTC close)')
by = base.groupby(base.sig_time.dt.day_name()).R.agg(['count', 'mean']).round(3)
md.append('By weekday of the signal candle (2019-2026):\n\n' + to_md(by.reset_index()) + '\n')
print(by)
md.append(f"ETF-like BTC stop exits gapped through the stop at the open in {int((tw[tw.reason=='stop'].gap>0).sum())} of "
          f"{int((tw.reason=='stop').sum())} cases, mean gap {tw[tw.reason=='stop'].gap.mean()*1e4:.0f} bp, max {tw.gap.max()*1e4:.0f} bp.\n")

ib = E.load('ibit_daily')
ib = ib.iloc[:-1] if ib.index[-1].date() == pd.Timestamp.today().date() else ib
rows = []
for ma in [200, 100]:
    oi = E.indicators(ib, ma_len=ma)
    for mb in [30, 21]:
        ti = E.addR(E.sim_daily(oi, max_bars=mb))
        sm = E.summ(ti.R, f'IBIT, {ma}-day SMA, {mb}-bar exit')
        sm['first_signal_possible'] = str(oi.dropna().index.min().date())
        sm['stop_gaps'] = int((ti.gap > 0).sum()) if len(ti) else 0
        sm['max_gap_bp'] = round(ti.gap.max() * 1e4) if len(ti) else 0
        rows.append(sm)
        if ma == 200 and mb == 30:
            ti.to_csv(f'{OUT}/ibit_trades.csv', index=False)
            first = oi.dropna().index.min()
    # BTC on the same window
bt = E.addR(E.sim_daily(o, start=str(first.date())))
rows.append(E.summ(bt.R, f'BTC-USD 24/7, same window from {first.date()}'))
oi100 = E.indicators(ib, ma_len=100)
bt2 = E.addR(E.sim_daily(o, start=str(oi100.dropna().index.min().date())))
rows.append(E.summ(bt2.R, f'BTC-USD 24/7, from {oi100.dropna().index.min().date()} (100-day IBIT window)'))
t5b = pd.DataFrame(rows)
table(t5b, f'Task 5b: IBIT daily ({ib.index[0].date()} to {ib.index[-1].date()}) vs BTC 24/7')

# ---------------------------------------------------------------- Task 6: CFD costs
px_now = d.Close.iloc[-1]
rows = []
for sp in [10, 20, 40]:
    r = dict(spread_usd=sp)
    for sw in [0, .10, .20, .30]:
        r[f'swap_{int(sw*100)}%'] = round(E.addR(base, cost_bp=0, spread=sp, swap_pa=sw).R.mean(), 3)
    rows.append(r)
t6a = pd.DataFrame(rows)
table(t6a, 'Task 6a: avg R, 2019-2026, spread in fixed $ per BTC round trip (historical prices, so early trades at $4-10k pay a lot) + swap per year on notional, no commission')
rows = []
for sp in [10, 20, 40]:
    bp = sp / px_now * 1e4
    r = dict(spread_usd=sp, spread_bp_at_today=round(bp, 1))
    for sw in [0, .10, .20, .30]:
        r[f'swap_{int(sw*100)}%'] = round(E.addR(base, cost_bp=bp / 2, swap_pa=sw).R.mean(), 3)
    rows.append(r)
t6b = pd.DataFrame(rows)
table(t6b, f'Task 6b: same, spread scaled to today\'s price (${px_now:,.0f}) i.e. charged as bp of price')
md.append(f"Average holding period: {base.days.mean():.1f} days; median stop distance {base.risk.div(base.entry).median()*100:.1f}% of price. "
          f"Each 10%/yr of swap costs about {0.10/365*base.days.mean()/base.risk.div(base.entry).median():.3f}R per trade on average.\n")

# realistic all-in
rows = []
for lab, kw in [('claim-like: 10 bp/side, next open', dict()),
                ('CFD mid: $20 spread (today bp), 20% swap, 10 bp entry+stop slip', dict(cost_bp=20 / px_now * 1e4 / 2, swap_pa=.2, slip_entry_bp=10, slip_stop_bp=10)),
                ('CFD bad: $40 spread (today bp), 30% swap, 25 bp entry+stop slip', dict(cost_bp=40 / px_now * 1e4 / 2, swap_pa=.3, slip_entry_bp=25, slip_stop_bp=25)),
                ('CFD bad, fixed-$ spread on historical prices', dict(cost_bp=0, spread=40, swap_pa=.3, slip_entry_bp=25, slip_stop_bp=25))]:
    rows.append(E.summ(E.addR(base, **kw).R, lab))
t6c = pd.DataFrame(rows)
table(t6c, 'Task 6c: all-in expectancy, 2019-2026 Yahoo daily')
# by year for the mid case
mid = E.addR(base, cost_bp=20 / px_now * 1e4 / 2, swap_pa=.2, slip_entry_bp=10, slip_stop_bp=10)
yr = mid.groupby(mid.sig_time.dt.year).R.agg(['count', 'mean', 'sum']).round(2)
md.append('CFD mid case by year:\n\n' + to_md(yr.reset_index()) + '\n')
print(yr)

open(f'{OUT}/tables.md', 'w').write('\n'.join(md))
