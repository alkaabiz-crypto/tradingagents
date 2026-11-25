"""WIDE candle study (pre-registered 2026-11-25, before any run; the user asked to widen the candle research more).

Markets (51, daily from Yahoo, cached in the session scratchpad, not in git): oil USO BNO XLE XOP CL=F; US stocks
SPY QQQ IWM DIA ES=F NQ=F + 9 sectors XLF XLK XLU XLV XLP XLY XLI XLB; world EFA EEM EWJ EWZ EWG FXI EWU EWC EWA EWY;
bonds TLT IEF HYG LQD; commodities GLD SLV GC=F SI=F DBC UNG CPER DBA; forex EURUSD GBPUSD USDJPY AUDUSD USDCAD
USDCHF; crypto BTC ETH SOL XRP.
Timeframes: D (daily) and W (weekly candles, Monday-Friday; crypto weeks end Sunday).
Signals: all 61 TA-Lib patterns (bullish -> long, bearish -> short) + IBS_LOW (close in the bottom 20% of the range
  -> long) + IBS_HIGH (top 20% -> short) + HA_UP / HA_DOWN (Heikin-Ashi candle turns green / red).
Context filters: ALL | UP (close > 50-candle average) | DOWN (close < 50-candle average) | AT_LOW (low within 1 ATR of
  the 20-candle low) | AT_HIGH (high within 1 ATR of the 20-candle high).
Holds: D 1/3/5 candles; W 1/2/4 candles. Entry next open, exit at the close.
Costs per side: ETFs 5 bp, futures 2 bp, forex 1 bp, crypto 10 bp.
POOLED test (the point of widening): for each signal x side x context x hold x timeframe, every event in every market
  since 2014 (crypto since 2018) is scored as EXCESS = its return in the signal's direction minus that market's own
  average return over the same hold and period. Events are averaged by DATE first (markets move together), and the
  t-stat is over dates. Reported: events, markets, breadth (share of markets with positive excess), excess and net
  bp, OOS (2014-19) and HOLDOUT (2020+) excess, pre-2014 excess.
PASS (fixed): pooled t >= the Sidak 1% luck bar for the number of combinations judged (>= 100 events, >= 10
  markets); excess > 0 in OOS AND HOLDOUT; net > 0 at 2x cost; breadth >= 60%. Research, not financial advice.
"""
import os, sys, math, itertools
import numpy as np, pandas as pd, talib

HERE = os.path.dirname(os.path.abspath(__file__))
MKT = "/tmp/claude-0/-home-user-tradingagents/862edda5-54ef-5bf8-971e-481bdcdf4dee/scratchpad/mkt"
PATTERNS = sorted(f for f in talib.get_functions() if f.startswith("CDL"))
CTX = ["ALL", "UP", "DOWN", "AT_LOW", "AT_HIGH"]
HOLDS = {"D": [1, 3, 5], "W": [1, 2, 4]}


def cost(sym):
    return 1e-3 if sym.endswith("-USD") else 1e-4 if sym.endswith("=X") else 2e-4 if sym.endswith("=F") else 5e-4


def load(sym, tf):
    d = pd.read_csv(os.path.join(MKT, f"{sym}.csv"), index_col=0, parse_dates=True)[["Open", "High", "Low", "Close"]].dropna()
    d.index = pd.to_datetime(d.index)
    d = d[d.index < pd.Timestamp.now().normalize()]
    if tf == "W":
        rule = "W-SUN" if sym.endswith("-USD") else "W-FRI"
        d = d.resample(rule).agg({"Open": "first", "High": "max", "Low": "min", "Close": "last"}).dropna().iloc[:-1]
    ok = (d.High > d.Low) & (d.High >= d[["Open", "Close"]].max(axis=1)) & (d.Low <= d[["Open", "Close"]].min(axis=1))
    return d[ok]


def signals(b):
    o, h, l, c = (b[x].values.astype(float) for x in ("Open", "High", "Low", "Close"))
    S = {}
    for p in PATTERNS:
        v = getattr(talib, p)(o, h, l, c); S[(p, 1)] = v > 0; S[(p, -1)] = v < 0
    ibs = (c - l) / (h - l); S[("IBS_LOW", 1)] = ibs < 0.2; S[("IBS_HIGH", -1)] = ibs > 0.8
    hc = (o + h + l + c) / 4; ho = np.empty_like(hc); ho[0] = (o[0] + c[0]) / 2
    for i in range(1, len(hc)):
        ho[i] = (ho[i - 1] + hc[i - 1]) / 2
    g = hc > ho; S[("HA_UP", 1)] = g & ~np.roll(g, 1); S[("HA_DOWN", -1)] = ~g & np.roll(g, 1)
    C = b.Close; tr = pd.concat([b.High - b.Low, (b.High - C.shift()).abs(), (b.Low - C.shift()).abs()], axis=1).max(axis=1)
    atr = tr.rolling(14).mean(); sma = C.rolling(50).mean()
    X = {"ALL": np.ones(len(b), bool), "UP": (C > sma).values, "DOWN": (C < sma).values,
         "AT_LOW": (b.Low - b.Low.rolling(20).min() <= atr).values, "AT_HIGH": (b.High.rolling(20).max() - b.High <= atr).values}
    return S, X


