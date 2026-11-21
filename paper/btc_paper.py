#!/usr/bin/env python3
"""BTC paper trader (no real money).

Two modes, each with its own $300 paper account:
  --mode daily  daily candles, swing trades   (ledger.json / journal.md)
  --mode 2h     2-hour candles, intraday trades (ledger_2h.json / journal_2h.md)

Each run fetches BTC/USD candles and the live price from Gemini's public API,
applies the trend rules, updates the paper account and journal, and prints a
short report.

Rules (spot only, no leverage). On the last completed candle:
  BUY when all hold:
    - close > 20-period average
    - 20-period average > 50-period average
    - 40 <= RSI(14) <= 65
    - close no more than DIP% above the 20-period average (buy dips, not spikes)
  Size: half of the account.
  Stop-loss: STOP% below entry (checked against each candle's low).
  Take profit: sell half at TP% (checked against each candle's high), then move
    the stop to the entry price.
  Exit the rest when a candle closes below the 20-period average.
  Brakes: after 2 losing trades in a row, no buys for the rest of that day
    (2h) or the next day (daily); if the account is $20 or more below the
    week's start, no buys until next Monday.
  Fees: 0.4% per side on every paper fill.
"""
import argparse
import datetime as dt
import json
import os
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
START_CASH = 300.0
FEE = 0.004
SIZE_FRAC = 0.5
WEEKLY_LOSS_LIMIT = 20.0

MODES = {
    "daily": dict(period_h=24, source="1day", stop=0.04, tp=0.07, dip=0.03,
                  ledger="ledger.json", journal="journal.md", label="daily"),
    "2h": dict(period_h=2, source="1hr", stop=0.015, tp=0.03, dip=0.01,
               ledger="ledger_2h.json", journal="journal_2h.md", label="2-hour"),
}


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


def to_2h(hourly):
    """Merge 1h candles into 2h candles aligned to even UTC hours."""
    groups = {}
    for c in hourly:
        key = c[0] - (c[0] % (2 * 3600 * 1000))
        groups.setdefault(key, []).append(c)
    out = []
    for key, cs in groups.items():
        if len(cs) != 2:
            continue
        cs.sort(key=lambda c: c[0])
        out.append([key, cs[0][1], max(c[2] for c in cs), min(c[3] for c in cs),
                    cs[-1][4], sum(c[5] for c in cs)])
    return out


def monday(d):
    return d - dt.timedelta(days=d.weekday())


def stamp(ms, period_h):
    t = dt.datetime.fromtimestamp(ms / 1000, dt.timezone.utc)
    return t.date().isoformat() if period_h >= 24 else t.strftime("%Y-%m-%d %H:%M")


def new_ledger(today):
    return {"start_cash": START_CASH, "cash": START_CASH, "btc": 0.0, "position": None,
            "consecutive_losses": 0, "cooldown_until": None,
            "week_start": monday(today).isoformat(), "week_start_equity": START_CASH,
            "last_processed_candle": None, "trades": []}


def sell(L, qty, price, reason, when):
    gross = qty * price
    fee = gross * FEE
    L["cash"] += gross - fee
    L["btc"] -= qty
    pos = L["position"]
    pnl = gross - fee - qty * pos["entry"] * (1 + FEE)
    pos["realized"] = pos.get("realized", 0.0) + pnl
    L["trades"].append({"date": when, "side": "SELL", "qty": round(qty, 8),
                        "price": round(price, 2), "fee": round(fee, 2),
                        "pnl": round(pnl, 2), "reason": reason})
    return pnl


