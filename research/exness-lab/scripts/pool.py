"""Candidate pool: every lab pass so far as a daily $ series at Exness min lots (today's exposure)."""
from planA_legs import *
def rsi(x, n):
    dd = x.diff(); a = dd.clip(lower=0).ewm(alpha=1/n, adjust=False).mean(); b = (-dd.clip(upper=0)).ewm(alpha=1/n, adjust=False).mean(); return 100 - 100 / (1 + a / b)
def ibs(d): return ((d.Close - d.Low) / (d.High - d.Low)) < 0.2
def wr(d): return (-100 * (d.High.rolling(10).max() - d.Close) / (d.High.rolling(10).max() - d.Low.rolling(10).min())) < -90
def pool():
    P = {}
    q, s, di, b, e, g = D("QQQ"), D("SPY"), D("DIA"), D("BTC-USD"), D("ETH-USD"), D("GLD")
    vix = D("^VIX").Close.reindex(q.index).ffill()
    s200 = q.Close > q.Close.rolling(200).mean()
    P["USTEC overnight"] = ((q.Open.shift(-1) / q.Close - 1) - 3.4e-4).where(s200, 0).shift().fillna(0) * 1330
    P["IBS USTEC"] = pos_ret(q, hold(ibs(q).astype(float).values, 2), 1.4) * 1330
    P["IBS US30"] = pos_ret(di, hold(ibs(di).astype(float).values, 2), 1.3) * 500
    P["%R USTEC"] = pos_ret(q, hold(wr(q).astype(float).values, 2), 1.4) * 1330
    P["IBS USTEC fear days"] = pos_ret(q, hold((ibs(q) & (vix > vix.rolling(20).mean())).astype(float).values, 2), 1.4) * 1330
    c = s.Close; r2 = rsi(c, 2)
    ent = (r2 < r2.shift()) & (r2.shift() < r2.shift(2)) & (r2.shift(2) < r2.shift(3)) & (r2.shift(2) < 60) & (r2 < 10) & (c > c.rolling(200).mean())
    p, out = 0, []
    for a_, x_ in zip(ent.values, (r2 > 70).values):
        if p == 0 and a_: p = 1
        elif p == 1 and x_: p = 0
        out.append(p)
    P["Connors R3 US500"] = pos_ret(s, np.array(out, float), 1.6) * 1000
    mon_dn = ((q.index.dayofweek == 0) & (q.Close < q.Close.shift())).astype(float).values
    P["Turnaround Tue USTEC"] = pos_ret(q, hold(mon_dn, 1), 1.4) * 1330
    cb = b.Close; ee = cb.ewm(span=15, adjust=False).mean().ewm(span=15, adjust=False).mean().ewm(span=15, adjust=False).mean(); tr = ee.pct_change()
    P["BTC TRIX"] = pos_ret(b, (tr > tr.ewm(span=9, adjust=False).mean()).astype(float).values, 1.1) * 595
    Pe = CB.detect_patterns(e); sh = lambda m: m.shift().fillna(False).astype(bool)
    P["ETH ID/NR4"] = straddle(e, e.High.shift(), e.Low.shift(), sh(Pe.inside_bar & Pe.nr4), 5.0) * 165
    P["ETH NR4"] = straddle(e, e.High.shift(), e.Low.shift(), sh(Pe.nr4), 5.0) * 165
    rg = e.High - e.Low
    P["ETH Williams"] = straddle(e, e.Open + 0.5 * rg.shift(), e.Open - 0.5 * rg.shift(), pd.Series(True, index=e.index), 5.0) * 165
    m = pd.Series(g.index.to_period("M"), index=g.index); tdom = m.groupby(m).cumcount() + 1; last = m != m.shift(-1)
    tom = (last | (tdom <= 3)).shift(-1).fillna(False).astype(float).values
    P["Gold turn of month"] = pos_ret(g, tom, 1.5) * 3640
    return P
