# Brain tournament: shared rules (fixed 2026-11-24, before any brain runs)

Each brain is an independent researcher with its own folder `brains/<name>/` holding:
- `BRAIN.md`: its memory (mechanisms with sources, every rule tried, every result, idea queue).
- `studyN.py`: one script per study, with a pre-registration docstring written BEFORE running.
- `scorecard.json`: written last, see below.

## The same test for everyone
- Use `oil-brain/engine.py` unchanged: `evaluate(name, pos, ret, cost_bps, bench, start)`.
  IS up to 2013 (choose parameters here or take them from the paper), OOS 2014-2019,
  HOLDOUT 2020-now. Never tune on OOS or HOLDOUT. Positions are known at the close of day t.
- Costs: at least 5 bp per unit of turnover for ETFs; 10 bp for anything less liquid.
- Shared data (read only): `oil-brain/data/*.csv` (Yahoo daily: oil, energy, commodity ETFs,
  SPY, QQQ, IWM, VIX, OVX, dollar index, 10y yield, GLD, TLT; CFTC WTI positions).
  More Yahoo data: save it in your own folder (`brains/<name>/data/`). Do not edit shared files.
- Do NOT run git commands. Do NOT touch other brains' folders.
- Long or short ETFs, futures-free. Paper research only, never place orders.
- Budget: at most 15 rules per brain. Count every rule you run, including failures.

## Winner bar (stricter than the single-brain bar, because many brains = many tries)
A rule wins only if it passes all 6 engine gates AND has post-2014 t >= 3.0
(Harvey, Liu & Zhu 2016). A rule with all 6 gates but t < 3 is a "candidate" for forward testing.

## scorecard.json
{"brain": "<name>", "rules_tried": N, "best_rule": "...", "best": {IS, OOS, HOLDOUT, post, bench_post,
 t_post, placebo_p, cagr_post, trades_per_year, verdict}, "winners": [...], "candidates": [...],
 "one_line": "what this brain learned"}
