"""Batch 38b, pre-registered 2026-11-28: real Exness minimum-lot portfolios for $3,000.
Legs at their minimum lot (USTEC 0.05 $1,330, US500 0.14 $1,000, US30 0.01 $500, BTC 0.01 $600, ETH 0.1 $170).
Search every combination of 1-5 legs. Keep those with (a) worst drop 2014-2023 >= -$300 (10% of $3,000), (b) at most $3,000 of
positions open at once (no extra leverage), (c) every year 2014-2023 not worse than -$150. Rank by 2014-2023 Sharpe (in sample);
2024-now is reported as the out-of-sample check. Gold is excluded (1 oz > $3,000)."""
import io, contextlib, itertools, numpy as np, pandas as pd
with contextlib.redirect_stdout(io.StringIO()): exec(open("lab/batch38_3k.py").read().split("# ---------- portfolios")[0])
NOT = {"QQQ": 1330, "SPY": 1000, "DIA": 500, "BTC-USD": 600, "ETH-USD": 170}
legs = ["IBS USTEC", "IBS US500", "IBS US30", "%R USTEC", "%R US500", "Connors R3 US500", "10-day low US500", "BTC NR4", "BTC Williams (T1)",
        "BTC TRIX trend", "ETH Williams (T2)", "ETH above 50-day", "USTEC overnight", "N1 IBS USTEC above 200-day", "N2 IBS USTEC when VIX above 20-day avg", "N5 BTC TRIX vol-sized"]
U = pd.DataFrame({l: R[l][1] * NOT[R[l][0]] for l in legs}).loc["2014":].fillna(0)
G = pd.DataFrame({l: (R[l][1] != 0) * NOT[R[l][0]] * (1.5 if l.startswith("N5") else 1) for l in legs}).loc["2014":].fillna(0)
pre, oos = U.index < "2024", U.index >= "2024"; yrs_oos = (U.index[-1] - pd.Timestamp("2024-01-01")).days / 365.25
def dd(x): e = np.cumsum(x); return (e - np.maximum.accumulate(e)).min()
res = []
for k in range(1, 6):
    for combo in itertools.combinations(legs, k):
        u = U[list(combo)].sum(axis=1).values; g = G[list(combo)].sum(axis=1).values
        if g.max() > 3000: continue
        d1 = dd(u[pre])
        if d1 < -300: continue
        yr = pd.Series(u[pre], index=U.index[pre]).groupby(U.index[pre].year).sum()
        if yr.min() < -150: continue
        s = u[pre].mean() / u[pre].std() * np.sqrt(365)
        res.append(dict(legs=" + ".join(combo), n=k, sharpe_1423=s, per_year_1423=u[pre].sum() / 10, dd_1423=d1, worst_year_1423=yr.min(),
                        per_year_24=u[oos].sum() / yrs_oos, per_day_24=u[oos].sum() / (yrs_oos * 365.25), dd_24=dd(u[oos]), max_open=g.max()))
df = pd.DataFrame(res).sort_values("sharpe_1423", ascending=False); df.to_csv("lab/batch38b_combos.csv", index=False)
pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 120)
print(len(df), "combos qualify"); print(df.head(25).round(1).to_string(index=False))
print("\nOOS check: share of the top 50 positive in 2024-now:", (df.head(50).per_year_24 > 0).mean(), " median $/yr", df.head(50).per_year_24.median().round(0))
