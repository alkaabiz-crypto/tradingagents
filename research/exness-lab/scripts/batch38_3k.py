"""Batch 38, pre-registered 2026-11-28 (Hazza: $3,000, low risk, daily signals, >= 5 candidates). Target worst drop <= ~$300.
New single rules (period bar + random-timing check as Batch 35, BH across these 5):
 N1 IBS USTEC only when QQQ > 200-day.  N2 IBS USTEC only when VIX > its 20-day average.
 N3 Bond-stock split: TLT up > 0.5% and QQQ down on the day -> long USTEC for 1 day.
 N4 Dollar-down: UUP down > 0.3% and QQQ down -> long USTEC 1 day.
 N5 BTC TRIX with volatility sizing: exposure x min(1.5, 50% / 30-day realised annual vol).
Portfolios of existing passes (weights inverse to 2014-19 daily vol; ONE scale chosen so the 2014-2023 worst drop = $300,
then 2024-now is out of sample; each leg must reach its Exness minimum lot; no leg above $3,000 notional):
 P1 index dip basket: IBS USTEC, IBS US500, IBS US30, %R USTEC, R3 US500, 10-day low US500
 P2 crypto basket: BTC NR4, BTC Williams, BTC TRIX, ETH Williams, ETH above 50-day
 P3 everything above + USTEC overnight
 P4 low-correlation trio: IBS USTEC + BTC NR4 + ETH Williams
 P5 BTC NR4 + BTC Williams + IBS USTEC + USTEC overnight
Gold legs are left out: 1 oz (~$4,140) is above the $3,000 cap."""
import io, contextlib, numpy as np, pandas as pd
from math import erf, sqrt
with contextlib.redirect_stdout(io.StringIO()): exec(open("lab/batch36_pre2024.py").read())
MIN = {"QQQ": 1330, "SPY": 1000, "DIA": 500, "BTC-USD": 600, "ETH-USD": 170}
def sh(x, ann=252): x = np.asarray(x); x = x[~np.isnan(x)]; return x.mean() / x.std() * np.sqrt(ann) if len(x) > 30 and x.std() > 0 else np.nan
def ddv(u): e = np.cumsum(np.asarray(u)); return (e - np.maximum.accumulate(e)).min() if len(e) else 0
q = D["QQQ"]; c = q.Close; vix = L("VIX").Close.reindex(c.index).ffill(); tlt = L("TLT").Close.reindex(c.index); uup = L("UUP").Close.reindex(c.index)
ib = ibs(q); qr = c.pct_change()
N = {"N1 IBS USTEC above 200-day": hold(ib & (c > c.rolling(200).mean()).values, 2),
     "N2 IBS USTEC when VIX above 20-day avg": hold(ib & (vix > vix.rolling(20).mean()).values, 2),
     "N3 bonds up, stocks down -> USTEC 1 day": ((tlt.pct_change() > 0.005) & (qr < 0)).astype(float).values,
     "N4 dollar down, stocks down -> USTEC 1 day": ((uup.pct_change() < -0.003) & (qr < 0)).astype(float).values}
rng = np.random.default_rng(38); rows = []
def test(nm, pos, d, bp, ann, exp, start="2010"):
    r = d.Close.pct_change().fillna(0).values; ix = d.index; p = np.nan_to_num(np.asarray(pos, float))
    def net(pp, k=1): p1 = np.r_[0, pp[:-1]]; return p1 * r - np.abs(np.diff(np.r_[0, p1])) * bp * k / 2e4
    x = net(p); per = [(ix >= start) & (ix < "2020"), (ix >= "2020") & (ix < "2024"), ix >= "2024"]; post = ix >= start
    s = [sh(x[k], ann) for k in per]; S0 = sh(x[post], ann); pp = p[post]; rp = r[post]; nul = []
    for k in rng.integers(60, len(pp) - 60, 500):
        qq = np.roll(pp, k); q1 = np.r_[0, qq[:-1]]; z = q1 * rp - np.abs(np.diff(np.r_[0, q1])) * bp / 2e4; nul.append(z.mean() / z.std() * np.sqrt(ann))
    nul = np.array(nul); z = (S0 - nul.mean()) / nul.std()
    rows.append(dict(rule=nm, s_a=s[0], s20=s[1], s24=s[2], t=S0 * np.sqrt(post.sum() / ann), x2=net(p, 2)[post].sum() > 0, z=z, p=0.5 * (1 - erf(z / sqrt(2))),
                     usd_pre=(x[post & (ix < "2024")] * exp).sum(), dd_pre=ddv(x[post & (ix < "2024")] * exp), usd24=(x[per[2]] * exp).sum(), dd24=ddv(x[per[2]] * exp)))
    return pd.Series(x, index=ix)
