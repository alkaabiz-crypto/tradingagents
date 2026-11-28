"""Plan A legs as daily $ series at min lots (scaled to today's exposure), plus helper to build candidate series."""
from brainlab import *
def planA():
    out = {}
    s = D("SPY"); c = s.Close
    out["A US500 10-day low"] = pos_ret(s, hold((c <= c.rolling(10).min()).astype(float).values, 3), 1.6) * 1000
    b = D("BTC-USD"); o, h, l, cc = b.Open, b.High, b.Low, b.Close; rg = h - l
    ok = (rg <= rg.rolling(4).min()).shift().fillna(False).astype(bool)
    out["A BTC NR4"] = straddle(b, h.shift(), l.shift(), ok, 1.1) * 595
    out["A BTC Williams"] = straddle(b, o + 0.5 * rg.shift(), o - 0.5 * rg.shift(), pd.Series(True, index=b.index), 1.1) * 595
    e = D("ETH-USD"); out["A ETH above 50d"] = pos_ret(e, (e.Close > e.Close.rolling(50).mean()).astype(float).values, 5.0) * 165
    return out
