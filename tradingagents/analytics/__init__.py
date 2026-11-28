"""Deterministic market 'brains': pure pandas analytics with no vendor calls.

The data layer fetches prices; these modules only compute from the frames they are
given, so they are safe to use in backtests and inside agent tools alike.
"""
