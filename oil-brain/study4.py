"""Study 4 (pre-registered 2026-11-24): EIA Wednesday 10:30 ET reaction, hourly USO and CL=F.
Data: Yahoo 1-hour bars, last ~730 days only (too short for IS/OOS/HOLDOUT splits), so the gate is:
t >= 2 on per-event net returns AND the same rule on the other weekdays (no EIA at 10:30)
must be clearly weaker (placebo days). Cost 5 bp a round trip on USO.
Rules (fixed):
 E1 continuation: sign of the 10:30-11:30 bar on Wednesday, hold 11:30 -> 15:30 close of bar (exit 16:00).
 E2 reversal: the opposite of E1.
 E3 pre-report drift: Tuesday close -> Wednesday 10:30, long (does oil rise into the report?).
 E4 big reaction only: E1 when |10:30 bar| > 0.75%.
"""
import numpy as np, pandas as pd, yfinance as yf
COST=5e-4
def bars(sym):
    b=yf.Ticker(sym).history(period="730d",interval="1h"); b.index=b.index.tz_convert("America/New_York"); return b
for sym in ["USO","CL=F"]:
    b=bars(sym)
    b=b[(b.index.strftime("%H:%M")>="09:30")&(b.index.strftime("%H:%M")<="15:30")]
    days=b.groupby(b.index.date)
    rows={wd:{"E1":[],"E2":[],"E4":[]} for wd in range(5)}
    pre=[]
    prev_close=None
    for d,g in days:
        g=g.sort_index(); hh=g.index.strftime("%H:%M")
        wd=pd.Timestamp(d).dayofweek
        if "10:30" in hh and "11:30" in hh:
            rb=g[hh=="10:30"].iloc[0]; react=rb.Close/rb.Open-1
            entry=rb.Close; ext=g.Close.iloc[-1]; hold=ext/entry-1
            rows[wd]["E1"].append(np.sign(react)*hold-COST); rows[wd]["E2"].append(-np.sign(react)*hold-COST)
            if abs(react)>0.0075: rows[wd]["E4"].append(np.sign(react)*hold-COST)
            if wd==2 and prev_close is not None:
                pre.append(g[hh=="10:30"].Open.iloc[0]/prev_close-1-COST)
        prev_close=g.Close.iloc[-1]
    print(f"\n== {sym}: {b.index[0].date()} to {b.index[-1].date()}")
    print(f"{'rule':5}{'weekday':>9}{'n':>5}{'mean bp':>9}{'t':>7}{'win%':>6}")
    for k in ["E1","E2","E4"]:
        for wd,name in enumerate(["Mon","Tue","Wed","Thu","Fri"]):
            x=np.array(rows[wd][k]); 
            if len(x)<5: continue
            print(f"{k:5}{name:>9}{len(x):5}{x.mean()*1e4:9.1f}{x.mean()/x.std()*np.sqrt(len(x)):7.2f}{(x>0).mean()*100:6.0f}")
    x=np.array(pre); print(f"E3   Tue close->Wed 10:30 long: n {len(x)} mean {x.mean()*1e4:.1f} bp t {x.mean()/x.std()*np.sqrt(len(x)):.2f}")
