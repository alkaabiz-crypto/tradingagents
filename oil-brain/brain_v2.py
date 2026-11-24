"""Oil brain v2: one feature engine for US crude (WTI / Exness USOIL), used by the backtest and the live report.

Every feature is aligned to the day it was PUBLICLY KNOWN (no look-ahead):
  prices (Yahoo)     known at that day's close
  EIA weekly         week ends Friday, published the next Wednesday 10:30 ET -> usable from that Wednesday's close
  CFTC positions     as of Tuesday, published Friday 15:30 ET -> usable from the next trading day's close

Components (votes in -1..+1), the sign fixed by economics or the literature BEFORE any backtest:
  trend       sign of the 126-day USO return            + (time-series momentum, Moskowitz et al. 2012)
  curve       USO minus USL 63-day return > 0           + (backwardation = tight market, Gorton et al. 2013)
  stocks      commercial crude vs its 5-year same-week average: below -> +, above -> -   (tightness)
  draws       4-week stock change vs the 5-year same-weeks average change: bigger draw -> +
  cushing     Cushing stocks vs 5-year same-week average: below -> +
  crowding    managed-money net long / open interest, 3-year percentile: >80% -> -, <20% -> + (contrarian)
  dollar      63-day dollar index change > 0 -> - (strong dollar weighs on oil; weaker since 2020)
Composite = average of the available votes, in -1..+1.
"""
import os
import numpy as np, pandas as pd

D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


def _px(name):
    s = pd.read_csv(os.path.join(D, name), index_col=0, parse_dates=True)["Close"]
    s.index = pd.to_datetime(s.index).tz_localize(None).normalize()
    return s[~s.index.duplicated()]


def _seasonal_dev(s, years=5):
    """Value minus the average of the same ISO week over the previous `years` years (only past data)."""
    out = pd.Series(np.nan, index=s.index)
    wk = s.index.isocalendar().week.values
    yr = s.index.year.values
    df = pd.DataFrame({"v": s.values, "wk": wk, "yr": yr}, index=s.index)
    for i, (d, row) in enumerate(df.iterrows()):
        past = df[(df.wk == row.wk) & (df.yr < row.yr) & (df.yr >= row.yr - years)]
        if len(past) >= 3:
            out.iloc[i] = row.v - past.v.mean()
    return out


def _to_daily(weekly, cal, lag_days):
    """Weekly series -> daily calendar, each value usable from date + lag_days (next trading day on/after)."""
    w = weekly.dropna().copy()
    w.index = w.index + pd.Timedelta(days=lag_days)
    return w.reindex(cal.union(w.index)).ffill().reindex(cal)


def features():
    uso, usl, dxy = _px("USO.csv"), _px("USL.csv"), _px("DX-Y.NYB.csv")
    cal = uso.index
    f = pd.DataFrame(index=cal)
    f["uso"] = uso
    f["ret126"] = uso.pct_change(126)
    f["curve63"] = uso.pct_change(63) - usl.reindex(cal).pct_change(63)
    f["dxy63"] = dxy.reindex(cal, method="ffill").pct_change(63)
    eia = pd.read_csv(os.path.join(D, "EIA_weekly.csv"), index_col=0, parse_dates=True)
    stocks_dev = _seasonal_dev(eia["crude_ex_spr"])
    chg4 = eia["crude_ex_spr"].diff(4)
    draws_dev = _seasonal_dev(chg4)
    cush_dev = _seasonal_dev(eia["cushing"])
    f["stocks_dev"] = _to_daily(stocks_dev, cal, 5)          # Friday -> Wednesday release
    f["draws_dev"] = _to_daily(draws_dev, cal, 5)
    f["cushing_dev"] = _to_daily(cush_dev, cal, 5)
    f["refinery_util"] = _to_daily(eia["refinery_util"], cal, 5)
    f["production"] = _to_daily(eia["production"], cal, 5)
    g = pd.read_csv(os.path.join(D, "COT_disagg_WTI.csv"), index_col=0, parse_dates=True)
    mm = (g.m_money_positions_long_all - g.m_money_positions_short_all) / g.open_interest_all
    pct = mm.rolling(156, min_periods=52).apply(lambda x: (x[:-1] < x[-1]).mean(), raw=True)
    f["mm_net"] = _to_daily(mm, cal, 4)                      # Tuesday -> after Friday release
    f["mm_pct3y"] = _to_daily(pct, cal, 4)
    return f


def votes(f):
    v = pd.DataFrame(index=f.index)
    v["trend"] = np.sign(f.ret126)
    v["curve"] = np.sign(f.curve63)
    v["stocks"] = -np.sign(f.stocks_dev)
    v["draws"] = -np.sign(f.draws_dev)
    v["cushing"] = -np.sign(f.cushing_dev)
    v["crowding"] = np.where(f.mm_pct3y > 0.8, -1.0, np.where(f.mm_pct3y < 0.2, 1.0, 0.0))
    v.loc[f.mm_pct3y.isna(), "crowding"] = np.nan
    v["dollar"] = -np.sign(f.dxy63)
    v["composite"] = v[["trend", "curve", "stocks", "draws", "cushing", "crowding", "dollar"]].mean(axis=1)
    return v
