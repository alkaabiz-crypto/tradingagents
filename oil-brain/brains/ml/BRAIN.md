# Brain `ml`: can machine learning combine many weak signals into a 1-5 day edge?

## Mechanisms and sources
- Gu, Kelly & Xiu (2020, RFS) "Empirical asset pricing via machine learning": trees and neural nets
  beat linear models on the US stock **cross-section** (thousands of stocks x 60 years); the gains
  come from nonlinear interactions of momentum, liquidity and volatility signals. Monthly horizon.
- López de Prado (2018) "Advances in Financial Machine Learning"; Bailey et al. (2014) "Probability
  of backtest overfitting": overlapping labels leak information unless purged/embargoed; trying
  many models inflates the best result; use controls.
- Our setting is the opposite of GKX: one time series per instrument, ~4,500 daily rows, and the
  single features already failed in the parent lab (BRAIN.md: carry, COT, reversal, momentum).

## Study 1 (`study1.py`, pre-registered 2026-11-24). 0 PASS, 0 candidates of 12 rules (+3 charged for controls = 15)
Setup: 41 features (returns 1/5/21/63d of USO, XLE, SPY, TLT, GLD, DXY; VIX/OVX level and 5d
change; USO-USL 21d carry; CFTC weekly changes with release lag; volume z-scores; weekday).
Targets: sign of next 1d / 5d return. LOGIT (L2, C=0.05) and GBM (HistGB, depth 3, 150 iters,
lr 0.03), hyperparameters fixed a priori. Expanding walk-forward refit every Jan 1 with h-day
purge + 5-day embargo; predictions from 2011 (so "IS" = 2011-13 genuine walk-forward).
Position sign(p-0.5), flat if |p-0.5| < 0.02, 5 bp costs.

| rule | IS 11-13 | OOS | HOLDOUT | post (bench) | t | placebo p | AUC post | verdict |
|---|---|---|---|---|---|---|---|---|
| LOGIT USO h1 | 0.23 | -0.15 | 0.16 | 0.04 (0.05) | 0.13 | 0.16 | 0.528 | FAIL |
| LOGIT USO h5 | -0.20 | 0.14 | 0.34 | 0.26 (0.05) | 0.94 | 0.10 | 0.539 | FAIL (best) |
| LOGIT XLE h1 | 0.69 | -0.98 | -0.75 | -0.80 (0.36) | -2.87 | 0.95 | 0.494 | FAIL |
| LOGIT XLE h5 | 1.11 | -0.32 | -0.65 | -0.52 (0.36) | -1.86 | 0.96 | 0.490 | FAIL |
| LOGIT SPY h1 | 0.55 | 0.35 | 0.43 | 0.39 (0.80) | 1.41 | 0.21 | 0.489 | FAIL |
| LOGIT SPY h5 | 0.93 | 0.37 | 0.09 | 0.18 (0.80) | 0.66 | 0.92 | 0.497 | FAIL |
| GBM USO h1 | -0.32 | -0.14 | 0.11 | 0.01 (0.05) | 0.03 | 0.19 | 0.508 | FAIL |
| GBM USO h5 | 0.04 | -0.04 | -0.15 | -0.11 (0.05) | -0.38 | 0.44 | 0.512 | FAIL |
| GBM XLE h1 | 1.07 | -0.89 | -0.01 | -0.30 (0.36) | -1.09 | 0.56 | 0.497 | FAIL |
| GBM XLE h5 | 0.96 | -0.75 | -0.41 | -0.52 (0.36) | -1.87 | 0.95 | 0.482 | FAIL |
| GBM SPY h1 | 1.06 | -0.27 | 0.39 | 0.15 (0.80) | 0.53 | 0.53 | 0.497 | FAIL |
| GBM SPY h5 | 0.32 | 0.59 | 0.24 | 0.36 (0.80) | 1.28 | 0.43 | 0.504 | FAIL |

**Shuffled-label control** (labels permuted inside each training window, same pipeline): one seed
per config gave post-2014 Sharpe -0.43..+0.48, i.e. the same range as the real models; the
shuffled GBM USO h1 even beat the real one (t 1.45, placebo 0.03). Ten extra seeds x 6 (h5):
max t 3.06, 18% of shuffles reach t >= 2 -- all on SPY, because a model that learns nothing
still learns the base rate (SPY up 61% of 5-day windows) and goes long the market. That is beta,
not skill: shuffled SPY models trail buy-and-hold by ~0.2 Sharpe, as do the real ones.

**Feature importances** (`study1_importance.csv`): no stable winner across configs. LOGIT puts
its largest weights on slow cross-asset returns (XLE_r63, GLD_r21, DXY_r63, TLT_r21, SPY_r63);
GBM leans on levels (VIX, OVX) and the CFTC changes -- regime/level features a tree can use to
memorise periods. Different instruments and horizons pick different features: the signature of
fitting noise.

**Reading:**
1. Out-of-sample AUC 0.48-0.54 everywhere; the real models are indistinguishable from the
   shuffled-label controls. ML found no combination edge that the single signals lacked.
2. XLE is the overfitting textbook case: walk-forward 2011-13 Sharpe ~1.0 for both models, then
   negative in every later period (t -2.9 for LOGIT h1). Early-sample "edges" decay.
3. The only faint positive (LOGIT USO h5, AUC 0.539, Sharpe 0.26, t 0.94) is driven by slow
   cross-asset momentum terms, consistent with the parent lab's crash-driven TSMOM, not new.

## Idea queue
- None worth spending budget on in this brain (15/15 used). If revisited: a cross-section of
  many commodity/sector ETFs (closer to GKX's setting), monthly horizon, ranking target.
