#!/usr/bin/env python3
"""Download long hourly WTI oil history from Dukascopy's free data feed.

Instrument LIGHTCMDUSD (WTI crude oil CFD), BID hourly candles, one LZMA file
per month: https://datafeed.dukascopy.com/datafeed/LIGHTCMDUSD/YYYY/MM-1/BID_candles_hour_1.bi5
Each record is 24 bytes: seconds from month start, open, close, low, high
(prices x1000, big-endian ints) and volume (float). Candles with zero volume
are market-closed filler and are dropped. The feed rate-limits, so requests
are spaced out and 429 answers are retried after a pause. Months already
downloaded are cached.

Usage: python3 paper/dukascopy_oil.py --out DIR [--start 2010]
Writes DIR/wti_hourly.json as a list of [unix_seconds, open, high, low, close, volume].
"""
import argparse
import datetime as dt
import json
import lzma
import os
import struct
import time
import urllib.error
import urllib.request

BASE = "https://datafeed.dukascopy.com/datafeed/LIGHTCMDUSD"


def fetch_month(y, m, cache):
    path = os.path.join(cache, f"{y}-{m:02d}.bi5")
    if os.path.exists(path):
        return open(path, "rb").read()
    url = f"{BASE}/{y}/{m - 1:02d}/BID_candles_hour_1.bi5"
    for attempt in range(15):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Referer": "https://www.dukascopy.com/"})
            with urllib.request.urlopen(req, timeout=30) as r:
                data = r.read()
            open(path, "wb").write(data)
            time.sleep(8)
            return data
        except urllib.error.HTTPError as e:
            if e.code == 404:
                open(path, "wb").write(b"")
                return b""
            time.sleep(min(60 * (attempt + 1), 600))
        except Exception:                       # connection reset while blocked
            time.sleep(min(60 * (attempt + 1), 600))
    raise RuntimeError(f"could not download {y}-{m:02d}")


def decode(raw, y, m):
    if not raw:
        return []
    x = lzma.decompress(raw, format=lzma.FORMAT_ALONE)
    t0 = int(dt.datetime(y, m, 1, tzinfo=dt.timezone.utc).timestamp())
    out = []
    for k in range(len(x) // 24):
        s, o, c, l, h, v = struct.unpack(">5if", x[k * 24:k * 24 + 24])
        if v > 0:
            out.append([t0 + s, o / 1000, h / 1000, l / 1000, c / 1000, v])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--start", type=int, default=2010)
    a = ap.parse_args()
    cache = os.path.join(a.out, "cache")
    os.makedirs(cache, exist_ok=True)
    now = dt.datetime.now(dt.timezone.utc)
    rows = []
    y, m = a.start, 1
    while (y, m) < (now.year, now.month):          # the current month is not published yet
        rows += decode(fetch_month(y, m, cache), y, m)
        print(f"{y}-{m:02d}: {len(rows)} candles so far", flush=True)
        m += 1
        if m == 13:
            y, m = y + 1, 1
    json.dump(rows, open(os.path.join(a.out, "wti_hourly.json"), "w"))
    print("done", len(rows))


if __name__ == "__main__":
    main()
