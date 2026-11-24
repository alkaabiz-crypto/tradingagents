"""Study 1 (calendar brain): overnight vs intraday returns. PRE-REGISTERED 2026-11-24, before running.

Literature: Cliff, Cooper & Gulen (2008) "Return differences between trading and non-trading
hours: like night and day": US equity returns accrue overnight (close->open); intraday ~0.
Kelly & Clark (2011) find the same for ETFs. Lou, Polk & Skouras (2019 JFE) "A tug of war":
the market premium is earned overnight, momentum overnight, other anomalies intraday.

Rules (4, fixed, no parameters):
  O1 SPY: long close->open, flat open->close.
  O2 QQQ: same.
  O3 IWM: same.
  O4 USO: same (Kelly & Clark-style ETF test; oil ETF prior is weak).
Method: a half-day return series (overnight at 09:30 stamp, intraday at 16:00 stamp) fed to
engine.evaluate unchanged. Position = 1 at each close stamp, 0 at each open stamp, so the rule
trades twice a day; engine charges cost_bps per unit of turnover = per side.
Costs: 5 bp per side (RULES.md minimum for ETFs; that is 10 bp per round trip per day,
~25% a year). Benchmark: buy-and-hold of the same half-day series.
Caveat fixed in advance: engine's Sharpe uses sqrt(252) on 504 obs/yr, so all Sharpes (rule and
benchmark) are understated by sqrt(2); t-stats are correct. Gates use engine values as-is.
Placebo: circular shifts of the alternating 1/0 pattern; odd shifts become "intraday only".
Diagnostics (not separate rules, no selection on them): gross (0 bp) and 2 bp/side versions.
Prior expectation: gross overnight premium ~3-5 bp/day, costs 10 bp/day -> all FAIL at 5 bp.
"""
import pandas as pd
from common import engine, halfday, sharpe_fix_halfday

rows, diag = [], []
for name, sym in [("O1 SPY overnight", "SPY"), ("O2 QQQ overnight", "QQQ"),
                  ("O3 IWM overnight", "IWM"), ("O4 USO overnight", "USO")]:
    r = halfday(sym)
    pos = pd.Series((r.index.hour == 16).astype(float), index=r.index)
    out = engine.evaluate(name, pos, r, cost_bps=5)
    rows.append(out)
    for c in (0, 2):
        o = engine.evaluate(f"{name} @{c}bp", pos, r, cost_bps=c, n_placebo=100)
        diag.append(o)
print(engine.table(rows))
print("\nDiagnostics (not rules): gross and 2 bp/side")
print(engine.table(diag))
print("\nsqrt(2)-corrected post-2014 Sharpe (5bp):",
      {o["rule"]: round(sharpe_fix_halfday(o["post"]), 2) for o in rows},
      "bench:", {o["rule"]: round(sharpe_fix_halfday(o["bench_post"]), 2) for o in rows})
