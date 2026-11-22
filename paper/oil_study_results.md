# Oil strategy study

Run 2026-11-22 18:35 UTC. Rules fixed before testing. Whole account in each trade; next-bar-open fills; 0.10% cost per side (0.30% stress).

**Luck check** = share of 500 random strategies (same number of trades and holding times, random dates) that the real strategy beat. Around 50% = no better than chance; 95%+ = unlikely to be luck.

## Daily strategies on USO (2006-04-10 to 2026-11-20, 20.6 years)

Buy and hold: -74.4% total, -6.4% a year.

| Strategy | Trades | Win rate | Profit factor | Total | Per year | Worst drop | Per year at stress cost | 1st half / 2nd half per year | Luck check |
|---|---|---|---|---|---|---|---|---|---|
| 50/200-day trend, long only | 19 | 21% | 1.46 | -0.5% | -0.0% | -68% | -0.4% | -2.6% / +2.6% | 70% |
| 50/200-day trend, long and short | 38 | 21% | 1.18 | -46.2% | -3.0% | -81% | -3.7% | -0.6% / -5.3% | 77% |
| Turtle 20/10-day breakout, long only | 85 | 44% | 1.13 | -9.4% | -0.5% | -65% | -2.1% | -5.6% / +4.9% | 64% |
| Turtle 20/10-day breakout, long and short | 164 | 40% | 1.15 | -10.5% | -0.5% | -75% | -3.7% | +0.2% / -1.2% | 80% |
| RSI(2) dip-buy above 200-day avg | 103 | 56% | 1.10 | +7.5% | +0.4% | -37% | -1.6% | +1.5% / -0.8% | 76% |
| RSI(14) oversold (<30, exit >50) | 34 | 65% | 0.51 | -86.1% | -9.1% | -92% | -9.8% | -13.0% / -5.1% | 1% |
| Bollinger band dip-buy | 90 | 70% | 0.75 | -79.7% | -7.4% | -91% | -9.1% | -15.0% / +0.8% | 14% |
| Seasonal: long March-April | 21 | 67% | 1.64 | -15.9% | -0.8% | -76% | -1.3% | +6.9% / -8.0% | 49% |
| Seasonal: short Nov-Dec | 21 | 48% | 1.59 | +40.8% | +1.7% | -40% | +1.3% | +4.2% / -0.8% | 83% |

## Daily strategies on CL=F (2000-08-23 to 2026-11-20, 26.2 years)

Buy and hold: +161.1% total, +3.7% a year.

| Strategy | Trades | Win rate | Profit factor | Total | Per year | Worst drop | Per year at stress cost | 1st half / 2nd half per year | Luck check |
|---|---|---|---|---|---|---|---|---|---|
| 50/200-day trend, long only | 19 | 42% | 2.75 | +186.6% | +4.1% | -42% | +3.8% | +8.9% / -0.5% | 61% |
| 50/200-day trend, long and short | 38 | 37% | 1.51 | +21.8% | +0.8% | -74% | +0.2% | +6.9% / -5.1% | 77% |
| Turtle 20/10-day breakout, long only | 108 | 44% | 1.17 | +8.7% | +0.3% | -55% | -1.3% | -3.9% / +4.8% | 47% |
| Turtle 20/10-day breakout, long and short | 206 | 39% | 0.88 | -98.0% | -13.9% | -98% | -16.9% | -11.3% / -16.4% | 15% |
| RSI(2) dip-buy above 200-day avg | 135 | 60% | 0.91 | -28.2% | -1.3% | -60% | -3.3% | -0.4% / -2.1% | 39% |
| RSI(14) oversold (<30, exit >50) | 39 | 69% | 0.76 | -62.5% | -3.7% | -83% | -4.3% | -1.0% / -6.3% | 9% |
| Bollinger band dip-buy | 106 | 67% | 0.97 | -61.0% | -3.5% | -88% | -5.1% | -2.9% / -4.2% | 18% |
| Seasonal: long March-April | 26 | 69% | 1.98 | +86.3% | +2.4% | -59% | +2.0% | +4.7% / +0.1% | 68% |
| Seasonal: short Nov-Dec | 27 | 44% | 1.40 | +26.0% | +0.9% | -48% | +0.5% | -0.2% / +2.0% | 92% |

## Intraday: opening-range breakout on hourly CL=F (2024-07-02 to 2026-11-20)

First New York hour sets the range; trade a close outside it; stop at the other side; exit by 14:00 New York.

| Variant | Trades | Win rate | Profit factor | Total | Worst drop | Total at stress cost |
|---|---|---|---|---|---|---|
| All days, long and short | 513 | 37% | 0.52 | -73.4% | -74% | -96.6% |
| Long only | 271 | 39% | 0.50 | -52.8% | -54% | -84.1% |
| Skip Wednesdays (EIA report) | 406 | 38% | 0.53 | -63.7% | -65% | -92.9% |
