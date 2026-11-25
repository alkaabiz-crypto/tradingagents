"""Small wins, many trades (pre-registered 2026-11-25, before any run; the user wants small, frequent wins
rather than big ones, in oil first, then other markets).

Classic short-term setups that usually win often with small gains (daily bars; signal at the close, entry AT
THAT CLOSE, e.g. a market-on-close or a CFD order just before the close; one position at a time):
  S1 IBS: internal bar strength (C-L)/(H-L) < 0.2 -> exit at the first close with IBS > 0.5 or after 5 days
  S2 IBS < 0.2 AND close above the 200-day average (trend filter), same exit
  S3 RSI(2) < 10 -> exit when the close is above the 5-day average, or after 10 days (Connors-style)
  S4 RSI(2) < 10 AND above the 200-day average, same exit
  S5 three down closes in a row -> exit at the first up close, or after 5 days
  S6 close below the lower Bollinger band (20, 2 sd) -> exit at the 20-day average, or after 10 days
  S7 overnight: buy every close, sell the next open (the overnight-drift effect)
  S8 small fixed target on the S1 signal: take profit +0.5 x ATR(14), stop -1.5 x ATR(14), max 5 days
     (target/stop checked on daily highs/lows; if a bar touches both, count the STOP)
Each long setup also runs MIRRORED as a short (IBS > 0.8, RSI(2) > 90, three up closes, above the upper band,
below the 200-day average for the filtered ones; S7 short = sell the close, buy back the open).
Markets: USO, BNO, XLE, XOP (oil) and SPY, QQQ, IWM, GLD, TLT.
Systems: 8 setups x 2 sides x 9 markets = 144.
Costs: 5 bp per side (ETFs / a tight CFD spread); robustness at 2x cost (10 bp per side).
Periods by entry date: IS up to 2013, OOS 2014-2019, HOLDOUT 2020-2026.
PASS (fixed): average trade > 0 net of costs in OOS AND HOLDOUT; post-2014 t >= 2; average > 0 at 2x cost;
  random-entry placebo (same number of trades post-2014, random entry days, the same exit rule; 200 runs)
  p <= 0.01. A high win rate alone is NOT a pass: small wins with rare big losses can still lose money.
Reported: trades a year, win rate, average win, average loss, worst trade, average trade (bp), t.
Research, not financial advice.
"""
import os
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); OB = os.path.dirname(HERE)
MARKETS = ["USO", "BNO", "XLE", "XOP", "SPY", "QQQ", "IWM", "GLD", "TLT"]
SETUPS = ["S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8"]
DESC = {"S1": "IBS dip", "S2": "IBS dip + trend", "S3": "RSI2 dip", "S4": "RSI2 dip + trend", "S5": "3 down closes",
        "S6": "below Bollinger", "S7": "overnight hold", "S8": "IBS + small target"}
COST = 5e-4


def load(sym):
    p = os.path.join(OB, "data", f"{sym}.csv")
    if not os.path.exists(p):
        p = os.path.join(OB, "brains/liquidity/data", f"{sym}.csv")
    df = pd.read_csv(p, index_col=0, parse_dates=True)
    df.index = pd.to_datetime(df.index).tz_localize(None).normalize()
    df = df[~df.index.duplicated()][["Open", "High", "Low", "Close"]].dropna()
    return df[(df.High >= df.Low) & (df.Close > 0)]


def rsi(x, n):
    d = x.diff(); up = d.clip(lower=0).ewm(alpha=1 / n).mean(); dn = (-d.clip(upper=0)).ewm(alpha=1 / n).mean()
    return 100 - 100 / (1 + up / dn)


