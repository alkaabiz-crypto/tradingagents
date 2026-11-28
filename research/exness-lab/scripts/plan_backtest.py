"""Backtest of the $700 core + $300 satellite plan, 2024-01-02 .. 2026-11-25.
Pre-registered before running (2026-11-26):
- Core: $700 into US500 (SPY data, dividend-adjusted) at the first open; held. Cost: spread 1.5 bp once.
- Satellite $300, watchlist SPY QQQ IWM DIA GLD. Daily after the close, a 'Buy' signal enters at the next open.
  stop = clip(2 x ATR14 / price, 3%, 10%) below entry; shares sized so a stop-out loses $12; notional cap $150;
  max 2 open; exit at stop (gap below -> open price), else at the close of the 5th session. Both stop and
  later close same day -> stop. Kill switch: satellite equity <= $200 -> no new trades.
- Signal proxies (the AI cannot be run here: no API key, and 2024-25 dates are inside model training data):
  ALWAYS: every day is Buy.  TREND: Buy if close > 50-day average.  RANDOM: Buy with p=0.6 (AI's Buy share was
  ~60% in its tickets), 200 seeds, report median and 5th percentile.
- Costs: Exness Standard = spread (costs.py estimates) + 2 bp slippage on stop exits, PLUS overnight swap
  on non-swap-free: long pays an assumed 7%/yr per calendar night (estimate: ~4.5% policy rate + broker markup).
  Swap-free: no swap.
"""
import sys, numpy as np, pandas as pd
D = sys.argv[1] if len(sys.argv) > 1 else "data"
SPREAD = {"SPY": 1.5, "QQQ": 1.5, "DIA": 2.0, "IWM": 3.0, "GLD": 1.0}
SLIP = 2.0; SWAP_LONG = 0.07
START, END = "2024-01-02", "2026-11-25"


def load(t):
    d = pd.read_csv(f"{D}/{t}.csv", parse_dates=["Date"], index_col="Date")
    tr = pd.concat([d.High - d.Low, (d.High - d.Close.shift()).abs(), (d.Low - d.Close.shift()).abs()], axis=1).max(axis=1)
    d["atr"] = tr.rolling(14).mean(); d["sma50"] = d.Close.rolling(50).mean()
    return d


W = ["SPY", "QQQ", "IWM", "DIA", "GLD"]
DATA = {t: load(t) for t in W}
days = DATA["SPY"].loc[START:END].index
for _t in W: days = days.intersection(DATA[_t].index)


def core(swap):
    s = DATA["SPY"].loc[days]
    units = 700 * (1 - SPREAD["SPY"] / 1e4) / s.Open.iloc[0]
    eq = units * s.Close
    if swap:
        nights = pd.Series(s.index, index=s.index).diff().dt.days.fillna(0).cumsum()
        # swap charged on notional each night
        cost = (eq.shift().fillna(eq.iloc[0]) * SWAP_LONG / 365 * pd.Series(s.index, index=s.index).diff().dt.days.fillna(0)).cumsum()
        eq = eq - cost
    return eq


