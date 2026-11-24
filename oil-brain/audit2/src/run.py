import sys, json
import numpy as np, pandas as pd
sys.path.insert(0, sys.argv[1] + "/src")
import engine
engine.REENTRY = sys.argv[2] == 'B'
from engine import load, backtest, stats, period, indicators, simulate_from

ROOT = sys.argv[1]
D = ROOT + "/data/"
gld = load(D + "GLD_raw.csv")
P = {"2006-2013": ("2006-01-01", "2013-12-31"), "2014-2019": ("2014-01-01", "2019-12-31"),
     "2020-now": ("2020-01-01", None), "2014-now": ("2014-01-01", None)}

def fmt(s):
    return f"n={s['n']:3d} win={s['win']:.0%} avgR={s['avgR']:+.2f} t={s['t']:+.2f} totR={s['totR']:+.1f} maxDD={s['maxDD']:.1f}"

def table(t, label=""):
    rows = {}
    for k, (a, b) in P.items():
        rows[k] = stats(period(t, a, b))
    print(label)
    for k, s in rows.items():
        print(f"  {k:10s} {fmt(s)}")
    return rows

out = {}
print("=== 1. BASE ===")
base = backtest(gld)
out["base"] = table(base, "GLD base")
base.to_csv(ROOT + f"/trades_base_{sys.argv[2]}.csv", index=False)
print("open trades:", base[base.open].to_dict("records"))
print("sensitivity: exclude open trade ->", fmt(stats(period(base[~base.open], "2014-01-01"))))

print("\n=== 2. NEIGHBOURS (2014-now) ===")
nb = []
variants = [("thr5", dict(thr=5)), ("thr15", dict(thr=15)), ("thr20", dict(thr=20)), ("rsi3", dict(rsi_n=3)),
            ("sma150", dict(sma=150)), ("sma250", dict(sma=250)), ("init1.5", dict(init_k=1.5)),
            ("init2.5", dict(init_k=2.5)), ("trail2", dict(trail_k=2)), ("trail2.5", dict(trail_k=2.5)),
            ("trail3.5", dict(trail_k=3.5)), ("trail4", dict(trail_k=4))]
for name, kw in variants:
    t = backtest(gld, **kw)
    s = stats(period(t, "2014-01-01")); s0 = stats(period(t, "2006-01-01", "2013-12-31"))
    ok = s["avgR"] > 0 and s["t"] > 1.5
    nb.append(dict(name=name, **{k: s[k] for k in s}, pre_avgR=s0["avgR"], pre_t=s0["t"], pre_n=s0["n"], ok=ok))
    print(f"  {name:9s} {fmt(s)} | 2006-13 n={s0['n']} avgR={s0['avgR']:+.2f} t={s0['t']:+.2f} {'PASS' if ok else 'fail'}")
print("  pass:", sum(x["ok"] for x in nb), "/", len(nb))
out["neighbours"] = nb

print("\n=== 3a. BUY & HOLD vs RULE per year (rule: compounded % per exit-year, full capital) ===")
c = gld.Close
bh = c.groupby(c.index.year).last() / c.groupby(c.index.year).last().shift(1) - 1
first = c[c.index.year == 2006].iloc[0]
bh.loc[2006] = c[c.index.year == 2006].iloc[-1] / c[c.index.year == 2005].iloc[-1] - 1
rule_y = base.groupby(base.exit_date.dt.year).ret.apply(lambda r: np.prod(1 + r) - 1)
yr = pd.DataFrame({"BH": bh, "rule": rule_y}).loc[2006:].fillna(0)
Ry = base.groupby(base.entry_date.dt.year).R.agg(["count", "sum", "mean"])
for y in yr.index:
    rr = Ry.loc[y] if y in Ry.index else pd.Series({"count": 0, "sum": 0, "mean": np.nan})
    print(f"  {y} BH={yr.BH[y]:+6.1%} rule={yr.rule[y]:+6.1%} | trades(entry yr)={int(rr['count'])} sumR={rr['sum']:+.2f}")
def cagr(series_ret, years):
    return np.prod(1 + series_ret) ** (1 / years) - 1
