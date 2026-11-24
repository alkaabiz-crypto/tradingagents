"""Forward test (registered 2026-11-24, before any forward data): follow a big USO day.
Rule: if USO's close-to-close return is beyond +/-2.5 x its prior 20-day sd, take the SAME
direction at that close and hold 5 trading days (close to close). Overlapping signals extend
the hold. 5 bp a round trip. Only events dated after 2026-11-24 count.
Run daily after the close: python3 oil-brain/forward.py  (rewrites forward.csv from data/USO.csv)
Pass bar (fixed): at least 20 events, mean net return > 0 and t >= 2.0.
"""
import os, numpy as np, pandas as pd
from engine import load
START = "2026-11-25"
uso = load("USO"); r = uso.pct_change(); z = r / r.rolling(20).std().shift(1)
rows = []
for d in z.index[(z.index >= START) & (z.abs() > 2.5)]:
    i = uso.index.get_loc(d); side = int(np.sign(z.loc[d]))
    done = i + 5 < len(uso)
    exit_px = uso.iloc[min(i + 5, len(uso) - 1)]
    net = side * (exit_px / uso.loc[d] - 1) - 5e-4
    rows.append(dict(date=d.date(), side="long" if side > 0 else "short", z=round(z.loc[d], 2),
                     entry=round(uso.loc[d], 2), exit=round(exit_px, 2), status="closed" if done else "open",
                     net_bp=round(net * 1e4, 1)))
df = pd.DataFrame(rows, columns=["date", "side", "z", "entry", "exit", "status", "net_bp"])
df.to_csv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "forward.csv"), index=False)
c = df[df.status == "closed"].net_bp
t = c.mean() / c.std() * np.sqrt(len(c)) if len(c) > 2 else float("nan")
print(f"Forward test since {START}: {len(df)} events, {len(c)} closed, mean {c.mean() if len(c) else 0:.1f} bp, t {t:.2f}."
      + (" Last USO z today: %.2f" % z.iloc[-1]))
