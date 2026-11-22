#!/usr/bin/env python3
"""BTC weekly trend-following paper account (no real money).

The rule that passed paper/edge_study.py (time-series momentum):
  - Once a week (first run of each ISO week, UTC), look at the last completed
    daily close:
      * half the target: BTC is up over the past 28 days -> 50%, else 0%
      * other half:     BTC is up over the past 56 days -> 50%, else 0%
  - Volatility sizing: multiply by min(1, 50% / last 30 days' yearly volatility).
  - Buy or sell to that target (only if it differs by more than 5% of the
    account). No leverage, no shorting. 0.4% fee per trade, like the other
    paper accounts.
Backtest 2014-2026 (0.10% cost): +46% a year, worst drop -54%, Sharpe 1.23,
vs buy and hold +49% a year, worst drop -83%, Sharpe 0.94.

Usage: python3 paper/trend_paper.py [--dry-run]
"""
import argparse
import datetime as dt
import json
import math
import os
import statistics as st
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
LEDGER = os.path.join(HERE, "ledger_trend.json")
JOURNAL = os.path.join(HERE, "journal_trend.md")
START, FEE, VOL_TARGET, MIN_TRADE = 300.0, 0.004, 0.5, 0.05


def get(url, ua="paper-trader/1.0"):
    req = urllib.request.Request(url, headers={"User-Agent": ua})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def closes():
    now = int(dt.datetime.now().timestamp())
    j = get(f"https://query2.finance.yahoo.com/v8/finance/chart/BTC-USD?period1={now - 200 * 86400}"
            f"&period2={now}&interval=1d", ua="Mozilla/5.0")["chart"]["result"][0]
    today = dt.datetime.now(dt.timezone.utc).date()
    out = [(dt.datetime.fromtimestamp(t, dt.timezone.utc).date(), c)
           for t, c in zip(j["timestamp"], j["indicators"]["quote"][0]["close"]) if c]
    return [(d, c) for d, c in out if d < today]        # completed days only


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    now = dt.datetime.now(dt.timezone.utc)
    week = "%d-W%02d" % now.isocalendar()[:2]
    price = float(get("https://api.gemini.com/v1/pubticker/btcusd")["last"])
    px = closes()
    c = [p for _, p in px]
    r28, r56 = c[-1] / c[-29] - 1, c[-1] / c[-57] - 1
    rets = [c[i] / c[i - 1] - 1 for i in range(len(c) - 30, len(c))]
    vol = st.pstdev(rets) * math.sqrt(365)
    scale = min(1.0, VOL_TARGET / vol) if vol > 0 else 1.0
    target = (0.5 * (r28 > 0) + 0.5 * (r56 > 0)) * scale

    L = json.load(open(LEDGER)) if os.path.exists(LEDGER) else \
        {"start_cash": START, "cash": START, "btc": 0.0, "last_week": None, "trades": []}
    equity = L["cash"] + L["btc"] * price
    weight = L["btc"] * price / equity if equity else 0
    action = "-"
    if L["last_week"] != week:
        diff = target - weight
        if abs(diff) > MIN_TRADE:
            usd = diff * equity
            if usd > 0:
                fee = usd * FEE
                L["cash"] -= usd
                L["btc"] += (usd - fee) / price
                action = f"BOUGHT ${usd:.2f} of BTC at ${price:,.0f}"
            else:
                qty = min(L["btc"], -usd / price)
                gross = qty * price
                fee = gross * FEE
                L["btc"] -= qty
                L["cash"] += gross - fee
                action = f"SOLD ${gross:.2f} of BTC at ${price:,.0f}"
            L["trades"].append({"date": now.isoformat(timespec="minutes"), "price": round(price, 2),
                                "usd": round(usd, 2), "fee": round(fee, 2), "target": round(target, 3)})
        L["last_week"] = week
        rebalanced = True
    else:
        rebalanced = False
    equity = L["cash"] + L["btc"] * price
    weight = L["btc"] * price / equity if equity else 0
    status = ("HOLDING" if weight > 0.01 else "CASH") + (" (weekly rebalance done)" if rebalanced else "")
    print(f"Paper trader [BTC weekly trend] - run {now:%Y-%m-%d %H:%M} UTC, week {week}")
    print(f"Status: {status}")
    print(f"Price now ${price:,.0f} | 28-day return {r28 * 100:+.1f}% | 56-day return {r56 * 100:+.1f}% | "
          f"30-day volatility {vol * 100:.0f}%/yr")
    print(f"Target {target * 100:.0f}% in BTC, now {weight * 100:.0f}% in BTC")
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
                f.write("# BTC weekly trend journal\n\nPaper money only. Starting balance $300.\n\n"
                        "| Week | Price | 28d | 56d | Vol | Target | Action | Equity |\n|---|---|---|---|---|---|---|---|\n")
            f.write(f"| {week} | {price:,.0f} | {r28 * 100:+.1f}% | {r56 * 100:+.1f}% | {vol * 100:.0f}% | "
                    f"{target * 100:.0f}% | {action} | {equity:,.2f} |\n")


if __name__ == "__main__":
    main()