for lab, a in [("2006-now", 2006), ("2014-now", 2014)]:
    nyrs = (gld.index[-1] - pd.Timestamp(f"{a}-01-01")).days / 365.25
    bhc = (c.iloc[-1] / c[c.index < f"{a}-01-01"].iloc[-1]) ** (1 / nyrs) - 1
    tr = base[base.entry_date >= f"{a}-01-01"]
    rc = cagr(tr.ret.values, nyrs)
    expo = tr.days.sum() / (nyrs * 365.25)
    print(f"  {lab}: BH CAGR {bhc:+.1%}  rule CAGR {rc:+.1%}  time in market {expo:.0%}")
    out[f"cagr_{lab}"] = dict(bh=bhc, rule=rc, exposure=expo)
out["years"] = yr.to_dict()

print("\n=== 3b. PLACEBO (2014-now) ===")
ind = indicators(gld)
o, h, l, cl = (gld[x].values for x in ["Open", "High", "Low", "Close"])
atr = ind.atr.values; dates = gld.index
real = period(base, "2014-01-01")
N = len(real)
elig = np.where(((gld.Close > ind.sma).values) & (dates >= "2014-01-01") & ~np.isnan(atr))[0]
elig = elig[elig < len(cl) - 1]
rng = np.random.default_rng(42)
def one_R(i):
    x, xp, ep, _ = simulate_from(o, h, l, cl, atr, i, i + 1, 2.0, 3.0)
    return (xp - ep - 5e-4 * (ep + xp)) / (2 * atr[i])
Rall = np.array([one_R(i) for i in elig])
pl = np.array([Rall[rng.choice(len(elig), N, replace=False)].mean() for _ in range(500)])
# non-overlapping sequential placebo: pick random eligible day, trade, continue after exit
el = np.zeros(len(cl), bool); el[elig] = True
def seq_run(q):
    # walk forward through 2014-now; when flat on an eligible day enter with prob q; same exits, one at a time
    rs = []; i = 0; n = len(cl)
    while i < n - 1:
        if el[i] and rng.random() < q:
            x, xp, ep, _ = simulate_from(o, h, l, cl, atr, i, i + 1, 2.0, 3.0)
            rs.append((xp - ep - 5e-4 * (ep + xp)) / (2 * atr[i])); i = x if engine.REENTRY else x + 1; continue
        i += 1
    return rs
qs = np.linspace(0.02, 0.2, 19)
cnt = [np.mean([len(seq_run(q)) for _ in range(20)]) for q in qs]
q = qs[np.argmin(np.abs(np.array(cnt) - N))]
runs = [seq_run(q) for _ in range(500)]
pl2 = np.array([np.mean(r) for r in runs])
print(f"  non-overlap placebo q={q:.2f} mean trades={np.mean([len(r) for r in runs]):.1f}")
p = (pl >= real.R.mean()).mean(); p2 = (pl2 >= real.R.mean()).mean()
print(f"  real avgR={real.R.mean():+.3f} N={N}; eligible-day mean R={Rall.mean():+.3f}")
print(f"  placebo (independent draws) mean={pl.mean():+.3f} sd={pl.std():.3f} 95th={np.percentile(pl,95):+.3f} p={p:.3f}")
print(f"  placebo (non-overlapping)  mean={pl2.mean():+.3f} sd={pl2.std():.3f} 95th={np.percentile(pl2,95):+.3f} p={p2:.3f}")
out["placebo"] = dict(real=real.R.mean(), N=N, mean=pl.mean(), p=p, p_seq=p2, mean_seq=pl2.mean(), allday=Rall.mean())

print("\n=== 3c. OTHER INSTRUMENTS ===")
out["other"] = {}
for tk in ["IAU", "GC_F", "SLV"]:
    t = backtest(load(D + f"{tk}_raw.csv"))
    out["other"][tk] = table(t, tk)

