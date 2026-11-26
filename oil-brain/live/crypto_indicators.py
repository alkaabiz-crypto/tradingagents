"""Can other indicators help the crypto trend day trade? (pre-registered 2026-11-26, before any run; the user asked
"can the bots skills help with this strategy or any other indicator"). The bot's market analyst reads the classic
indicators (SMA/EMA, MACD, RSI, Bollinger, ATR, volume), so they are tested here as fixed rules, free and fast.
Base: BTC+ETH, direction = sign(close - SMA50), stop 0.5 ATR14, vol sizing min(1, 2%/ATR%), entry at the UTC open,
out at the UTC close; costs from costs.py (Exness Standard swap-free: spread + stop slippage).
DIRECTION replacements (7): D1 MACD(12,26,9) line vs signal | D2 position in the 20-day range (above/below its middle)
  | D3 +DI vs -DI (14) | D4 yesterday's Heikin-Ashi colour | D5 EMA20 vs EMA50 | D6 RSI14 above/below 50 | D7 20-day
  rate of change sign.
FILTERS on the base direction (trade only when ...; else flat) (8): F1 ADX14 > 20 | F2 ADX14 > 25 | F3 RSI14 not
  stretched (long only if RSI < 70, short only if > 30) | F4 volume above its 20-day average | F5 Bollinger(20,2)
  width above its 20-day average | F6 MACD agrees | F7 close within 2 ATR of SMA50 | F8 not the day after a > 2 ATR move.
15 variants. "HELPS" (fixed): higher Sharpe AND higher return/worst-drop than the base in BOTH 2014-21 and 2022+.
With 15 tries, one may help by luck; a helper then needs a forward demo check. Research, not financial advice.
    python3 oil-brain/live/crypto_indicators.py
"""
import os, sys
import numpy as np, pandas as pd, talib

HERE = os.path.dirname(os.path.abspath(__file__)); OB = os.path.dirname(HERE)
sys.path.insert(0, HERE); sys.path.insert(0, OB)
import costs
from crypto_trend_opt import stats

COINS = ["BTC-USD", "ETH-USD"]; _b = {}


def bars(sym):
    if sym not in _b:
        import yfinance as yf
        d = yf.Ticker(sym).history(period="max")[["Open", "High", "Low", "Close", "Volume"]].dropna()
        d.index = d.index.tz_localize(None).normalize(); d = d[~d.index.duplicated()]
        _b[sym] = d[(d.index < pd.Timestamp.now().normalize()) & (d.High > d.Low) & (d.Open > 0)]
    return _b[sym]


def positions(d, v):
    o, h, l, c, vol = (d[k].values.astype(float) for k in ("Open", "High", "Low", "Close", "Volume"))
    S = lambda x: pd.Series(x, index=d.index)
    atr = S(talib.ATR(h, l, c, 14)); sma = S(talib.SMA(c, 50)); C = d.Close
    base = np.sign(C - sma)
    macd, sig, _ = talib.MACD(c, 12, 26, 9); macd_dir = S(np.sign(macd - sig))
    if v == "BASE": return base, atr
    if v == "D1 MACD": return macd_dir, atr
    if v == "D2 20d range": return np.sign(C - (d.High.rolling(20).max() + d.Low.rolling(20).min()) / 2), atr
    if v == "D3 DI": return S(np.sign(talib.PLUS_DI(h, l, c, 14) - talib.MINUS_DI(h, l, c, 14))), atr
    if v == "D4 Heikin-Ashi":
        hc = (d.Open + d.High + d.Low + d.Close) / 4; ho = hc.copy(); ho.iloc[0] = (d.Open.iloc[0] + d.Close.iloc[0]) / 2
        for i in range(1, len(ho)): ho.iloc[i] = (ho.iloc[i - 1] + hc.iloc[i - 1]) / 2
        return np.sign(hc - ho), atr
    if v == "D5 EMA20/50": return S(np.sign(talib.EMA(c, 20) - talib.EMA(c, 50))), atr
    if v == "D6 RSI>50": return S(np.sign(talib.RSI(c, 14) - 50)), atr
    if v == "D7 ROC20": return S(np.sign(talib.ROC(c, 20))), atr
    adx, rsi = S(talib.ADX(h, l, c, 14)), S(talib.RSI(c, 14))
    up, mid, lo = talib.BBANDS(c, 20, 2, 2); bw = S((up - lo) / mid)
    keep = {"F1 ADX>20": adx > 20, "F2 ADX>25": adx > 25,
            "F3 RSI not stretched": ((base > 0) & (rsi < 70)) | ((base < 0) & (rsi > 30)),
            "F4 volume up": d.Volume > d.Volume.rolling(20).mean(), "F5 BB width up": bw > bw.rolling(20).mean(),
            "F6 MACD agrees": macd_dir == base, "F7 near SMA50": (C - sma).abs() < 2 * atr,
            "F8 no shock day": (C - C.shift()).abs() < 2 * atr.shift()}[v]
    return base.where(keep, 0.0), atr


def coin(sym, v):
    d = bars(sym); pos, atr = positions(d, v)
    f = pd.DataFrame({"O": d.Open.shift(-1), "H": d.High.shift(-1), "L": d.Low.shift(-1), "C": d.Close.shift(-1),
                      "a": atr, "p": pos, "ok": d.Close.rolling(200).mean().notna()}, index=d.index)
    f = f[f[["O", "H", "L", "C", "a", "p"]].notna().all(axis=1) & f.ok & (f.index >= "2014-01-01")]
    s = np.sign(f.p.values); w = np.minimum(1.0, 0.02 / (f.a / f.O).values)
    st = f.O.values - s * 0.5 * f.a.values
    hit = np.where(s > 0, f.L.values <= st, np.where(s < 0, f.H.values >= st, False))
    g = s * (np.where(hit, st, f.C.values) / f.O.values - 1)
    cost = (s != 0) * (costs.round_trip(sym) + hit * costs.STOP_SLIPPAGE_BP / 1e4)
    return pd.Series(w * (g - cost), index=f.index + pd.Timedelta(days=1))


VARIANTS = ["BASE", "D1 MACD", "D2 20d range", "D3 DI", "D4 Heikin-Ashi", "D5 EMA20/50", "D6 RSI>50", "D7 ROC20",
            "F1 ADX>20", "F2 ADX>25", "F3 RSI not stretched", "F4 volume up", "F5 BB width up", "F6 MACD agrees",
            "F7 near SMA50", "F8 no shock day"]


def main():
    rows = []
    for v in VARIANTS:
        r = pd.concat([coin(s, v) for s in COINS], axis=1).mean(axis=1).dropna()
        for per, m in (("2014-21", r.index < "2022-01-01"), ("2022+", r.index >= "2022-01-01")):
            rows.append(dict(variant=v, period=per, days_in_trade=float((r[m] != 0).mean()), **stats(r[m])))
    df = pd.DataFrame(rows); b = df[df.variant == "BASE"].set_index("period")
    helps = [v for v in VARIANTS[1:] if all(df[(df.variant == v) & (df.period == p)].sharpe.iloc[0] > b.sharpe[p] and
                                            df[(df.variant == v) & (df.period == p)].MAR.iloc[0] > b.MAR[p] for p in b.index)]
    df.to_csv(os.path.join(HERE, "crypto_indicators_results.csv"), index=False)
    pd.set_option("display.width", 200)
    print(df.pivot(index="variant", columns="period", values=["sharpe", "year_pct", "worst_drop"]).reindex(VARIANTS).round(2).to_string())
    print("\nHELPS (better Sharpe and return/drop in both periods):", helps or "none")


if __name__ == "__main__":
    main()
