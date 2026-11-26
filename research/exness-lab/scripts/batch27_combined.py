"""Batch 27 (no new rules): combined risk of the two survivors and the daily signal export.
USTEC overnight: hold close->next open above the 200-day, 0.05 lot, 1.4 bp (QQQ x 41 proxy).
BTC NR4: rule from Batch 21b, 0.01 lot, 3 bp + 2 bp slip, worst case on both-side days.
Dollars: (a) real fixed-lot $ at the prices of the day; (b) scaled to today's exposure (% return x $1,300 USTEC, x $584 BTC)
so 2000-2023 compare fairly. Calendar-day join (BTC trades weekends; USTEC P&L booked on the open day)."""
import numpy as np, pandas as pd, sys
q = pd.read_csv("data/QQQ.csv", parse_dates=["Date"], index_col="Date").dropna(); b = pd.read_csv("data/BTC-USD.csv", parse_dates=["Date"], index_col="Date").dropna()
on = (q.Close > q.Close.rolling(200).mean()).shift().fillna(False)
u_pct = ((q.Open / q.Close.shift() - 1) - 1.4e-4).where(on, 0).fillna(0)
u_usd = (0.05 * 41 * (q.Open - q.Close.shift()) - 0.05 * 1.4e-4 * 41 * q.Close.shift()).where(on, 0).fillna(0)
c, h, l, o = b.Close, b.High, b.Low, b.Open; rg = h - l; nr4 = (rg <= rg.rolling(4).min()).shift().fillna(False); ph, pl = h.shift(), l.shift()
up, dn = nr4 & (h >= ph), nr4 & (l <= pl); eL, eS = np.maximum(ph, o) * 1.0002, np.minimum(pl, o) * 0.9998
b_pct = pd.Series(np.where(up & dn, np.minimum(pl / eL - 1, eS / ph - 1), np.where(up, c / eL - 1, np.where(dn, eS / c - 1, 0.0))), index=c.index).fillna(0) - (up | dn) * 3e-4
b_usd = b_pct * 0.01 * np.where(up, eL, np.where(dn, eS, c))
side = pd.Series(np.where(up & dn, "both", np.where(up, "long", np.where(dn, "short", np.where(nr4, "setup, no fill", "")))), index=c.index)
idx = q.index.union(b.index)
J = pd.DataFrame({"ustec_signal": on.reindex(idx).fillna(False).map({True: "hold overnight", False: ""}), "ustec_pnl_usd": u_usd.reindex(idx).fillna(0),
                  "ustec_pnl_scaled": (u_pct * 1300).reindex(idx).fillna(0), "btc_nr4_setup": nr4.reindex(idx).fillna(False), "btc_buy_stop": ph.where(nr4).reindex(idx),
                  "btc_sell_stop": pl.where(nr4).reindex(idx), "btc_filled": side.reindex(idx).fillna(""), "btc_pnl_usd": pd.Series(b_usd, index=c.index).reindex(idx).fillna(0),
                  "btc_pnl_scaled": (b_pct * 584).reindex(idx).fillna(0)})
J.index.name = "date"; J.round(2).to_csv(sys.argv[1])
def dd(x): e = x.cumsum(); return (e - e.cummax()).min()
for nm, a, bb, start in (("real $, 2024-now", J.ustec_pnl_usd, J.btc_pnl_usd, "2024"), ("scaled to today, 2014-2023", J.ustec_pnl_scaled, J.btc_pnl_scaled, "2014"), ("scaled, 2024-now", J.ustec_pnl_scaled, J.btc_pnl_scaled, "2024")):
    A, B = a.loc[start:], bb.loc[start:]
    if "2014" in start: A, B = A.loc[:"2023"], B.loc[:"2023"]
    both = (A != 0) & (B != 0)
    print(f"{nm}: USTEC ${A.sum():+.0f} / drop ${dd(A):.0f}; BTC ${B.sum():+.0f} / drop ${dd(B):.0f}; combined ${(A+B).sum():+.0f} / drop ${dd(A+B):.0f}; "
          f"worst day ${(A+B).min():.0f}; days both open {both.mean():.0%}; corr on shared days {np.corrcoef(A[both], B[both])[0,1]:.2f}")
m = (J.ustec_pnl_scaled + J.btc_pnl_scaled).loc["2014":]; mm = m.groupby(m.index.to_period("M")).sum()
print(f"worst calendar month combined (scaled) ${mm.min():.0f} ({mm.idxmin()}); worst rolling 60-day ${m.rolling(60).sum().min():.0f}")
for yr in range(2014, 2027):
    A, B = J.ustec_pnl_scaled.loc[str(yr)], J.btc_pnl_scaled.loc[str(yr)]; print(yr, f"USTEC {A.sum():+.0f} BTC {B.sum():+.0f} both {(A+B).sum():+.0f} drop {dd(A+B):.0f}")