for nm, pos in N.items(): R[nm] = ("QQQ", test(nm, pos, q, 1.4, 252, 1330))
b = D["BTC-USD"]; bc = b.Close; e = bc.ewm(span=15, adjust=False).mean().ewm(span=15, adjust=False).mean().ewm(span=15, adjust=False).mean(); tr = e.pct_change()
vol = bc.pct_change().rolling(30).std() * np.sqrt(365); w = np.minimum(1.5, 0.5 / vol).fillna(0)
R["N5 BTC TRIX vol-sized"] = ("BTC-USD", test("N5 BTC TRIX vol-sized", ((tr > tr.ewm(span=9, adjust=False).mean()) * w).values, b, 1.1, 365, 600, "2015"))
df = pd.DataFrame(rows); n = len(df); sp = np.sort(df.p.values); ok = sp <= 0.10 * np.arange(1, n + 1) / n; cut = sp[np.where(ok)[0].max()] if ok.any() else -1
df["PASS"] = df[["s_a", "s20", "s24"]].gt(0.3).all(axis=1) & (df.t >= 2) & df.x2 & (df.p <= cut)
print(df.round(2).to_string(index=False))
# ---------- portfolios ----------
PF = {"P1 index dip basket": ["IBS USTEC", "IBS US500", "IBS US30", "%R USTEC", "Connors R3 US500", "10-day low US500"],
      "P2 crypto basket": ["BTC NR4", "BTC Williams (T1)", "BTC TRIX trend", "ETH Williams (T2)", "ETH above 50-day"],
      "P4 low-corr trio": ["IBS USTEC", "BTC NR4", "ETH Williams (T2)"],
      "P5 NR4 + Williams + IBS + overnight": ["BTC NR4", "BTC Williams (T1)", "IBS USTEC", "USTEC overnight"]}
PF["P3 everything"] = PF["P1 index dip basket"] + PF["P2 crypto basket"] + ["USTEC overnight"]
if df.PASS.any(): PF["P6 P5 + passing new rules"] = PF["P5 NR4 + Williams + IBS + overnight"] + list(df[df.PASS].rule)
print("\n== Portfolios on $3,000 (scale set on 2014-23 drop = $300; 2024-now out of sample) ==")
out = []
for pn, legs in PF.items():
    S = pd.DataFrame({l: R[l][1] for l in legs}).loc["2014":].fillna(0)  # crypto days: index legs 0 on weekends
    v = S.loc["2014":"2019"].replace(0, np.nan).std() * np.sqrt(S.loc["2014":"2019"].ne(0).mean())
    wts = (1 / v) / (1 / v).sum(); unit = (S * wts).sum(axis=1)
    K = 300 / -ddv(unit.loc[:"2023"].values); K = min(K, 3000 / wts.max())
    leg_n = (wts * K).round(0); short = [f"{l} ${leg_n[l]:.0f} < min ${MIN[R[l][0]]}" for l in legs if leg_n[l] < MIN[R[l][0]] * 0.95]
    usd = unit * K; u24 = usd.loc["2024":]; yrs = len(u24) / 365.25 * (365.25 / 365); days = (u24.index.max() - u24.index.min()).days / 365.25
    yr = usd.loc[:"2023"].groupby(usd.loc[:"2023"].index.year).sum()
    corr = S.loc["2014":].corr().values; ac = corr[np.triu_indices(len(legs), 1)].mean() if len(legs) > 1 else np.nan
    out.append(dict(portfolio=pn, notional_K=round(K), legs=" | ".join(f"{l} ${leg_n[l]:.0f}" for l in legs), per_year_24=u24.sum() / days, per_day_24=u24.sum() / (days * 365.25),
                    dd24=ddv(u24.values), dd_1423=ddv(usd.loc[:"2023"].values), per_year_1423=usd.loc[:"2023"].sum() / 10, losing_years_1423=int((yr < 0).sum()),
                    worst_month_24=u24.groupby(u24.index.to_period("M")).sum().min(), avg_corr=ac, too_small=("; ".join(short) or "ok")))
P = pd.DataFrame(out); pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 200)
print(P.drop(columns="legs").round(1).to_string(index=False)); print(); [print(r.portfolio, "->", r.legs) for r in P.itertuples()]
P.to_csv("lab/batch38_portfolios.csv", index=False); df.to_csv("lab/batch38_rules.csv", index=False)
