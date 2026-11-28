"""Batch 42, pre-registered 2026-11-28 (Hazza: free 'Bloomberg-style' data). FRED, AAII, Binance and on-chain sites are blocked from
this machine, so free market-data versions from Yahoo are used. Each filter makes a leg flat on days the filter (known at the prior
close) is off; applied to every leg of Plan A and Plan F. Picked on 2014-23 (higher Sharpe and >= 80% of the profit), checked on 2024+.
 TS  VIX term structure calm: VIX / VIX3M < 1 (backwardation = panic selling that tends to keep going)
 YC  yield curve not inverted: 10-year (^TNX) minus 3-month (^IRX) > 0
 CR  credit calm: high-yield bonds (HYG) / Treasuries (IEF) at or above their 50-day average
 BS  BTC legs only: CME bitcoin futures basis (BTC=F / spot - 1) below its 1-year median (longs less crowded)"""
import io, contextlib, numpy as np, pandas as pd
with contextlib.redirect_stdout(io.StringIO()): exec(open("lab/batch41_fixes.py").read().split("def stats")[0])
def LL(t): return pd.read_csv(f"data/{t}.csv", parse_dates=["Date"], index_col="Date")["Close"].dropna()
legs = {"BTC NR4": LEGS["BTC NR4"]["none"], "BTC Williams": LEGS["BTC Williams"]["none"], "10-day low US500": LEGS["10-day low US500"]["none"],
        "ETH above 50-day": LEGS["ETH above 50-day"]["none"], "IBS US30": R["IBS US30"][1] * 500, "Connors R3 US500": R["Connors R3 US500"][1] * 1000}
days = pd.date_range("2000-01-01", "2026-11-24")
def ff(s): return s.reindex(days.union(s.index)).ffill().reindex(days)
vix, v3 = ff(LL("VIX")), ff(LL("VIX3M")); tnx, irx = ff(LL("TNX")), ff(LL("IRX")); hyg, ief = ff(LL("HYG")), ff(LL("IEF"))
fut = ff(LL("BTC_F")); spot = ff(D["BTC-USD"].Close); basis = fut / spot - 1
cr = hyg / ief
FIL = {"TS VIX term structure calm": (vix / v3 < 1), "YC yield curve not inverted": (tnx - irx > 0), "CR credit calm": (cr >= cr.rolling(50).mean()),
       "BS BTC futures basis low": (basis < basis.rolling(365).median())}
for k in FIL: FIL[k] = FIL[k].shift().fillna(True).astype(bool)  # known at the prior close; no data yet = allowed
FIL["BS BTC futures basis low"] = FIL["BS BTC futures basis low"].where(basis.shift().notna(), True)
PLANS = {"Plan A": ["10-day low US500", "BTC NR4", "BTC Williams", "ETH above 50-day"], "Plan F": ["IBS US30", "Connors R3 US500", "BTC NR4", "ETH above 50-day"]}
def st(u, a, z):
    u = u.loc[a:z]; e = u.cumsum(); mo = u.groupby(u.index.to_period("M")).sum(); y = len(mo) / 12
    return u.sum() / y, (e - e.cummax()).min(), (mo < 0).sum() / y, u.mean() / u.std()
for pn, ls in PLANS.items():
    print(f"== {pn} ==")
    def build(fk=None):
        out = []
        for l in ls:
            u = legs[l].reindex(days).fillna(0)
            if fk and not (fk.startswith("BS") and "BTC" not in l): u = u.where(FIL[fk], 0)
            out.append(u)
        return sum(out)
    base = build(); b1 = st(base, "2014-10", "2023"); b2 = st(base, "2024", "2026")
    print(f"  {'no filter':28s} 2014-23 ${b1[0]:+5.0f}/yr drop {b1[1]:5.0f} losing mo/yr {b1[2]:.1f} | 2024+ ${b2[0]:+4.0f}/yr drop {b2[1]:5.0f} losing mo/yr {b2[2]:.1f}")
    for fk in FIL:
        u = build(fk); a, o = st(u, "2014-10", "2023"), st(u, "2024", "2026"); keep = a[3] > b1[3] and a[0] >= 0.8 * b1[0]
        print(f"  {fk:28s} 2014-23 ${a[0]:+5.0f}/yr drop {a[1]:5.0f} losing mo/yr {a[2]:.1f} | 2024+ ${o[0]:+4.0f}/yr drop {o[1]:5.0f} losing mo/yr {o[2]:.1f}  {'PICK' if keep else ''}")
        if keep: print("     years:", {y: int(v) for y, v in u.loc["2015":].groupby(u.loc["2015":].index.year).sum().items()})
    print("     base years:", {y: int(v) for y, v in base.loc["2015":].groupby(base.loc["2015":].index.year).sum().items()})
print("\nshare of days each filter is ON 2014+:", {k: round(v.loc["2014":].mean(), 2) for k, v in FIL.items()})
