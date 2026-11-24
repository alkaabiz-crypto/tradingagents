"""Study 2: robustness of R1 + volatility-managed crypto (pre-registered 2026-11-24, before running,
after seeing study 1 results; nothing here changes R1's parameters).

Part A (counted as 1 rule slot, R5: no parameter is selected from it, it is a diagnostic):
  R1 with lookbacks 14, 21, 35, 42, 56 days; R1 with a 1-day execution delay; R1 per calendar year
  vs buy-and-hold; R1 at 25 bp; R1 traded through IBIT (2024-01-11+, US hours) with 5 bp,
  signal = BTC 28d return from the PREVIOUS UTC day (BTC bar t closes 00:00 UTC t+1, after the
  ETF close on t, so it must be lagged one day for the ETF).
  Pass condition stated now: neighbours all post-2019 Sharpe > buy-and-hold; delay version still
  beats buy-and-hold. If not, R1 is fragile and stays a candidate at most.

Part B (vol-managed; Moreira & Muir 2017 idea applied to crypto):
  R6 btc_volman: position = min(1, 0.6 / realized vol(30d, annualized sqrt365)). Target 0.6 is a
     round number below BTC's long-run vol (~0.7-0.8), fixed now, not fitted.
  R7 btc_tsmom28_volman: R1 signal x R6 sizing.
Expectation: vol-managed long-only reduces drawdown, Sharpe gain small (crypto vol clusters but
returns are not lower in high-vol states -> may fail vs buy-and-hold).
"""
from common import *

btc = ret("BTC-USD"); cb = px("BTC-USD")
print("== Part A: R1 neighbours / delay (engine post Sharpe, crypto post Sharpe, crypto HO) ==")
bh = crypto_eval("bh", pd.Series(1.0, index=btc.index), btc, n_placebo=1)
print("buy-hold: cpost %.2f cHO %.2f dd %.2f" % (bh["cpost"], bh["cHO"], bh["dd"]))
for L in [14, 21, 28, 35, 42, 56]:
    pos = (cb.pct_change(L) > 0).astype(float)
    e = engine.evaluate(f"L{L}", pos, btc, 10, n_placebo=1)
    c = crypto_eval(f"L{L}", pos, btc, n_placebo=1)
    print(f"L={L:3d} eng_post {e['post']:.2f} (bench {e['bench_post']:.2f}) t {e['t_post']:.2f} | "
          f"c_post {c['cpost']:.2f} cOOS {c['cOOS']:.2f} cHO {c['cHO']:.2f} dd {c['dd']:.2f}")
pos1 = (cb.pct_change(28) > 0).astype(float)
for d in [1, 2]:
    e = engine.evaluate(f"delay{d}", pos1.shift(d), btc, 10, n_placebo=1)
    c = crypto_eval(f"delay{d}", pos1.shift(d), btc, n_placebo=1)
    print(f"R1 delay {d}: eng_post {e['post']:.2f} t {e['t_post']:.2f} | c_post {c['cpost']:.2f} cHO {c['cHO']:.2f}")
r1 = engine.pnl(pos1, btc, 10)
yr = pd.DataFrame({"R1": r1.groupby(r1.index.year).apply(s365),
                   "BH": btc.groupby(btc.index.year).apply(s365),
                   "R1_ret": r1.groupby(r1.index.year).apply(lambda x: (1 + x).prod() - 1),
                   "BH_ret": btc.groupby(btc.index.year).apply(lambda x: (1 + x).prod() - 1)})
print(yr.round(2).to_string())
ib = px("IBIT"); ibr = ib.pct_change().dropna()
sig = pos1.shift(1).reindex(ibr.index, method="ffill")
ri = engine.pnl(sig, ibr, 5)
print("IBIT 2024+: R1 Sharpe252 %.2f  BH Sharpe252 %.2f  R1 tot %.2f BH tot %.2f  dd %.2f vs %.2f" % (
    engine.sharpe(ri), engine.sharpe(ibr), (1 + ri).prod() - 1, (1 + ibr).prod() - 1, maxdd(ri), maxdd(ibr)))

print("\n== Part B ==")
vol = btc.rolling(30).std() * np.sqrt(365)
w = (0.6 / vol).clip(upper=1).fillna(0)
E, C = [], []
for name, pos in [("R6 btc_volman", w), ("R7 btc_tsmom28_volman", w * pos1)]:
    e, c = both(name, pos, btc); E.append(e); C.append(c)
show(E, C)
pd.DataFrame(E).merge(pd.DataFrame(C), on="rule").to_csv(os.path.join(HERE, "study2_results.csv"), index=False)
