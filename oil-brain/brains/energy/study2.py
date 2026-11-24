"""Study 2 (pre-registered 2026-11-24, before running; written after study 1 failed, no
parameter taken from study 1's results): pairs / mean reversion of hedged energy spreads
(Gatev, Goetzmann & Rouwenhorst 2006 RFS: enter at a 2-sd divergence, exit at convergence).
Spread return h_t = r_A - b_{t-1}' r_H with rolling 252-day OLS betas (no look-ahead).
Divergence z_t = sum of h over the last 20 days / (std of h over 252 days * sqrt(20)).
Rule (fixed from the paper, not tuned): z > +2 -> short the spread; z < -2 -> long; hold until
z crosses 0 (sign change) or 10 trading days have passed (short-term trader's cap), then flat.
Signals daily at the close. Costs 10 bp per unit of spread turnover (two legs; 15 bp for P3's three).
P1 XLE vs USO (A = XLE, H = USO)          start 2007-06-01
P2 XOP vs XLE (E&P vs the sector)        start 2007-06-01
P3 refiners vs crack proxy: A = equal-weight VLO, MPC, PSX (those listed), H = XLE and the
   crack proxy (UGA - USO)                start 2009-03-01 (UGA starts 2008-02)
Benchmark: the spread held long (engine default).
"""
from common import *

def pair_rule(h, z_in=2.0, look=20, win=252, cap=10):
    z = h.rolling(look).sum() / (h.rolling(win).std() * np.sqrt(look))
    pos = pd.Series(0.0, index=h.index); cur = 0.0; age = 0
    zv = z.values
    for i in range(len(h)):
        zi = zv[i]
        if np.isnan(zi): pos.iloc[i] = 0; continue
        if cur != 0:
            age += 1
            if np.sign(zi) == cur or age >= cap:   # z crossed zero (cur is opposite of z sign at entry)
                cur = 0.0; age = 0
        if cur == 0:
            if zi > z_in: cur, age = -1.0, 0
            elif zi < -z_in: cur, age = 1.0, 0
        pos.iloc[i] = cur
    return pos, z

R = rets(["XLE", "XOP", "USO", "UGA", "VLO", "MPC", "PSX"])
rows = []
h1 = hedged(R["XLE"], R[["USO"]], roll_beta(R["XLE"], R[["USO"]])).dropna()
p1, _ = pair_rule(h1)
rows.append(evaluate("P1 pair XLE vs USO", p1, h1, 10, start="2007-06-01"))
h2 = hedged(R["XOP"], R[["XLE"]], roll_beta(R["XOP"], R[["XLE"]])).dropna()
p2, _ = pair_rule(h2)
rows.append(evaluate("P2 pair XOP vs XLE", p2, h2, 10, start="2007-06-01"))
ref = R[["VLO", "MPC", "PSX"]].mean(axis=1)
H3 = pd.DataFrame({"XLE": R["XLE"], "CRACK": R["UGA"] - R["USO"]})
h3 = hedged(ref, H3, roll_beta(ref, H3)).dropna()
p3, _ = pair_rule(h3)
rows.append(evaluate("P3 refiners vs XLE + crack", p3, h3, 15, start="2009-03-01"))
print(table(rows))
for p, nm in [(p1, "P1"), (p2, "P2"), (p3, "P3")]:
    print(nm, "exposure %.2f" % p.abs().mean())
