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
    # EXPERIMENT: counter-trend bounce buying. Riskier than the trend modes.
    "dip2h": dict(period_h=2, source="1hr", stop=0.02, tp=0.025, dip=0.0,
                  strategy="dip", size=0.25, max_hold=12,
                  ledger="ledger_dip2h.json", journal="journal_dip2h.md",
                  label="2-hour dip-buy EXPERIMENT"),
    # Range trading: buy near the bottom of a sideways range, sell in the
    # middle and near the top. Entries also need a fresh news check.
    "range2h": dict(period_h=2, source="1hr", stop=0.0, tp=0.0, dip=0.0,
                    strategy="range", size=0.3, max_hold=12, lookback=24,
                    ledger="ledger_range2h.json", journal="journal_range2h.md",
                    label="2-hour range"),
}
NEWS_GATE = os.path.join(HERE, "news_gate.json")
NEWS_MAX_AGE_H = 2


def news_gate(now):
    """Read the news check written before each run. Missing or stale = not OK."""
    try:
        g = json.load(open(NEWS_GATE))
        t = dt.datetime.fromisoformat(g["checked_at"].replace("Z", "+00:00"))
        fresh = (now - t) <= dt.timedelta(hours=NEWS_MAX_AGE_H)
        return bool(g.get("ok")) and fresh, g.get("reason", "") + ("" if fresh else " (stale)")
    except Exception as e:  # no file or bad file: block entries
        return False, f"no news check ({type(e).__name__})"


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


