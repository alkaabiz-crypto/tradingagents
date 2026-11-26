"""Cost check for day tickets v2 + v3 (2026-11-26). The user trades an Exness STANDARD, SWAP-FREE account:
no commission, the cost is the spread only, and a same-day trade pays no swap anyway. v2/v3 charged 4-20 bp a round
trip. This re-scores all 1,000 versions (v2: 200 on the 17 ticket markets, v3: 800 on fast movers) at a round-trip
cost of 0 (no cost at all), 2, 5 and 10 bp, with the same checks (both halves > 0, t >= the Sidak 1% bar for the count).
If nothing clears even at 0 cost, the spread is not what is losing; direction is. Research, not financial advice.
    python3 oil-brain/live/day_ticket_costs.py
"""
import os, sys
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from day_ticket_backrun import ALL17
from day_ticket_v2 import gross, daily, sidak_t, KS, MS, DIRS
from day_ticket_v3 import panel, GROUPS


def series(P):
    O, H, L, C, a = (P[c].values for c in "OHLCa"); out = []
    for k in KS:
        for m in MS:
            gl, gs = gross(O, H, L, C, a, np.ones(len(P)), k, m), gross(O, H, L, C, a, -np.ones(len(P)), k, m)
            for d in DIRS:
                s = P["s_" + d].values; on = s != 0
                out.append(((d, k or "none", m or "none"), daily(P.index[on], np.where(s > 0, gl, gs)[on])))
    return out


def main():
    sets = {"v2 ticket markets": panel(ALL17, np.random.default_rng(61))}
    sets.update({f"v3 {g}": panel(s, np.random.default_rng(71)) for g, (s, _) in GROUPS.items()})
    bar = sidak_t(1000); rows = []
    for name, P in sets.items():
        for (d, k, m), g in series(P):
            mid = g.index[len(g) // 2]; sd = g.std(ddof=1) / np.sqrt(len(g))
            for c in (0, 2, 5, 10):
                n = g - c / 1e4
                rows.append(dict(set=name, direction=d, stop=k, target=m, cost_bp=c, bp=n.mean() * 1e4, t=n.mean() / sd,
                                 both=n[n.index < mid].mean() > 0 and n[n.index >= mid].mean() > 0))
    df = pd.DataFrame(rows); df["clears"] = df.both & (df.t >= bar)
    df.to_csv(os.path.join(HERE, "day_ticket_costs_results.csv"), index=False)
    pd.set_option("display.width", 200)
    print(f"1,000 versions, luck bar t >= {bar:.2f}. Versions positive in both halves / clearing the bar, by round-trip cost:")
    print(df.groupby(["set", "cost_bp"]).agg(positive_both=("both", "sum"), clear_bar=("clears", "sum"), best_bp=("bp", "max"), best_t=("t", "max")).round(2).to_string())
    print("\nBest 8 versions at ZERO cost:")
    print(df[df.cost_bp == 0].sort_values("t", ascending=False).head(8).round(2).to_string(index=False))


if __name__ == "__main__":
    main()
