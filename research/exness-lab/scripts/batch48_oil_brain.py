"""Batch 48 (pre-registered 2026-11-28 before running): oil brain rules. Earlier oil tests were day trades and
overnight holds on price alone (failed). These use the oil brain's gauges (curve/carry, trend, crack spread,
Brent-WTI spread, OVX, energy stocks vs oil, gold/oil ratio, CAD link). Traded: USOIL 0.01 lot (10 bbl, $830, USO
returns so roll yield is included), UKOIL 0.01 (BNO, $950), USDCAD 0.01 ($1,000, via 6C futures, clean bars).
Cost 8 bp round trip on oil, 3 bp USDCAD. Signals at close t, filled at that close.
 O1 long while carry > 0          O2 carry long/short (deadband 2%)     O3 trend L/S (USO vs 50 and 200-day both)
 O4 trend and carry agree L/S     O5 crack z252 > 1 long, < -1 short   O6 Brent-WTI z60 > 2 / < -2 pair (WTI vs Brent), out at |z| < 0.5
 O7 OVX +25% vs 20d and USO 5d < -5% -> long 5d                         O8 big Wednesday move (>1.5 sd) faded for Thursday
 O9 oil big day (>1.5 sd) and CAD lagged (<0.5 sd same way) -> trade CAD with oil 2d
 O10 XLE minus WTI 20d > +10% long oil 10d, < -10% short 10d           O11 long Feb-Apr (gasoline season)
 O12 USO IBS < 0.2 above 200-day -> long 2d   O13 gold/oil z252 > 2 long oil 20d, < -2 short 20d
 O14 RSI(2) < 10 with carry > 0 -> long until RSI(2) > 70              O15 Donchian 20/10 L/S on USO
 O16 close at 20-day high with carry > 0 -> long 10d
 O17-O20 = O1-O4 on UKOIL (BNO, its own trend; carry from WTI)
Same PASS bar as Batch 47 (random timing = 300 circular shifts of the signal, BH over all tests)."""
import numpy as np, pandas as pd
from brainlab import *
fr = {k: D(t) for k, t in dict(wti="CL=F", brent="BZ=F", rbob="RB=F", ho="HO=F", uso="USO", ovx="^OVX", usdcad="CAD=X", xle="XLE").items()}
F = OB.oil_features(fr)
U = D("USO"); B = D("BNO"); C6 = D("6C=F"); G = D("GLD")
f = F.reindex(U.index).ffill(limit=3); c = U.Close
def rsi(x, n):
    dd = x.diff(); a = dd.clip(lower=0).ewm(alpha=1/n, adjust=False).mean(); b = (-dd.clip(upper=0)).ewm(alpha=1/n, adjust=False).mean(); return 100 - 100 / (1 + a / b)
def state(ent_l, ex_l, ent_s=None, ex_s=None):
    p, out = 0, []
    el, xl = np.asarray(ent_l, bool), np.asarray(ex_l, bool)
    es = np.zeros(len(el), bool) if ent_s is None else np.asarray(ent_s, bool); xs = np.zeros(len(el), bool) if ex_s is None else np.asarray(ex_s, bool)
    for i in range(len(el)):
        if p == 0: p = 1 if el[i] else (-1 if es[i] else 0)
        elif p == 1 and (xl[i] or es[i]): p = -1 if es[i] else 0
        elif p == -1 and (xs[i] or el[i]): p = 1 if el[i] else 0
        out.append(p)
    return np.array(out, float)
tests = []  # (name, market, frame, exposure, bp, signal array, builder(sig)->returns)
def add(nm, mk, d, exp, bp, sig, n=None):
    sig = np.nan_to_num(np.asarray(sig, float))
    b = (lambda x, d=d, n=n, bp=bp: pos_ret(d, hold(x, n) if n else x, bp))
    tests.append((nm, mk, d, exp, bp, sig, b))