def indicators(b):
    c = b.Close; rng = (b.High - b.Low).replace(0, np.nan)
    i = pd.DataFrame(index=b.index)
    i["ibs"] = ((c - b.Low) / rng).fillna(0.5)
    i["sma200"] = c.rolling(200).mean(); i["sma5"] = c.rolling(5).mean(); i["sma20"] = c.rolling(20).mean()
    sd = c.rolling(20).std(); i["bbl"] = i.sma20 - 2 * sd; i["bbu"] = i.sma20 + 2 * sd
    i["rsi2"] = rsi(c, 2)
    up = c.diff() > 0; dn = c.diff() < 0
    i["dn3"] = dn & dn.shift(1, fill_value=False) & dn.shift(2, fill_value=False)
    i["up3"] = up & up.shift(1, fill_value=False) & up.shift(2, fill_value=False)
    tr = pd.concat([b.High - b.Low, (b.High - c.shift()).abs(), (b.Low - c.shift()).abs()], axis=1).max(axis=1)
    i["atr"] = tr.rolling(14).mean()
    return i


def entries(setup, side, i, c):
    L = side == 1
    trend = (c > i.sma200) if L else (c < i.sma200)
    e = {"S1": i.ibs < 0.2 if L else i.ibs > 0.8,
         "S3": i.rsi2 < 10 if L else i.rsi2 > 90,
         "S5": i.dn3 if L else i.up3,
         "S6": c < i.bbl if L else c > i.bbu,
         "S7": pd.Series(True, index=c.index)}
    e["S2"] = e["S1"] & trend; e["S4"] = e["S3"] & trend; e["S8"] = e["S1"]
    return e[setup].fillna(False) & i.sma200.notna()


def exit_from(setup, side, b, i, k):
    """Given entry at close of bar k, return (exit bar index, exit price)."""
    c = b.Close.values; n = len(c); L = side == 1
    if setup == "S7":
        return (k + 1, b.Open.values[k + 1]) if k + 1 < n else (None, None)
    if setup == "S8":
        a = i.atr.values[k]; e = c[k]; tgt = e + side * 0.5 * a; stp = e - side * 1.5 * a
        for j in range(k + 1, min(k + 6, n)):
            hi, lo = b.High.values[j], b.Low.values[j]
            hit_s = lo <= stp if L else hi >= stp; hit_t = hi >= tgt if L else lo <= tgt
            if hit_s:
                return j, (min(stp, b.Open.values[j]) if L else max(stp, b.Open.values[j]))  # gap through = worse
            if hit_t:
                return j, (max(tgt, b.Open.values[j]) if L else min(tgt, b.Open.values[j]))
        j = min(k + 5, n - 1)
        return (j, c[j]) if j > k else (None, None)
    maxd = {"S1": 5, "S2": 5, "S3": 10, "S4": 10, "S5": 5, "S6": 10}[setup]
    ibs, s5, s20 = i.ibs.values, i.sma5.values, i.sma20.values
    for j in range(k + 1, min(k + 1 + maxd, n)):
        done = {"S1": ibs[j] > 0.5 if L else ibs[j] < 0.5,
                "S3": c[j] > s5[j] if L else c[j] < s5[j],
                "S5": c[j] > c[j - 1] if L else c[j] < c[j - 1],
                "S6": c[j] > s20[j] if L else c[j] < s20[j]}[{"S2": "S1", "S4": "S3"}.get(setup, setup)]
        if done:
            return j, c[j]
    j = min(k + maxd, n - 1)
    return (j, c[j]) if j > k else (None, None)


def trades(setup, side, b, i, flags):
    out = []; k = 0; f = flags.values; c = b.Close.values; n = len(c); idx = b.index
    while k < n - 1:
        if f[k]:
            j, px = exit_from(setup, side, b, i, k)
            if j is None:
                break
            out.append((idx[k], side * (px / c[k] - 1), j - k))
            k = j if setup != "S7" else k + 1  # overnight: the next close is a new entry
        else:
            k += 1
    return pd.DataFrame(out, columns=["date", "gross", "days"])


def stats(t, cost):
    if len(t) < 2:
        return dict(n=len(t), avg_bp=np.nan, t=np.nan, win=np.nan)
    r = t.gross - 2 * cost
    return dict(n=len(t), avg_bp=round(r.mean() * 1e4, 2), t=round(r.mean() / (r.std(ddof=1) / np.sqrt(len(r))), 2),
                win=round((r > 0).mean(), 3))


