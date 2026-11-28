"""Batch 54: the final 10 candidates as $ series at the stated size, real calendar-year $ (crypto years are 365 days),
% of $3,000, worst drop since each rule's first trade, max correlation with Plan A legs and with each other (2018+)."""
import numpy as np, pandas as pd
from pool import *
def coin_brk(coin, kind, bp=20):
    d = D(f"{coin}-USD"); d = d[d.High > d.Low]; P = CB.detect_patterns(d); rg = d.High - d.Low
    if kind == "Williams": return straddle(d, d.Open + 0.5 * rg.shift(), d.Open - 0.5 * rg.shift(), pd.Series(True, index=d.index), bp)
    m = {"NR4": P.nr4, "NR7": P.nr7, "inside bar": P.inside_bar, "ID/NR4": P.inside_bar & P.nr4}[kind]
    return straddle(d, d.High.shift(), d.Low.shift(), m.shift().fillna(False).astype(bool), bp)
P = pool(); A = planA()
b = D("BTC-USD"); cb = b.Close; ee = cb.ewm(span=15, adjust=False).mean().ewm(span=15, adjust=False).mean().ewm(span=15, adjust=False).mean(); tr = ee.pct_change()
sig = (tr > tr.ewm(span=9, adjust=False).mean()).astype(float); vol = np.log(cb).diff().rolling(30).std() * np.sqrt(365)
size = np.where(vol < 0.33, 2.0, 1.0) * sig  # 0.02 lot when 30d vol < 33%, else 0.01
C = {
 "ADA NR4 breakout ($500)": coin_brk("ADA", "NR4") * 500,
 "XRP NR7 breakout ($500)": coin_brk("XRP", "NR7") * 500,
 "XLM NR7 breakout ($500)": coin_brk("XLM", "NR7") * 500,
 "DOGE inside-bar breakout ($500)": coin_brk("DOGE", "inside bar") * 500,
 "XRP Williams breakout ($500)": coin_brk("XRP", "Williams") * 500,
 "ETH ID/NR4 breakout (0.5 ETH)": coin_brk("ETH", "ID/NR4", 5) * 825,
 "USTEC overnight (0.05)": P["USTEC overnight"],
 "Connors R3 US500 (0.14)": P["Connors R3 US500"],
 "Turnaround Tuesday USTEC (0.05)": P["Turnaround Tue USTEC"],
 "BTC TRIX vol-sized (0.01-0.02)": pos_ret(b, size.values if hasattr(size, "values") else size, 1.1) * 595,
}
rows = []
df = pd.DataFrame({**A, **C}).loc["2018":].fillna(0); cr = df.corr()
for k, r in C.items():
    r = r.fillna(0); r = r[r.index >= r[r != 0].index[0]]
    yr = r.groupby(r.index.year).sum(); e = r.cumsum(); dd = (e - e.cummax()).min()
    pre = yr.loc[:2023]; rec = r.loc["2024":]; rec_yr = rec.sum() / ((rec.index[-1] - rec.index[0]).days / 365.25)
    others = [x for x in C if x != k]
    rows.append({"candidate": k, "from": int(yr.index[0]), "pre-2024 $/yr": round(pre.mean()), "losing yrs pre": f"{(pre < 0).sum()}/{len(pre)}",
                 "2024": round(yr.get(2024, 0)), "2025": round(yr.get(2025, 0)), "2026": round(yr.get(2026, 0)), "2024+ %/yr on $3k": round(rec_yr / 30, 1),
                 "worst drop": round(dd), "max corr Plan A": round(cr.loc[k, list(A)].max(), 2), "max corr others": round(cr.loc[k, others].max(), 2)})
R = pd.DataFrame(rows).sort_values("2024+ %/yr on $3k", ascending=False); R.to_csv("batch54_final10.csv", index=False)
pd.set_option("display.width", 250); print(R.to_string(index=False))
tot = pd.DataFrame(C).fillna(0).loc["2018":].sum(axis=1); e = tot.cumsum(); yt = tot.groupby(tot.index.year).sum()
print("ALL 10 together: per year", yt.round(0).astype(int).to_dict(), "worst drop", round((e - e.cummax()).min()))
