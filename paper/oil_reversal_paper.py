#!/usr/bin/env python3
"""Oil day-trading forward test (EXPERIMENT, paper money only).

Rule frozen on 2026-11-22 from oil_indicator_search2.py (it was NOT a pass:
best variant on unseen data, but chosen after looking, so only a live
forward test can show whether it is real):
  * Hourly WTI futures (Yahoo CL=F), New York session only.
  * Count the 6 reversal indicators (RSI(14) 30/70, RSI(2) 10/90, Bollinger
    2-sd, Stochastic 20/80, CCI +-100, VWAP stretch). BUY when at least 2 say
    "oversold, buy" (and more say buy than sell). Long only.
  * New buys only on completed 9:00-13:00 New York candles, never Wednesday
    9:00-12:00 (EIA report window).
  * Sell when fewer than 2 say buy, or at the first run after the 14:00
    candle (flat overnight). 0.05% fee per side; whole paper account per trade.
Judge it only after >= 40 live trades.

Usage: python3 paper/oil_reversal_paper.py [--dry-run]
"""
import argparse
import datetime as dt
import json
import os

import oil_indicator_search as S
from oil_indicator_search2 import consensus

HERE = os.path.dirname(os.path.abspath(__file__))
LEDGER = os.path.join(HERE, "ledger_oil_reversal.json")
JOURNAL = os.path.join(HERE, "journal_oil_reversal.md")
START, FEE = 300.0, 0.0005


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    now = dt.datetime.now(dt.timezone.utc)
    bars = S.yahoo("60d", "60m")
    done = [b for b in bars if b["t"] + 3600 <= now.timestamp()]
    I, _ = S.indicators(done)
    sig = max(consensus(I, 2)[-1], 0)
    last = done[-1]
    et = last["et"]
    fresh = now.timestamp() - last["t"] < 3 * 3600          # market open, candle recent
    in_window = et.weekday() < 5 and 9 <= et.hour <= 13 and not (et.weekday() == 2 and 9 <= et.hour <= 11)
    session_over = et.weekday() >= 5 or et.hour >= 14 or et.hour < 9
    px = last["c"]
    L = json.load(open(LEDGER)) if os.path.exists(LEDGER) else \
        {"start_cash": START, "cash": START, "qty": 0.0, "entry": None, "last_bar": None, "trades": []}
    action = "-"
    if L["last_bar"] != last["t"] and fresh:
        if L["qty"] > 0 and (sig <= 0 or session_over):
            gross = L["qty"] * px
            fee = gross * FEE
            pnl = gross - fee - L["qty"] * L["entry"] * (1 + FEE)
            L["cash"] += gross - fee
            L["trades"].append({"exit": last["et"].isoformat(timespec="minutes"), "price": round(px, 2), "pnl": round(pnl, 2)})
            action = f"SOLD at ${px:,.2f} ({pnl:+.2f})"
            L["qty"], L["entry"] = 0.0, None
        elif L["qty"] == 0 and sig > 0 and in_window:
            spend = L["cash"]
            L["qty"] = spend * (1 - FEE) / px
            L["entry"], L["cash"] = px, 0.0
            action = f"BOUGHT ${spend:.2f} of oil at ${px:,.2f}"
        L["last_bar"] = last["t"]
    equity = L["cash"] + L["qty"] * px
    closed = len(L["trades"])
    wins = sum(1 for t in L["trades"] if t["pnl"] > 0)
    status = ("HOLD" if L["qty"] > 0 else "FLAT") + ("" if fresh else " (market closed)")
    print(f"Paper trader [OIL hourly reversal EXPERIMENT] - run {now:%Y-%m-%d %H:%M} UTC (last candle {et:%Y-%m-%d %H:%M} NY)")
    print(f"Status: {status} | buy signals now: {sig > 0} | closed trades {closed}, won {wins}")
    if action != "-":
        print(f"Actions: {action}")
    print(f"Oil ${px:,.2f} | Paper account: ${equity:,.2f} | total P/L {equity - L['start_cash']:+.2f}")
    if a.dry_run:
        return
    json.dump(L, open(LEDGER, "w"), indent=2)
    if action != "-":
        new = not os.path.exists(JOURNAL)
        with open(JOURNAL, "a") as f:
            if new:
                f.write("# Oil hourly reversal EXPERIMENT journal\n\nPaper money only. Starting balance $300.\n\n"
                        "| Candle (NY) | Price | Action | Equity |\n|---|---|---|---|\n")
            f.write(f"| {et:%Y-%m-%d %H:%M} | {px:,.2f} | {action} | {equity:,.2f} |\n")


if __name__ == "__main__":
    main()
