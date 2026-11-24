"""Phase 4 forward paper test of the audited survivors (registered 2026-11-24, before any forward data).

Only days after START count. Positions are decided at the close of day t and earn close t -> t+1.
Rules (fixed, from the audit in oil-brain/audit/AUDIT.md):
  D  IEF long over the last 3 trading days of each month (enter at the close 4 trading days
     before month-end, exit at the month's last close). 2 bp per side assumed (IEF with
     market-on-close orders); also reported at 5 bp. Audit: real before costs (t 5.4), thin after.
  A1 BTC long when its 28-day return > 0, else cash. 10 bp per side. Audit: WEAK, cuts drawdowns.
  A2 BTC long when price > 100-day average, else cash. 10 bp per side.
  B  ETH long when its 28-day return > 0, else cash. 10 bp per side. Audit: WEAK.
Benchmarks: buy and hold of the same instrument over the same forward days.
Pass bar (fixed): at least 3 months forward, net profit > 0 after costs, and for A/B a smaller
max drawdown than buy and hold; D additionally needs at least 9 month-ends with a positive
average. Going live is the user's decision. Research, not financial advice.

Run after the close: python3 oil-brain/forward_tournament.py  (downloads fresh Yahoo data)
"""
import os
import numpy as np, pandas as pd, yfinance as yf

START = "2026-11-25"
HERE = os.path.dirname(os.path.abspath(__file__))


def close(sym):
    s = yf.Ticker(sym).history(period="2y", auto_adjust=True)["Close"]
    s.index = s.index.tz_localize(None).normalize()
    return s[~s.index.duplicated()]


def run(pos, ret, cost_bp):
    turn = pos.diff().abs().fillna(pos.abs())
    pl = pos.shift(1).fillna(0) * ret - turn.shift(1).fillna(0) * cost_bp / 1e4
    return pl[pl.index >= START]


def summary(name, pl, bh):
    eq, beq = (1 + pl).cumprod(), (1 + bh).cumprod()
    dd = (eq / eq.cummax() - 1).min() if len(eq) else 0.0
    bdd = (beq / beq.cummax() - 1).min() if len(beq) else 0.0
    return dict(rule=name, days=len(pl), net_pct=round((eq.iloc[-1] - 1) * 100, 2) if len(eq) else 0.0,
                hold_pct=round((beq.iloc[-1] - 1) * 100, 2) if len(beq) else 0.0,
                max_dd_pct=round(dd * 100, 2), hold_max_dd_pct=round(bdd * 100, 2))


rows, today = [], {}
ief = close("IEF"); r = ief.pct_change()
m = pd.Series(ief.index.to_period("M"), index=ief.index)
left = pd.Series(1, index=ief.index).groupby(m).transform("sum") - pd.Series(1, index=ief.index).groupby(m).cumsum()
# Note: for the current month, "left" counts only days seen so far; the true last-3-day window
# is known from the NYSE calendar, so use business days to month-end for the live position.
# NYSE full-day holidays (2025-2027), so the last-3-trading-days window is right in holiday weeks.
NYSE_HOLIDAYS = pd.to_datetime([
    "2025-01-01", "2025-01-09", "2025-01-20", "2025-02-17", "2025-04-18", "2025-05-26", "2025-06-19",
    "2025-07-04", "2025-09-01", "2025-11-27", "2025-12-25",
    "2026-01-01", "2026-01-19", "2026-02-16", "2026-04-03", "2026-05-25", "2026-06-19", "2026-07-03",
    "2026-09-07", "2026-11-26", "2026-12-25",
    "2027-01-01", "2027-01-18", "2027-02-15", "2027-03-26", "2027-05-31", "2027-06-18", "2027-07-05",
    "2027-09-06", "2027-11-25", "2027-12-24"])
bday = pd.offsets.CustomBusinessDay(holidays=NYSE_HOLIDAYS)
bd_left = pd.Series([len(pd.date_range(d, d + pd.offsets.MonthEnd(0), freq=bday)) - 1 for d in ief.index],
                    index=ief.index)
pos_d = (bd_left.shift(-1).fillna(bd_left.iloc[-1] - 1) < 3).astype(float)
for c in (2, 5):
    rows.append(summary(f"D IEF last 3 days ({c} bp)", run(pos_d, r, c), r[r.index >= START]))
ny_today = pd.Timestamp.now(tz="America/New_York").tz_localize(None).normalize()
left_after_today = len(pd.date_range(ny_today, ny_today + pd.offsets.MonthEnd(0), freq=bday)) - 1
today[f"D IEF month-end (decision at the {ny_today.date()} close)"] = (
    f"BE LONG ({left_after_today} trading days left this month)" if 0 < left_after_today <= 3
    else f"cash ({left_after_today} trading days left this month)")

for sym, tag in (("BTC-USD", "A"), ("ETH-USD", "B")):
    p = close(sym); rr = p.pct_change(); bh = rr[rr.index >= START]
    p28 = (p.pct_change(28) > 0).astype(float)
    rows.append(summary(f"{tag}1 {sym} 28-day trend", run(p28, rr, 10), bh))
    today[f"{tag}1 {sym} 28d"] = "LONG" if p28.iloc[-1] else "cash"
    if tag == "A":
        ma = (p > p.rolling(100).mean()).astype(float)
        rows.append(summary("A2 BTC-USD above 100-day avg", run(ma, rr, 10), bh))
        today["A2 BTC 100d"] = "LONG" if ma.iloc[-1] else "cash"

df = pd.DataFrame(rows).set_index("rule")
df.to_csv(os.path.join(HERE, "forward_tournament.csv"))
print(f"Forward paper test since {START}")
print(df.to_string())
print("\nPositions now:", today)
