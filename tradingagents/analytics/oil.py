"""Oil brain: the state of the crude market from free daily series.

Inputs are daily frames (or Close series) keyed by role. Any may be missing; the
features that need it are then left out.

    "wti"    WTI front-month futures (Yahoo CL=F)
    "brent"  Brent front-month futures (BZ=F)
    "rbob"   RBOB gasoline futures, $/gal (RB=F)
    "ho"     heating oil futures, $/gal (HO=F)
    "uso"    USO fund, a rolled front-month position
    "ovx"    CBOE crude oil volatility index (^OVX)
    "usdcad" USD/CAD (CAD=X)
    "xle"    energy-sector equities (XLE)

Carry: CL=F is an unadjusted chain of front contracts, so on roll days it jumps by the
spread between contracts (up in contango, down in backwardation) while USO, which holds
the position through the roll, does not. Over a window, the USO return minus the WTI
chain return is therefore a running estimate of the roll yield: positive in
backwardation, negative in contango (checked: 2009 and 2020 super-contango negative,
2022 backwardation positive).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

GAL_PER_BBL = 42.0


def _close(x) -> pd.Series:
    if isinstance(x, pd.DataFrame):
        if "Date" in x.columns:
            x = x.set_index(pd.to_datetime(x["Date"]))
        x = x["Close"]
    return x.astype(float).sort_index()


def _z(s: pd.Series, n: int) -> pd.Series:
    return (s - s.rolling(n, min_periods=n // 2).mean()) / s.rolling(n, min_periods=n // 2).std()


def oil_features(frames: dict) -> pd.DataFrame:
    """One row per WTI trading day, using only data up to that day."""
    if "wti" not in frames:
        raise ValueError("oil_features needs at least the 'wti' series")
    s = {k: _close(v) for k, v in frames.items() if v is not None and len(v)}
    wti = s["wti"].where(s["wti"] > 0)  # April 2020 printed a negative front month
    idx = wti.index
    al = {k: v.reindex(idx).ffill(limit=3) for k, v in s.items()}
    f = pd.DataFrame(index=idx)
    f["wti"] = wti
    for n in (20, 50, 200):
        f[f"wti_vs_sma{n}"] = wti / wti.rolling(n).mean() - 1
    f["wti_ret_5d"] = wti.pct_change(5)
    f["wti_ret_20d"] = wti.pct_change(20)
    f["wti_ret_60d"] = wti.pct_change(60)
    f["wti_vol_20d"] = np.log(wti).diff().rolling(20).std() * np.sqrt(252)
    if "brent" in al:
        spread = al["brent"] - wti
        f["brent_wti_spread"] = spread
        f["brent_wti_z60"] = _z(spread, 60)
    if "rbob" in al and "ho" in al:
        crack = (2 * al["rbob"] * GAL_PER_BBL + al["ho"] * GAL_PER_BBL - 3 * wti) / 3
        f["crack_321"] = crack
        f["crack_321_z252"] = _z(crack, 252)
        f["crack_321_chg_20d"] = crack - crack.shift(20)
    if "uso" in al:
        lw, lu = np.log(wti), np.log(al["uso"])
        f["carry_60d"] = (lu.diff(60) - lw.diff(60)) * (252 / 60)
    if "ovx" in al:
        ovx = al["ovx"]
        f["ovx"] = ovx
        f["ovx_vs_20d"] = ovx / ovx.rolling(20).mean() - 1
        f["ovx_pct_rank"] = ovx.rolling(252, min_periods=60).rank(pct=True)
    if "usdcad" in al:
        cad = al["usdcad"]
        f["usdcad_ret_20d"] = cad.pct_change(20)
        f["oil_cad_corr_60d"] = np.log(wti).diff().rolling(60).corr(np.log(cad).diff())
    if "xle" in al:
        f["xle_minus_wti_20d"] = al["xle"].pct_change(20) - f["wti_ret_20d"]
    f["weekday"] = idx.dayofweek
    f["eia_day"] = f["weekday"] == 2  # weekly EIA inventory report is on Wednesdays (holiday weeks shift it)
    return f


def oil_regime(row: pd.Series) -> dict:
    """Plain labels for one feature row."""
    lab = {}
    t = row.get("wti_vs_sma200")
    lab["trend"] = "n/a" if pd.isna(t) else ("up" if t > 0 and row.get("wti_vs_sma50", 0) > 0 else
                                             "down" if t < 0 and row.get("wti_vs_sma50", 0) < 0 else "mixed")
    cy = row.get("carry_60d")
    lab["curve"] = "n/a" if cy is None or pd.isna(cy) else ("backwardation" if cy > 0.02 else "contango" if cy < -0.02 else "flat")
    ov = row.get("ovx_pct_rank")
    lab["oil_fear"] = "n/a" if ov is None or pd.isna(ov) else ("high" if ov > 0.8 else "low" if ov < 0.2 else "normal")
    cz = row.get("crack_321_z252")
    lab["refining_margin"] = "n/a" if cz is None or pd.isna(cz) else ("rich" if cz > 1 else "poor" if cz < -1 else "normal")
    bz = row.get("brent_wti_z60")
    lab["brent_wti"] = "n/a" if bz is None or pd.isna(bz) else ("wide" if bz > 1.5 else "narrow" if bz < -1.5 else "normal")
    return lab


def oil_report(frames: dict, as_of: str | pd.Timestamp | None = None) -> str:
    """Markdown summary of the latest oil state on or before ``as_of``."""
    f = oil_features(frames)
    if as_of is not None:
        f = f.loc[: pd.Timestamp(as_of)]
    f = f.dropna(subset=["wti"])
    if len(f) < 60:
        return "Not enough oil history for a read (need at least 60 daily bars)."
    r = f.iloc[-1]
    lab = oil_regime(r)

    def pct(k):
        v = r.get(k)
        return "n/a" if v is None or pd.isna(v) else f"{v * 100:+.1f}%"

    def num(k, fmt="{:.2f}"):
        v = r.get(k)
        return "n/a" if v is None or pd.isna(v) else fmt.format(v)

    rows = [
        ("WTI", num("wti"), f"vs 50-day {pct('wti_vs_sma50')}, vs 200-day {pct('wti_vs_sma200')}; trend {lab['trend']}"),
        ("Momentum", f"5d {pct('wti_ret_5d')}", f"20d {pct('wti_ret_20d')}, 60d {pct('wti_ret_60d')}"),
        ("Realised vol", pct("wti_vol_20d"), "20-day, annualised"),
        ("Curve (roll yield est.)", pct("carry_60d"), f"{lab['curve']} (USO minus WTI chain, 60d, annualised)"),
        ("Brent-WTI", num("brent_wti_spread", "${:.2f}"), f"z60 {num('brent_wti_z60')}; {lab['brent_wti']}"),
        ("3-2-1 crack", num("crack_321", "${:.2f}/bbl"), f"z252 {num('crack_321_z252')}; refining margin {lab['refining_margin']}"),
        ("OVX", num("ovx", "{:.1f}"), f"vs 20d {pct('ovx_vs_20d')}, 1y rank {num('ovx_pct_rank')}; oil fear {lab['oil_fear']}"),
        ("USD/CAD", f"20d {pct('usdcad_ret_20d')}", f"oil-CAD 60d corr {num('oil_cad_corr_60d')}"),
        ("Energy stocks vs oil", pct("xle_minus_wti_20d"), "XLE 20d return minus WTI 20d return"),
    ]
    out = [f"## Oil read for {f.index[-1].date()}", "", "| Gauge | Value | Detail |", "|---|---|---|"]
    out += [f"| {a} | {b} | {c} |" for a, b, c in rows]
    out += ["", "Wednesday is the weekly EIA inventory report." if bool(r.get("eia_day")) else "",
            "These are descriptive gauges, not a forecast; the lab's tested oil rules are in research/exness-lab."]
    return "\n".join(x for x in out if x is not None)
