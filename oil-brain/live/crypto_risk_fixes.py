"""Risk fixes for the crypto trend demo ticket (pre-registered 2026-11-26, before any run; the user asked "can u fix
these" about the remaining risks). Base = the frozen ticket rule: BTC+ETH, SMA50 direction, stop 0.5 ATR, size
min(1, 2%/ATR%), UTC open to UTC close, costs.py.
1) SLIPPAGE STRESS (measures, cannot fix): stop fills worse by 2 (base), 10, 25, 50 bp. Does it still make money?
2) SMALLER RISK: size min(1, 1%/ATR%) (half the size).
3) DRAWDOWN BRAKE: trade half size while the equity is more than 10% below its peak (back to full when it recovers).
   "Helps" only if Sharpe AND return/worst-drop are better than the base in BOTH 2014-21 and 2022+.
4) KILL SWITCH for the demo (fixed now, before any live result): stop the ticket and review if the demo record is
   down more than 15% from its peak, or after 60 coin-days the average day is below 0.
Research, not financial advice.    python3 oil-brain/live/crypto_risk_fixes.py
"""
import os, sys
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); OB = os.path.dirname(HERE)
sys.path.insert(0, HERE); sys.path.insert(0, OB)
import costs
import crypto_trend_opt as C


def run(slip_bp=2.0, risk=0.02, brake=False):
    costs.STOP_SLIPPAGE_BP = slip_bp
    parts = []
    for sym in ("BTC-USD", "ETH-USD"):
        r = C.coin(sym, "SMA50", 0.5, "vol", "none") * (risk / 0.02)   # vol size scales linearly while < 1
        parts.append(r)
    r = pd.concat(parts, axis=1).mean(axis=1).dropna()
    if brake:
        out, eq, peak = [], 1.0, 1.0
        for x in r.values:
            m = 0.5 if eq < 0.9 * peak else 1.0
            eq *= 1 + m * x; peak = max(peak, eq); out.append(m * x)
        r = pd.Series(out, index=r.index)
    costs.STOP_SLIPPAGE_BP = 2.0
    return r


def table(rows):
    out = []
    for name, r in rows:
        for per, m in (("2014-21", r.index < "2022-01-01"), ("2022+", r.index >= "2022-01-01")):
            out.append(dict(version=name, period=per, **C.stats(r[m])))
    return pd.DataFrame(out)


def main():
    pd.set_option("display.width", 200)
    s = table([(f"stop slippage {b} bp", run(slip_bp=b)) for b in (2, 10, 25, 50)])
    print("1) Slippage stress:"); print(s.round(2).to_string(index=False))
    f = table([("BASE 2% vol", run()), ("half size 1% vol", run(risk=0.01)), ("drawdown brake", run(brake=True))])
    print("\n2-3) Smaller risk and drawdown brake:"); print(f.round(2).to_string(index=False))
    b = f[f.version == "BASE 2% vol"].set_index("period")
    for v in ("drawdown brake",):
        q = f[f.version == v].set_index("period")
        ok = all(q.sharpe[p] > b.sharpe[p] and q.MAR[p] > b.MAR[p] for p in b.index)
        print(f"{v}: {'HELPS' if ok else 'does not help'}")
    pd.concat([s, f]).to_csv(os.path.join(HERE, "crypto_risk_fixes_results.csv"), index=False)


if __name__ == "__main__":
    main()
