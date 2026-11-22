#!/usr/bin/env python3
"""Risk-parity paper account: SPY + TLT + GLD (no real money).

Rule (Asness, Frazzini & Pedersen 2012; passed anomaly_study5.py test 37):
  Once a month (first run while the US market is open in a new month), split
  the account between SPY (US stocks), TLT (long US bonds) and GLD (gold) in
  proportion to 1 / each fund's last 63 trading days' volatility, so each
  contributes about the same risk. Trade a fund only if its weight is off by
  more than 3%. No leverage. 0.10% fee per trade.
Backtest 2004-2026: +8.8% a year, worst drop -22%, Sharpe 0.98 vs 60/40
stocks/bonds 0.77; better in both halves; luck check 97%.

Usage: python3 paper/riskparity_paper.py [--dry-run]
"""
import argparse
import datetime as dt
import json
import os
import statistics as st
import urllib.request
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))
# method -> (funds, ledger, journal, label)
METHODS = {
    "riskparity": (("SPY", "TLT", "GLD"), "ledger_riskparity.json", "journal_riskparity.md", "Risk parity SPY/TLT/GLD"),
    # minimum variance, 63-day covariance, long only, 5% steps; allocation_study.py test 54
    "minvar": (("SPY", "TLT", "GLD"), "ledger_minvar.json", "journal_minvar.md", "Minimum variance SPY/TLT/GLD"),
    # Permanent Portfolio: fixed 25% each; allocation_study.py test 49
    "permanent": (("SPY", "TLT", "GLD", "SHY"), "ledger_permanent.json", "journal_permanent.md", "Permanent Portfolio"),
    # fixed 31.67% SPY / TLT / GLD + 5% BTC; allocation_study2.py test 64 (hindsight risk: BTC's 2014-2026 run)
    "thirds_btc": (("SPY", "TLT", "GLD", "BTC-USD"), "ledger_thirds_btc.json", "journal_thirds_btc.md",
                   "Equal thirds + 5% BTC"),
}
START, FEE, MIN_TRADE = 300.0, 0.001, 0.03
ET = ZoneInfo("America/New_York")


def history(sym):
    now = int(dt.datetime.now().timestamp())
    req = urllib.request.Request(
        f"https://query2.finance.yahoo.com/v8/finance/chart/{sym}?period1={now - 150 * 86400}&period2={now}&interval=1d",
        headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        j = json.load(r)["chart"]["result"][0]
    today = dt.datetime.now(ET).date()
    rows = [(dt.datetime.fromtimestamp(t, ET).date(), c)
            for t, c in zip(j["timestamp"], j["indicators"]["quote"][0]["close"]) if c]
    return [c for d, c in rows if d < today], float(j["meta"]["regularMarketPrice"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--method", choices=METHODS, default="riskparity")
    a = ap.parse_args()
    FUNDS, ledger, journal, label = METHODS[a.method]
    LEDGER, JOURNAL = os.path.join(HERE, ledger), os.path.join(HERE, journal)
    now = dt.datetime.now(dt.timezone.utc)
    et = now.astimezone(ET)
    is_open = et.weekday() < 5 and (9, 30) <= (et.hour, et.minute) < (16, 0)
    month = f"{et:%Y-%m}"
    price, rets = {}, {}
    for s in FUNDS:
        c, price[s] = history(s)
        rets[s] = [c[i] / c[i - 1] - 1 for i in range(len(c) - 63, len(c))]
    if a.method == "riskparity":
        inv = {s: 1 / st.pstdev(rets[s]) for s in FUNDS}
        tot = sum(inv.values())
        target = {s: inv[s] / tot for s in FUNDS}
    elif a.method == "minvar":
        m = {s: st.mean(rets[s]) for s in FUNDS}
        C = {(x, y): sum((rets[x][k] - m[x]) * (rets[y][k] - m[y]) for k in range(63)) / 63
             for x in FUNDS for y in FUNDS}
        best = None
        for i in range(21):
            for j in range(21 - i):
                w = {"SPY": i / 20, "TLT": j / 20, "GLD": 1 - (i + j) / 20}
                v = sum(w[x] * w[y] * C[(x, y)] for x in FUNDS for y in FUNDS)
                if best is None or v < best[0]:
                    best = (v, w)
        target = best[1]
    elif a.method == "thirds_btc":
        target = {"SPY": 0.95 / 3, "TLT": 0.95 / 3, "GLD": 0.95 / 3, "BTC-USD": 0.05}
    else:
        target = {s: 1 / len(FUNDS) for s in FUNDS}

    L = json.load(open(LEDGER)) if os.path.exists(LEDGER) else \
        {"start_cash": START, "cash": START, "shares": {s: 0.0 for s in FUNDS}, "last_month": None, "trades": []}
    equity = L["cash"] + sum(L["shares"][s] * price[s] for s in FUNDS)
    actions, rebalanced = [], False
    if L["last_month"] != month and is_open:
        # sells first, then buys, so the cash is there
        for s in sorted(FUNDS, key=lambda s: target[s] - L["shares"][s] * price[s] / equity):
            diff = target[s] - L["shares"][s] * price[s] / equity
            if abs(diff) > MIN_TRADE:
                usd = diff * equity
                fee = abs(usd) * FEE
                L["cash"] -= usd + fee
                L["shares"][s] += usd / price[s]
                actions.append(f"{'BOUGHT' if usd > 0 else 'SOLD'} ${abs(usd):.2f} of {s} at ${price[s]:,.2f}")
                L["trades"].append({"date": now.isoformat(timespec="minutes"), "fund": s, "price": round(price[s], 2),
                                    "usd": round(usd, 2), "fee": round(fee, 2), "target": round(target[s], 3)})
        L["last_month"], rebalanced = month, True
    equity = L["cash"] + sum(L["shares"][s] * price[s] for s in FUNDS)
    now_w = {s: L["shares"][s] * price[s] / equity for s in FUNDS}
    pend = "" if L["last_month"] == month else (" (rebalance pending, " + ("market open" if is_open else
                                                 "market closed, waits for the next open") + ")")
    print(f"Paper trader [{label}] - run {now:%Y-%m-%d %H:%M} UTC")
    print("Status: " + ", ".join(f"{now_w[s] * 100:.0f}% {s}" for s in FUNDS)
          + (" (monthly rebalance done)" if rebalanced else pend))
    print("Target: " + ", ".join(f"{target[s] * 100:.0f}% {s} (${price[s]:,.2f})" for s in FUNDS))
    if actions:
        print("Actions: " + "; ".join(actions))
    print(f"Paper account: ${equity:,.2f} (cash ${L['cash']:,.2f}) | total P/L {equity - L['start_cash']:+.2f}")
    if a.dry_run:
        return
    json.dump(L, open(LEDGER, "w"), indent=2)
    if rebalanced:
        new = not os.path.exists(JOURNAL)
        with open(JOURNAL, "a") as f:
            if new:
                f.write(f"# {label} journal\n\nPaper money only. Starting balance $300.\n\n"
                        f"| Month | Target {' / '.join(FUNDS)} | Actions | Equity |\n|---|---|---|---|\n")
            f.write(f"| {month} | " + " / ".join(f"{target[s] * 100:.0f}%" for s in FUNDS)
                    + f" | {'; '.join(actions) or '-'} | {equity:,.2f} |\n")


if __name__ == "__main__":
    main()
