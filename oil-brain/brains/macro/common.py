"""Shared helpers for the macro brain (no parameters live here)."""
import os, sys
import pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..")))
import engine  # noqa: E402  (unchanged shared engine)

def px(sym):
    f = os.path.join(HERE, "data", sym.replace("^", "") + ".csv")
    if os.path.exists(f):
        return pd.read_csv(f, index_col=0, parse_dates=True)["Close"]
    return engine.load(sym)

def ret(sym):
    return px(sym).pct_change()

def monthly(sig, index):
    """Sample a daily signal at each month's last trading day, hold until next month-end."""
    sig = sig.reindex(index).ffill()
    me = sig.groupby(index.to_period("M")).tail(1)
    return me.reindex(index).ffill()
