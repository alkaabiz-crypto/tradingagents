"""BTC breakout rule rebuild. Usage: python3 bt.py [variant]"""
import sys, numpy as np, pandas as pd

HERE = '/tmp/claude-0/-home-user/8b993c28-efa9-5855-8d47-a8a3f974ffea/scratchpad/oil/oil-brain/btc_research'

def load():
    df = pd.read_csv(f'{HERE}/replication/data/BTC-USD.csv', parse_dates=['Date']).set_index('Date')
    return df.dropna()

def backtest(df, lookback=20, sma_n=200, atr_n=20, stop_k=2.0, tgt_R=4.0, max_days=30,
             cost=0.001, time_exit_mode='close_day30'):
    o, h, l, c = (df[x].values for x in ['Open', 'High', 'Low', 'Close'])
    dates = df.index
    sma = pd.Series(c).rolling(sma_n).mean().values
    hh = pd.Series(h).rolling(lookback).max().shift(1).values
    ll = pd.Series(l).rolling(lookback).min().shift(1).values
    pc = np.r_[np.nan, c[:-1]]
    tr = np.nanmax(np.vstack([h - l, np.abs(h - pc), np.abs(l - pc)]), axis=0)
    atr = pd.Series(tr).rolling(atr_n).mean().values
    n = len(c); trades = []; t = sma_n
    while t < n - 1:
        side = 0
        if not np.isnan(sma[t]) and not np.isnan(atr[t]):
            if c[t] > sma[t] and c[t] > hh[t]: side = 1
            elif c[t] < sma[t] and c[t] < ll[t]: side = -1
        if side == 0:
            t += 1; continue
        e = t + 1; entry = o[e]; sd = stop_k * atr[t]
        stop = entry - side * sd; tgt = entry + side * tgt_R * sd
        last = e + max_days - 1  # 30 bars incl. entry bar, exit at close of bar 30
        exit_px = None; j = e
        while j < n:
            if j > e:  # gap through levels at open
                if side == 1 and o[j] <= stop: exit_px, why = o[j], 'stop'; break
                if side == -1 and o[j] >= stop: exit_px, why = o[j], 'stop'; break
                if side == 1 and o[j] >= tgt: exit_px, why = o[j], 'target'; break
                if side == -1 and o[j] <= tgt: exit_px, why = o[j], 'target'; break
            hit_s = (l[j] <= stop) if side == 1 else (h[j] >= stop)
            hit_t = (h[j] >= tgt) if side == 1 else (l[j] <= tgt)
            if hit_s: exit_px, why = stop, 'stop'; break
            if hit_t: exit_px, why = tgt, 'target'; break
            if j == last: exit_px, why = c[j], 'time'; break
            j += 1
        if exit_px is None:  # still open at data end
            j = n - 1; exit_px, why = c[j], 'open'
        move = side * (exit_px - entry)
        R = (move - cost * (entry + exit_px)) / sd
        trades.append(dict(signal=dates[t].date(), entry_date=dates[e].date(), exit_date=dates[j].date(),
                           side='LONG' if side == 1 else 'SHORT', entry=round(entry, 2), exit=round(exit_px, 2),
                           stop_dist=round(sd, 2), stop_pct=round(sd / entry * 100, 2), R=round(R, 3),
                           days=int(j - e + 1), reason=why))
        t = j  # flat at close of exit bar; may signal same day
    return pd.DataFrame(trades)

def summ(tr):
    r = tr.R.values
    return dict(n=len(r), avgR=r.mean(), t=r.mean() / r.std(ddof=1) * np.sqrt(len(r)) if len(r) > 1 else np.nan,
                win=(r > 0).mean(), totR=r.sum())

if __name__ == '__main__':
    df = load(); tr = backtest(df)
    tr.to_csv(f'{HERE}/risk/trades_2015_now.csv', index=False)
    d = pd.to_datetime(tr.entry_date)
    print('all', summ(tr)); print('2019+', summ(tr[d >= '2019-01-01']))
    print(tr.tail(10).to_string())
