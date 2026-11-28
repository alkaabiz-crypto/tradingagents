"""Batch 49 (pre-registered 2026-11-28 before running): walk-forward 'brain score'. Instead of single patterns, a ridge
regression (alpha 10 on standardised features, fixed) learns each market's own mix of candle-brain features, indicators
and cross-market/oil-brain gauges, retrained every January on all earlier data (min 5 years), applied to that year only.
Features at close t: candle (IBS, signed body, wicks, range/ATR, gap/ATR, trend 50/200, distance to 20d low/high in ATR,
ATR rank), price (1/5/20-day returns over 20d vol, RSI2, RSI14), cross (VIX 1d change, WTI 1d return, dollar index
1d return, TLT 1d return, oil carry and crack z from the oil brain). Target: next-day return / 20d vol.
Trade: side = sign(score) only when |score| > the 70th percentile of |score| on the training years; hold 1 day (S1) or
2 days (S2). Markets: US500, USTEC, US30, XAU, XAG, USOIL (USO), BTC, ETH, EURUSD/GBPUSD/USDJPY/AUDUSD/USDCAD via CME
futures (clean bars; JPY/CAD futures are the inverse pair, sign handled by trading the future).
Same PASS bar as Batches 47-48."""
import numpy as np, pandas as pd
from brainlab import *
MKS = dict(MK); MKS.update({"EURUSD": ("6E=F", "6E=F", 1100, 2.0), "GBPUSD": ("6B=F", "6B=F", 1300, 3.0), "USDJPY": ("6J=F", "6J=F", 1000, 2.5),
                           "AUDUSD": ("6A=F", "6A=F", 650, 3.0), "USDCAD": ("6C=F", "6C=F", 1000, 3.0)}); MKS.pop("UKOIL")
def rsi(x, n):
    dd = x.diff(); a = dd.clip(lower=0).ewm(alpha=1/n, adjust=False).mean(); b = (-dd.clip(upper=0)).ewm(alpha=1/n, adjust=False).mean(); return 100 - 100 / (1 + a / b)
fr = {k: D(t) for k, t in dict(wti="CL=F", brent="BZ=F", rbob="RB=F", ho="HO=F", uso="USO", ovx="^OVX", usdcad="CAD=X", xle="XLE").items()}
OF = OB.oil_features(fr)
X0 = pd.DataFrame({"vix_chg": D("^VIX").Close.pct_change(), "wti_r1": D("USO").Close.pct_change(), "dxy_r1": D("DX-Y.NYB").Close.pct_change(),
                   "tlt_r1": D("TLT").Close.pct_change(), "oil_carry": OF.carry_60d, "crack_z": OF.crack_321_z252})
def feats(d):
    F = CB.candle_features(d); c = d.Close; r = c.pct_change(); v = r.rolling(20).std()
    X = pd.DataFrame(index=d.index)
    for k in ("ibs", "upper_wick", "lower_wick", "range_atr", "gap_atr", "trend_200", "trend_50", "dist_20d_low_atr", "dist_20d_high_atr", "atr_pct_rank"): X[k] = F[k]
    X["body"] = (d.Close - d.Open) / (d.High - d.Low).replace(0, np.nan)
    X["r1"], X["r5"], X["r20"] = r / v, c.pct_change(5) / (v * np.sqrt(5)), c.pct_change(20) / (v * np.sqrt(20))
    X["rsi2"], X["rsi14"] = rsi(c, 2) / 100, rsi(c, 14) / 100
    X = X.join(X0.reindex(d.index).ffill(limit=3))
    y = (r.shift(-1) / v)
    return X.clip(-10, 10), y
def walk(d, hold_n, alpha=10.0, q=0.70):
    X, y = feats(d); X = X.replace([np.inf, -np.inf], np.nan)
    score = pd.Series(np.nan, index=d.index); thr = pd.Series(np.nan, index=d.index)
    yrs = sorted(set(d.index.year)); first = d.index[0].year + 5
    for Y in yrs:
        if Y < first: continue
        tr = (X.index.year < Y); te = (X.index.year == Y)
        Xt, yt = X[tr], y[tr]; m = Xt.notna().all(axis=1) & yt.notna(); Xt, yt = Xt[m], yt[m].clip(-5, 5)
        if len(Xt) < 750: continue
        mu, sd = Xt.mean(), Xt.std().replace(0, 1); Z = ((Xt - mu) / sd).values
        w = np.linalg.solve(Z.T @ Z + alpha * np.eye(Z.shape[1]), Z.T @ (yt.values - yt.mean()))
        th = np.quantile(np.abs(Z @ w), q)
        Ze = ((X[te] - mu) / sd).fillna(0).values; score[te] = Ze @ w; thr[te] = th
    sig = np.where(score.abs() > thr, np.sign(score), 0.0)
    return np.nan_to_num(sig)
rows = []
for mk, (hp, _, exp, bp) in MKS.items():
    d = D(hp)
    for nm, n in (("S1 hold 1d", 1), ("S2 hold 2d", 2)):
        sig = walk(d, n); b = (lambda x, d=d, n=n, bp=bp: pos_ret(d, hold(x, n), bp))
        r = b(sig); st = stats(r, exp); st2 = stats(pos_ret(d, hold(sig, n), 2 * bp), exp)
        rows.append(dict(rule=nm, market=mk, **st, usd_pre_2x=st2["usd_pre_yr"], _b=(b, sig)))
R = pd.DataFrame(rows); R["p"] = 1.0
cand = R.pre_sh_ok & (R.t_post14 >= 2)
for i in R.index[cand]:
    b, x = R.at[i, "_b"]; R.at[i, "p"] = shift_p(x, b, n=300)
R["fdr"] = bh(R.p.values); R["PASS"] = cand & R.recent_ok & R.fdr & (R.usd_pre_2x > 0)
sigs = {f"{a}|{b}": c[1] for a, b, c in zip(R["rule"], R["market"], R["_b"])}
pd.to_pickle(sigs, "batch49_signals.pkl")
R = R.drop(columns="_b"); R.to_csv("batch49_results.csv", index=False)
pd.set_option("display.width", 250); print(R.to_string(index=False))
