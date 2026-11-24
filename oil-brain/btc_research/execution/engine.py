"""BTC breakout rule: signal + simulators (daily-bar and hourly-path).

Rule: at bar close, trend = close vs SMA(200). LONG if close > max(high, prev 20 bars) and
close > SMA; SHORT if close < min(low, prev 20 bars) and close < SMA. Stop = entry -/+ 2*ATR(20)
(ATR known at signal close), target = 4x stop distance, time exit after 30 bars, both touched
-> stop. One position at a time.
"""
import numpy as np
import pandas as pd

DIR = __file__.rsplit('/', 1)[0]


def load(name):
    df = pd.read_csv(f'{DIR}/data/{name}.csv', index_col=0, parse_dates=True)
    return df[['Open', 'High', 'Low', 'Close']].astype(float)


def btc_daily():
    d = load('btc_daily')
    return d.iloc[:-1]  # drop today's partial candle


def btc_hourly():
    h = load('btc_hourly')
    h.index = h.index.tz_convert('UTC').tz_localize(None)
    return h.iloc[:-1]  # drop partial hour


def indicators(df, ma_len=200, chan=20, atr_len=20, sma=None):
    o = df.copy()
    o['sma'] = df['Close'].rolling(ma_len).mean() if sma is None else sma
    o['hh'] = df['High'].shift(1).rolling(chan).max()
    o['ll'] = df['Low'].shift(1).rolling(chan).min()
    pc = df['Close'].shift(1)
    tr = pd.concat([df['High'] - df['Low'], (df['High'] - pc).abs(), (df['Low'] - pc).abs()], axis=1).max(axis=1)
    o['atr'] = tr.rolling(atr_len).mean()
    sig = np.where((o['Close'] > o['hh']) & (o['Close'] > o['sma']), 1,
                   np.where((o['Close'] < o['ll']) & (o['Close'] < o['sma']), -1, 0))
    o['sig'] = sig
    o.loc[o[['sma', 'hh', 'll', 'atr']].isna().any(axis=1), 'sig'] = 0
    return o


def r_costs(t, cost_bp=10.0, slip_entry_bp=0.0, slip_stop_bp=0.0, spread=0.0, swap_pa=0.0):
    """Turn a raw trade (entry, exit, dir, risk, days) into R after costs.
    Slippage is applied adversely to the entry price and to stop-exit prices.
    spread: $ per BTC round trip (paid once). swap_pa: annual rate charged on notional per day held."""
    d = t['dir']
    e = t['entry'] * (1 + d * slip_entry_bp / 1e4)
    x = t['exit']
    if t['reason'] == 'stop':
        x = x * (1 - d * slip_stop_bp / 1e4)
    risk = t['risk']  # stop distance in $ (fixed at signal ATR)
    gross = d * (x - e)
    cost = cost_bp / 1e4 * (e + x) + spread + swap_pa / 365.0 * t['days'] * e
    return (gross - cost) / risk


def sim_daily(o, start=None, end=None, delay_bars=1, max_bars=30, stop_mult=2.0, tgt_mult=4.0,
              allow_weekday=None):
    """Daily-bar simulator. Entry at the open of bar i+delay_bars after signal bar i.
    Stop gap: if a bar opens beyond the stop, fill at the open (recorded as gap)."""
    idx = o.index
    O, H, L, C = (o[c].values for c in ['Open', 'High', 'Low', 'Close'])
    sig, atr = o['sig'].values, o['atr'].values
    trades = []
    i = 0
    n = len(o)
    while i < n - delay_bars:
        if sig[i] == 0 or (start is not None and idx[i] < pd.Timestamp(start)) or (end is not None and idx[i] > pd.Timestamp(end)):
            i += 1
            continue
        if allow_weekday is not None and idx[i].weekday() not in allow_weekday:
            i += 1
            continue
        d = sig[i]
        j0 = i + delay_bars
        entry = O[j0]
        risk = stop_mult * atr[i]
        stop = entry - d * risk
        tgt = entry + d * tgt_mult * risk
        exit_px, reason, j, both, gap = None, None, None, False, 0.0
        for j in range(j0, min(j0 + max_bars, n)):
            # gap through stop/target at open (not on entry bar's open)
            if j > j0:
                if d * (O[j] - stop) <= 0:
                    exit_px, reason, gap = O[j], 'stop', d * (stop - O[j]) / stop
                    break
                if d * (O[j] - tgt) >= 0:
                    exit_px, reason = O[j], 'target'
                    break
            hit_s = (L[j] <= stop) if d == 1 else (H[j] >= stop)
            hit_t = (H[j] >= tgt) if d == 1 else (L[j] <= tgt)
            if hit_s:
                exit_px, reason, both = stop, 'stop', hit_t
                break
            if hit_t:
                exit_px, reason = tgt, 'target'
                break
        else:
            if j == n - 1 and j - j0 + 1 < max_bars:
                reason = 'open'
            else:
                reason = 'time'
            exit_px = C[j]
        days = (idx[j] - idx[j0]).days + 1
        trades.append(dict(sig_time=idx[i], dir=d, entry_time=idx[j0], entry=entry, risk=risk, stop=stop,
                           tgt=tgt, exit_time=idx[j], exit=exit_px, reason=reason, both=both, gap=gap,
                           days=days, bars=j - j0 + 1))
        i = j + 1 if reason != 'open' else n  # a signal on the exit bar's own close is skipped (matches claimed 74-75 trades)
    return pd.DataFrame(trades)


