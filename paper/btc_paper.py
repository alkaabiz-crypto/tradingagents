#!/usr/bin/env python3
"""Daily BTC paper trader (no real money).

Run once a day. It fetches BTC/USD daily candles and the live price from
Gemini's public API, applies the trend rules below, updates the paper
portfolio in paper/ledger.json, appends a line to paper/journal.md and
prints a short report.

Rules (conservative, spot only, no leverage):
  Trend filter for a BUY (all must hold, on the last completed daily close):
    - close > 20-day average
    - 20-day average > 50-day average
    - 40 <= RSI(14) <= 65
    - close within 3% of the 20-day average (buy dips, not spikes)
  Size: half of equity (~$150 of $300), stop-loss 4% below entry,
        so one losing trade costs about 2% of the account.
  Exits:
    - stop-loss hit (checked against each day's low)       -> sell all
    - +7% hit (checked against each day's high)             -> sell half,
      move stop to entry price
    - daily close below the 20-day average                  -> sell the rest
  Brakes:
    - after 2 losing trades in a row, skip new buys for 1 day
    - if equity is $20 or more below the week's start, no new buys until
      next Monday
  Fees: 0.4% per side are charged on every paper fill.

Usage: python3 paper/btc_paper.py [--candles FILE] [--price P] [--dry-run]
"""
import argparse
import datetime as dt
import json
import os
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
LEDGER = os.path.join(HERE, "ledger.json")
JOURNAL = os.path.join(HERE, "journal.md")

START_CASH = 300.0
FEE = 0.004
STOP_PCT = 0.04
TP_PCT = 0.07
SIZE_FRAC = 0.5
DIP_PCT = 0.03
WEEKLY_LOSS_LIMIT = 20.0


def fetch_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "paper-trader/1.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)


def sma(xs, n):
    return sum(xs[-n:]) / n


def rsi(closes, n=14):
    gains = losses = 0.0
    for i in range(1, n + 1):
        d = closes[i] - closes[i - 1]
        gains += max(d, 0)
        losses += max(-d, 0)
    ag, al = gains / n, losses / n
    for i in range(n + 1, len(closes)):
        d = closes[i] - closes[i - 1]
        ag = (ag * (n - 1) + max(d, 0)) / n
        al = (al * (n - 1) + max(-d, 0)) / n
    return 100.0 if al == 0 else 100 - 100 / (1 + ag / al)


def new_ledger(today):
    return {
        "start_cash": START_CASH,
        "cash": START_CASH,
        "btc": 0.0,
        "position": None,
        "consecutive_losses": 0,
        "cooldown_until": None,
        "week_start": monday(today).isoformat(),
        "week_start_equity": START_CASH,
        "last_processed_candle": None,
        "trades": [],
    }


def monday(d):
    return d - dt.timedelta(days=d.weekday())


def sell(L, qty, price, reason, day):
    gross = qty * price
    fee = gross * FEE
    L["cash"] += gross - fee
    L["btc"] -= qty
    pos = L["position"]
    cost = qty * pos["entry"] * (1 + FEE)
    pnl = gross - fee - cost
    pos["realized"] = pos.get("realized", 0.0) + pnl
    L["trades"].append({"date": day, "side": "SELL", "qty": round(qty, 8),
                        "price": round(price, 2), "fee": round(fee, 2),
                        "pnl": round(pnl, 2), "reason": reason})
    return pnl


