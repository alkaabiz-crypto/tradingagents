"""Independent re-implementation of the GLD pullback rule (audit2)."""
import numpy as np, pandas as pd

REENTRY = False  # False = signals on the exit day are ignored (matches claim)

def load(path, drop_after="2026-11-23"):
    df = pd.read_csv(path, index_col=0, parse_dates=True)
    df = df[["Open", "High", "Low", "Close"]].dropna()
    df = df[(df > 0).all(axis=1)]
    df = df[df.index <= drop_after]  # drop today's partial bar
    return df

def indicators(df, sma=200, rsi_n=2, atr_n=20):
    c = df.Close
    out = pd.DataFrame(index=df.index)
    out["sma"] = c.rolling(sma).mean()
    d = c.diff()
    g = d.clip(lower=0).ewm(alpha=1 / rsi_n, adjust=False).mean()
    l = (-d).clip(lower=0).ewm(alpha=1 / rsi_n, adjust=False).mean()
    out["rsi"] = 100 - 100 / (1 + g / l.replace(0, np.nan))
    out.loc[l == 0, "rsi"] = 100
    pc = c.shift(1)
    tr = pd.concat([df.High - df.Low, (df.High - pc).abs(), (df.Low - pc).abs()], axis=1).max(axis=1)
    out["atr"] = tr.rolling(atr_n).mean()
    return out

def simulate_from(o, h, l, c, atr, i_sig, entry_idx, init_k, trail_k):
    """Run one trade. Returns (exit_idx, exit_px, entry_px, open_flag)."""
    n = len(c)
    e = entry_idx
    entry = o[e]
    stop = entry - init_k * atr[i_sig]
    j = e
    while j < n:
        if j > e and o[j] <= stop:
            return j, o[j], entry, False
        if l[j] <= stop:
            return j, stop, entry, False
        stop = max(stop, c[j] - trail_k * atr[j])
        j += 1
    return n - 1, c[n - 1], entry, True

def backtest(df, thr=10, sma=200, rsi_n=2, init_k=2.0, trail_k=3.0, cost_bp=5.0,
             delay=1, fin_daily=0.0, r_k=2.0, reentry=None):
    reentry = REENTRY if reentry is None else reentry
    ind = indicators(df, sma, rsi_n)
    o, h, l, c = (df[x].values for x in ["Open", "High", "Low", "Close"])
    atr = ind.atr.values
    sig = ((df.Close > ind.sma) & (ind.rsi < thr)).values
    dates = df.index
    trades = []
    i = 0
    n = len(c)
    while i < n:
        if sig[i] and not np.isnan(atr[i]) and i + delay < n:
            e = i + delay
            x, xp, ep, opn = simulate_from(o, h, l, c, atr, i, e, init_k, trail_k)
            days = (dates[x] - dates[e]).days
            cost = cost_bp / 1e4 * (ep + xp) + fin_daily * ep * days
            R = (xp - ep - cost) / (r_k * atr[i])
            trades.append(dict(sig=dates[i], entry_date=dates[e], exit_date=dates[x], entry=ep,
                               exit=xp, atr=atr[i], R=R, ret=(xp - ep - cost) / ep,
                               days=days, bars=x - e + 1, open=opn))
            i = x if reentry else x + 1  # reentry: a signal on the exit-day close is allowed
            continue
        i += 1
    return pd.DataFrame(trades)

def stats(t):
    if len(t) == 0:
        return dict(n=0, win=np.nan, avgR=np.nan, t=np.nan, totR=0, maxDD=0)
    r = t.R.values
    cum = np.cumsum(r)
    dd = (np.maximum.accumulate(np.concatenate([[0], cum])) - np.concatenate([[0], cum])).max()
    sd = r.std(ddof=1) if len(r) > 1 else np.nan
    return dict(n=len(r), win=(r > 0).mean(), avgR=r.mean(), t=r.mean() / (sd / np.sqrt(len(r))) if sd else np.nan,
                totR=r.sum(), maxDD=dd)

def period(t, a, b=None):
    m = t.entry_date >= a
    if b:
        m &= t.entry_date <= b
    return t[m]
