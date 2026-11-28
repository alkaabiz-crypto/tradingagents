"""Data-layer wrappers that feed Yahoo prices to the candle and oil brains.

The brains themselves (tradingagents.analytics) are pure computations; this module
only loads the frames, point-in-time, and hands them over.
"""

from __future__ import annotations

import pandas as pd

from tradingagents.analytics import candles, oil
from tradingagents.dataflows.errors import NoMarketDataError, VendorUnavailableError
from tradingagents.dataflows.symbols import normalize_symbol
from tradingagents.dataflows.vendors.yahoo.ohlcv import load_ohlcv

# Oil brain inputs: role -> Yahoo symbol.
OIL_SERIES = {
    "wti": "CL=F", "brent": "BZ=F", "rbob": "RB=F", "ho": "HO=F",
    "uso": "USO", "ovx": "^OVX", "usdcad": "CAD=X", "xle": "XLE",
}


def _rows(symbol: str, as_of_date: str) -> pd.DataFrame:
    data = load_ohlcv(symbol, as_of_date, fill_gaps=False)
    if data is None or data.empty:
        raise NoMarketDataError(symbol, normalize_symbol(symbol), "no price rows")
    df = data.copy()
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.dropna(subset=["Date", "Open", "High", "Low", "Close"])
    return df[df["Date"] <= pd.to_datetime(as_of_date)].sort_values("Date")


def build_candle_report(symbol: str, as_of_date: str, horizon: int = 2) -> str:
    """Candle read for ``symbol`` on the last bar on or before ``as_of_date``."""
    df = _rows(symbol, as_of_date)
    if df.empty:
        raise NoMarketDataError(symbol, normalize_symbol(symbol), f"no price rows on or before {as_of_date}")
    return f"# {symbol.upper()}\n" + candles.candle_report(df, horizon=horizon)


def build_oil_report(as_of_date: str) -> str:
    """Oil read on or before ``as_of_date``. Only WTI is required; other gauges drop out if missing."""
    frames, missing = {}, []
    for role, sym in OIL_SERIES.items():
        try:
            frames[role] = _rows(sym, as_of_date)
        except (NoMarketDataError, VendorUnavailableError):
            if role == "wti":
                raise
            missing.append(sym)
    report = oil.oil_report(frames, as_of=as_of_date)
    if missing:
        report += f"\n\nNot available for this read: {', '.join(missing)}."
    return report
