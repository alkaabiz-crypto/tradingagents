# Insiders brain: SEC Form 4 insider trading in large US stocks

Memory of brain `insiders` (tournament, rules in `../RULES.md`). Engine `../../engine.py` unchanged.
Result: **11 of 15 rules used. 0 PASS, 0 winners, 0 candidates.**

## Data (what is in `data/`)
- SEC DERA "Insider Transactions Data Sets", 83 quarterly zips 2006q1-2026q3, from
  sec.gov/data-research/sec-markets-data/insider-transactions-data-sets (the old /dera/data/form-345
  path redirects there; the zip paths changed in 2026q2). `fetch.py` streamed each zip in memory
  (~14 MB each, about 1.1 GB total transferred, nothing kept on disk), kept only Form 4
  (no 4/A), non-derivative, codes P and S, for the ~800 largest SEC filers -> `data/trades.csv.gz`
  (692k rows, 38 MB for the whole folder).
- Pre-2009 filings list sales lot by lot (many rows per filing); later ones use weighted
  averages. Everything is aggregated to one event per filing, so this does not matter.
- Universe: first 500 issuers in SEC `company_tickers.json` (ordered by current size) that have
  Form 4 P/S rows and Yahoo prices (`fetch_prices.py`, adjusted closes 2005-06..2026-11).
  **Survivorship bias: this is today's large caps.** Measured size of the bias: an equal-weight
  basket of these 500 names minus SPY has post-2014 Sharpe 1.00. Every SPY-hedged rule is
  compared with that basket (gate 2), and with event-shift placebos on the same stocks.
- ~550 purchase filings a year by officers/directors in ~160 of the 500 firms; median size
  $50-200k. Median filing lag 2 days after the trade.

## Method (lib.py)
Signal date = FILING_DATE; entry at the close of the NEXT trading day (filings can land up to
10 pm). Equal weight over names with an active event, short SPY 1:1 (or another hedge, below),
10 bp per side on every leg. Splits: IS 2006-2013 (data start 2006, engine IS_END unchanged),
OOS 2014-2019, HOLDOUT 2020-now. engine.evaluate is fed the book's daily return (pos = 1 when
anything is held, cost_bps 0 because costs are already in the return at stock level). Two
gates replaced because the engine's versions are degenerate for an always-on book:
placebo = each event date shifted by an independent random +/-60..750 trading days (same
stock, same hold), 500 books, p = share with post-2014 Sharpe >= real; 2x cost = 20 bp per side
computed at stock level.
Bug caught: lib first put `oil-brain/` at the FRONT of sys.path, so `from study1 import ...`
ran the shared `oil-brain/study1.py` (it only prints; nothing written). Fixed (append).

## Mechanisms and sources (abstract-level, not re-verified)
- Lakonishok & Lee (2001 RFS): purchases predict returns, sales mostly do not; effect mainly in
  small firms. Jeng, Metrick & Zeckhauser (2003 REStat): purchases earn ~6%/yr abnormal, much
  of it in the first month. Cohen, Malloy & Pomorski (2012 JF): "opportunistic" (non-calendar)
  insiders carry the information, routine ones none. Seyhun (1986): larger trades and top
  executives more informative. Clustered buying by several insiders: practitioner idea, also studied in the literature (source not checked here).

## Rules tried (11 of 15). 0 PASS

| # | rule (all: officer/director buys, entry next close after filing) | IS | OOS | HOLD | post (bench) | t | placebo p (mean) | verdict |
|---|---|---|---|---|---|---|---|---|
| I1 | any buy >= $10k, SPY hedge, hold 21 | 0.65 | -0.38 | -0.25 | -0.28 (1.00) | -1.01 | 0.99 (0.11) | FAIL 6 |
| I2 | any buy >= $10k, SPY hedge, hold 63 | 1.13 | 0.67 | 0.47 | 0.50 (1.00) | 1.79 | 0.096 (0.37) | FAIL 3: best |
| I3 | cluster >= 2 insiders in 30d, hold 63 | 0.87 | 0.25 | -0.06 | 0.06 (1.00) | 0.21 | 0.92 (0.25) | FAIL 6 |
| I4 | opportunistic (CMP 2012) buys, hold 63 | 0.99 | 0.19 | 0.02 | 0.09 (1.00) | 0.32 | 0.94 (0.41) | FAIL 5 |
| I5 | buys >= $100k, hold 63 | 1.13 | 0.34 | 0.45 | 0.40 (1.00) | 1.43 | 0.27 (0.33) | FAIL 3 |
| I6 | CEO/CFO/President/Chair buys, hold 63 | 1.19 | 0.44 | 0.07 | 0.21 (1.00) | 0.75 | 0.39 (0.16) | FAIL 4 |
| I7 | I2 events, hedged with EW universe | 0.27 | -0.28 | -0.12 | -0.17 (0) | -0.63 | 0.014 (-0.58) | FAIL 5 |
| I8 | CONTROL: long after sales cluster >= 3 sellers | 0.82 | 1.18 | 0.78 | 0.88 (1.00) | 3.14 | 1.00 (1.40) | FAIL 2 |
| I9 | I2 events, hedged with control pool (past buyers) | 0.18 | -0.21 | -0.13 | -0.15 (0) | -0.55 | 0.078 (-0.49) | FAIL 6 |
| I10 | I5 events, control-pool hedge | 0.20 | -0.56 | -0.12 | -0.28 (0) | -1.00 | 0.27 (-0.41) | FAIL 6 |
| I11 | any buy, SPY hedge, hold 5 | 0.03 | -1.07 | -0.62 | -0.78 (1.00) | -2.79 | 0.72 (-0.67) | FAIL 6 |

I9-I10 were designed after seeing I7's post-2014 numbers (flagged in study3's docstring);
they could have been candidates at most, and failed anyway.

## Facts measured here
- Event study (study1 diagnostic, excess over SPY, NOT survivorship-adjusted): all buys CAR+63
  IS +5.0% (t 13.6), OOS +0.75% (t 2.9), HOLDOUT +1.8% (t 5.5); CAR+21 OOS -0.18%. The big IS
  number is 2008-2009 (insiders bought the crash in names that are large today) plus survivorship.
- Placebo books (same stocks, random dates) have post Sharpe 0.37 for I2 vs real 0.50: most of
  the SPY-hedged return is "these stocks went up", not "insiders timed it".
- Stocks where insiders buy underperform the rest of today's large caps at ALL times (EW-hedged
  placebo mean -0.58). Real timing beats random timing there (I7 p 0.014), but the book still
  loses money; the timing effect is a smaller loss, not a profit.
- Clusters, opportunistic insiders, top executives and big trades all did WORSE than plain
  buys post-2014 in large caps. The published refinements did not transfer.
- Sales clusters: the same stocks after 3+ insiders sell do worse than at random times
  (I8 placebo mean 1.40 vs real 0.88): consistent with sales carrying some negative information
  (or selling after run-ups), but not tested as a short rule.
- IS-chosen 63-day hold beats 21 and 5 days in every split; short holds lose to costs and
  the 1-day filing lag.

## Idea queue (4 rules left; none looks worth spending)
- Small/mid caps (where LL01/JMZ find the effect) need point-in-time size and delisted prices
  (CRSP); Yahoo cannot supply delisted tickers, so survivorship would be worse there.
- Short side from sales clusters vs a control pool (I8 timing looked informative).
- Entry on the filing day itself using acceptance timestamps (EDGAR full index) before 4 pm.
