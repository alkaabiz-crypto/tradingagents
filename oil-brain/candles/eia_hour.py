"""USO hourly candles around the weekly EIA oil report (pre-registered 2026-11-25, before any run). From the candle
brain's open questions (CANDLES.md section 7): oil first, small frequent trades.
The EIA Weekly Petroleum Status Report comes out Wednesday 10:30 New York (7:30 pm Abu Dhabi); holiday weeks move it.
Data: Yahoo USO 1-hour bars (~2 years); the 10:30 bar (10:30-11:30) holds the release reaction.
Systems (entry at the 11:30 bar's close = after the first hour of reaction, exit at the 16:00 close, same day):
  CONT      trade in the direction of the 10:30-11:30 move (continuation)
  REV       trade against it (fade the first reaction)
  BIG_CONT  CONT only when |that move| > 1 standard deviation of the same hour on non-EIA days
  BIG_REV   REV  only when |that move| > 1 standard deviation
  SURPRISE  the report's crude-stock change minus its 5-year same-week normal change (from data/EIA_weekly.csv):
            a bigger draw than normal -> long, a bigger build -> short (same entry/exit)
Control: the same rules on Tuesdays and Thursdays (no report), to see whether the report hour is special.
Costs 5 bp a side. Luck bar for 5 systems: t >= 2.9. PASS (fixed): EIA-day average > 0 net in BOTH halves of the
sample, > 0 at 2x cost, t >= 2.9, and better than the same rule on control days. Research, not financial advice.
"""
import os
import numpy as np, pandas as pd, yfinance as yf

HERE = os.path.dirname(os.path.abspath(__file__)); OB = os.path.dirname(HERE)
COST = 5e-4


def hourly():
    h = yf.Ticker("USO").history(period="730d", interval="1h")[["Open", "High", "Low", "Close"]].dropna()
    h.index = h.index.tz_convert("America/New_York")
    return h


def surprise():
    e = pd.read_csv(os.path.join(OB, "data/EIA_weekly.csv"), index_col=0, parse_dates=True)["crude_ex_spr"].dropna()
    chg = e.diff(); wk = chg.index.isocalendar().week.values
    norm = pd.Series([chg[(wk == w) & (chg.index < d) & (chg.index >= d - pd.Timedelta(days=5 * 366))].mean()
                      for d, w in zip(chg.index, wk)], index=chg.index)
    s = chg - norm
    s.index = (s.index + pd.Timedelta(days=5)).normalize()  # week ending Friday -> released Wednesday
    return s


def day_rows(h):
    rows = []
    for d, g in h.groupby(h.index.date):
        g = g.sort_index(); t = g.index.strftime("%H:%M")
        if "10:30" not in t or "11:30" not in t or "15:30" not in t:
            continue
        b1030 = g.iloc[list(t).index("10:30")]; b1130 = g.iloc[list(t).index("11:30")]
        first = b1030.Close / b1030.Open - 1
        rest = g.iloc[-1].Close / b1130.Close - 1  # 11:30 bar close (12:30) is a fair entry; use its close
        rows.append(dict(date=pd.Timestamp(d), wd=pd.Timestamp(d).weekday(), first=first, rest=rest))
    return pd.DataFrame(rows)


def main():
    h = hourly(); D = day_rows(h); S = surprise()
    sd = D[D.wd.isin([1, 3])]["first"].std()
    D["sur"] = D.date.map(S)
    out = []
    for label, days in [("EIA (Wednesday)", D[D.wd == 2]), ("control (Tue/Thu)", D[D.wd.isin([1, 3])])]:
        half = days.date.iloc[len(days) // 2] if len(days) else None
        for name in ["CONT", "REV", "BIG_CONT", "BIG_REV", "SURPRISE"]:
            x = days.copy()
            if name.startswith("BIG"):
                x = x[x["first"].abs() > sd]
            if name == "SURPRISE":
                x = x[x.sur.notna() & (x.sur != 0)]; side = np.where(x.sur < 0, 1, -1)  # draw (negative) -> long
            else:
                side = np.sign(x["first"]) * (1 if "CONT" in name else -1)
            r = side * x.rest - 2 * COST
            if len(r) < 5:
                out.append(dict(days=label, system=name, n=len(r))); continue
            t = r.mean() / (r.std(ddof=1) / np.sqrt(len(r)))
            a = r[x.date < half]; b = r[x.date >= half]
            out.append(dict(days=label, system=name, n=len(r), avg_bp=r.mean() * 1e4, t=t, win=(r > 0).mean(),
                            half1_bp=a.mean() * 1e4, half2_bp=b.mean() * 1e4, bp_2x=(r.mean() - 2 * COST) * 1e4))
    df = pd.DataFrame(out); df.to_csv(os.path.join(HERE, "eia_hour_results.csv"), index=False)
    pd.set_option("display.width", 200)
    print(f"USO 1h from {h.index[0].date()} to {h.index[-1].date()}; Wednesdays with data: {int((D.wd == 2).sum())}")
    print(df.round(2).to_string(index=False))
    e = df[df.days.str.startswith("EIA")].set_index("system"); c = df[df.days.str.startswith("control")].set_index("system")
    for s in e.index:
        ok = all(k in e.columns for k in ("avg_bp",)) and e.loc[s, "half1_bp"] > 0 and e.loc[s, "half2_bp"] > 0 and \
            e.loc[s, "bp_2x"] > 0 and e.loc[s, "t"] >= 2.9 and e.loc[s, "avg_bp"] > c.loc[s, "avg_bp"]
        print(f"{s}: {'PASS' if ok else 'fail'}")


if __name__ == "__main__":
    main()
