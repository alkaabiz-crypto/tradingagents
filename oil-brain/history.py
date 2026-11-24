"""History of US crude: every big rally and crash since 2000 (WTI front month, CL=F levels; a 25% zigzag),
what the brain's indicators said at the start, and how each indicator's buckets were followed by USO returns.
Descriptive knowledge for BRAIN/KNOWLEDGE, not a trading test (full sample, no splits)."""
import numpy as np, pandas as pd
import brain_v2 as B
f = B.features(); v = B.votes(f)
cl = B._px("CL_F.csv"); cl = cl[cl > 0]  # skip the negative April 2020 print
# zigzag: a swing ends when price reverses 25% from the extreme
piv = []; mode = None; hi = lo = (cl.index[0], cl.iloc[0])
for d, p in cl.items():
    if p > hi[1]: hi = (d, p)
    if p < lo[1]: lo = (d, p)
    if mode != "down" and p < hi[1] * 0.75 and (mode == "up" or hi[0] > lo[0] or mode is None):
        if mode is None: piv.append(lo if lo[0] < hi[0] else (cl.index[0], cl.iloc[0]))
        piv.append(hi); mode = "down"; lo = (d, p)
    elif mode != "up" and p > lo[1] * 1.25:
        if mode is None: piv.append(hi if hi[0] < lo[0] else (cl.index[0], cl.iloc[0]))
        piv.append(lo); mode = "up"; hi = (d, p)
piv.append(hi if mode == "up" else lo)
rows = []
for (d0, p0), (d1, p1) in zip(piv[:-1], piv[1:]):
    move = p1 / p0 - 1
    if abs(move) < 0.25: continue
    snap = f.reindex([d0], method="ffill").iloc[0] if d0 >= f.index[0] else None
    vv = v.reindex([d0], method="ffill").iloc[0] if d0 >= v.index[0] else None
    rows.append(dict(start=d0.date(), end=d1.date(), days=(d1 - d0).days, from_=round(p0, 1), to=round(p1, 1),
                     move_pct=round(move * 100), kind="RALLY" if move > 0 else "CRASH",
                     stocks_vs_5y_mb=None if snap is None else round(snap.stocks_dev / 1000, 1),
                     backwardation=None if snap is None else bool(snap.curve63 > 0),
                     funds_pct3y=None if snap is None or pd.isna(snap.mm_pct3y) else round(snap.mm_pct3y, 2),
                     brain=None if vv is None else round(vv.composite, 2)))
ep = pd.DataFrame(rows)
pd.set_option("display.width", 220)
print(ep.to_string(index=False))
# conditional forward returns of USO (4 weeks), by indicator bucket, 2008-2026
fwd = f.uso.shift(-20) / f.uso - 1
out = []
for name, col, cuts, labels in [
    ("Stocks vs 5y avg", "stocks_dev", [-1e12, -20000, 0, 20000, 1e12], ["<-20mb", "-20..0", "0..+20", ">+20mb"]),
    ("Curve (USO-USL 63d)", "curve63", [-9, -0.02, 0, 0.02, 9], ["contango deep", "contango", "backw.", "backw. deep"]),
    ("Funds net long, 3y pct", "mm_pct3y", [-1, 0.2, 0.5, 0.8, 2], ["<20%", "20-50%", "50-80%", ">80%"]),
    ("6-month trend", "ret126", [-9, -0.2, 0, 0.2, 9], ["< -20%", "-20..0", "0..+20", "> +20%"]),
    ("Dollar 3m change", "dxy63", [-9, -0.03, 0, 0.03, 9], ["< -3%", "-3..0", "0..+3", "> +3%"]),
    ("Refinery utilization", "refinery_util", [0, 85, 90, 93, 200], ["<85%", "85-90", "90-93", ">93%"])]:
    b = pd.cut(f[col], cuts, labels=labels)
    for lab in labels:
        x = fwd[(b == lab)].dropna()
        if len(x) > 50:
            out.append(dict(indicator=name, bucket=lab, days=len(x), avg_4w_pct=round(x.mean() * 100, 2),
                            up_pct=round((x > 0).mean() * 100), worst_4w=round(x.min() * 100)))
print(pd.DataFrame(out).to_string(index=False))
m = pd.Series(f.uso.pct_change().values, index=f.index)
mon = m.groupby(m.index.month).mean() * 21 * 100
print("USO average return by calendar month (%):", mon.round(1).to_dict())
dow = m.groupby(m.index.day_of_week).mean() * 1e4
print("USO average daily return by weekday (bp, Mon=0):", dow.round(1).to_dict())
ep.to_csv("episodes.csv", index=False); pd.DataFrame(out).to_csv("indicator_buckets.csv", index=False)
