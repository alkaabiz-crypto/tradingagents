"""Trade costs for the user's Exness STANDARD SWAP-FREE account (see ACCOUNT.md). Import this in every new study.
No commission, no swap: the round-trip cost is the spread (+ slippage on stop exits).
SPREAD_BP values are ESTIMATES (round trip, basis points of price) until the user reads the real spreads in the app;
update them here when they do. Always also report results at 0/2/5/10 bp (ROUND_TRIPS_TO_REPORT).
"""
SWAP_PER_NIGHT = 0.0          # swap-free account
COMMISSION = 0.0              # Standard account
STOP_SLIPPAGE_BP = 2.0        # extra cost assumed on a stop exit (fast moves can be worse)
ROUND_TRIPS_TO_REPORT = (0, 2, 5, 10)

# Exness symbol, estimated round-trip spread in bp (ESTIMATE - replace with the app's numbers)
SPREAD_BP = {
    "USTEC": 1.5, "US500": 1.5, "US30": 2.0, "XAUUSD": 1.0, "XAGUSD": 6.0, "USOIL": 5.0, "UKOIL": 5.0,
    "XNGUSD": 15.0, "BTCUSD": 3.0, "ETHUSD": 5.0, "EURUSD": 1.5, "STOCK_CFD": 10.0,
}
YAHOO_TO_EXNESS = {"QQQ": "USTEC", "NQ=F": "USTEC", "SPY": "US500", "DIA": "US30", "GLD": "XAUUSD", "GC=F": "XAUUSD",
                   "SLV": "XAGUSD", "SI=F": "XAGUSD", "USO": "USOIL", "CL=F": "USOIL", "XLE": "USOIL", "BNO": "UKOIL",
                   "NG=F": "XNGUSD", "BTC-USD": "BTCUSD", "ETH-USD": "ETHUSD"}


def round_trip(yahoo_symbol, stop_exit=False):
    """Round-trip cost as a fraction of price for one trade on the user's account."""
    sym = YAHOO_TO_EXNESS.get(yahoo_symbol, "STOCK_CFD")
    return (SPREAD_BP[sym] + (STOP_SLIPPAGE_BP if stop_exit else 0.0)) / 1e4
