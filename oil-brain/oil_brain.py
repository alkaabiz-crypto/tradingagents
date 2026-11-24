"""Ask the oil brain what the US crude market looks like right now.

    python3 oil-brain/oil_brain.py now        # refresh data, print the full market reading
    python3 oil-brain/oil_brain.py now --no-refresh

It prints every indicator with its historical meaning (KNOWLEDGE.md), the 7 votes, the composite, the
turning-point warnings from the history study, and the upcoming calendar. It never places orders.
The brain failed as a stand-alone signal after 2020 (study 12), so it reports a reading, not a trade.
"""
import subprocess, sys, os, datetime as dt
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import brain_v2 as B


def refresh():
    for script in ("fetch.py", "fetch_eia.py", "fetch_cot.py"):
        subprocess.run([sys.executable, os.path.join(HERE, script)], capture_output=True, timeout=600)


def now():
    if "--no-refresh" not in sys.argv:
        refresh()
    f = B.features(); v = B.votes(f)
    last = f.dropna(subset=["uso"]).iloc[-1]; vv = v.iloc[-1]; d = f.index[-1].date()
    wti = B._px("CL_F.csv")
    print(f"OIL BRAIN v2 reading, data to {d} (WTI front month ${wti.iloc[-1]:.2f})")
    print("-" * 72)
    def line(name, val, vote, note):
        arrow = {1: "bullish", -1: "bearish", 0: "neutral"}.get(int(vote) if not pd.isna(vote) else 0, "n/a")
        print(f"{name:34} {val:>16}  {arrow:8}  {note}")
    line("6-month trend (USO)", f"{last.ret126:+.1%}", vv.trend, "trend > +20%: next 4w avg +2.0%; < -20%: -1.0%")
    line("Curve (USO-USL 63d)", f"{last.curve63:+.1%}", vv.curve, "+ = backwardation (tight); 10/19 crashes started there")
    line("Crude stocks vs 5y same week", f"{last.stocks_dev/1000:+.1f}m bbl", vv.stocks, "below normal = tight")
    line("4-week change vs normal", f"{last.draws_dev/1000:+.1f}m bbl", vv.draws, "worked to 2019, not since 2020")
    line("Cushing vs 5y same week", f"{last.cushing_dev/1000:+.1f}m bbl", vv.cushing, "the WTI delivery hub")
    line("Funds net long, 3y percentile", f"{last.mm_pct3y:.0%}", vv.crowding, "11/19 rallies began below 25%; 0 above 70%")
    line("Dollar index 3m change", f"{last.dxy63:+.1%}", vv.dollar, "> +3%: next 4w avg -2.7%")
    print(f"{'Refinery utilization':34} {last.refinery_util:>15.1f}%            <85% has been followed by +1.3%")
    print(f"{'US crude production':34} {last.production/1000:>11.2f}m b/d")
    print("-" * 72)
    c = vv.composite
    view = "LEAN LONG" if c >= 0.25 else "LEAN SHORT" if c <= -0.25 else "NO EDGE (mixed)"
    print(f"Composite {c:+.2f} of +/-1  ->  {view}")
    warn = []
    if last.mm_pct3y < 0.25: warn.append("Funds have given up on oil (bottom quarter of 3 years): the setup most rallies started from.")
    if last.mm_pct3y > 0.7: warn.append("Funds are crowded long: 7 of 19 crashes started from here.")
    if last.curve63 > 0 and last.mm_pct3y > 0.7: warn.append("Tight curve plus crowded longs: the classic top setup.")
    if last.dxy63 > 0.03: warn.append("Dollar up >3% in 3 months: historically the weakest oil backdrop.")
    for w in warn: print("WARNING: " + w)
    today = dt.date.today()
    nxt = {"Tue 16:30 API": 1, "Wed 10:30 EIA": 2, "Fri 15:30 CFTC": 4}
    cal = []
    for k, wd in nxt.items():
        days = (wd - today.weekday()) % 7
        cal.append(f"{k} ({(today + dt.timedelta(days=days)).isoformat()})")
    print("Next: " + ", ".join(cal))
    print("Backtest: the brain worked 2014-2019 and failed since 2020 (study 12). A reading, not a trade signal.")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "now":
        now()
    else:
        print(__doc__)
