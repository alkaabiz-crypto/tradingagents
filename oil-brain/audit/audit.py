"""Independent audit of four tournament rules. Own re-implementation; own Yahoo download (audit/data).
Convention: pos decided at close t, earns close t -> t+1. Cost = |delta pos| * bps (per side / per unit turnover).
Run: python audit.py > results.txt
"""
import os
import numpy as np
import pandas as pd

H = os.path.dirname(os.path.abspath(__file__))
TODAY = "2026-11-24"  # drop any bar dated today (possibly partial)


def load(sym, col="Adj Close"):
    df = pd.read_csv(os.path.join(H, "data", sym + ".csv"), index_col=0, parse_dates=True)
    df = df[~df.index.duplicated()].sort_index()
    df = df[df.index < TODAY]
    return df[col].dropna()


def metrics(r, ann):
    r = r.dropna()
    if len(r) < 30 or r.std() == 0:
        return dict(sh=np.nan, cagr=np.nan, mdd=np.nan, t=np.nan, n=len(r))
    eq = (1 + r).cumprod()
    return dict(sh=r.mean() / r.std() * np.sqrt(ann),
                cagr=eq.iloc[-1] ** (ann / len(r)) - 1,
                mdd=(eq / eq.cummax() - 1).min(),
                t=r.mean() / r.std() * np.sqrt(len(r)), n=len(r))


def pnl(pos, ret, bps, delay=0):
    """pos at close t -> earns ret[t+1]. delay=1: act one bar later."""
    pos = pos.reindex(ret.index).fillna(0).shift(delay).fillna(0)
    turn = pos.diff().abs().fillna(pos.abs())
    # cost charged on the bar where the new position starts earning
    return (pos.shift(1) * ret - turn.shift(1) * bps / 1e4).fillna(0)


def fmt(m):
    return f"Sh {m['sh']:5.2f}  CAGR {m['cagr']*100:6.1f}%  MDD {m['mdd']*100:6.1f}%  t {m['t']:5.2f}  n {m['n']}"


def periods(start, crypto):
    p = [("full", start, None), ("2014-2019", "2014-01-01", "2019-12-31"), ("2020-now", "2020-01-01", None)]
    if crypto:
        p.append(("2022-now", "2022-01-01", None))
    return p


def report(label, r, ann, crypto, start=None):
    start = start or r.index[0]
    out = []
    for nm, a, b in periods(start, crypto):
        out.append(f"    {nm:10s} {fmt(metrics(r.loc[a:b], ann))}")
    print(f"  {label}")
    print("\n".join(out))


def summary(r, ann, a=None, b=None):
    m = metrics(r.loc[a:b], ann)
    return f"{m['sh']:5.2f} (t {m['t']:4.2f})"


def by_year(r, bench, ann):
    print("    year  rule_ret  bench_ret  rule_Sh")
    for y, g in r.groupby(r.index.year):
        bg = bench.loc[g.index]
        sh = g.mean() / g.std() * np.sqrt(ann) if g.std() > 0 else np.nan
        print(f"    {y}  {((1+g).prod()-1)*100:8.1f}%  {((1+bg).prod()-1)*100:8.1f}%  {sh:6.2f}")


def ex_year(r, ann, years):
    return metrics(r[~r.index.year.isin(years)], ann)


def top_contrib(r, k=5, freq="M"):
    s = r.groupby(r.index.to_period(freq)).sum().sort_values(ascending=False)
    tot = r.sum()
    return s.head(k), tot


# ---------------------------------------------------------------- A / B crypto trend
def crypto_rule(sym, name, signal_fn, ann=365):
    print("=" * 100)
    print(f"{name}  ({sym}, 365-day annualisation, 10 bp/side)")
    px = load(sym)
    ret = px.pct_change().dropna()
    pos = signal_fn(px).astype(float)
    r = pnl(pos, ret, 10)
    # start when the longest lookback (here up to 100) is available
    first = px.index[100] if len(px) > 100 else px.index[0]
    r = r.loc[first:]
    bh = ret.loc[first:]
    report("RULE", r, ann, True)
    report("BUY&HOLD", bh, ann, True)
    print(f"  exposure {pos.loc[first:].mean():.2f}, switches/yr {pos.diff().abs().loc[first:].sum()/(len(r)/365):.1f}")
    # execution / costs
    print("  -- execution & cost stress (full / 2022-now)")
    for lab, d, c in [("base", 0, 10), ("delay1", 1, 10), ("cost25", 0, 25), ("delay1+cost25", 1, 25)]:
        rr = pnl(pos, ret, c, d).loc[first:]
        print(f"    {lab:14s} full {summary(rr, ann)}  2014-19 {summary(rr, ann, None, '2019-12-31')}  2020+ {summary(rr, ann, '2020-01-01')}  2022+ {summary(rr, ann, '2022-01-01')}")
    # 252-day annualisation check (weekday-only series)
    wk = px[px.index.dayofweek < 5]
    print(f"  (annualisation sensitivity: same daily rule Sharpe with sqrt(252) would be {metrics(r, 252)['sh']:.2f})")
    return px, ret, pos, r, bh, first