def main(argv=None, raw_candles=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=MODES, default="daily")
    ap.add_argument("--candles", help="JSON file of Gemini candles instead of fetching")
    ap.add_argument("--price", type=float, help="live price instead of fetching")
    ap.add_argument("--dry-run", action="store_true", help="do not write ledger/journal")
    # backtesting helpers
    ap.add_argument("--now", help="pretend the current UTC time is this ISO time")
    ap.add_argument("--dir", help="folder for the ledger and journal (default: paper/)")
    ap.add_argument("--assume-news-ok", action="store_true", help="skip the news gate")
    a = ap.parse_args(argv)
    M = MODES[a.mode]
    P = M["period_h"]
    out_dir = a.dir or HERE
    ledger_path = os.path.join(out_dir, M["ledger"])
    journal_path = os.path.join(out_dir, M["journal"])

    if raw_candles is not None:
        raw = raw_candles
    elif a.candles:
        raw = json.load(open(a.candles))
    else:
        raw = fetch_json(f"https://api.gemini.com/v2/candles/btcusd/{M['source']}")
    if M["source"] == "1hr":
        raw = to_2h(raw)
    price = a.price
    if price is None:
        price = float(fetch_json("https://api.gemini.com/v1/pubticker/btcusd")["last"])

    now = (dt.datetime.fromisoformat(a.now.replace("Z", "+00:00")) if a.now
           else dt.datetime.now(dt.timezone.utc))
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

    dip_mode = M.get("strategy") == "dip"
    range_mode = M.get("strategy") == "range"

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
                actions.append(f"SOLD half at target ${pos['tp']:,.0f} ({pnl:+.2f}); stop moved to entry")
            c20 = sma([x[4] for x in candles[:i + 1]], 20)
            if range_mode:
                pos["held"] = pos.get("held", 0) + 1
                if hi >= pos["top"] or pos["held"] >= M["max_hold"]:
                    px = pos["top"] if hi >= pos["top"] else cl
                    why = "reached top of range" if hi >= pos["top"] else f"time stop ({M['max_hold']} candles)"
                    pnl = sell(L, L["btc"], px, why, when)
                    actions.append(f"SOLD rest at ${px:,.0f}, {why} ({pnl:+.2f})")
                    close_position(L, cdate, P, c[0])
                    break
            elif dip_mode:
                pos["held"] = pos.get("held", 0) + 1
                if cl >= c20 or pos["held"] >= M["max_hold"]:
                    why = "bounced to 20-period avg" if cl >= c20 else f"time stop ({M['max_hold']} candles)"
                    pnl = sell(L, L["btc"], cl, why, when)
                    actions.append(f"SOLD rest at ${cl:,.0f}, {why} ({pnl:+.2f})")
                    close_position(L, cdate, P, c[0])
                    break
            elif cl < c20:
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
    if dip_mode:
        # oversold in one of the 3 candles before the last, RSI back to 30+,
        # and the last candle is green and closed above the one before it
        recent_low_rsi = min(rsi(closes[-200 - k:-k]) for k in (1, 2, 3))
        oversold_ok = recent_low_rsi < 30
        turn_ok = r >= 30 and close > last[1] and close > closes[-2]
        signal = oversold_ok and turn_ok
    elif range_mode:
        win = candles[-M["lookback"]:]
        rh, rl = max(c[2] for c in win), min(c[3] for c in win)
        span = rh - rl
        width = span / rl
        width_ok = 0.02 <= width <= 0.08                      # a real but calm range
        s20_before = sma(closes[:-10], 20)
        flat_ok = abs(s20 - s20_before) / s20 < 0.01          # no strong trend
        zone_ok = price <= rl + 0.25 * span                   # bottom quarter
        bounce_ok = close > last[1] and r < 50                # green candle, not overbought
        r_stop, r_mid, r_top = rl * 0.995, rl + 0.5 * span, rl + 0.85 * span
        rr_ok = price > r_stop and (r_mid - price) >= 1.2 * (price - r_stop)
        sizes = [(c[2] - c[3]) / c[4] for c in candles[-21:-1]]
        calm_ok = (last[2] - last[3]) / close <= 2.5 * (sum(sizes) / len(sizes))
        news_ok, news_why = (True, "assumed OK") if a.assume_news_ok else news_gate(now)
        signal = all([width_ok, flat_ok, zone_ok, bounce_ok, rr_ok, calm_ok, news_ok])
    else:
        signal = trend_ok and rsi_ok and dip_ok

    if L["position"]:
        status = "HOLD"
    elif signal and fresh and not weekly_brake and not cooldown:
        spend = round(equity * M.get("size", SIZE_FRAC), 2)
        fee = spend * FEE
        qty = (spend - fee) / price
        L["cash"] -= spend
        L["btc"] = qty
        L["position"] = {"entry": price, "qty": qty, "opened": now.isoformat(timespec="minutes"),
                         "stop": round(r_stop if range_mode else price * (1 - M["stop"]), 2),
                         "tp": round(r_mid if range_mode else price * (1 + M["tp"]), 2),
                         "tp_done": False, "last_checked_ms": last[0], "realized": 0.0}
        if range_mode:
            L["position"].update(top=round(r_top, 2), range_low=round(rl, 2), range_high=round(rh, 2))
        L["trades"].append({"date": now.isoformat(timespec="minutes"), "side": "BUY",
                            "qty": round(qty, 8), "price": round(price, 2),
                            "fee": round(fee, 2), "pnl": 0.0,
                            "reason": "range bottom bounce" if range_mode else
                                      "oversold bounce" if dip_mode else "trend + dip signal"})
        actions.append(f"BOUGHT ${spend:.2f} of BTC at ${price:,.0f}")
        status = "BUY SIGNAL"
    elif weekly_brake:
        status = "WAIT (weekly loss limit)"
    elif cooldown:
        status = "WAIT (paused after 2 losses)"
    elif not fresh:
        status = "WAIT (just exited, next candle)"
    elif dip_mode:
        status = "GET READY (oversold, watching for a turn)" if r < 30 else "WAIT"
    elif range_mode:
        if not (width_ok and flat_ok):
            status = "WAIT (no clean range)"
        elif price <= rl + 0.4 * span:
            status = "GET READY (near range bottom)"
        else:
            status = "WAIT (price not near range bottom)"
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
            f"range ${rl:,.0f}-${rh:,.0f} ({width*100:.1f}% wide) {'ok' if width_ok else 'no'}",
            f"sideways {'yes' if flat_ok else 'no'}",
            f"in bottom quarter {'yes' if zone_ok else 'no'}",
            f"green bounce {'yes' if bounce_ok else 'no'}",
            f"reward 1.2x risk {'yes' if rr_ok else 'no'}",
            f"calm candle {'yes' if calm_ok else 'no'}",
            f"news {'OK' if news_ok else 'BLOCK'} ({news_why})",
        ] if range_mode else [
            f"RSI was <30 recently {'yes' if oversold_ok else 'no'}",
            f"turning up (RSI 30+, green candle) {'yes' if turn_ok else 'no'}",
        ] if dip_mode else [
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
