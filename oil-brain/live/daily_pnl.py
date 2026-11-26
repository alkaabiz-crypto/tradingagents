"""Daily profit report (the user asked on 2026-11-26 to see the profits every day). Read-only on the accounts.

Run after the evening scripts:  python3 oil-brain/live/daily_pnl.py
It reads each paper account's saved value, appends one row per day to live/daily_pnl.csv, and prints a table:
today's profit, profit since the start, and the total. Day tickets (scored in R) are converted to dollars as if
each ticket were $1,000 of notional (stated in the table). Paper money only. Research, not financial advice.
"""
import os, json, datetime as dt
import pandas as pd

OB = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG = os.path.join(OB, "live", "daily_pnl.csv")
TICKET_SIZE = 1000.0


def accounts():
    a = {}
    eq = pd.read_csv(os.path.join(OB, "live", "equity.csv")).drop_duplicates("date", keep="last")
    a["Paper book"] = (10000.0, float(eq.total.iloc[-1]))
    ta = json.load(open(os.path.join(OB, "live", "ta_state.json")))
    a["TradingAgents sleeve"] = (5000.0, float(ta["history"][-1]["long_only"]) if ta.get("history") else 5000.0)
    c = json.load(open(os.path.join(OB, "combo", "combo_state.json")))
    a["Combo trader"] = (8000.0, float(sum(v.get("equity", 2000) for v in c.values())))
    i = json.load(open(os.path.join(OB, "smallwins", "ibs_state.json")))
    a["QQQ IBS sleeves"] = (2000.0 * len(i), float(sum(v.get("equity", 2000) for v in i.values())))
    t = pd.read_csv(os.path.join(OB, "live", "day_tickets.csv"))
    t = t[pd.to_numeric(t.pct, errors="coerce").notna()]
    a[f"Day tickets (${TICKET_SIZE:,.0f} each)"] = (0.0, float((t.pct.astype(float) * TICKET_SIZE).sum()))
    return a


def main():
    today = str(dt.datetime.now(dt.timezone.utc).date())
    acc = accounts()
    row = {"date": today, **{k: round(v[1] - v[0], 2) for k, v in acc.items()}}
    row["TOTAL"] = round(sum(v[1] - v[0] for v in acc.values()), 2)
    log = pd.read_csv(LOG) if os.path.exists(LOG) else pd.DataFrame(columns=row.keys())
    log = pd.concat([log[log.date != today], pd.DataFrame([row])], ignore_index=True)
    log.to_csv(LOG, index=False)
    prev = log.iloc[-2] if len(log) > 1 else None
    print(f"Daily profit report {today} (paper money)")
    print(f"{'Account':30s} {'today':>10s} {'since start':>12s}")
    for k in list(acc) + ["TOTAL"]:
        since = float(row[k]); day = since - (float(prev[k]) if prev is not None and k in prev and pd.notna(prev[k]) else 0.0)
        print(f"{k:30s} {day:>+10.2f} {since:>+12.2f}")


if __name__ == "__main__":
    main()