def sim_hourly(sigs, h, delay_h=1, max_hours=30 * 24, stop_mult=2.0, tgt_mult=4.0, end_time=None):
    """Hourly-path simulator. sigs: DataFrame indexed by signal close time with dir, atr.
    Entry at open of the hourly bar starting signal_close + delay_h - 1 hours (delay 1h = close of
    the first hour after the signal; delay 0 means open at the signal close).
    Records whether the stop/target were both hit inside the same hour (assume stop)."""
    hidx = h.index
    O, H, L, C = (h[c].values for c in ['Open', 'High', 'Low', 'Close'])
    trades = []
    busy_until = pd.Timestamp.min
    for t, row in sigs.iterrows():
        if t < busy_until:
            continue
        et = t + pd.Timedelta(hours=delay_h)
        k0 = hidx.searchsorted(et)
        if k0 >= len(h):
            break
        d = row['dir']
        entry = O[k0]
        risk = stop_mult * row['atr']
        stop = entry - d * risk
        tgt = entry + d * tgt_mult * risk
        tend = hidx[k0] + pd.Timedelta(hours=max_hours)
        reason = None
        gap = 0.0
        worst = 0.0
        after = np.nan
        k = k0
        for k in range(k0, len(h)):
            if hidx[k] >= tend:
                exit_px, reason = O[k], 'time'
                break
            if k > k0:
                if d * (O[k] - stop) <= 0:
                    exit_px, reason, gap = O[k], 'stop', d * (stop - O[k]) / stop
                    worst = d * (stop - (L[k] if d == 1 else H[k])) / stop
                    after = d * (stop - C[k]) / stop
                    break
                if d * (O[k] - tgt) >= 0:
                    exit_px, reason = O[k], 'target'
                    break
            hit_s = (L[k] <= stop) if d == 1 else (H[k] >= stop)
            hit_t = (H[k] >= tgt) if d == 1 else (L[k] <= tgt)
            if hit_s:
                exit_px, reason = stop, 'stop'
                worst = d * (stop - (L[k] if d == 1 else H[k])) / stop  # extreme beyond stop in that hour
                # next available price after the touch: close of the touching hour
                after = d * (stop - C[k]) / stop
                break
            if hit_t:
                exit_px, reason = tgt, 'target'
                break
        else:
            exit_px, reason = C[k], 'open'
        xt = hidx[k]
        trades.append(dict(sig_time=t, dir=d, entry_time=hidx[k0], entry=entry, risk=risk, stop=stop, tgt=tgt,
                           exit_time=xt, exit=exit_px, reason=reason, gap=gap, worst=worst, after=after,
                           days=max(1, int(np.ceil((xt - hidx[k0]).total_seconds() / 86400)))))
        # flat after exit; next signal must close after exit time
        busy_until = xt + pd.Timedelta(hours=24)  # skip the signal on the exit bar's close, as in sim_daily
    return pd.DataFrame(trades)


def summ(R, label=''):
    R = pd.Series(R).dropna()
    n = len(R)
    if n == 0:
        return dict(label=label, n=0, avgR=np.nan, t=np.nan, win=np.nan, totR=0)
    sd = R.std(ddof=1) if n > 1 else np.nan
    return dict(label=label, n=n, avgR=round(R.mean(), 3), t=round(R.mean() / sd * np.sqrt(n), 2) if n > 1 and sd > 0 else np.nan,
                win=round((R > 0).mean(), 2), totR=round(R.sum(), 1))


def addR(tr, **kw):
    tr = tr.copy()
    tr['R'] = [r_costs(r, **kw) for _, r in tr.iterrows()] if len(tr) else []
    return tr


def candles_from_hourly(h, close_hour):
    """Daily candles closing at close_hour UTC, labelled by their CLOSE time."""
    off = pd.Timedelta(hours=close_hour)
    g = h.resample('24h', offset=off, label='right', closed='left')
    c = pd.DataFrame({'Open': g['Open'].first(), 'High': g['High'].max(), 'Low': g['Low'].min(),
                      'Close': g['Close'].last(), 'cnt': g['Close'].count()})
    c = c[(c['cnt'] >= 20) & (c.index <= h.index[-1] + pd.Timedelta(hours=1))].drop(columns='cnt')
    return c
