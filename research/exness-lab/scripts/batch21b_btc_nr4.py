"""Batch 21b, pre-registered after Batch 21 found BTC NR4 positive in 2025 and 2026 on hourly bars. Long-history check on
daily bars 2014-now: after an NR4 day, buy-stop at its high / sell-stop at its low, stop at the other side, exit at the
close. If both sides trade in one day, assume the worst (stopped on the first, -range). 3 bp + 2 bp slippage. Also NR7."""
import numpy as np, pandas as pd
d = pd.read_csv("data/BTC-USD.csv", parse_dates=["Date"], index_col="Date").dropna(); c, h, l, o = d.Close, d.High, d.Low, d.Open
def sh(x): return x.mean() / x.std() * np.sqrt(365) if x.std() > 0 else np.nan
for n in (4, 7):
    rg = h - l; nr = (rg <= rg.rolling(n).min()).shift().fillna(False); ph, pl = h.shift(), l.shift()
    up, dn = nr & (h >= ph), nr & (l <= pl); eL = np.maximum(ph, o) * 1.0002; eS = np.minimum(pl, o) * 0.9998
    lr = np.where(l <= pl, pl / eL - 1, c / eL - 1); sr = np.where(h >= ph, eS / ph - 1, eS / c - 1)
    r = pd.Series(np.where(up & dn, -(ph - pl) / ph, np.where(up, lr, np.where(dn, sr, 0.0))), index=c.index) - (up | dn) * 3e-4
    usd = (r * 0.01 * c).loc["2024":]
    print(f"NR{n}: Sharpe 2014-19 {sh(r.loc['2014':'2019']):.2f}, 2020-23 {sh(r.loc['2020':'2023']):.2f}, 2024-now {sh(r.loc['2024':]):.2f}; "
          f"$ per year at 0.01 lot: {usd.groupby(usd.index.year).sum().round(0).to_dict()}; trades/yr {(up|dn).loc['2014':].mean()*365:.0f}")
print("--- NR4 detail")
rg = h - l; nr = (rg <= rg.rolling(4).min()).shift().fillna(False); ph, pl = h.shift(), l.shift()
for bp in (3, 10):
    up, dn = nr & (h >= ph), nr & (l <= pl); eL = np.maximum(ph, o) * 1.0002; eS = np.minimum(pl, o) * 0.9998
    r = pd.Series(np.where(up & dn, -(ph - pl) / ph, np.where(up, c / eL - 1, np.where(dn, eS / c - 1, 0.0))), index=c.index) - (up | dn) * bp / 1e4
    u = (r * 0.01 * c); yr = u.groupby(u.index.year).sum().round(0).to_dict(); e = u.loc["2024":].cumsum()
    print(f"{bp} bp: $/yr {yr}; worst drop since 2024 ${(e - e.cummax()).min():.0f}; worst day ${u.loc['2024':].min():.0f}; long-only 2024-now ${u.where(up & ~dn, 0).loc['2024':].sum():.0f}, short-only ${u.where(dn & ~up, 0).loc['2024':].sum():.0f}; both-side days {(up&dn).loc['2024':].sum()}")