def close_position(L, when_date, period_h, candle_ms):
    L["last_exit_ms"] = candle_ms
    if L["position"].get("realized", 0.0) < 0:
        L["consecutive_losses"] += 1
    else:
        L["consecutive_losses"] = 0
    if L["consecutive_losses"] >= 2:
        days = 1 if period_h >= 24 else 0
        # 2h: blocked until midnight UTC; daily: blocked the next day as well
        L["cooldown_until"] = (when_date + dt.timedelta(days=days + 1)).isoformat()
        L["consecutive_losses"] = 0
    L["position"] = None
    L["btc"] = 0.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=MODES, default="daily")
    ap.add_argument("--candles", help="JSON file of Gemini candles instead of fetching")
    ap.add_argument("--price", type=float, help="live price instead of fetching")
    ap.add_argument("--dry-run", action="store_true", help="do not write ledger/journal")
    a = ap.parse_args()
    M = MODES[a.mode]
    P = M["period_h"]
    ledger_path = os.path.join(HERE, M["ledger"])
    journal_path = os.path.join(HERE, M["journal"])

    if a.candles:
        raw = json.load(open(a.candles))
    else:
        raw = fetch_json(f"https://api.gemini.com/v2/candles/btcusd/{M['source']}")
    if a.mode == "2h":
        raw = to_2h(raw)
    price = a.price
    if price is None:
        price = float(fetch_json("https://api.gemini.com/v1/pubticker/btcusd")["last"])

    now = dt.datetime.now(dt.timezone.utc)
    now_ms = int(now.timestamp() * 1000)
    today = now.date()
    period_ms = P * 3600 * 1000
    candles = sorted((c for c in raw if c[0] + period_ms <= now_ms), key=lambda c: c[0])
    if len(candles) < 60:
        sys.exit("not enough candle history")
    closes = [c[4] for c in candles]
    last = candles[-1]
    last_label = stamp(last[0], P)
    close = last[4]
    s20, s50, r = sma(closes, 20), sma(closes, 50), rsi(closes[-200:])

    L = json.load(open(ledger_path)) if os.path.exists(ledger_path) else new_ledger(today)
    actions = []
    run_label = now.strftime("%Y-%m-%d") if P >= 24 else last_label

    if dt.date.fromisoformat(L["week_start"]) < monday(today):
        L["week_start"] = monday(today).isoformat()
        L["week_start_equity"] = L["cash"] + L["btc"] * price

    # 1) manage an open position against every completed candle since the last check
    pos = L["position"]
    if pos:
        for i, c in enumerate(candles):
            if c[0] <= pos["last_checked_ms"]:
                continue
            _, _, hi, lo, cl, _ = c
            when = stamp(c[0], P)
            cdate = dt.datetime.fromtimestamp(c[0] / 1000, dt.timezone.utc).date()
            if lo <= pos["stop"]:
                pnl = sell(L, L["btc"], pos["stop"], "stop-loss", when)
                actions.append(f"SOLD all at stop ${pos['stop']:,.0f} ({pnl:+.2f})")
                close_position(L, cdate, P, c[0])
                break
            if not pos["tp_done"] and hi >= pos["tp"]:
                pnl = sell(L, L["btc"] / 2, pos["tp"], "take-profit half", when)
                pos["tp_done"] = True
                pos["stop"] = pos["entry"]
                actions.append(f"SOLD half at +{M['tp']*100:g}% ${pos['tp']:,.0f} ({pnl:+.2f}); stop moved to entry")
            if cl < sma([x[4] for x in candles[:i + 1]], 20):
                pnl = sell(L, L["btc"], cl, "close below 20-period avg", when)
                actions.append(f"SOLD rest at ${cl:,.0f}, close below 20-period avg ({pnl:+.2f})")
                close_position(L, cdate, P, c[0])
                break
            pos["last_checked_ms"] = c[0]
    L["last_processed_candle"] = last_label

    # 2) look for a new entry
    trend_ok = close > s20 > s50
    rsi_ok = 40 <= r <= 65
    dip_ok = s20 < close <= s20 * (1 + M["dip"])
    equity = L["cash"] + L["btc"] * price
    weekly_brake = equity <= L["week_start_equity"] - WEEKLY_LOSS_LIMIT
    cooldown = bool(L["cooldown_until"]) and today.isoformat() < L["cooldown_until"]
    # after an exit, wait for a fresh completed candle before buying again
    fresh = last[0] > L.get("last_exit_ms", 0)

    if L["position"]:
        status = "HOLD"
    elif trend_ok and rsi_ok and dip_ok and fresh and not weekly_brake and not cooldown:
        spend = round(equity * SIZE_FRAC, 2)
        fee = spend * FEE
        qty = (spend - fee) / price
        L["cash"] -= spend
        L["btc"] = qty
        L["position"] = {"entry": price, "qty": qty, "opened": now.isoformat(timespec="minutes"),
                         "stop": round(price * (1 - M["stop"]), 2),
                         "tp": round(price * (1 + M["tp"]), 2),
                         "tp_done": False, "last_checked_ms": last[0], "realized": 0.0}
        L["trades"].append({"date": now.isoformat(timespec="minutes"), "side": "BUY",
                            "qty": round(qty, 8), "price": round(price, 2),
                            "fee": round(fee, 2), "pnl": 0.0, "reason": "trend + dip signal"})
        actions.append(f"BOUGHT ${spend:.2f} of BTC at ${price:,.0f}")
        status = "BUY SIGNAL"
    elif weekly_brake:
        status = "WAIT (weekly loss limit)"
    elif cooldown:
        status = "WAIT (paused after 2 losses)"
    elif not fresh:
        status = "WAIT (just exited, next candle)"
    elif close > s20 or (r > 40 and close > s20 * 0.98):
        status = "GET READY"
    else:
        status = "WAIT"

    equity = L["cash"] + L["btc"] * price
    lines = [
        f"BTC paper trader [{M['label']}] - run {now.strftime('%Y-%m-%d %H:%M')} UTC (last candle {last_label})",
        f"Status: {status}",
        f"Price now ${price:,.0f} | close ${close:,.0f} | 20-avg ${s20:,.0f} | 50-avg ${s50:,.0f} | RSI {r:.1f}",
        "Checks: " + ", ".join([
            f"close>20-avg {'yes' if close > s20 else 'no'}",
            f"20-avg>50-avg {'yes' if s20 > s50 else 'no'}",
            f"RSI 40-65 {'yes' if rsi_ok else 'no'}",
            f"near 20-avg {'yes' if dip_ok else 'no'}",
        ]),
    ]
    if actions:
        lines.append("Actions: " + "; ".join(actions))
    if L["position"]:
        p = L["position"]
        lines.append(f"Position: {L['btc']:.6f} BTC from ${p['entry']:,.0f} | stop ${p['stop']:,.0f}"
                     f" | target {'done' if p['tp_done'] else '$' + format(p['tp'], ',.0f')}")
    lines.append(f"Paper account: ${equity:,.2f} (cash ${L['cash']:,.2f}) | total P/L {equity - L['start_cash']:+.2f}")
    print("\n".join(lines))

    if a.dry_run:
        return
    with open(ledger_path, "w") as f:
        json.dump(L, f, indent=2)
    header = (f"# BTC paper trading journal ({M['label']})\n\nPaper money only. Starting balance $300.\n\n"
              "| Time | Status | Price | 20-avg | 50-avg | RSI | Actions | Equity |\n"
              "|---|---|---|---|---|---|---|---|\n")
    rows = []
    if os.path.exists(journal_path):
        rows = [ln for ln in open(journal_path).read().splitlines(True) if ln.startswith("| 2")]
    # one row per day (daily) or per candle (2h); a rerun replaces that row and
    # keeps any actions it already recorded
    prev = [ln for ln in rows if ln.startswith(f"| {run_label} |")]
    rows = [ln for ln in rows if not ln.startswith(f"| {run_label} |")]
    acts = "; ".join(actions)
    if prev:
        old = prev[-1].split(" | ")[6]
        if old != "-":
            acts = old + ("; " + acts if acts else "")
    rows.append(f"| {run_label} | {status} | {price:,.0f} | {s20:,.0f} | {s50:,.0f} | {r:.1f} | "
                f"{acts or '-'} | {equity:,.2f} |\n")
    with open(journal_path, "w") as f:
        f.write(header + "".join(rows))


if __name__ == "__main__":
    main()
