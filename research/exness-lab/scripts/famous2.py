"""Famous daily strategies on Exness CFD markets, two account types. PRE-REGISTERED 2026-11-26 before any run.
Parameters are the published defaults; nothing is tuned. 16 strategies x 7 markets = 112 tests (+7 benchmarks).
Markets (Yahoo proxy -> Exness): SPY->US500, QQQ->USTEC, DIA->US30, IWM->US2000, GLD->XAUUSD, SLV->XAGUSD, BTC-USD->BTCUSD.
Execution: signal at the close of day t, filled at that close (order placed just before the close; CFDs trade
through the US close); P&L on close(t)->close(t+1). Intraday systems (overnight drift, Williams, NR7) use the stated bars.
Costs: Standard = spread only (round-trip bp below; EURUSD/XAUUSD from review sites, rest are the repo's costs.py
estimates), charged half per side on every change of position. Swap-free: no swap. Standard (non-swap-free):
every night a position is held costs an ESTIMATED 7%/yr (long) or 2%/yr (short) of notional per calendar night.
Splits: IS <= 2013, OOS 2014-2019, HO 2020-2023, RECENT 2024-01-01..2026-11-25.
PASS (swap-free costs): Sharpe > 0.3 in OOS, HO and RECENT; post-2014 Sharpe > buy-and-hold's; post-2014 t >= 2;
still positive post-2014 at 2x costs. ROBUST = PASS on >= 4 of the 7 markets. With 112 tests, ~5 t>=2 results
are expected from luck alone, so a single-market PASS is a lead, not proof.
"""
import sys, numpy as np, pandas as pd
D = sys.argv[1]
MK = {"SPY": 1.5, "QQQ": 1.5, "DIA": 2.0, "IWM": 3.0, "GLD": 1.0, "SLV": 6.0, "BTC-USD": 3.0}
SW_L, SW_S = 0.07, 0.02
PER = {"IS": ("1990", "2013-12-31"), "OOS": ("2014", "2019-12-31"), "HO": ("2020", "2023-12-31"),
       "RECENT": ("2024", "2026-11-25"), "POST14": ("2014", "2026-11-25")}


def rsi(c, n):
    d = c.diff(); up = d.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean(); dn = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    return 100 - 100 / (1 + up / dn)


def hold_until(entry, exit_):
    """Position 1 from an entry signal until an exit signal (state machine)."""
    pos, out = 0, []
    for e, x in zip(entry.values, exit_.values):
        if pos == 0 and e: pos = 1
        elif pos == 1 and x: pos = 0
        out.append(pos)
    return pd.Series(out, index=entry.index, dtype=float)