def placebo_shift(pos, ret, bps, real_sh, ann, first, n=500, seed=1):
    rng = np.random.default_rng(seed)
    p = pos.reindex(ret.index).fillna(0).values
    L = len(p)
    out = []
    for _ in range(n):
        k = int(rng.integers(L // 10, L - L // 10))
        rr = pnl(pd.Series(np.roll(p, k), index=ret.index), ret, bps).loc[first:]
        out.append(metrics(rr, ann)["sh"])
    out = np.array(out)
    return (out >= real_sh).mean(), np.percentile(out, 95)


def ret_n(px, n):
    return px / px.shift(n) - 1


def run_A():
    sig = lambda px: (ret_n(px, 28) > 0) | (px > px.rolling(100).mean())
    px, ret, pos, r, bh, first = crypto_rule("BTC-USD", "A. BTC trend: 28d return > 0 OR price > SMA100", sig)
    # components
    print("  -- components and neighbours (10bp, full / 2014-19 / 2020+ / 2022+ / ex-2020)")
    variants = {}
    for n in [14, 21, 28, 42, 56]:
        variants[f"mom{n}"] = ret_n(px, n) > 0
    for m in [50, 100, 150, 200]:
        variants[f"sma{m}"] = px > px.rolling(m).mean()
    for n in [14, 21, 28, 42, 56]:
        for m in [50, 100, 150, 200]:
            variants[f"mom{n}|sma{m}"] = (ret_n(px, n) > 0) | (px > px.rolling(m).mean())
    rows = []
    for k, v in variants.items():
        rr = pnl(v.astype(float), ret, 10).loc[first:]
        rows.append((k, metrics(rr, 365)["sh"], metrics(rr.loc[:"2019-12-31"], 365)["sh"], metrics(rr.loc["2020-01-01":], 365)["sh"],
                     metrics(rr.loc["2022-01-01":], 365)["sh"], ex_year(rr, 365, [2020])["sh"], metrics(rr, 365)["t"],
                     metrics(pnl(v.astype(float), ret, 10, 1).loc[first:], 365)["sh"]))
    df = pd.DataFrame(rows, columns=["variant", "full", "14-19", "20+", "22+", "ex2020", "t_full", "full_delay1"]).set_index("variant")
    print(df.round(2).to_string())
    bh_m = {p: metrics(bh.loc[a:b], 365)["sh"] for p, a, b in [("full", None, None), ("14-19", None, "2019-12-31"), ("20+", "2020-01-01", None), ("22+", "2022-01-01", None)]}
    print(f"  buy&hold Sharpe: {', '.join(f'{k} {v:.2f}' for k, v in bh_m.items())}; ex-2020 {ex_year(bh, 365, [2020])['sh']:.2f}")
    print(f"  share of 20 grid variants beating B&H full-sample Sharpe: {(df.full > bh_m['full']).mean():.2f}; 2022+: {(df['22+'] > bh_m['22+']).mean():.2f}")
    regime(r, bh, 365, pos, ret, first)
    return r


def run_B():
    sig = lambda px: ret_n(px, 28) > 0
    px, ret, pos, r, bh, first = crypto_rule("ETH-USD", "B. ETH trend: 28d return > 0", sig)
    print("  NOTE Yahoo ETH-USD starts 2017-11-09: '2014-2019' is only 2018-2019.")
    print("  -- neighbours")
    rows = []
    variants = {f"mom{n}": ret_n(px, n) > 0 for n in [14, 21, 28, 42, 56]}
    variants.update({f"sma{m}": px > px.rolling(m).mean() for m in [50, 100, 150, 200]})
    for k, v in variants.items():
        rr = pnl(v.astype(float), ret, 10).loc[first:]
        rows.append((k, metrics(rr, 365)["sh"], metrics(rr.loc[:"2019-12-31"], 365)["sh"], metrics(rr.loc["2020-01-01":], 365)["sh"],
                     metrics(rr.loc["2022-01-01":], 365)["sh"], ex_year(rr, 365, [2020])["sh"], metrics(rr, 365)["t"],
                     metrics(pnl(v.astype(float), ret, 10, 1).loc[first:], 365)["sh"]))
    print(pd.DataFrame(rows, columns=["variant", "full", "18-19", "20+", "22+", "ex2020", "t_full", "full_delay1"]).set_index("variant").round(2).to_string())
    print(f"  buy&hold ex-2020 Sharpe {ex_year(bh, 365, [2020])['sh']:.2f}")
    regime(r, bh, 365, pos, ret, first)
    return r


def regime(r, bh, ann, pos, ret, first, bps=10):
    print("  -- regime")
    m0 = ex_year(r, ann, [2020]); mb = ex_year(bh, ann, [2020])
    print(f"    ex-2020: rule {fmt(m0)}\n             B&H  {fmt(mb)}")
    by_year(r, bh, ann)
    hs, tot = top_contrib(r, 5)
    print(f"    top-5 months contribute {hs.sum():.3f} of total log-ish sum {tot:.3f} ({hs.sum()/tot*100:.0f}%): {', '.join(f'{k}:{v:.2f}' for k, v in hs.items())}")
    rr = r.copy()
    mo = rr.groupby(rr.index.to_period('M')).sum().sort_values(ascending=False)
    drop = mo.index[:5]
    rest = rr[~rr.index.to_period('M').isin(drop)]
    print(f"    without the 5 best months: {fmt(metrics(rest, ann))}")
    p, p95 = placebo_shift(pos, ret, bps, metrics(r, ann)["sh"], ann, first)
    print(f"    circular-shift placebo (500): p = {p:.3f}, placebo 95th pct Sharpe {p95:.2f}")


# ---------------------------------------------------------------- C credit -> oil
def weekly_signal_days(idx, freq="W"):
    s = idx.to_series()
    if freq == "W":
        key = idx.to_period("W-FRI")
    else:
        key = idx.to_period("M")
    return s.groupby(key).max().values  # last trading day of each week/month


def build_C(hyg, lqd, uso_idx, n=63, freq="W", lag=0):
    spread = (hyg / hyg.shift(n) - 1) - (lqd / lqd.shift(n) - 1)
    spread = spread.reindex(uso_idx).ffill()
    days = weekly_signal_days(uso_idx, freq)
    sig = pd.Series(np.nan, index=uso_idx)
    sig.loc[days] = np.where(spread.loc[days] > 0, 1.0, -1.0)
    sig[spread.isna()] = np.nan
    return sig.ffill().shift(lag)


def run_C():
    print("=" * 100)
    print("C. Credit appetite -> USO: weekly (last trading day of week) sign(HYG63 - LQD63) -> long/short USO; 252-day annualisation; 5 bp per unit turnover")
    hyg, lqd, uso = load("HYG"), load("LQD"), load("USO")
    ret = uso.pct_change().dropna()
    pos = build_C(hyg, lqd, ret.index).fillna(0)
    first = pos[pos != 0].index[0]
    r = pnl(pos, ret, 5).loc[first:]
    bh = ret.loc[first:]
    report("RULE", r, 252, False)
    report("BUY&HOLD USO", bh, 252, False)
    report("SHORT USO (always)", -bh, 252, False)
    print(f"  long fraction {(pos.loc[first:] > 0).mean():.2f}, first signal {first.date()}")
    lf = (pos.loc[first:] > 0).mean()
    print("  -- execution / cost / data stress (full / 2014-19 / 2020+)")
    hyg_raw, lqd_raw = load("HYG", "Close"), load("LQD", "Close")
    cases = [("base", pos, 5, 0), ("delay1", pos, 5, 1), ("cost25", pos, 25, 0), ("delay1+cost25", pos, 25, 1),
             ("RAW closes (no div) for HYG/LQD", build_C(hyg_raw, lqd_raw, ret.index).fillna(0), 5, 0),
             ("signal from Thursday (lag-1 data)", build_C(hyg.shift(1), lqd.shift(1), ret.index).fillna(0), 5, 0)]
    for lab, p, c, d in cases:
        rr = pnl(p, ret, c, d).loc[first:]
        print(f"    {lab:34s} full {summary(rr, 252)}  2014-19 {summary(rr, 252, '2014-01-01', '2019-12-31')}  2020+ {summary(rr, 252, '2020-01-01')}")
    print("  -- neighbours (full / 2014-19 / 2020+ / ex-2020 / t full)")
    rows = []
    for n in [21, 42, 63, 126]:
        for f in ["W", "M"]:
            p = build_C(hyg, lqd, ret.index, n, f).fillna(0)
            rr = pnl(p, ret, 5).loc[first:]
            rows.append((f"n{n}_{f}", metrics(rr, 252)["sh"], metrics(rr.loc['2014':'2019'], 252)["sh"], metrics(rr.loc['2020':], 252)["sh"],
                         ex_year(rr, 252, [2020])["sh"], metrics(rr, 252)["t"], metrics(rr.loc[:'2013'], 252)["sh"]))
    print(pd.DataFrame(rows, columns=["variant", "full", "14-19", "20+", "ex2020", "t_full", "pre2014"]).set_index("variant").round(2).to_string())
    # long-only / short-only decomposition
    lo = pnl(pos.clip(lower=0), ret, 5).loc[first:]; so = pnl(pos.clip(upper=0), ret, 5).loc[first:]
    print(f"  long-leg only: {fmt(metrics(lo, 252))}\n  short-leg only: {fmt(metrics(so, 252))}")
    # random weekly placebo with same long fraction
    rng = np.random.default_rng(3)
    days = weekly_signal_days(ret.loc[first:].index, "W")
    real = metrics(r, 252)["sh"]
    sims = []; sims20 = []
    for _ in range(2000):
        s = pd.Series(np.nan, index=ret.index)
        s.loc[days] = np.where(rng.random(len(days)) < lf, 1.0, -1.0)
        s = s.ffill().fillna(0)
        rr = pnl(s, ret, 5).loc[first:]
        sims.append(metrics(rr, 252)["sh"]); sims20.append(metrics(rr.loc["2020":], 252)["sh"])
    sims = np.array(sims); sims20 = np.array(sims20)
    print(f"  random weekly L/S placebo (2000, long frac {lf:.2f}): mean Sh {sims.mean():.2f}, 95th {np.percentile(sims,95):.2f}, p(full) = {(sims >= real).mean():.3f}; "
          f"2020+: 95th {np.percentile(sims20,95):.2f}, p = {(sims20 >= metrics(r.loc['2020':],252)['sh']).mean():.3f}")
    regime(r, bh, 252, pos, ret, first, 5)
    # 2020 detail
    print("  -- 2020 by month (rule vs USO)")
    g = r.loc["2020"].groupby(r.loc["2020"].index.month).apply(lambda x: (1 + x).prod() - 1)
    gb = bh.loc["2020"].groupby(bh.loc["2020"].index.month).apply(lambda x: (1 + x).prod() - 1)
    print("    " + "  ".join(f"{m}:{a*100:.0f}/{b*100:.0f}" for m, a, b in zip(g.index, g.values, gb.values)))
    return r


# ---------------------------------------------------------------- D month-end Treasuries
def month_end_pos(idx, k=3):
    """hold over the last k trading days: pos=1 at the close of days ranked (from end) 2..k+1."""
    s = idx.to_series()
    rk = s.groupby(idx.to_period("M")).rank(method="first", ascending=False)
    pos = ((rk >= 2) & (rk <= k + 1)).astype(float)
    # the final (possibly incomplete) month: don't know its end yet -> only use completed months
    last_m = idx[-1].to_period("M")
    pos[idx.to_period("M") == last_m] = 0.0
    return pos


def run_D():
    print("=" * 100)
    print("D. Month-end Treasuries: IEF long over last 3 trading days; 252-day annualisation; 5 bp/side")
    out = {}
    for sym in ["IEF", "TLT", "SHY"]:
        px = load(sym)
        ret = px.pct_change().dropna()
        pos = month_end_pos(ret.index, 3)
        r = pnl(pos, ret, 5)
        if sym == "IEF":
            report("RULE (IEF, k=3)", r, 252, False)
            report("BUY&HOLD IEF", ret, 252, False)
            bh = ret
            print(f"  exposure {pos.mean():.3f}; month-end-day returns vs others: mean bp in-window {ret[pos.shift(1)==1].mean()*1e4:.2f}, out {ret[pos.shift(1)==0].mean()*1e4:.2f}")
            print("  -- execution / cost / data stress (full / 2014-19 / 2020+)")
            raw = load("IEF", "Close").pct_change().dropna()
            for lab, rr in [("base", r), ("delay1 (=enter 1 day later, exit 1 day after month-end)", pnl(pos, ret, 5, 1)),
                            ("cost25", pnl(pos, ret, 25)), ("delay1+cost25", pnl(pos, ret, 25, 1)),
                            ("RAW close (no dividends)", pnl(pos, raw, 5)), ("B&H on RAW close", raw)]:
                print(f"    {lab:56s} full {summary(rr, 252)}  2014-19 {summary(rr, 252, '2014-01-01', '2019-12-31')}  2020+ {summary(rr, 252, '2020-01-01')}")
            # placebo: random 3 consecutive days per month and random 3 scattered days
            rng = np.random.default_rng(5)
            real = metrics(r, 252)["sh"]; real14 = metrics(r.loc["2014":], 252)["sh"]
            per = ret.index.to_period("M")
            groups = [np.where(per == p)[0] for p in per.unique()]
            simc, sims, simc14 = [], [], []
            for _ in range(1000):
                pc = np.zeros(len(ret)); ps = np.zeros(len(ret))
                for g in groups[:-1]:
                    if len(g) < 5:
                        continue
                    st = rng.integers(0, len(g) - 3)
                    pc[g[st:st + 3]] = 1
                    ps[rng.choice(g, 3, replace=False)] = 1
                rc = pnl(pd.Series(pc, index=ret.index), ret, 5)
                simc.append(metrics(rc, 252)["sh"]); simc14.append(metrics(rc.loc["2014":], 252)["sh"])
                sims.append(metrics(pnl(pd.Series(ps, index=ret.index), ret, 5), 252)["sh"])
            simc, sims, simc14 = map(np.array, (simc, sims, simc14))
            print(f"  placebo random 3 consecutive days/month: mean Sh {simc.mean():.2f}, 95th {np.percentile(simc,95):.2f}, p = {(simc>=real).mean():.3f}; 2014+: 95th {np.percentile(simc14,95):.2f}, p = {(simc14>=real14).mean():.3f}")
            print(f"  placebo random 3 scattered days/month (more turnover): mean Sh {sims.mean():.2f}, 95th {np.percentile(sims,95):.2f}, p = {(sims>=real).mean():.3f}")
            # vs IEF hold all the time, same capital: compare return per unit exposure
            print(f"  return per day in market: rule {r[pos.shift(1)==1].mean()*1e4:.2f} bp vs B&H {ret.mean()*1e4:.2f} bp/day; B&H earns {((1+ret).prod()**(252/len(ret))-1)*100:.1f}%/yr vs rule {metrics(r,252)['cagr']*100:.1f}%/yr")
            regime(r, bh, 252, pos, ret, ret.index[0], 5)
            print("  -- neighbours k (last k days) per instrument: full / 2014-19 / 2020+ / ex-2020 / t full / pre-2014")
        rows = []
        for k in [2, 3, 4, 5]:
            p = month_end_pos(ret.index, k)
            rr = pnl(p, ret, 5)
            rows.append((f"{sym}_k{k}", metrics(rr, 252)["sh"], metrics(rr.loc['2014':'2019'], 252)["sh"], metrics(rr.loc['2020':], 252)["sh"],
                         ex_year(rr, 252, [2020])["sh"], metrics(rr, 252)["t"], metrics(rr.loc[:'2013'], 252)["sh"], metrics(rr, 252)["cagr"]))
        print(pd.DataFrame(rows, columns=["variant", "full", "14-19", "20+", "ex2020", "t_full", "pre2014", "cagr"]).set_index("variant").round(3).to_string())
    return r


if __name__ == "__main__":
    pd.set_option("display.width", 200)
    run_A(); run_B(); run_C(); run_D()
