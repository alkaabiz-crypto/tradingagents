"""Candle and oil brains: pattern detection, point-in-time stats, carry sign, and the agent tools."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from tradingagents.analytics import candles, oil


def _bars(rows, start="2025-01-01"):
    idx = pd.bdate_range(start, periods=len(rows))
    return pd.DataFrame(rows, columns=["Open", "High", "Low", "Close"], index=idx)


def _random_walk(n=400, seed=1):
    rng = np.random.default_rng(seed)
    c = 100 * np.exp(np.cumsum(rng.normal(0, 0.01, n)))
    o = np.r_[c[0], c[:-1]] * (1 + rng.normal(0, 0.002, n))
    h = np.maximum(o, c) * (1 + np.abs(rng.normal(0, 0.004, n)))
    l = np.minimum(o, c) * (1 - np.abs(rng.normal(0, 0.004, n)))
    return pd.DataFrame({"Open": o, "High": h, "Low": l, "Close": c}, index=pd.bdate_range("2020-01-01", periods=n))


@pytest.mark.unit
class TestCandlePatterns:
    def test_hammer_inside_bar_and_engulfing(self):
        d = _bars([
            (100, 101, 99, 100.5),
            (100.5, 100.8, 95, 100.6),   # long lower wick, close near the top: hammer
            (100.5, 100.7, 96, 100.0),   # inside the hammer's range
            (100.0, 100.2, 98, 98.5),    # red bar
            (98.0, 101.0, 97.9, 100.5),  # opens below, closes above the red body: bull engulfing
        ])
        p = candles.detect_patterns(d)
        assert p["hammer"].iloc[1]
        assert p["inside_bar"].iloc[2]
        assert p["bull_engulfing"].iloc[4]
        assert not p["bull_engulfing"].iloc[3]

    def test_nr4_is_the_narrowest_of_four(self):
        d = _bars([(100, 103, 97, 100), (100, 102, 98, 100), (100, 101.5, 98.5, 100), (100, 100.5, 99.5, 100)])
        assert candles.detect_patterns(d)["nr4"].iloc[3]

    def test_stats_never_use_bars_after_as_of(self):
        d = _random_walk()
        cut = d.index[250]
        early = candles.pattern_stats(d, "inside_bar", 2, as_of=cut)
        trimmed = candles.pattern_stats(d.loc[:cut], "inside_bar", 2)
        assert early == trimmed

    def test_unknown_pattern_is_rejected(self):
        with pytest.raises(ValueError):
            candles.pattern_stats(_random_walk(), "not_a_pattern")

    def test_report_names_context_and_needs_history(self):
        d = _random_walk()
        rep = candles.candle_report(d)
        assert "Context:" in rep and "Patterns on this bar" in rep
        assert "Not enough" in candles.candle_report(d.iloc[:10])


@pytest.mark.unit
class TestOilBrain:
    def test_carry_is_negative_in_contango(self):
        # A rolled position (USO) drifts down while the unadjusted front chain jumps up at
        # each monthly roll: that is contango, so the carry estimate must be negative.
        idx = pd.bdate_range("2020-01-01", periods=300)
        uso = pd.Series(100 * np.exp(-0.0004 * np.arange(300)), index=idx)
        jumps = np.cumsum([(i % 21 == 0) * 0.008 for i in range(300)])
        wti = pd.Series(50 * np.exp(np.log(uso / 100) + jumps), index=idx)
        f = oil.oil_features({"wti": wti, "uso": uso})
        assert f["carry_60d"].dropna().iloc[-1] < 0
        assert oil.oil_regime(f.iloc[-1])["curve"] == "contango"

    def test_report_works_with_wti_only_and_needs_wti(self):
        d = _random_walk(300)
        assert "Oil read for" in oil.oil_report({"wti": d})
        with pytest.raises(ValueError):
            oil.oil_features({"uso": d})


@pytest.mark.unit
class TestBrainTools:
    def test_tools_hide_trade_date_and_cap_at_it(self, monkeypatch):
        import tradingagents.dataflows.vendors.yahoo.brains as brains
        from tradingagents.agents import tools

        for t in (tools.get_candle_patterns, tools.get_oil_context):
            assert "trade_date" not in t.tool_call_schema.model_json_schema()["properties"]

        d = _random_walk().reset_index().rename(columns={"index": "Date"})
        future = pd.DataFrame({"Date": [pd.Timestamp("2030-01-02")], "Open": [999.0], "High": [999.0], "Low": [999.0], "Close": [999.0]})
        monkeypatch.setattr(brains, "load_ohlcv", lambda s, day, fill_gaps=True: pd.concat([d, future], ignore_index=True))
        day = str(d.Date.iloc[-1].date())
        out = tools.get_candle_patterns.func("SPY", "2031-01-01", trade_date=day)
        assert f"Candle read for {day}" in out and "999" not in out
        assert "Oil read for" in tools.get_oil_context.func("2031-01-01", trade_date=day)

    def test_market_analyst_offers_the_brains(self):
        from tradingagents.agents.analysts import market_analyst

        names = {t.name for t in market_analyst.TOOLS}
        assert {"get_candle_patterns", "get_oil_context"} <= names