def strategies(d):
    c, h, l, o = d.Close, d.High, d.Low, d.Open
    s200, s50 = c.rolling(200).mean(), c.rolling(50).mean()
    P = {}  # name -> (kind, series) kind 'pos' = close-to-close position; 'ret' = own daily gross return + turnover
    P["Buy and hold"] = ("pos", pd.Series(1.0, index=c.index))
    r2 = rsi(c, 2)
    P["Connors RSI(2) <10 above 200-day, out RSI>70"] = ("pos", hold_until((r2 < 10) & (c > s200), r2 > 70))
    ibs = (c - l) / (h - l).replace(0, np.nan)
    P["IBS < 0.2 buy, out IBS > 0.8"] = ("pos", hold_until(ibs < 0.2, ibs > 0.8))
    P["Double 7s (7-day low above 200-day, out 7-day high)"] = ("pos", hold_until((c <= c.rolling(7).min()) & (c > s200), c >= c.rolling(7).max()))
    down3 = (c < c.shift()) & (c.shift() < c.shift(2)) & (c.shift(2) < c.shift(3))
    P["3 down closes above 200-day, out first up close"] = ("pos", hold_until(down3 & (c > s200), c > c.shift()))
    m = pd.Series(c.index.to_period("M"), index=c.index)
    tdom = m.groupby(m).cumcount() + 1; last = m != m.shift(-1)
    # hold the return of: last trading day of month and the first 3 trading days -> position set at prior close
    ret_day = last | (tdom <= 3)
    P["Turn of the month (last day + first 3)"] = ("pos", ret_day.shift(-1).fillna(False).astype(float))
    P["Golden cross (50-day above 200-day)"] = ("pos", (s50 > s200).astype(float))
    me = m != m.shift(-1); s210 = c.rolling(210).mean()
    fab = pd.Series(np.where(me, (c > s210).astype(float), np.nan), index=c.index).ffill().fillna(0)
    P["Faber 10-month average, monthly"] = ("pos", fab)
    hi20, lo10, lo20, hi10 = h.rolling(20).max().shift(), l.rolling(10).min().shift(), l.rolling(20).min().shift(), h.rolling(10).max().shift()
    pos, out = 0, []
    for ci, a, b, e, f in zip(c.values, hi20.values, lo10.values, lo20.values, hi10.values):
        if pos <= 0 and ci > a: pos = 1
        elif pos >= 0 and ci < e: pos = -1
        elif pos == 1 and ci < b: pos = 0
        elif pos == -1 and ci > f: pos = 0
        out.append(pos)
    P["Turtle/Donchian 20-day breakout, 10-day exit, long+short"] = ("pos", pd.Series(out, index=c.index, dtype=float))
    macd = c.ewm(span=12, adjust=False).mean() - c.ewm(span=26, adjust=False).mean()
    P["MACD 12/26/9 above signal, long only"] = ("pos", (macd > macd.ewm(span=9, adjust=False).mean()).astype(float))
    mid, sd = c.rolling(20).mean(), c.rolling(20).std()
    P["Bollinger 20/2: buy below lower band, out at middle"] = ("pos", hold_until(c < mid - 2 * sd, c > mid))
    tsm = pd.Series(np.where(me, (c / c.shift(252) - 1 > 0).astype(float), np.nan), index=c.index).ffill().fillna(0)
    P["12-month time-series momentum, monthly, long/flat"] = ("pos", tsm)
    vol = c.pct_change().rolling(20).std() * np.sqrt(252)
    P["Volatility-targeted hold (15%/yr, max 1x)"] = ("pos", (0.15 / vol).clip(upper=1.0).fillna(0))
    # intraday / overnight systems: (gross return, turnover per day, overnight exposure)
    on = o / c.shift() - 1
    P["Overnight drift (buy close, sell next open)"] = ("ret", on.fillna(0), pd.Series(2.0, index=c.index), pd.Series(1.0, index=c.index))
    rng_prev = (h - l).shift()
    trig = o + 0.5 * rng_prev
    hit = h >= trig
    wret = np.where(hit, c / np.maximum(trig, o) - 1, 0.0)
    P["Larry Williams breakout (open + 0.5 x prior range, out at close)"] = ("ret", pd.Series(wret, index=c.index).fillna(0), hit.astype(float) * 2, pd.Series(0.0, index=c.index))
    rngs = h - l; nr7 = (rngs <= rngs.rolling(7).min()).shift().fillna(False).astype(bool)
    ph, pl = h.shift(), l.shift()
    up = nr7 & (h > ph); dn = nr7 & (l < pl)
    long_r = c / np.maximum(ph, o) - 1; short_r = np.minimum(pl, o) / c - 1
    both = up & dn
    nr = np.where(both, np.minimum(long_r, short_r), np.where(up, long_r, np.where(dn, short_r, 0.0)))
    P["NR7 breakout both ways (Crabel), out at close"] = ("ret", pd.Series(nr, index=c.index).fillna(0), (up | dn).astype(float) * 2, pd.Series(0.0, index=c.index))
    return P