def placebo(setup, side, b, i, ntr, start, seed, runs=200):
    rng = np.random.default_rng(seed); pos = np.where(b.index >= start)[0]; pos = pos[pos < len(b) - 11]
    res = []
    for _ in range(runs):
        ks = np.sort(rng.choice(pos, size=min(ntr, len(pos)), replace=False)); g = []
        for k in ks:
            j, px = exit_from(setup, side, b, i, k)
            if j is not None:
                g.append(side * (px / b.Close.values[k] - 1))
        res.append(np.mean(g) - 2 * COST if g else np.nan)
    return np.array(res)


def main():
    rows = []; start = pd.Timestamp("2014-01-01")
    for sym in MARKETS:
        b = load(sym); i = indicators(b)
        years = (b.index[-1] - start).days / 365.25
        for s in SETUPS:
            for side in (1, -1):
                t = trades(s, side, b, i, entries(s, side, i, b.Close))
                per = {"IS": t[t.date < start], "OOS": t[(t.date >= start) & (t.date < "2020-01-01")],
                       "HOLDOUT": t[t.date >= "2020-01-01"], "POST": t[t.date >= start]}
                r = dict(sym=sym, setup=s, side="long" if side == 1 else "short", name=DESC[s])
                for k, v in per.items():
                    st = stats(v, COST); r.update({f"{k}_{a}": st[a] for a in ("n", "avg_bp", "t")})
                post = per["POST"]; net = post.gross - 2 * COST
                r.update(per_year=round(len(post) / years, 1), win=round((net > 0).mean(), 3) if len(post) else np.nan,
                         avg_win_bp=round(net[net > 0].mean() * 1e4, 1) if (net > 0).any() else np.nan,
                         avg_loss_bp=round(net[net <= 0].mean() * 1e4, 1) if (net <= 0).any() else np.nan,
                         worst_bp=round(net.min() * 1e4, 0) if len(post) else np.nan,
                         avg_days=round(post.days.mean(), 1) if len(post) else np.nan,
                         POST_avg_bp_2x=stats(post, 2 * COST)["avg_bp"])
                rows.append(r)
    df = pd.DataFrame(rows)
    cand = df[(df.OOS_avg_bp > 0) & (df.HOLDOUT_avg_bp > 0) & (df.POST_t >= 2) & (df.POST_avg_bp_2x > 0)].copy()
    ps = []
    for _, r in cand.iterrows():
        b = load(r.sym); i = indicators(b); side = 1 if r.side == "long" else -1
        pl = placebo(r.setup, side, b, i, int(r.POST_n), start, seed=1000 + len(ps))  # fixed integer seed (MISTAKES C4 fix, 2026-11-25)
        ps.append(round(float(np.nanmean(pl >= r.POST_avg_bp / 1e4)), 3))
    cand["placebo_p"] = ps
    df = df.merge(cand[["sym", "setup", "side", "placebo_p"]], how="left", on=["sym", "setup", "side"])
    df["PASS"] = df.placebo_p <= 0.01
    df.to_csv(os.path.join(HERE, "smallwins_results.csv"), index=False)
    pd.set_option("display.width", 260); pd.set_option("display.max_rows", 200); pd.set_option("display.max_columns", 30)
    cols = ["sym", "name", "side", "per_year", "win", "avg_win_bp", "avg_loss_bp", "worst_bp", "avg_days",
            "IS_avg_bp", "OOS_avg_bp", "HOLDOUT_avg_bp", "POST_t", "POST_avg_bp_2x", "placebo_p", "PASS"]
    print(f"Systems tested: {len(df)}; passed the first gates: {len(cand)}; PASS (placebo p <= 0.01): {int(df.PASS.sum())}")
    print("\nAll systems with post-2014 t >= 1.5, best first:")
    print(df[df.POST_t >= 1.5].sort_values("POST_t", ascending=False)[cols].to_string(index=False))
    print("\nOil markets, long side, every setup (win rate vs average trade):")
    print(df[df.sym.isin(["USO", "BNO", "XLE", "XOP"]) & (df.side == "long")][cols].to_string(index=False))


if __name__ == "__main__":
    main()
