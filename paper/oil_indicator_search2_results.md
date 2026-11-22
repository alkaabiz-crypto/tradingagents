# Oil indicator search, round 4: one pre-chosen reversal-consensus rule

Run 2026-11-22 19:40 UTC.

## Hourly WTI, New York session (day trading)

TRAIN to 2025-12-09, TEST after.

| Rule | TRAIN Sharpe | TEST Sharpe | TEST total (0.02%) | TEST total (0.05%) | TEST trades | Luck (TEST) | Verdict |
|---|---|---|---|---|---|---|---|
| MAIN: reversal consensus, 2+ agree | 0.09 | 0.41 | +14.9% | +1.8% | 201 | 91% | fail |
| 3+ agree | 0.02 | 0.20 | +5.2% | -4.6% | 164 | 84% | info only |
| 2+ agree, long side only | 0.11 | 0.82 | +23.9% | +17.1% | 94 | 98% | info only |
| 2+ agree, skip Wednesday EIA window | 0.08 | 0.52 | +17.9% | +5.4% | 187 | 96% | info only |

## Daily WTI since 2000 (swing)

TRAIN to 2016-05-26, TEST after.

| Rule | TRAIN Sharpe | TEST Sharpe | TEST total (0.02%) | TEST total (0.05%) | TEST trades | Luck (TEST) | Verdict |
|---|---|---|---|---|---|---|---|
| MAIN: reversal consensus, 2+ agree | 0.10 | 0.06 | -35.4% | -45.9% | 293 | 64% | fail |
| 3+ agree | 0.18 | -0.15 | -59.9% | -64.9% | 220 | 0% | info only |
| 2+ agree, long side only | 0.05 | 0.17 | +7.9% | +0.0% | 127 | 52% | info only |
| 2+ agree, skip Wednesday EIA window | 0.10 | 0.06 | -35.4% | -45.9% | 293 | 64% | info only |
