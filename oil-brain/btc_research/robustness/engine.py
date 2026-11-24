"""BTC breakout backtest engine (daily bars, Yahoo BTC-USD).

Conventions (explicit, since the rule text leaves some open):
- Signal on close of day t: close[t] > max(high[t-N..t-1]) (long) / close[t] < min(low[t-N..t-1]) (short).
- Trend filter: close[t] vs SMA_L(close)[t]; L=None -> both directions allowed.
- Entry at open[t+1]. ATR = simple mean of true range over t-19..t (window 20, fixed regardless of N).
- Stop = entry -/+ K*ATR, target = entry +/- M*K*ATR. Checked intrabar from the entry bar on.
  If the open of a later bar gaps through the stop/target, fill at the open (gap_fill=True).
  Both touched in one bar -> stop.
- Time exit: at the close of the H-th bar held (entry bar = bar 1). H=None -> no time exit.
- M='trail': no target; trailing stop = max(initial stop, highest high since entry - 3*ATR(20) current),
  updated at each close, effective next bar (mirror for shorts).
- One position at a time; a new signal can fire on the close of the exit day.
- Cost 10 bp per side on notional: R = (signed move - 0.001*(entry+exit)) / stop distance.
"""
import numpy as np, pandas as pd, os

HERE = os.path.dirname(os.path.abspath(__file__))


def load(drop_last_partial=True):
    d = pd.read_csv(os.path.join(HERE, 'btc_yahoo.csv'), index_col=0, parse_dates=True)
    d = d[d.index <= '2026-11-23'] if drop_last_partial else d
    return d


class Data:
    def __init__(self, df):
        self.df = df
        self.idx = df.index
        self.o = df.Open.values; self.h = df.High.values; self.l = df.Low.values; self.c = df.Close.values
        pc = np.r_[np.nan, self.c[:-1]]
        tr = np.nanmax(np.vstack([self.h - self.l, np.abs(self.h - pc), np.abs(self.l - pc)]), axis=0)
        self.atr = pd.Series(tr).rolling(20).mean().values
        self._hh = {}; self._ll = {}; self._sma = {}
        self.year = df.index.year.values

    def hh(self, n):
        if n not in self._hh:
            self._hh[n] = pd.Series(self.h).rolling(n).max().shift(1).values
            self._ll[n] = pd.Series(self.l).rolling(n).min().shift(1).values
        return self._hh[n], self._ll[n]

    def sma(self, L):
        if L not in self._sma:
            self._sma[L] = pd.Series(self.c).rolling(L).mean().values
        return self._sma[L]


def backtest(D, N=20, K=2.0, M=4, L=200, H=30, cost=0.001, trail_mult=3.0, daily=False, gap_fill=True, reenter_exit_day=True, sig_override=None):
    """Returns DataFrame of trades (and optionally a daily R-pnl array)."""
    o, h, l, c, atr = D.o, D.h, D.l, D.c, D.atr
    hh, ll = D.hh(N)
    n = len(c)
    if L is None:
        up = np.ones(n, bool); dn = np.ones(n, bool); valid = ~np.isnan(hh) & ~np.isnan(atr)
    else:
        s = D.sma(L); valid = ~np.isnan(s) & ~np.isnan(hh) & ~np.isnan(atr)
        up = c > s; dn = c < s
    with np.errstate(invalid='ignore'):
        longsig = valid & up & (c > hh)
        shortsig = valid & dn & (c < ll)
    if sig_override is not None:
        longsig, shortsig = sig_override
    trail = (M == 'trail')
    trades = []
    dpnl = np.zeros(n) if daily else None
    t = 0
    while t < n - 1:
        if not (longsig[t] or shortsig[t]):
            t += 1; continue
        side = 1 if longsig[t] else -1
        e = t + 1; ent = o[e]; sd = K * atr[t]
        stop = ent - side * sd
        tgt = None if trail else ent + side * M * sd
        ext = None; exit_px = None; reason = None
        last = n - 1 if H is None else min(n - 1, e + H - 1)
        best = h[e] if side == 1 else l[e]
        prev_mark = ent
        j = e
        while j <= last:
            # gap at open (not on entry bar, which opens at entry)
            if j > e and gap_fill:
                if side == 1 and o[j] <= stop: exit_px, reason = o[j], 'stop'; break
                if side == -1 and o[j] >= stop: exit_px, reason = o[j], 'stop'; break
                if tgt is not None:
                    if side == 1 and o[j] >= tgt: exit_px, reason = o[j], 'target'; break
                    if side == -1 and o[j] <= tgt: exit_px, reason = o[j], 'target'; break
            hit_s = (l[j] <= stop) if side == 1 else (h[j] >= stop)
            hit_t = False if tgt is None else ((h[j] >= tgt) if side == 1 else (l[j] <= tgt))
            if hit_s: exit_px, reason = stop, 'stop'; break
            if hit_t: exit_px, reason = tgt, 'target'; break
            if daily:
                dpnl[j] += side * (c[j] - prev_mark) / sd
                prev_mark = c[j]
            if trail:
                best = max(best, h[j]) if side == 1 else min(best, l[j])
                ts = best - side * trail_mult * atr[j]
                stop = max(stop, ts) if side == 1 else min(stop, ts)
            j += 1
        if exit_px is None:
            j = last
            exit_px = c[j]
            reason = 'time' if (H is not None and last == e + H - 1) else 'open'
        if daily and reason in ('stop', 'target'):
            dpnl[j] += side * (exit_px - prev_mark) / sd
        cst = cost * (ent + exit_px)
        R = (side * (exit_px - ent) - cst) / sd
        if daily:
            dpnl[e] -= cost * ent / sd; dpnl[j] -= cost * exit_px / sd
        trades.append((D.idx[t], D.idx[e], D.idx[j], side, ent, exit_px, sd, reason, R, j - e + 1))
        t = j if reenter_exit_day else j + 1  # can signal on exit-day close
    tr = pd.DataFrame(trades, columns=['signal', 'entry_date', 'exit_date', 'side', 'entry', 'exit', 'stopdist', 'reason', 'R', 'bars'])
    return (tr, dpnl) if daily else tr


def stats(R):
    R = np.asarray(R, float)
    n = len(R)
    if n < 2: return dict(n=n, avgR=np.nan if n == 0 else R.mean(), t=np.nan, win=np.nan, totR=R.sum() if n else 0)
    sd = R.std(ddof=1)
    return dict(n=n, avgR=R.mean(), t=R.mean() / sd * np.sqrt(n) if sd > 0 else np.nan, win=(R > 0).mean(), totR=R.sum())


def period(tr, start, end=None):
    m = tr.entry_date >= start
    if end is not None: m &= tr.entry_date <= end
    return tr[m]
