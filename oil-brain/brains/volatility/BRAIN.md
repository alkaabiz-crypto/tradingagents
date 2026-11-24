# Brain `volatility`: volatility and fear as signals for US stocks and oil

Memory of this brain. Rules: `../RULES.md`. Engine: `oil-brain/engine.py` unchanged
(IS to 2013, OOS 2014-2019, HOLDOUT 2020-now; 5 bp per unit turnover; placebo = circular shifts).
Extra data (`fetch.py`, Yahoo, 2026-11-24): ^VIX3M (2006-07-), ^VIX9D (2011-), ^VVIX (2007-),
^VIX6M (2008-, unused) in `data/`. Shared VIX, OVX, SPY, QQQ, IWM, USO, TLT, GLD read only.

## Mechanisms and sources (abstract level; paper tables not re-read)
- **Volatility-managed portfolios** (Moreira & Muir 2017 JF): scaling exposure by 1/variance
  raised Sharpe; Cederburg, O'Doherty, Wang & Yan 2020 JFE: mostly fails out of sample /
  in real-time implementable form. The parent lab found plain SPY vol-targeting FAILS; not retried.
- **VIX term structure** (Johnson 2017 JFQA; Simon & Campasano 2014 JD): the slope summarises
  risk premia and predicts VIX-futures returns. Inversion (VIX > VIX3M) is a popular risk-off flag.
  Short-VIX carry failed in the parent lab; not retried.
- **Variance risk premium** (Bollerslev, Tauchen & Zhou 2009 RFS): VIX^2 minus realised variance
  predicts equity returns at 1-6 months. Oil analogue: Trolle & Schwartz 2010 (implied > realised).
- **Vol-of-vol** (Huang, Schlag, Shaliastovich & Thimme 2019 JFQA; Park 2015): VOV risk priced.
- Practical: VIX (and VIX3M/VVIX) close at 16:15 ET, 15 min after SPY. Using the same-day
  VIX close is a small look-ahead, so every rule was also run with the signal lagged a day.

## Results (all pre-registered in the study docstrings; 15 of 15 rules used)

### Study 1 (`study1.py`): VIX term structure as risk-off filter. 0 PASS of 8
| rule | IS | OOS | HOLD | post (bench) | t | placebo p | lag-1 post / p |
|---|---|---|---|---|---|---|---|
| T1 SPY flat if VIX/VIX3M>1 | 0.47 | 0.72 | 0.85 | 0.79 (0.80) | 2.84 | 0.15 | 0.63 / 0.77 |
| T2 QQQ same | 0.83 | 0.86 | 0.71 | 0.75 (0.86) | 2.70 | 0.57 | 0.66 / 0.91 |
| T3 IWM same | 0.52 | 0.28 | 0.46 | 0.39 (0.46) | 1.40 | 0.54 | 0.26 / 0.95 |
| T4 SPY flat if VIX9D/VIX>1 | 0.54 | 0.41 | 0.72 | 0.59 (0.80) | 2.13 | 0.41 | 0.70 / 0.12 |
| T5 TLT long if VIX/VIX3M>1 | 0.35 | -0.96 | -0.11 | -0.35 (0.15) | -1.26 | 0.82 | -0.10 |
| T6 USO flat if VIX/VIX3M>1 | 0.09 | -0.39 | 0.95 | 0.37 (0.05) | 1.33 | 0.00 | 0.39 / 0.00 |
| T7 GLD long if VIX/VIX3M>1 | 0.32 | -0.26 | 0.12 | 0.00 (0.58) | 0.01 | 0.65 | 0.32 |
| T8 SPY 21d after VIX >= 1.5x 63d median | -0.05 | 0.85 | 0.41 | 0.55 (0.80) | 1.98 | 0.20 | 0.68 / 0.13 |

### Study 2 (`study2.py`): variance risk premium, vol-of-vol, oil fear. 0 PASS of 5
| rule | IS | OOS | HOLD | post (bench) | t | placebo p |
|---|---|---|---|---|---|---|
| P1 SPY long if VIX^2-RV21^2>0, month-end | 0.59 | 0.98 | 0.66 | 0.75 (0.80) | 2.70 | 0.39 |
| P2 USO long if OVX^2-RV21^2>0, month-end | 0.46 | -0.39 | 0.05 | -0.11 (0.05) | -0.41 | 0.92 |
| P3 SPY flat if VVIX > 252d p90 | 0.40 | 0.53 | 0.63 | 0.59 (0.80) | 2.10 | 0.91 |
| P4 SPY long if VIX/VIX3M<1 and VRP>0 | 0.54 | 0.75 | 0.82 | 0.79 (0.80) | 2.82 | 0.09 |
| P5 USO flat 21d after OVX >= 1.5x 63d median | 0.15 | -0.33 | 0.48 | 0.11 (0.05) | 0.38 | 0.22 |

### Study 3 (`study3.py`, chosen from IS-only `diag_is.py`): inversion with memory. 0 PASS of 2
IS diagnostic: SPY next-day Sharpe 0.85 in calm days (no inversion in 63d) vs ~0.3 otherwise.
| rule | IS | OOS | HOLD | post (bench) | t | placebo p | post exposure |
|---|---|---|---|---|---|---|---|
| T9 SPY long if no inversion in 63d | 0.38 | 0.37 | 0.56 | 0.48 (0.80) | 1.72 | 0.42 | 37% |
| T10 same, 21d | 0.41 | 0.37 | 0.57 | 0.49 (0.80) | 1.76 | 0.73 | 66% |
T9 halves the post-2014 max drawdown (-18% vs -34%) but also the return; it loses on Sharpe.

## What this brain learned
1. **Fear filters do not beat buy-and-hold SPY on Sharpe.** Every equity filter (T1-T4, P1, P3,
   P4, T9, T10) lands at or below 0.80, and none beats its placebo. Being out during inversions
   avoids crashes but also misses the sharpest rebounds, which start while VIX is still inverted.
2. **The best-looking filters rely on the same-day VIX close.** T1 falls from 0.79 to 0.63 and
   placebo p from 0.15 to 0.77 with one day of lag; same for P4. Part of the "edge" is the
   15-minute VIX look-ahead plus reacting at the exact turn. Any VIX timing result must be lagged.
3. **Oil risk-off (T6) has the strongest timing signal of all** (placebo p 0.00, also lagged)
   but OOS is negative: the 2014-15 oil crash was a supply shock with calm equity VIX, so a
   stock-fear filter missed it. It helps only in demand shocks (2008, 2020). t 1.33.
4. **Variance premia do not time direction.** Oil VRP (P2) is useless for USO direction; equity
   VRP (P1) is just "almost always long" (86% of months) and matches buy-and-hold.
5. Bonds and gold are not reliable havens in VIX inversions after 2013 (T5, T7 negative OOS;
   2022 broke the stock-bond hedge). Note: the engine earns 0 on cash, which penalises long/flat
   rules a little after 2022.

## Idea queue (budget spent; for a future brain)
1. T6-style oil risk-off with a lag, combined with an oil-specific supply signal (curve shape),
   since VIX only catches demand shocks. Would need fresh pre-registration and a new budget.
2. Use VIX inversion for position SIZE in a diversified portfolio (drawdown control), judged on
   max drawdown or Calmar, not Sharpe vs buy-and-hold.
3. Forward-track T1 (lagged) only as a risk dashboard, not as a trading rule.

**Rules tried: 15 of 15. Winners 0. Candidates 0.**
