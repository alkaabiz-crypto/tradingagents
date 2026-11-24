"""Shared helpers for the calendar brain (no tuning here)."""
import os, sys
import numpy as np
import pandas as pd
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)
import engine  # noqa: E402

# Closures that were NOT known in advance: a trader could not have used them as "pre-holiday".
UNSCHEDULED = pd.to_datetime(["2001-09-11", "2001-09-12", "2001-09-13", "2001-09-14",
                              "2012-10-29", "2012-10-30"])


def ohlc(sym):
    return engine.load(sym, col=None)


def daily_ret(sym):
    c = engine.load(sym)
    return c.pct_change().dropna()


def halfday(sym):
    """Half-day return series: stamp d 09:30 = overnight (close d-1 -> open d),
    stamp d 16:00 = intraday (open d -> close d). Two observations per trading day."""
    d = ohlc(sym)
    on = d.Open / d.Close.shift() - 1
    idr = d.Close / d.Open - 1
    on.index = on.index + pd.Timedelta(hours=9, minutes=30)
    idr.index = idr.index + pd.Timedelta(hours=16)
    s = pd.concat([on, idr]).sort_index().dropna()
    return s


def month_day_ranks(idx):
    """For each trading day: rank from month start (1,2,..) and from month end (-1,-2,..)."""
    s = pd.Series(1, index=idx)
    key = [idx.year, idx.month]
    first = s.groupby(key).cumsum()
    last = -(s[::-1].groupby([idx[::-1].year, idx[::-1].month]).cumsum())[::-1]
    return first, last


def pos_from_earn_days(earn):
    """earn: bool Series over trading days = 'I want the close-to-close return OF this day'.
    The position must be set at the previous close, so pos_t = earn_{t+1} (calendar is known)."""
    return earn.astype(float).shift(-1).fillna(0)


def holidays(idx):
    """Weekdays with no trading inside the sample (exchange holidays), minus unscheduled closures."""
    bd = pd.bdate_range(idx[0], idx[-1])
    h = bd.difference(idx).difference(UNSCHEDULED)
    return h


def sharpe_fix_halfday(x):
    """engine.sharpe annualizes with sqrt(252); a half-day series has 504 obs/yr, so the true
    annual Sharpe is engine value * sqrt(2). Reported for information; gates use engine values."""
    return x * np.sqrt(2) if x == x else x