def daily_returns(d, spec, spread_bp, swap, cost_mult=1.0):
    c = d.Close; r = c.pct_change().fillna(0)
    nights = pd.Series(c.index, index=c.index).diff().dt.days.fillna(1)
    half = spread_bp / 2 / 1e4 * cost_mult
    if spec[0] == "pos":
        p = spec[1].shift().fillna(0)  # position decided at prior close
        turn = spec[1].diff().abs().fillna(spec[1].iloc[0] if len(spec[1]) else 0).shift().fillna(0)
        net = p * r - turn * half
        expo = p
    else:
        _, g, turn, overnight = spec
        net = g - turn * half
        p = overnight; expo = overnight + (turn > 0)  # rough exposure
    if swap:
        pos_on = spec[1].shift().fillna(0) if spec[0] == "pos" else spec[3]
        net = net - np.where(pos_on > 0, pos_on * SW_L, -pos_on * SW_S) / 365 * nights
    return net, expo


def stats(x, ann):
    if len(x) < 30 or x.std() == 0: return dict(cagr=np.nan, sh=np.nan, dd=np.nan, t=np.nan)
    eq = (1 + x).cumprod(); yrs = len(x) / ann
    sh = x.mean() / x.std() * np.sqrt(ann)
    return dict(cagr=eq.iloc[-1] ** (1 / yrs) - 1, sh=sh, dd=(eq / eq.cummax() - 1).min(), t=sh * np.sqrt(yrs))


rows = []
for t, sp in MK.items():
    d = pd.read_csv(f"{D}/{t}.csv", parse_dates=["Date"], index_col="Date").dropna()
    ann = 365 if t == "BTC-USD" else 252
    for name, spec in strategies(d).items():
        res = {"strategy": name, "market": t}
        for acct, swap in (("free", False), ("std", True)):
            net, expo = daily_returns(d, spec, sp, swap)
            for pn, (a, b) in PER.items():
                st = stats(net.loc[a:b], ann)
                for k, v in st.items(): res[f"{acct}_{pn}_{k}"] = v
            if acct == "free": res["exposure"] = float(expo.loc["2014":].mean())
        net2, _ = daily_returns(d, spec, sp, False, 2.0)
        res["post14_cagr_2x"] = stats(net2.loc["2014":], ann)["cagr"]
        rec = net.loc["2024":"2026-11-25"]
        res["recent_dollars_300_free"] = 300 * ((1 + daily_returns(d, spec, sp, False)[0].loc["2024":"2026-11-25"]).prod() - 1)
        res["recent_dollars_300_std"] = 300 * ((1 + rec).prod() - 1)
        rows.append(res)
df = pd.DataFrame(rows)
bh = df[df.strategy == "Buy and hold"].set_index("market")["free_POST14_sh"]
df["bh_post14_sh"] = df.market.map(bh)
df["PASS"] = ((df.free_OOS_sh > 0.3) & (df.free_HO_sh > 0.3) & (df.free_RECENT_sh > 0.3) & (df.free_POST14_sh > df.bh_post14_sh)
              & (df.free_POST14_t >= 2) & (df.post14_cagr_2x > 0) & (df.strategy != "Buy and hold"))
df.to_csv(sys.argv[2], index=False)
print(f"tests: {int((df.strategy != 'Buy and hold').sum())}; PASS: {int(df.PASS.sum())}")
print(df[df.PASS][["strategy", "market", "free_POST14_sh", "bh_post14_sh", "free_POST14_t", "free_RECENT_sh", "exposure"]].to_string())
agg = df[df.strategy != "Buy and hold"].groupby("strategy").agg(passes=("PASS", "sum"), med_sh_free=("free_POST14_sh", "median"),
        med_sh_std=("std_POST14_sh", "median"), med_recent_free=("recent_dollars_300_free", "median"),
        med_recent_std=("recent_dollars_300_std", "median")).sort_values("med_sh_free", ascending=False)
print(agg.round(2).to_string())
print(df[df.strategy == "Buy and hold"][["market", "free_POST14_sh", "free_POST14_cagr", "free_POST14_dd", "std_POST14_sh", "recent_dollars_300_free", "recent_dollars_300_std"]].round(2).to_string())
