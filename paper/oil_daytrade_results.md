# Oil day-trading study

Run 2026-11-22 18:38 UTC on hourly WTI futures (CL=F), 2024-07-02 to 2026-11-20. Rules fixed before testing; all trades closed by about 15:00 New York; whole account per trade.

**Luck check** = share of 500 random strategies (same trades, direction and holding time at random session hours) that the real one beat. 95%+ would suggest a real edge.

| Strategy | Trades | Win rate | Avg per trade (0.02% cost) | Total, low cost 0.02% | Total, main cost 0.10% | Profit factor (low) | Worst drop (low) | 1st half / 2nd half (low) | Luck check (low) |
|---|---|---|---|---|---|---|---|---|---|
| 1. Opening-range breakout | 507 | 45% | -0.090% | -38.5% | -72.7% | 0.79 | -44% | -6.9% / -33.9% | 17% |
| 2. Overnight-range breakout | 401 | 47% | -0.063% | -24.3% | -60.2% | 0.86 | -32% | -5.8% / -19.7% | 37% |
| 3. Overnight breakout, tight nights only | 228 | 44% | -0.081% | -17.9% | -43.1% | 0.81 | -20% | -5.2% / -13.4% | 28% |
| 4. Previous-day high/low breakout | 467 | 38% | -0.024% | -13.3% | -59.0% | 0.94 | -28% | +3.8% / -16.5% | 64% |
| 5. Gap fade | 375 | 47% | -0.035% | -15.8% | -53.8% | 0.94 | -22% | -6.1% / -10.4% | 55% |
| 6. VWAP stretch fade | 318 | 41% | -0.017% | -6.6% | -43.8% | 0.95 | -17% | -11.1% / +5.2% | 64% |
| 7. Hourly RSI(2) pullback with trend | 168 | 54% | -0.036% | -7.0% | -29.0% | 0.92 | -22% | -8.5% / +1.6% | 51% |
| 8. Hourly 9/21 EMA crossover | 156 | 44% | -0.132% | -19.4% | -37.2% | 0.72 | -23% | -6.3% / -14.0% | 18% |
| 9. EIA reaction follow (Wednesdays) | 78 | 40% | -0.080% | -6.4% | -17.4% | 0.81 | -13% | -2.1% / -4.4% | 39% |
| Benchmark: long 9:00-14:00 every day | 596 | 50% | -0.022% | -19.1% | -68.9% | 0.96 | -45% | -32.1% / +19.1% | - |
| Benchmark: long overnight (14:00-9:00) | 595 | 53% | -0.020% | -24.4% | -70.9% | 0.97 | -52% | -12.0% / -14.1% | - |
