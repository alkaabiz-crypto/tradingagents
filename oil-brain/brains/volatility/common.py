import os, sys
import pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..")))
from engine import load, evaluate, table  # noqa

def vload(sym):
    return pd.read_csv(os.path.join(HERE, "data", sym + ".csv"), index_col=0, parse_dates=True)["Close"]

def lagcheck(name, pos, ret, **kw):
    """Same rule with the signal used one day later (guards against VIX's 16:15 close)."""
    r = evaluate(name + " [lag1]", pos.shift(1), ret, n_placebo=100, **kw)
    return r