def sidak_t(m, alpha=0.01):
    p = 1 - (1 - alpha) ** (1 / max(m, 1)); lo, hi = 0.0, 12.0
    for _ in range(60):
        mid = (lo + hi) / 2
        if math.erfc(mid / math.sqrt(2)) > p: lo = mid
        else: hi = mid
    return hi


def main():
    syms = sorted(f[:-4] for f in os.listdir(MKT) if f.endswith(".csv"))
    acc = {}  # key -> list of DataFrames (date, sym, x, net)
    for tf in ("D", "W"):
        for sym in syms:
            b = load(sym, tf)
            if len(b) < 300:
                continue
            S, X = signals(b); start = pd.Timestamp("2018-01-01" if sym.endswith("-USD") else "2014-01-01")
            for hold in HOLDS[tf]:
                r = (b.Close.shift(-hold) / b.Open.shift(-1) - 1).values
                idx = b.index; post = (idx >= start) & ~np.isnan(r)
                oos = post & (idx < pd.Timestamp("2020-01-01" if not sym.endswith("-USD") else "2022-01-01")); ho = post & ~oos
                pre = (idx < start) & ~np.isnan(r)
                mu = {"post": np.nanmean(r[post]), "oos": np.nanmean(r[oos]), "ho": np.nanmean(r[ho]), "pre": np.nanmean(r[pre]) if pre.any() else np.nan}
                for (p, side), m in S.items():
                    for ctx in CTX:
                        mm = m & X[ctx]
                        sel = mm & (post | pre)
                        if not sel.any():
                            continue
                        per = np.where(oos[sel], "oos", np.where(ho[sel], "ho", "pre"))
                        base = np.array([mu[x] for x in per])
                        rr = r[sel]
                        acc.setdefault((tf, p, side, ctx, hold), []).append(pd.DataFrame(
                            {"date": idx[sel], "sym": sym, "per": per, "x": side * (rr - base), "net": side * rr - 2 * cost(sym), "c": cost(sym)}))
    rows = []
    for key, parts in acc.items():
        d = pd.concat(parts); post = d[d.per != "pre"]
        if post.empty:
            continue
        byd = post.groupby("date").x.mean()
        t = byd.mean() / (byd.std(ddof=1) / np.sqrt(len(byd))) if len(byd) > 2 and byd.std() > 0 else np.nan
        bym = post.groupby("sym").x.mean()
        rows.append(dict(tf=key[0], signal=key[1], side="long" if key[2] > 0 else "short", ctx=key[3], hold=key[4],
                         events=len(post), markets=post.sym.nunique(), breadth=float((bym > 0).mean()),
                         excess_bp=post.x.mean() * 1e4, net_bp=post.net.mean() * 1e4,
                         net_bp_2x=(post.net - post.c * 2).mean() * 1e4, t=t,
                         oos_bp=d[d.per == "oos"].x.mean() * 1e4, ho_bp=d[d.per == "ho"].x.mean() * 1e4,
                         pre_bp=d[d.per == "pre"].x.mean() * 1e4))
    df = pd.DataFrame(rows)
    judged = df[(df.events >= 100) & (df.markets >= 10)]; bar = sidak_t(len(judged))
    df["PASS"] = (df.events >= 100) & (df.markets >= 10) & (df.t >= bar) & (df.oos_bp > 0) & (df.ho_bp > 0) & (df.net_bp_2x > 0) & (df.breadth >= 0.6)
    df.to_csv(os.path.join(HERE, "wide_results.csv"), index=False)
    pd.set_option("display.width", 250); pd.set_option("display.max_rows", 200)
    cols = ["tf", "signal", "side", "ctx", "hold", "events", "markets", "breadth", "excess_bp", "net_bp", "net_bp_2x", "t", "pre_bp", "oos_bp", "ho_bp", "PASS"]
    print(f"Combinations: {len(df)}; judged: {len(judged)}; luck bar t >= {bar:.2f}; PASS: {int(df.PASS.sum())}")
    print("\nTop 30 by pooled t (judged):"); print(judged.sort_values("t", ascending=False).head(30)[cols].round(2).to_string(index=False))
    print("\nBottom 15 by pooled t (most WRONG-WAY):"); print(judged.sort_values("t").head(15)[cols].round(2).to_string(index=False))
    print("\nPASS list:"); print(df[df.PASS].sort_values("t", ascending=False)[cols].round(2).to_string(index=False))


if __name__ == "__main__":
    main()