cy = f.carry_60d
tr = np.where((c > c.rolling(50).mean()) & (c > c.rolling(200).mean()), 1, np.where((c < c.rolling(50).mean()) & (c < c.rolling(200).mean()), -1, 0))
add("O1 long while carry > 0", "USOIL", U, 830, 8, (cy > 0).astype(float))
add("O2 carry L/S", "USOIL", U, 830, 8, np.where(cy > 0.02, 1, np.where(cy < -0.02, -1, 0)))
add("O3 trend L/S", "USOIL", U, 830, 8, tr)
add("O4 trend+carry agree", "USOIL", U, 830, 8, np.where((tr == 1) & (cy > 0), 1, np.where((tr == -1) & (cy < 0), -1, 0)))
add("O5 crack z", "USOIL", U, 830, 8, np.where(f.crack_321_z252 > 1, 1, np.where(f.crack_321_z252 < -1, -1, 0)))
z = f.brent_wti_z60
add("O7 OVX spike dip", "USOIL", U, 830, 8, ((f.ovx_vs_20d > 0.25) & (c.pct_change(5) < -0.05)).astype(float), 5)
r1 = c.pct_change(); sd = r1.rolling(20).std().shift()
add("O8 Wednesday fade", "USOIL", U, 830, 8, np.where((U.index.dayofweek == 2) & (r1.abs() > 1.5 * sd), -np.sign(r1), 0), 1)
add("O10 XLE lead", "USOIL", U, 830, 8, np.where(f.xle_minus_wti_20d > 0.10, 1, np.where(f.xle_minus_wti_20d < -0.10, -1, 0)), 10)
add("O11 Feb-Apr long", "USOIL", U, 830, 8, U.index.month.isin([2, 3, 4]).astype(float) * 1.0)
ibs = (U.Close - U.Low) / (U.High - U.Low)
add("O12 IBS dip above 200d", "USOIL", U, 830, 8, ((ibs < 0.2) & (c > c.rolling(200).mean())).astype(float), 2)
go = np.log(G.Close.reindex(U.index).ffill() / c); gz = (go - go.rolling(252).mean()) / go.rolling(252).std()
add("O13 gold/oil ratio", "USOIL", U, 830, 8, np.where(gz > 2, 1, np.where(gz < -2, -1, 0)), 20)
r2 = rsi(c, 2)
add("O14 RSI2 dip with carry", "USOIL", U, 830, 8, state((r2 < 10) & (cy > 0), r2 > 70))
hi20, lo20, hi10, lo10 = c.rolling(20).max(), c.rolling(20).min(), c.rolling(10).max(), c.rolling(10).min()
add("O15 Donchian 20/10", "USOIL", U, 830, 8, state(c >= hi20, c <= lo10, c <= lo20, c >= hi10))
add("O16 20d high + carry", "USOIL", U, 830, 8, ((c >= hi20) & (cy > 0)).astype(float), 10)
# pair O6: returns of WTI minus Brent; signal from spread z
pairret = lambda x: (pd.Series(x, index=U.index).shift().fillna(0) * (U.Close.pct_change() - B.Close.reindex(U.index).pct_change()).fillna(0)
                     - pd.Series(x, index=U.index).diff().abs().fillna(0) * 16 / 2e4)
zz = z.reindex(U.index)
o6 = state(zz > 2, zz.abs() < 0.5, zz < -2, zz.abs() < 0.5)
tests.append(("O6 Brent-WTI pair", "USOIL/UKOIL", U, 890, 16, o6, pairret))
# O9 CAD: 6C = USD per CAD, so long 6C = short USDCAD
cr = C6.Close.pct_change(); csd = cr.rolling(20).std().shift(); w = F.wti.pct_change().reindex(C6.index); wsd = w.rolling(20).std().shift()
o9 = np.where((w > 1.5 * wsd) & (cr < 0.5 * csd), 1, np.where((w < -1.5 * wsd) & (cr > -0.5 * csd), -1, 0))
add("O9 CAD catch-up", "USDCAD", C6, 1000, 3, o9, 2)
# UKOIL
fb = F.reindex(B.index).ffill(limit=3); cb = B.Close; cyb = fb.carry_60d
trb = np.where((cb > cb.rolling(50).mean()) & (cb > cb.rolling(200).mean()), 1, np.where((cb < cb.rolling(50).mean()) & (cb < cb.rolling(200).mean()), -1, 0))
add("O17 long while carry > 0", "UKOIL", B, 950, 8, (cyb > 0).astype(float))
add("O18 carry L/S", "UKOIL", B, 950, 8, np.where(cyb > 0.02, 1, np.where(cyb < -0.02, -1, 0)))
add("O19 trend L/S", "UKOIL", B, 950, 8, trb)
add("O20 trend+carry agree", "UKOIL", B, 950, 8, np.where((trb == 1) & (cyb > 0), 1, np.where((trb == -1) & (cyb < 0), -1, 0)))
rows = []
for nm, mk, d, exp, bp, sig, b in tests:
    r = b(sig); st = stats(r, exp)
    b2 = (lambda x, b=b: b(x)) ; st2x = stats(r - (pd.Series(sig, index=r.index).shift().fillna(0).diff().abs().fillna(0)) * bp / 2e4, exp) if nm[:2] != "O6" else st
    rows.append(dict(rule=nm, market=mk, **st, usd_pre_2x=st2x["usd_pre_yr"], _b=(b, sig)))
R = pd.DataFrame(rows); R["p"] = 1.0
cand = R.pre_sh_ok & (R.t_post14 >= 2)
for i in R.index[cand]:
    b, x = R.at[i, "_b"]; R.at[i, "p"] = shift_p(x, b, n=300)
R["fdr"] = bh(R.p.values); R["PASS"] = cand & R.recent_ok & R.fdr & (R.usd_pre_2x > 0)
R = R.drop(columns="_b"); R.to_csv("batch48_results.csv", index=False)
pd.set_option("display.width", 250)
print(R.to_string(index=False))