print("\n=== 4. EXECUTION ===")
out["exec"] = {}
for name, kw in [("delay1", dict(delay=2)), ("cost10", dict(cost_bp=10)), ("cost20", dict(cost_bp=20)),
                 ("fin0.02", dict(fin_daily=0.0002)), ("fin0.02+cost10", dict(fin_daily=0.0002, cost_bp=10)),
                 ("fin0.02+delay1+cost10", dict(fin_daily=0.0002, cost_bp=10, delay=2))]:
    t = backtest(gld, **kw)
    out["exec"][name] = table(t, name)
    if name == "fin0.02":
        r14 = period(t, "2014-01-01")
        print("  financing drag per trade (2014-now) avg R:", (period(base, '2014-01-01').R.values - r14.R.values).mean().round(3),
              " avg calendar days held:", r14.days.mean().round(1))

print("\n=== 5. REGIME ===")
ex = base[~((base.entry_date >= "2020-01-01") & (base.entry_date <= "2025-12-31"))]
s = stats(period(ex, "2014-01-01")); print("  2014-now excl 2020-2025:", fmt(s)); out["ex2020_25"] = s
s = stats(ex[ex.entry_date >= "2006-01-01"]); print("  2006-now excl 2020-2025:", fmt(s)); out["ex2020_25_all"] = s
s = stats(period(base, "2024-01-01")); print("  2024-now only:", fmt(s))
r14 = period(base, "2014-01-01").R.sort_values(ascending=False)
top3 = r14.iloc[:3].sum(); print(f"  2014-now top-3 trades {r14.iloc[:3].round(2).tolist()} = {top3:.2f}R of total {r14.sum():.2f}R ({top3/r14.sum():.0%})")
s = stats(period(base, "2014-01-01").drop(r14.index[:3])); print("  2014-now without top3:", fmt(s)); out["no_top3"] = s
out["top3_share"] = top3 / r14.sum()
for y, g in base.groupby(base.entry_date.dt.year):
    st = stats(g); print(f"  {y}: n={st['n']} avgR={st['avgR']:+.2f} sumR={st['totR']:+.2f}")

print("\n=== 6. DATA ===")
for tk in ["GLD", "IAU", "SLV", "GC_F"]:
    r = pd.read_csv(D + f"{tk}_raw.csv", index_col=0, parse_dates=True)
    a = pd.read_csv(D + f"{tk}_adj.csv", index_col=0, parse_dates=True)
    diff = (r.Close / a.Close - 1).abs().max()
    adjdiff = (r["Adj Close"] / r.Close - 1).abs().max()
    spl = r[r["Stock Splits"] != 0]["Stock Splits"]
    dv = r[r["Dividends"] != 0]["Dividends"]
    bd = pd.bdate_range(r.index[0], "2026-11-23")
    miss = len(bd.difference(r.index))
    nan = r[["Open", "High", "Low", "Close"]].isna().any(axis=1).sum()
    bad = ((r.High < r[["Open", "Close"]].max(axis=1) - 1e-6) | (r.Low > r[["Open", "Close"]].min(axis=1) + 1e-6)).sum()
    zero = (r[["Open", "High", "Low", "Close"]] <= 0).any(axis=1).sum()
    big = (r.Close.pct_change().abs() > 0.08).sum()
    print(f"  {tk}: rows={len(r)} max|raw/adj-1|={diff:.2e} max|AdjClose/Close-1|={adjdiff:.2e} splits={spl.to_dict()} divs={len(dv)} "
          f"missing weekdays={miss} (holidays incl.) NaN rows={nan} OHLC-inconsistent={bad} nonpos={zero} |ret|>8% days={big}")
# gap check for GLD: weekday gaps >4 calendar days
g = gld.index.to_series().diff().dt.days
print("  GLD gaps >4 days:", g[g > 4].to_dict())
# GC=F roll-gap check: overnight open/prev close gaps
gc = load(D + "GC_F_raw.csv")
gap = (gc.Open / gc.Close.shift(1) - 1)
print("  GC=F |open gap|>3%:", gap[gap.abs() > 0.03].round(3).to_dict())
gl = gld.Open / gld.Close.shift(1) - 1
print("  GLD  |open gap|>3%:", len(gl[gl.abs() > 0.03]))
json.dump(out, open(ROOT + f"/results_{sys.argv[2]}.json", "w"), default=str, indent=1)
