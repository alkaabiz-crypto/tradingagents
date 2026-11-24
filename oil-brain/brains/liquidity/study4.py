"""Study 4 (pre-registered 2026-11-24, before running): funding / credit liquidity proxies available on Yahoo.
Mechanisms: when funding and credit liquidity tighten, intermediaries cut risk (Brunnermeier & Pedersen 2009 RFS);
broker-dealer / speculator risk capacity drives commodity futures premia (Etula 2013; Acharya, Lochstoer &
Ramadorai 2013 JFE); credit spreads carry forward-looking risk information (Gilchrist & Zakrajsek 2012 AER).
The short rate relative to its 12-month average negatively predicts stock returns (Campbell 1991; Ang & Bekaert 2007 RFS).
Proxies: credit = HYG minus LQD total return over 21 days (high yield vs investment grade);
relative bill rate = ^IRX minus its 252-day mean. 5 bp per turnover.
 F1 SPY: credit (HYG-LQD 21d) >= 0 -> long SPY, < 0 -> flat. Weekly (last close of the week) rebalance. Start 2007-06.
 F2 SPY: relative bill rate <= 0 -> long SPY, > 0 -> flat. Month-end rebalance. Start 1995.
 F3 USO: credit >= 0 -> long USO, < 0 -> short USO. Weekly rebalance. Start 2007-06.
IS for F1/F3 is short (mid-2007 to 2013, includes 2008), noted as a weakness up front.
"""
import numpy as np, pandas as pd
from lib import ld, evaluate, table
spy = ld("SPY"); rs = spy.pct_change(); uso = ld("USO"); ru = uso.pct_change()
cred = (ld("HYG").pct_change(21) - ld("LQD").pct_change(21))
irx = ld("IRX"); rb = irx - irx.rolling(252).mean()
def at(sig, idx, freq):
    sig = sig.reindex(idx).ffill()
    ends = idx.to_series().groupby(idx.to_period(freq)).last().values
    return sig.loc[ends].reindex(idx).ffill()
rows = [evaluate("F1 SPY long when HY beats IG (21d), weekly", at((cred >= 0).astype(float).where(cred.notna()), rs.index, "W"), rs, start="2007-06-01"),
        evaluate("F2 SPY long when bill rate below 1y mean, monthly", at((rb <= 0).astype(float).where(rb.notna()), rs.index, "M"), rs, start="1995-01-01"),
        evaluate("F3 USO long/short on HY-IG credit, weekly", at(np.sign(cred).where(cred.notna()), ru.index, "W"), ru, start="2007-06-01")]
print(table(rows))
print("latest: HYG-LQD 21d %+.4f, relative bill rate %+.3f" % (cred.dropna().iloc[-1], rb.dropna().iloc[-1]))