def close_position(L, day):
    pos = L["position"]
    if pos.get("realized", 0.0) < 0:
        L["consecutive_losses"] += 1
    else:
        L["consecutive_losses"] = 0
    if L["consecutive_losses"] >= 2:
        L["cooldown_until"] = (dt.date.fromisoformat(day) + dt.timedelta(days=1)).isoformat()
        L["consecutive_losses"] = 0
    L["position"] = None
    L["btc"] = 0.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--candles", help="JSON file of Gemini 1day candles instead of fetching")
    ap.add_argument("--price", type=float, help="live price instead of fetching")
    ap.add_argument("--dry-run", action="store_true", help="do not write ledger/journal")
    a = ap.parse_args()

    if a.candles:
        with open(a.candles) as f:
            raw = json.load(f)
    else:
        raw = fetch_json("https://api.gemini.com/v2/candles/btcusd/1day")
    price = a.price
    if price is None:
        price = float(fetch_json("https://api.gemini.com/v1/pubticker/btcusd")["last"])

    now = dt.datetime.now(dt.timezone.utc)
    today = now.date()
    today_start_ms = int(dt.datetime(today.year, today.month, today.day,
                                     tzinfo=dt.timezone.utc).timestamp() * 1000)
    # completed candles only, oldest first: [ts, open, high, low, close, vol]
    candles = sorted((c for c in raw if c[0] < today_start_ms), key=lambda c: c[0])
    if len(candles) < 60:
        sys.exit("not enough candle history")
    closes = [c[4] for c in candles]
    last = candles[-1]
    last_day = dt.datetime.fromtimestamp(last[0] / 1000, dt.timezone.utc).date().isoformat()
    close = last[4]
    s20, s50, r = sma(closes, 20), sma(closes, 50), rsi(closes[-200:])

    L = json.load(open(LEDGER)) if os.path.exists(LEDGER) else new_ledger(today)
    actions = []
    day = today.isoformat()

    # new week bookkeeping
    if dt.date.fromisoformat(L["week_start"]) < monday(today):
        L["week_start"] = monday(today).isoformat()
        L["week_start_equity"] = L["cash"] + L["btc"] * price

    # 1) manage an open position against every completed candle since entry
    pos = L["position"]
    if pos:
        for c in candles:
            cday = dt.datetime.fromtimestamp(c[0] / 1000, dt.timezone.utc).date().isoformat()
            if cday <= pos["last_checked"]:
                continue
            _, _, hi, lo, cl, _ = c
            if lo <= pos["stop"]:
                pnl = sell(L, L["btc"], pos["stop"], "stop-loss", cday)
                actions.append(f"SOLD all at stop ${pos['stop']:,.0f} ({pnl:+.2f})")
                close_position(L, cday)
                break
            if not pos["tp_done"] and hi >= pos["tp"]:
                pnl = sell(L, L["btc"] / 2, pos["tp"], "take-profit half", cday)
                pos["tp_done"] = True
                pos["stop"] = pos["entry"]
                actions.append(f"SOLD half at +7% ${pos['tp']:,.0f} ({pnl:+.2f}); stop moved to entry")
            day_s20 = sma([x[4] for x in candles if x[0] <= c[0]], 20)
            if cl < day_s20:
                pnl = sell(L, L["btc"], cl, "close below 20-day avg", cday)
                actions.append(f"SOLD rest at ${cl:,.0f}, close below 20-day avg ({pnl:+.2f})")
                close_position(L, cday)
                break
            pos["last_checked"] = cday
    L["last_processed_candle"] = last_day

    # 2) look for a new entry
    trend_ok = close > s20 and s20 > s50
    rsi_ok = 40 <= r <= 65
    dip_ok = s20 < close <= s20 * (1 + DIP_PCT)
    equity = L["cash"] + L["btc"] * price
    weekly_brake = equity <= L["week_start_equity"] - WEEKLY_LOSS_LIMIT
    cooldown = L["cooldown_until"] and day < L["cooldown_until"]

    if L["position"]:
        status = "HOLD"
    elif trend_ok and rsi_ok and dip_ok and not weekly_brake and not cooldown:
        spend = round(equity * SIZE_FRAC, 2)
        fee = spend * FEE
        qty = (spend - fee) / price
        L["cash"] -= spend
        L["btc"] = qty
        L["position"] = {"entry": price, "qty": qty, "opened": day,
                         "stop": round(price * (1 - STOP_PCT), 2),
                         "tp": round(price * (1 + TP_PCT), 2),
                         "tp_done": False, "last_checked": last_day, "realized": 0.0}
        L["trades"].append({"date": day, "side": "BUY", "qty": round(qty, 8),
                            "price": round(price, 2), "fee": round(fee, 2),
                            "pnl": 0.0, "reason": "trend + dip signal"})
        actions.append(f"BOUGHT ${spend:.2f} of BTC at ${price:,.0f}")
        status = "BUY SIGNAL"
    elif weekly_brake:
        status = "WAIT (weekly loss limit)"
    elif cooldown:
        status = "WAIT (cooldown after 2 losses)"
    elif close > s20 or (r > 40 and close > s20 * 0.97):
        status = "GET READY"
    else:
        status = "WAIT"

    equity = L["cash"] + L["btc"] * price
    pnl_total = equity - L["start_cash"]

    lines = [
        f"BTC paper trader - {day} (last daily close {last_day})",
        f"Status: {status}",
        f"Price now ${price:,.0f} | close ${close:,.0f} | 20d avg ${s20:,.0f} | 50d avg ${s50:,.0f} | RSI {r:.1f}",
        "Checks: " + ", ".join([
            f"close>20d {'yes' if close > s20 else 'no'}",
            f"20d>50d {'yes' if s20 > s50 else 'no'}",
            f"RSI 40-65 {'yes' if rsi_ok else 'no'}",
            f"near 20d {'yes' if dip_ok else 'no'}",
        ]),
    ]
    if actions:
        lines.append("Actions: " + "; ".join(actions))
    if L["position"]:
        p = L["position"]
        lines.append(f"Position: {L['btc']:.6f} BTC from ${p['entry']:,.0f} | stop ${p['stop']:,.0f}"
                     f" | target {'done' if p['tp_done'] else '$' + format(p['tp'], ',.0f')}")
    lines.append(f"Paper account: ${equity:,.2f} (cash ${L['cash']:,.2f}) | total P/L {pnl_total:+.2f}")
    report = "\n".join(lines)
    print(report)

    if not a.dry_run:
        with open(LEDGER, "w") as f:
            json.dump(L, f, indent=2)
        header = ("# BTC paper trading journal\n\nPaper money only. Starting balance $300.\n\n"
                  "| Date | Status | Price | 20d | 50d | RSI | Actions | Equity |\n"
                  "|---|---|---|---|---|---|---|---|\n")
        rows = []
        if os.path.exists(JOURNAL):
            rows = [ln for ln in open(JOURNAL).read().splitlines(True)
                    if ln.startswith("| 2")]
        # one row per day: a rerun on the same day replaces that day's row,
        # keeping any actions already recorded earlier that day
        prev = [ln for ln in rows if ln.startswith(f"| {day} |")]
        rows = [ln for ln in rows if not ln.startswith(f"| {day} |")]
        acts = "; ".join(actions)
        if prev:
            old = prev[-1].split(" | ")[6]
            if old != "-":
                acts = old + ("; " + acts if acts else "")
        rows.append(f"| {day} | {status} | {price:,.0f} | {s20:,.0f} | {s50:,.0f} | {r:.1f} | "
                    f"{acts or '-'} | {equity:,.2f} |\n")
        with open(JOURNAL, "w") as f:
            f.write(header + "".join(rows))


if __name__ == "__main__":
    main()
