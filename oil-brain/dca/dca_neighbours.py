"""Neighbour check for the one oil-DCA survivor (pre-registered 2026-11-25, before running).
Survivor in dca_study.py: USO, buy the piled-up weekly cash only when RSI(14) < 35, take profit when the holding
is up 50% on its cost (post-2014 multiple 2.35 vs placebo median 1.54, p = 0.01 on 200 runs).
Check: RSI threshold in {25, 30, 35, 40, 45} x take-profit in {30%, 40%, 50%, 60%, 75%} on USO and BNO,
each scored post-2014 against plain DCA and a 1000-run placebo. A real effect should hold on most neighbours
(fixed bar: >= 70% of the 25 USO neighbours beat plain DCA post-2014 AND their median placebo p <= 0.05).
Research, not financial advice.
"""
import os, sys
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(HERE))
import dca_study as S
import brain_v2 as B

A, Z = "2014-01-01", "2026-12-31"


def run_tp(c, entry, tp, start, end, override=None):
    """dca_study.run with a variable take-profit (same mechanics as X2)."""
    s = c.loc[start:end]
    wk = s.index.to_series().dt.isocalendar()
    weekly = ~pd.Series(list(zip(wk.year, wk.week)), index=s.index).duplicated()
    ent = override.reindex(s.index).fillna(False) if override is not None else entry.reindex(s.index)
    cash = units = added = basis = 0.0
    for d, p in s.items():
        if weekly[d]:
            cash += S.WEEKLY; added += S.WEEKLY
            if ent[d] and cash > 0:
                units += cash * (1 - S.COST) / p; basis += cash; cash = 0.0
        if units > 0 and units * p >= (1 + tp) * basis:
            cash += units * p * (1 - S.COST); units = basis = 0.0
    return (cash + units * s.iloc[-1]) / added


def main():
    rows = []
    for sym in ["USO", "BNO"]:
        c = S.px(sym); r14 = S.rsi(c)
        plain = S.run(c, pd.Series(True, index=c.index), "X0", {}, A, Z)[0]
        s = c.loc[A:Z]; wk = s.index.to_series().dt.isocalendar()
        wdays = s.index[~pd.Series(list(zip(wk.year, wk.week)), index=s.index).duplicated().values]
        for th in [25, 30, 35, 40, 45]:
            ent = (r14 < th)
            share = float(ent.reindex(wdays).mean())
            for tp in [0.30, 0.40, 0.50, 0.60, 0.75]:
                real = run_tp(c, ent, tp, A, Z)
                rng = np.random.default_rng(1); nb = int(np.ceil(len(wdays) / 4)); pl = []
                for _ in range(1000):
                    fl = pd.Series(np.repeat(rng.random(nb) < share, 4)[:len(wdays)], index=wdays)
                    pl.append(run_tp(c, None, tp, A, Z, override=fl))
                pl = np.array(pl)
                rows.append(dict(sym=sym, rsi_below=th, take_profit=tp, multiple=round(real, 3), plain=round(plain, 3),
                                 beats_plain=real > plain, placebo_med=round(float(np.median(pl)), 3),
                                 p=round(float((pl >= real).mean()), 3)))
    df = pd.DataFrame(rows); df.to_csv(os.path.join(HERE, "dca_neighbours.csv"), index=False)
    pd.set_option("display.width", 200)
    print(df.to_string(index=False))
    u = df[df.sym == "USO"]
    print(f"\nUSO neighbours beating plain DCA: {u.beats_plain.mean():.0%}; median placebo p {u.p.median():.3f}"
          f" -> {'HOLDS' if u.beats_plain.mean() >= 0.7 and u.p.median() <= 0.05 else 'DOES NOT HOLD'}")


if __name__ == "__main__":
    main()
