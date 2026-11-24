"""Study 5 (pre-registered 2026-11-24, before running): does an extreme day in energy
equities keep going for a week? Hypothesis comes from the oil brain's study 7, where FADING
+/-2.5 sd USO days lost money more the longer it was held (t -2.49 at 5 days), i.e. oil kept
going. That flipped USO rule was not pre-registered there, so here it is tested on DIFFERENT
instruments with the sign fixed in advance (follow), parameters copied unchanged (2.5 sd,
5-day hold), nothing tuned: an out-of-sample check of the idea, not of the USO numbers.
sd = rolling 63-day std of daily returns known at t (excluding nothing; the day itself is in it,
which makes the threshold slightly harder to hit). Event at close t: r_t > 2.5 sd -> long,
r_t < -2.5 sd -> short, hold 5 trading days; a new event during a hold restarts it.
Cost 5 bp. Benchmark: buy and hold. Start 2002-01-01 (OIH 2001-02, XLE 1998, XOP 2006-06+).
T1 XLE   T2 XOP   T3 OIH
"""
from common import *
def follow(r, k=2.5, hold=5, win=63):
    sd = r.rolling(win).std()
    ev = np.where(r > k * sd, 1.0, np.where(r < -k * sd, -1.0, 0.0))
    pos = np.zeros(len(r)); cur = 0.0; age = 0
    for i in range(len(r)):
        if ev[i] != 0: cur, age = ev[i], 0
        elif cur != 0:
            age += 1
            if age >= hold: cur = 0.0
        pos[i] = cur
    return pd.Series(pos, index=r.index), int((ev != 0).sum())
rows = []
for s, nm in [("XLE", "T1"), ("XOP", "T2"), ("OIH", "T3")]:
    r = px(s).pct_change().dropna()
    p, n = follow(r)
    o = evaluate(f"{nm} follow a 2.5 sd {s} day for 5 days", p, r, 5, start="2002-01-01")
    rows.append(o); print(s, "events", n, "exposure %.3f" % p.loc["2002":].abs().mean())
print(table(rows))
