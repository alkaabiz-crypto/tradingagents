"""Study 4 (pre-registered 2026-11-24, before running): the oil curve and energy equities.
Curve proxy (as in the oil brain): sum of (USO - USL) daily returns over the last 21 days;
> 0 means the front outperformed the 12-month strip (backwardation-like), < 0 contango-like.
Signals at month-end, held one month (the curve is slow). Hedge betas: rolling 252-day OLS.
B1 roll-yield pair: equity holders do not pay the futures roll; a USO holder does. In contango
   go long XLE / short beta*USO (short USO earns the roll); in backwardation the reverse.
   pos = -sign(curve) on the USO-hedged XLE return. Cost 10 bp. Start 2008-06-01 (USL 2007-12).
B2 tight market -> energy equities beat the market (Gorton, Hayashi & Rouwenhorst 2013:
   backwardation = low inventories = high spot cash flows): pos = +sign(curve) on the
   SPY-hedged XLE return. Cost 10 bp. Start 2008-06-01.
Descriptive (not a rule): XLE's oil beta in contango vs backwardation months.
"""
from common import *
R = rets(["XLE", "USO", "USL", "SPY"])
curve = (R["USO"] - R["USL"]).rolling(21).sum()
hU = hedged(R["XLE"], R[["USO"]], roll_beta(R["XLE"], R[["USO"]])).dropna()
hS = hedged(R["XLE"], R[["SPY"]], roll_beta(R["XLE"], R[["SPY"]])).dropna()
rows = [evaluate("B1 contango -> long XLE short USO (roll yield)", monthly(-np.sign(curve)), hU, 10, start="2008-06-01"),
        evaluate("B2 backwardation -> long XLE short SPY", monthly(np.sign(curve)), hS, 10, start="2008-06-01")]
print(table(rows))
# descriptive: oil beta of XLE (with SPY control) by regime, 2008-06 on
reg = monthly(np.sign(curve)).shift(1)
d = pd.concat([R[["XLE", "USO", "SPY"]], reg.rename("reg")], axis=1).dropna().loc["2008-06-01":]
for k, g in d.groupby("reg"):
    Z = np.column_stack([np.ones(len(g)), g.USO, g.SPY]); b = np.linalg.lstsq(Z, g.XLE, rcond=None)[0]
    print("regime %+d: days %d, XLE beta to USO %.2f, to SPY %.2f, corr(XLE,USO) %.2f" % (k, len(g), b[1], b[2], g.XLE.corr(g.USO)))
