#!/usr/bin/env python3
"""Backtest the paper-trading rules on recent Gemini BTC/USD history.

Replays history step by step through btc_paper.main(), exactly as the live
scheduled runs call it: every 2 hours for the 2-hour modes (5 minutes after
each candle closes, buying at the next hourly open) and once a day for the
daily mode. Each mode starts with $300 in a temporary folder, so the live
ledgers are not touched.

Limits:
  - News cannot be replayed, so the range mode assumes the news check passed.
  - Fills are idealised: stops and targets fill exactly at their price, and
    the 0.4% fee is the only cost (no slippage).
  - Gemini returns roughly 60 days of hourly and about a year of daily candles.

Usage: python3 paper/backtest.py [--out paper/backtest_results.md]
"""
import argparse
import contextlib
import datetime as dt
import io
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import btc_paper as bp  # noqa: E402

H = 3600 * 1000


def iso(ms):
    return dt.datetime.fromtimestamp(ms / 1000, dt.timezone.utc).isoformat()


def run_mode(mode, raw, steps, price_at, extra=(), daily=None):
    """Run one mode over the given step times; return stats."""
    with tempfile.TemporaryDirectory() as d:
        curve, start_price, end_price = [], None, None
        ledger = os.path.join(d, bp.MODES[mode]["ledger"])
        for t in steps:
            price = price_at(t)
            if price is None:
                continue
            start_price = start_price or price
            end_price = price
            argv = ["--mode", mode, "--price", str(price), "--now", iso(t + 5 * 60 * 1000),
                    "--dir", d, *extra]
            try:
                with contextlib.redirect_stdout(io.StringIO()):
                    bp.main(argv, raw_candles=raw, daily_candles=daily)
            except SystemExit:  # not enough history yet
                continue
            L = json.load(open(ledger))
            curve.append((t, L["cash"] + L["btc"] * price))
        L = json.load(open(ledger))
    trades = L["trades"]
    # group fills into round trips: a BUY starts one, sells add their P/L
    rounds, cur = [], None
    for tr in trades:
        if tr["side"] == "BUY":
            cur = {"pnl": 0.0, "fills": [tr]}
            rounds.append(cur)
        elif cur is not None:
            cur["pnl"] += tr["pnl"]
            cur["fills"].append(tr)
    closed = rounds if L["position"] is None else rounds[:-1]
    wins = [r for r in closed if r["pnl"] > 0]
    peak, mdd = 0.0, 0.0
    for _, e in curve:
        peak = max(peak, e)
        mdd = max(mdd, (peak - e) / peak)
    return {
        "mode": mode,
        "from": iso(curve[0][0])[:10] if curve else "-",
        "to": iso(curve[-1][0])[:10] if curve else "-",
        "final": curve[-1][1] if curve else 300.0,
        "trades": len(closed),
        "wins": len(wins),
        "max_dd": mdd * 100,
        "buy_hold": (end_price / start_price - 1) * 100 if start_price else 0.0,
        "open": L["position"] is not None,
        "rounds": rounds,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                  "backtest_results.md"))
    a = ap.parse_args()

    hourly = bp.fetch_json("https://api.gemini.com/v2/candles/btcusd/1hr")
    daily = bp.fetch_json("https://api.gemini.com/v2/candles/btcusd/1day")
    opens_h = {c[0]: c[1] for c in hourly}
    opens_d = {c[0]: c[1] for c in daily}

    h0, h1 = min(opens_h), max(opens_h)
    first_2h = h0 - h0 % (2 * H) + 2 * H
    steps_2h = list(range(first_2h, h1 + 1, 2 * H))
    d0, d1 = min(opens_d), max(opens_d)
    steps_d = list(range(d0, d1 + 1, 24 * H))

    oil, _ = bp.fetch_yahoo("CL=F", rng="730d")
    opens_o = {c[0]: c[1] for c in oil}
    o0, o1 = min(opens_o), max(opens_o)
    steps_o = list(range(o0 - o0 % (2 * H) + 2 * H, o1 + 1, 2 * H))

    results = [
        run_mode("2h", hourly, steps_2h, opens_h.get, daily=daily),
        dict(run_mode("2h", hourly, steps_2h, opens_h.get, ["--no-daily-filter"], daily=daily),
             mode="2h_raw"),
        run_mode("dip2h", hourly, steps_2h, opens_h.get),
        run_mode("range2h", hourly, steps_2h, opens_h.get, ["--assume-news-ok"]),
        run_mode("daily", daily, steps_d, opens_d.get),
        run_mode("oil_range2h", oil, steps_o, opens_o.get, ["--assume-news-ok"]),
        dict(run_mode("oil_range2h", oil, steps_o, opens_o.get, ["--assume-news-ok", "--no-oil-blackout"]),
             mode="oil_raw"),
    ]

    names = {"2h": "2-hour trend + daily filter", "2h_raw": "2-hour trend, no filter (old)", "dip2h": "Dip-buy (experiment)",
             "range2h": "Range (news assumed OK)", "daily": "Daily trend",
             "oil_range2h": "OIL range + blackouts (news assumed OK)",
             "oil_raw": "OIL range, no blackouts"}
    lines = ["# Backtest results", "",
             f"Run {dt.datetime.now(dt.timezone.utc):%Y-%m-%d %H:%M} UTC on Gemini BTC/USD history. "
             "Each account starts with $300 of paper money; 0.4% fee per fill, no slippage.", "",
             "| Strategy | Period | End balance | P/L | Trades | Wins | Worst drop | BTC buy & hold |",
             "|---|---|---|---|---|---|---|---|"]
    for r in results:
        pl = r["final"] - 300
        lines.append(f"| {names[r['mode']]} | {r['from']} to {r['to']} | ${r['final']:,.2f} | "
                     f"{pl:+.2f} ({pl / 3:+.1f}%) | {r['trades']}{' +1 open' if r['open'] else ''} | "
                     f"{r['wins']}/{r['trades']} | -{r['max_dd']:.1f}% | {r['buy_hold']:+.1f}% |")
    lines += ["", "## Trades", ""]
    for r in results:
        lines.append(f"### {names[r['mode']]}")
        if not r["rounds"]:
            lines.append("No trades.")
        for i, rd in enumerate(r["rounds"], 1):
            buy = rd["fills"][0]
            sells = "; ".join(f"{f['reason']} at ${f['price']:,.0f}" for f in rd["fills"][1:]) or "still open"
            lines.append(f"{i}. {buy['date'][:16]} bought at ${buy['price']:,.0f} -> {sells} "
                         f"(P/L {rd['pnl']:+.2f})")
        lines.append("")
    text = "\n".join(lines)
    with open(a.out, "w") as f:
        f.write(text)
    print(text)


if __name__ == "__main__":
    main()
