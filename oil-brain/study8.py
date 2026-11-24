"""Study 8 (pre-registered 2026-11-24): CFTC positioning in WTI (Kang, Rouwenhorst & Tang 2020 JF;
De Roon, Nijman & Veld 2000; Maréchal 2023). Positions are as of Tuesday, released Friday 15:30 ET;
to be safe a signal is used from the close of the next trading day after the Friday release
(usually Monday), held until the next signal. Traded: USO, 5 bp per turnover. Gates: engine.py.
K1 liquidity premium (the robust part per Maréchal 2023): weekly change in commercials' net
   position / open interest (legacy). Hedgers bought (change > 0) -> long USO; sold -> short.
K2 same with producer/merchant net (disaggregated, from 2006).
K3 fade managed money: weekly change in managed-money net / OI > 0 -> short USO; < 0 -> long.
K4 K1 with a 4-week change (smoother).
K5 insurance premium (expected weak): commercials' net short / OI above its 156-week median -> long, else flat.
"""
import numpy as np, pandas as pd
from engine import load, evaluate, table, D
import os
uso = load("USO"); r = uso.pct_change()
L = pd.read_csv(os.path.join(D, "COT_legacy_WTI.csv"), index_col=0, parse_dates=True)
G = pd.read_csv(os.path.join(D, "COT_disagg_WTI.csv"), index_col=0, parse_dates=True)
def usable(sig):
    # Tuesday report date -> Friday release -> first trading day after that Friday.
    out = pd.Series(np.nan, index=uso.index)
    for d, v in sig.dropna().items():
        rel = d + pd.Timedelta(days=3)
        nxt = uso.index[uso.index > rel]
        if len(nxt): out[nxt[0]] = v
    return out.ffill()
comm = (L.comm_positions_long_all - L.comm_positions_short_all) / L.open_interest_all
pm = (G.prod_merc_positions_long - G.prod_merc_positions_short) / G.open_interest_all
mm = (G.m_money_positions_long_all - G.m_money_positions_short_all) / G.open_interest_all
rows = [
  evaluate("K1 hedgers bought last week -> long (legacy)", usable(np.sign(comm.diff())), r, start="2006-06-01"),
  evaluate("K2 producers bought last week -> long", usable(np.sign(pm.diff())), r, start="2006-08-01"),
  evaluate("K3 fade managed-money weekly change", usable(-np.sign(mm.diff())), r, start="2006-08-01"),
  evaluate("K4 hedgers 4-week change -> sign", usable(np.sign(comm.diff(4))), r, start="2006-08-01"),
  evaluate("K5 hedging pressure high -> long", usable(((-comm) > (-comm).rolling(156).median()).astype(float)), r, start="2006-06-01"),
]
print(table(rows))
print("\nLatest (report 2026-11-17): commercial net/OI %.3f, weekly change %+.4f; managed-money net/OI %.3f, change %+.4f"
      % (comm.iloc[-1], comm.diff().iloc[-1], mm.iloc[-1], mm.diff().iloc[-1]))
