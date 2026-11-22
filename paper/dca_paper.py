#!/usr/bin/env python3
"""Plain DCA paper account (no real money): $100 a month into one fund.

Rule (dca_study.py: plain DCA was as good as every "smart" DCA variant):
  on the first run while the US market is open in each new month, add $100
  of paper money and buy the fund with all of it. Never sells. 0.05% fee.
Default fund: BNO (Brent oil fund; best oil fund in dca_study.py, much less
roll decay than USO).

Usage: python3 paper/dca_paper.py [--fund BNO] [--dry-run]
"""
import argparse
import datetime as dt
import json
import os
import urllib.request
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))
MONTHLY, FEE = 100.0, 0.0005
ET = ZoneInfo("America/New_York")


def price(sym):
    req = urllib.request.Request(f"https://query2.finance.yahoo.com/v8/finance/chart/{sym}?range=5d&interval=1d",
                                 headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return float(json.load(r)["chart"]["result"][0]["meta"]["regularMarketPrice"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fund", default="BNO")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    ledger = os.path.join(HERE, f"ledger_dca_{a.fund.lower()}.json")
    journal = os.path.join(HERE, f"journal_dca_{a.fund.lower()}.md")
    now = dt.datetime.now(dt.timezone.utc)
    et = now.astimezone(ET)
    is_open = et.weekday() < 5 and (9, 30) <= (et.hour, et.minute) < (16, 0)
    month = f"{et:%Y-%m}"
    px = price(a.fund)
    L = json.load(open(ledger)) if os.path.exists(ledger) else \
        {"put_in": 0.0, "shares": 0.0, "last_month": None, "buys": []}
    action = "-"
    if L["last_month"] != month and is_open:
        L["put_in"] += MONTHLY
        L["shares"] += MONTHLY * (1 - FEE) / px
        L["last_month"] = month
        L["buys"].append({"date": now.isoformat(timespec="minutes"), "price": round(px, 2), "usd": MONTHLY})
        action = f"BOUGHT ${MONTHLY:.0f} of {a.fund} at ${px:,.2f}"
    value = L["shares"] * px
    pend = "" if L["last_month"] == month else (" (this month's $100 buy pending, " +
                                                ("market open" if is_open else "waits for the US market open") + ")")
    print(f"Paper trader [Plain DCA into {a.fund}, $100/month] - run {now:%Y-%m-%d %H:%M} UTC")
    print(f"Status: {len(L['buys'])} monthly buys{pend}")
    if action != "-":
        print(f"Actions: {action}")
    pl = value - L["put_in"]
    print(f"{a.fund} ${px:,.2f} | put in ${L['put_in']:,.2f} | worth ${value:,.2f} | P/L {pl:+.2f}")
    if a.dry_run:
        return
    json.dump(L, open(ledger, "w"), indent=2)
    if action != "-":
        new = not os.path.exists(journal)
        with open(journal, "a") as f:
            if new:
                f.write(f"# Plain DCA into {a.fund} journal\n\nPaper money only. $100 every month.\n\n"
                        "| Month | Price | Put in | Worth |\n|---|---|---|---|\n")
            f.write(f"| {month} | {px:,.2f} | {L['put_in']:,.2f} | {value:,.2f} |\n")


if __name__ == "__main__":
    main()
