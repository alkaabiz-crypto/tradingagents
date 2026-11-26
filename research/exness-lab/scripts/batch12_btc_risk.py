"""Batch 12, pre-registered 2026-11-26 before running.
A) New trial: Williams SHORT side on weekdays only when 12-month momentum is negative (sell-stop at open - 0.5 x prior
   range, out at the close), and combined with rule 2 (long when momentum positive) = an always-armed version. 3 bp.
B) Risk at the real $228 balance: resample trade-day returns (% of exposure) from 2020-now in 20-day blocks, scale to
   today's 0.01 lot exposure ($584), 252 weekdays ahead, 5000 paths, seed 11. Report median $ after 1 year, chance of
   ending below the start, of ever being down $114 (half) and $200.
"""
import sys, numpy as np, pandas as pd
d = pd.read_csv(f"{sys.argv[1]}/BTC-USD.csv", parse_dates=["Date"], index_col="Date").dropna()
c, h, l, o = d.Close, d.High, d.Low, d.Open; cost = 3e-4; rng = np.random.default_rng(11)
def sh(x): x = x.dropna(); return x.mean() / x.std() * np.sqrt(365) if x.std() > 0 else np.nan
per = lambda x: " / ".join(f"{sh(x.loc[a:b]):.2f}" for a, b in (("2014", "2019"), ("2020", "2023"), ("2024", "2026")))
m = pd.Series(c.index.to_period("M"), index=c.index); me = m != m.shift(-1); wd = c.index.dayofweek < 5
mo = pd.Series(np.where(me, np.sign(c / c.shift(365) - 1), np.nan), index=c.index).ffill().fillna(0).shift().fillna(0)
R = (h - l).shift(); up_t, dn_t = o + 0.5 * R, o - 0.5 * R
lr = c / np.maximum(up_t, o) * (1 - 2e-4) - 1 - cost; sr = np.minimum(dn_t, o) / c * (1 - 2e-4) - 1 - cost
L1 = pd.Series(np.where(wd & (h >= up_t), lr, 0.0), index=c.index).fillna(0)
L2 = L1.where(mo > 0, 0); S = pd.Series(np.where(wd & (mo < 0) & (l <= dn_t), sr, 0.0), index=c.index).fillna(0)
print("## A) Sharpe 2014-19 / 2020-23 / 2024-now")
print(f"- short only, momentum negative: {per(S)}; post-2014 {sh(S.loc['2014':]):.2f}; 2024-now $ at 0.01 lot ~ {(S.loc['2024':] * 0.01 * c.loc['2024':]).sum():.0f}")
both = L2 + S; print(f"- long when momentum up + short when down: {per(both)}; post-2014 {sh(both.loc['2014':]):.2f}")
print("\n## B) one year ahead at $228, 0.01 lot ($584 exposure), resampled from 2020-now")
for START in ("2020", "2025"):
  print("from", START)
  for nm, x in (("1 Williams weekdays", L1), ("2 Williams + 12m momentum", L2)):
      x = x.loc[START:][wd[c.index >= START]].values * 584; n = len(x); fin, h114, h200 = [], 0, 0
      for _ in range(5000):
          idx = np.concatenate([np.arange(s, s + 20) % n for s in rng.integers(0, n, 252 // 20 + 1)])[:252]
          e = np.cumsum(x[idx]); dd = (e - np.maximum.accumulate(np.maximum(e, 0))).min()
          fin.append(e[-1]); h114 += e.min() <= -114; h200 += e.min() <= -200
      fin = np.array(fin)
      print(f"- {nm}: median +${np.median(fin):.0f}, 10th pct ${np.percentile(fin,10):.0f}, 90th pct ${np.percentile(fin,90):.0f}; "
            f"ends below start {np.mean(fin < 0):.0%}; ever down $114: {h114/5000:.0%}; ever down $200: {h200/5000:.0%}")
