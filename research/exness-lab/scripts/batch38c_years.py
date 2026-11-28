import io, contextlib, numpy as np, pandas as pd
with contextlib.redirect_stdout(io.StringIO()): exec(open("lab/batch38b_minlot.py").read().split("res = []")[0])
C = {"A": ["10-day low US500", "BTC NR4", "BTC Williams (T1)", "ETH above 50-day"],
     "B": ["IBS US30", "Connors R3 US500", "BTC NR4", "BTC Williams (T1)", "ETH above 50-day"],
     "C": ["10-day low US500", "BTC NR4", "BTC Williams (T1)", "ETH Williams (T2)"],
     "D": ["IBS US30", "BTC Williams (T1)", "ETH above 50-day"],
     "E": ["Connors R3 US500", "BTC Williams (T1)", "ETH above 50-day"],
     "N1": ["N1 IBS USTEC above 200-day"], "N2": ["N2 IBS USTEC when VIX above 20-day avg"], "N5": ["N5 BTC TRIX vol-sized"]}
for k, l in C.items():
    u = U[l].sum(axis=1); y = u.groupby(u.index.year).sum(); e = u.loc["2024":].cumsum()
    print(k, {yy: int(v) for yy, v in y.items()}, "| 2024+ drop", int((e - e.cummax()).min()), "| 2024+ $/yr", int(u.loc["2024":].sum() / 2.9), "| corr with A", round(u.corr(U[C['A']].sum(axis=1)), 2))
