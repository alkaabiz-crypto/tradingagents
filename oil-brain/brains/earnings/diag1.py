"""Diagnostics for study 1 (not rules): gross, leg split, sub-period."""
import numpy as np, pandas as pd
from common import prices, events, build, engine
from study1 import classify, trades
cl, ret = prices(); ev = events(ret.index); cev = classify(ev, ret)
for h in (60, 20, 5):
    for leg in (1, -1, 0):
        t = trades(cev, h); t = t if leg == 0 else t[t.sign == leg]
        g, _, _ = build(t, ret, cost_bps=0)
        n, _, _ = build(t, ret, cost_bps=10)
        f = lambda s: [round(engine.sharpe(s.loc[a:b]), 2) for a, b in (("2005-06", "2013"), ("2014", "2019"), ("2020", "2026"))]
        print(h, {1: "long", -1: "short", 0: "L/S"}[leg], "gross", f(g), "net", f(n), "gross ann", round(g.loc["2014":].mean()*252, 4))