def satellite(signal_fn, swap, rng=None):
    cash, open_pos, trades, eq_curve, killed = 300.0, [], [], [], False
    for i, day in enumerate(days):
        # 1) manage open positions today
        still = []
        for p in open_pos:
            bar = DATA[p["t"]].loc[day]
            p["n"] += 1
            exit_px, why = None, None
            if bar.Open <= p["stop"]:
                exit_px, why = bar.Open, "gap"
            elif bar.Low <= p["stop"]:
                exit_px, why = p["stop"], "stop"
            elif p["n"] >= 5:
                exit_px, why = bar.Close, "time"
            if swap:
                gap = (day - p["last"]).days
                cash -= p["sh"] * p["entry"] * SWAP_LONG / 365 * gap
                p["last"] = day
            if exit_px is not None:
                c = SPREAD[p["t"]] / 2 + (SLIP if why in ("stop", "gap") else 0)
                px = exit_px * (1 - c / 1e4)
                pnl = p["sh"] * (px - p["entry"])
                cash += p["sh"] * p["entry"] + pnl
                trades.append(pnl)
            else:
                still.append(p)
        open_pos = still
        # 2) mark to market
        mtm = cash + sum(p["sh"] * DATA[p["t"]].loc[day].Close for p in open_pos)
        eq_curve.append(mtm)
        if mtm <= 200: killed = True
        # 3) new entries for tomorrow's open
        if killed or i + 1 >= len(days): continue
        nxt = days[i + 1]
        for t in W:
            if len(open_pos) >= 2: break
            if any(p["t"] == t for p in open_pos): continue
            d = DATA[t]
            if day not in d.index or nxt not in d.index: continue
            if not signal_fn(t, day, rng): continue
            row = d.loc[day]; o = d.loc[nxt].Open
            stop_pct = float(np.clip(2 * row.atr / row.Close, 0.03, 0.10))
            entry = o * (1 + SPREAD[t] / 2 / 1e4)
            sh = min(12 / (entry * stop_pct), 150 / entry)
            if sh * entry > cash: continue
            cash -= sh * entry
            open_pos.append({"t": t, "entry": entry, "stop": entry * (1 - stop_pct), "sh": sh, "n": 0, "last": nxt,
                             "pending": True})
    return pd.Series(eq_curve, index=days), trades


# entries are bought at next open but counted from that day; n counts sessions incl. entry day
def sig_always(t, day, rng): return True
def sig_trend(t, day, rng): r = DATA[t].loc[day]; return r.Close > r.sma50
def sig_random(t, day, rng): return rng.random() < 0.6


def stats(eq):
    dd = (eq / eq.cummax() - 1).min()
    return eq.iloc[-1], eq.iloc[-1] - eq.iloc[0] if False else None, dd


def summarize(name, sat, trades, cr):
    tot = cr + sat
    dd_tot = (tot / tot.cummax() - 1).min(); dd_sat = (sat / sat.cummax() - 1).min()
    low_sat = sat.min()
    w = np.mean([x > 0 for x in trades]) if trades else float("nan")
    print(f"| {name} | ${sat.iloc[-1]:.0f} ({sat.iloc[-1]-300:+.0f}) | {len(trades)} | {w:.0%} | {dd_sat:.0%} (low ${low_sat:.0f}) | ${tot.iloc[-1]:.0f} ({tot.iloc[-1]-1000:+.0f}) | {dd_tot:.0%} ({(tot.cummax()-tot).max():.0f}$) |")


for swap in (False, True):
    acct = "Standard WITH overnight swap (est. 7%/yr long)" if swap else "Swap-free"
    cr = core(swap)
    print(f"\n### {acct}\nCore $700 US500: end ${cr.iloc[-1]:.0f} ({cr.iloc[-1]-700:+.0f}), worst drop {(cr/cr.cummax()-1).min():.0%} "
          f"(${(cr.cummax()-cr).max():.0f})")
    allin = core(swap) / 700 * 1000
    print(f"All $1,000 in US500: end ${allin.iloc[-1]:.0f}, worst drop ${(allin.cummax()-allin).max():.0f}")
    print("| Satellite signal | Satellite end | Trades | Win rate | Satellite worst drop | Total $1,000 end | Total worst drop |")
    print("|---|---|---|---|---|---|---|")
    for nm, fn in (("Always Buy", sig_always), ("Trend (close > 50-day avg)", sig_trend)):
        sat, tr = satellite(fn, swap); summarize(nm, sat, tr, cr)
    ends, dds, res = [], [], []
    for seed in range(200):
        sat, tr = satellite(sig_random, swap, np.random.default_rng(seed)); ends.append(sat.iloc[-1]); dds.append((sat / sat.cummax() - 1).min())
    print(f"| Random 60% Buy, 200 seeds | median ${np.median(ends):.0f}, 5th pct ${np.percentile(ends,5):.0f}, 95th ${np.percentile(ends,95):.0f} | | | median {np.median(dds):.0%}, worst {min(dds):.0%} | | |")
