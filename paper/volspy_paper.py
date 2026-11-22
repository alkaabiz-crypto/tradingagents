#!/usr/bin/env python3
"""Volatility-managed S&P 500 paper account (no real money).

Rule (Moreira & Muir 2017; passed anomaly_study2.py test 9):
  Once a month (first run while the US market is open in a new month), hold
  min(1, 15% / last 21 trading days' yearly volatility) of the account in SPY
  and the rest in cash. Trades only if the target differs by more than 5%.
  No leverage. 0.10% fee per trade.
Backtest 2000-2026: +7.8% a year, worst drop -40%, Sharpe 0.60 vs holding SPY
+7.8%, -55%, 0.49 (it passed, but only narrowly in the second half).

Usage: python3 paper/volspy_paper.py [--dry-run]
"""
import argparse
import datetime as dt
import json
import math
import os
import statistics as st
import urllib.request
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))
FILES = {"SPY": ("ledger_volspy.json", "journal_volspy.md", "S&P 500"),
         # QQQ: same rule, never tuned on QQQ; passed anomaly_study3.py test 16
         "QQQ": ("ledger_volqqq.json", "journal_volqqq.md", "Nasdaq 100")}
START, FEE, TARGET_VOL, MIN_TRADE = 300.0, 0.001, 0.15, 0.05


def history(sym):
    now = int(dt.datetime.now().timestamp())
    req = urllib.request.Request(
        f"https://query2.finance.yahoo.com/v8/finance/chart/{sym}?period1={now - 90 * 86400}&period2={now}&interval=1d",
        headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        j = json.load(r)["chart"]["result"][0]
    et_today = dt.datetime.now(ZoneInfo("America/New_York")).date()
    rows = [(dt.datetime.fromtimestamp(t, ZoneInfo("America/New_York")).date(), c)
            for t, c in zip(j["timestamp"], j["indicators"]["quote"][0]["close"]) if c]
    done = [c for d, c in rows if d < et_today]          # completed sessions only
    return done, float(j["meta"]["regularMarketPrice"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--asset", choices=FILES, default="SPY")
    a = ap.parse_args()
    sym = a.asset
    ledger, journal, label = FILES[sym]
    LEDGER, JOURNAL = os.path.join(HERE, ledger), os.path.join(HERE, journal)
    now = dt.datetime.now(dt.timezone.utc)
    et = now.astimezone(ZoneInfo("America/New_York"))
    is_open = et.weekday() < 5 and (9, 30) <= (et.hour, et.minute) < (16, 0)
    month = f"{et:%Y-%m}"
    closes, price = history(sym)
    r = [closes[i] / closes[i - 1] - 1 for i in range(len(closes) - 21, len(closes))]
    vol = st.pstdev(r) * math.sqrt(252)
    target = min(1.0, TARGET_VOL / vol) if vol > 0 else 1.0

    L = json.load(open(LEDGER)) if os.path.exists(LEDGER) else \
        {"start_cash": START, "cash": START, "shares": 0.0, "last_month": None, "trades": []}
    equity = L["cash"] + L["shares"] * price
    weight = L["shares"] * price / equity
    action, rebalanced = "-", False
    if L["last_month"] != month and is_open:
        diff = target - weight
        if abs(diff) > MIN_TRADE:
            usd = diff * equity
            fee = abs(usd) * FEE
            L["cash"] -= usd + fee
            L["shares"] += usd / price
            action = f"{'BOUGHT' if usd > 0 else 'SOLD'} ${abs(usd):.2f} of {sym} at ${price:,.2f}"
            L["trades"].append({"date": now.isoformat(timespec="minutes"), "price": round(price, 2),
                                "usd": round(usd, 2), "fee": round(fee, 2), "target": round(target, 3)})
        L["last_month"], rebalanced = month, True
    equity = L["cash"] + L["shares"] * price
    weight = L["shares"] * price / equity
    state = "market open" if is_open else "market closed, waits for the next open"
    status = (f"{weight * 100:.0f}% in {sym}" + (" (monthly rebalance done)" if rebalanced else
              ("" if L["last_month"] == month else f" (rebalance pending, {state})")))
    print(f"Paper trader [{label} volatility-managed] - run {now:%Y-%m-%d %H:%M} UTC")
    print(f"Status: {status}")
    print(f"{sym} ${price:,.2f} | last 21 days' volatility {vol * 100:.1f}%/yr | target {target * 100:.0f}% in {sym}")
    if action != "-":
        print(f"Actions: {action}")
    print(f"Paper account: ${equity:,.2f} (cash ${L['cash']:,.2f}) | total P/L {equity - L['start_cash']:+.2f}")
    if a.dry_run:
        return
    json.dump(L, open(LEDGER, "w"), indent=2)
    if rebalanced:
        new = not os.path.exists(JOURNAL)
        with open(JOURNAL, "a") as f:
            if new:
                f.write(f"# {label} volatility-managed journal\n\nPaper money only. Starting balance $300.\n\n"
                        f"| Month | {sym} | Vol | Target | Action | Equity |\n|---|---|---|---|---|---|\n")
            f.write(f"| {month} | {price:,.2f} | {vol * 100:.1f}% | {target * 100:.0f}% | {action} | {equity:,.2f} |\n")


if __name__ == "__main__":
    main()
