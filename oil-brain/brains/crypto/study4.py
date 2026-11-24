"""Study 4: BTC/ETH rotation (pre-registered 2026-11-24, before running).

Mechanism: cross-sectional crypto momentum (Liu, Tsyvinski & Wu 2022: winners keep winning over
weeks). With two coins, the ETH/BTC ratio trend is the cross-sectional signal ("alt season" vs
"BTC dominance" regimes). ETH data start 2017-11-09, so crypto-IS is only ~14 months; lookback 28d
taken from study 1 / the paper, not fitted.

Rules (2 of 15; running total 11 incl. R5 slot):
  R10 rot_ethbtc28: hold ETH if ETH/BTC ratio 28d change > 0 else hold BTC (always invested).
  R11 rot_dual28: hold the coin with the higher 28d return if that return > 0, else flat
      (R1 time-series filter + cross-sectional pick).
Benchmark: BTC buy-and-hold (the brain's benchmark). Return series starts 2017-11-10 (common
dates). Note: R11 vs R1 tests whether adding ETH helps over plain BTC trend.
Expectation: R10 near-zero edge vs BTC; R11 ~ R1 with higher vol.
"""
from common import *

cb, ce = px("BTC-USD"), px("ETH-USD")
idx = ce.index
cb = cb.reindex(idx)
rb, re_ = cb.pct_change(), ce.pct_change()
mb, me = cb.pct_change(28), ce.pct_change(28)
ratio_up = (ce / cb).pct_change(28) > 0
# Combined instrument: a weight vector on two coins is mapped to a single return series. Turnover
# cost is applied on each leg via engine.pnl on each leg separately.
def two_leg(wb, we, name):
    wb, we = wb.fillna(0), we.fillna(0)
    r = engine.pnl(wb, rb.dropna(), 10).add(engine.pnl(we, re_.dropna(), 10), fill_value=0)
    return r

E, C = [], []
specs = {
    "R10 rot_ethbtc28": ((~ratio_up).astype(float), ratio_up.astype(float)),
    "R11 rot_dual28": (((mb >= me) & (mb > 0)).astype(float), ((me > mb) & (me > 0)).astype(float)),
}
for name, (wb, we) in specs.items():
    # Build a synthetic "instrument" = net daily pnl with unit position and zero engine cost,
    # so engine.evaluate sees the costed rule return. Placebo then shifts nothing meaningful,
    # so we run the placebo on the gross-of-switch structure instead: see note below.
    net = two_leg(wb, we, name).dropna().iloc[1:]
    gross_inst = (wb.shift(1) * rb + we.shift(1) * re_).dropna()
    # Engine needs pos+ret: we pass the invested indicator as pos and the chosen-coin return as ret,
    # with 10bp per unit change of the invested indicator plus explicit switch costs folded in.
    inv = (wb + we).clip(upper=1)
    chosen = (wb.shift(1) * rb + we.shift(1) * re_) / inv.shift(1).replace(0, np.nan)
    chosen = chosen.fillna(re_ * 0 + rb).dropna()  # when flat, the 'instrument' is BTC (no P&L anyway)
    sw = ((wb.diff().abs() + we.diff().abs()) - inv.diff().abs()).clip(lower=0).shift(1).fillna(0)
    chosen = chosen - sw.reindex(chosen.index).fillna(0) * 10 / 1e4  # extra cost of coin switches
    bench = rb.reindex(chosen.index)
    e, c = both(name, inv, chosen, bench=bench)
    E.append(e); C.append(c)
    print(name, "check: net-two-leg Sharpe365 2019+ %.2f" % s365(net.loc["2019":]))
show(E, C)
bt = engine.pnl((cb.pct_change(28) > 0).astype(float), rb.dropna(), 10).loc["2019":]
print("R1 on same dates 2019+ Sharpe365 %.2f" % s365(bt))
pd.DataFrame(E).merge(pd.DataFrame(C), on="rule").to_csv(os.path.join(HERE, "study4_results.csv"), index=False)
