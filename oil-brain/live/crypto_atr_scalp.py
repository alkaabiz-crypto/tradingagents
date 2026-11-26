"""Two questions from the user (pre-registered 2026-11-26, before any run): "does changing the ATR help? or buying it
so low and selling it fast but buying a lot of times, does this help?"

PART A — ATR length. The fixed crypto trend day trade (BTC+ETH, SMA50 direction, vol sizing, out at the UTC close,
  from crypto_trend_opt.py) with the ATR measured over 7, 14 (current), 30 days x stop 0.35 / 0.5 / 0.75 ATR = 9.
  "Helps" = better Sharpe AND return/worst-drop than ATR14/0.5 in BOTH 2014-21 and 2022+.

PART B — "buy low, sell fast, many times" (a dip-buying scalp grid), on HOURLY bars (Yahoo keeps ~2 years of 1h).
  Each UTC day: buy level = the day's open - x * ATR14(daily); take profit = buy level + y * ATR14.
  When an hour's low touches the level -> buy at the level; sell at the take-profit (only on a LATER hour, so the
  order inside one hour never helps us), else at the day's close. After a take-profit, re-buy each time price comes
  back to the level (many trades a day). No stop (it is out by the close). Long only.
  x in {0.25, 0.5, 1.0}, y in {0.1, 0.25, 0.5}, trend filter {none, only above the 50-day average} = 18 per coin,
  BTC and ETH = 36. Costs from costs.py on EVERY trade (Exness Standard spread; no commission, no swap).
  Compared with the trend day trade on the same days. "Helps" = more money a day than the trend rule AND t >= 3.5
  (Sidak-style bar for 36 tries). Research, not financial advice.      python3 oil-brain/live/crypto_atr_scalp.py
"""
import os, sys
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); OB = os.path.dirname(HERE)
sys.path.insert(0, HERE); sys.path.insert(0, OB)
from day_ticket_backrun import full_bars
import costs
import crypto_trend_opt as C


def atr_n(d, n):
    tr = pd.concat([d.High - d.Low, (d.High - d.Close.shift()).abs(), (d.Low - d.Close.shift()).abs()], axis=1).max(axis=1)
    return tr.rolling(n).mean()


def part_a():
    rows = []
    for n in (7, 14, 30):
        C.atr = lambda d, n=n: atr_n(d, n)          # swap the ATR length used by the trend rule
        for k in (0.35, 0.5, 0.75):
            r = C.series(("BTC+ETH", "SMA50", k, "vol", "none"))
            for per, m in (("2014-21", r.index < "2022-01-01"), ("2022+", r.index >= "2022-01-01")):
                rows.append(dict(atr_days=n, stop=k, period=per, **C.stats(r[m])))
    C.atr = lambda d: atr_n(d, 14)
    df = pd.DataFrame(rows); b = df[(df.atr_days == 14) & (df.stop == 0.5)].set_index("period")
    print("PART A — ATR length x stop (BTC+ETH trend, vol sized):"); print(df.round(2).to_string(index=False))
    helps = [(n, k) for (n, k), g in df.groupby(["atr_days", "stop"]) if (n, k) != (14, 0.5) and
             all(g.set_index("period").sharpe[p] > b.sharpe[p] and g.set_index("period").MAR[p] > b.MAR[p] for p in b.index)]
    print("Helps in both periods:", helps or "none"); return df


def hourly(sym):
    import yfinance as yf
    h = yf.Ticker(sym).history(period="730d", interval="1h")[["Open", "High", "Low", "Close"]].dropna()
    h.index = h.index.tz_convert("UTC").tz_localize(None); return h


def scalp_day(h, lvl, tp, cost):
    pnl, n, holding, entry = 0.0, 0, False, 0.0
    for i in range(len(h)):
        lo, hi = h.Low.iloc[i], h.High.iloc[i]
        if holding and hi >= tp:
            pnl += tp / entry - 1 - cost; n += 1; holding = False; continue   # sold; may re-buy next hour
        if not holding and lo <= lvl:
            holding, entry = True, lvl
    if holding:
        pnl += h.Close.iloc[-1] / entry - 1 - cost; n += 1
    return pnl, n


def part_b():
    rows, trend_days = [], {}
    for sym in ("BTC-USD", "ETH-USD"):
        H = hourly(sym); D = full_bars(sym); a = atr_n(D, 14).shift(1); up = (D.Close > D.Close.rolling(50).mean()).shift(1)
        cost = costs.round_trip(sym); days = sorted(set(H.index.normalize()))[1:-1]
        tr = C.coin(sym, "SMA50", 0.5, "vol", "none"); trend_days[sym] = tr[tr.index.isin(days)]
        for x in (0.25, 0.5, 1.0):
            for y in (0.1, 0.25, 0.5):
                for filt in ("none", "uptrend"):
                    r, nt = [], 0
                    for d in days:
                        if d not in a.index or np.isnan(a[d]) or (filt == "uptrend" and not up.get(d, False)):
                            r.append(0.0); continue
                        h = H[(H.index >= d) & (H.index < d + pd.Timedelta(days=1))]
                        lvl = h.Open.iloc[0] - x * a[d]; p, n = scalp_day(h, lvl, lvl + y * a[d], cost); r.append(p); nt += n
                    r = pd.Series(r, index=days)
                    rows.append(dict(coin=sym, x_buy_below=x, y_take_profit=y, filter=filt, trades=nt,
                                     trades_per_day=nt / len(days), day_pct=r.mean() * 100,
                                     t=r.mean() / (r.std() / np.sqrt(len(r))) if r.std() > 0 else np.nan,
                                     worst_day_pct=r.min() * 100))
    df = pd.DataFrame(rows)
    print(f"\nPART B — buy-low / sell-fast scalp grid, hourly, {len(days)} days (~2 years), costs on every trade:")
    print(df.sort_values("t", ascending=False).round(3).to_string(index=False))
    for sym, r in trend_days.items():
        print(f"Trend day trade, same days, {sym}: {r.mean() * 100:+.3f}%/day, t {r.mean() / (r.std() / np.sqrt(len(r))):.2f}")
    best = df.loc[df.t.idxmax()]
    print("Helps (beats the trend rule and t >= 3.5):",
          "YES " + str(best[["coin", "x_buy_below", "y_take_profit", "filter"]].to_dict())
          if best.t >= 3.5 and best.day_pct > trend_days[best.coin].mean() * 100 else "none")
    return df


if __name__ == "__main__":
    a = part_a(); b = part_b()
    a.to_csv(os.path.join(HERE, "crypto_atr_results.csv"), index=False); b.to_csv(os.path.join(HERE, "crypto_scalp_results.csv"), index=False)
