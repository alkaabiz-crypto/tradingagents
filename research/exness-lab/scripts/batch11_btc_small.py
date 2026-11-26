"""Batch 11, pre-registered 2026-11-26 before running. BTC strategies that fit a $228 Exness swap-free balance.
Only BTCUSD fits the balance (min 0.01 lot = 0.01 BTC, ~$584 exposure = 2.6x leverage at $228); XAUUSD 0.01 = 1 oz
(~$3,450, 15x) and the indexes need $1,000+. So every rule is long/flat (or short) at a FIXED 0.01 lot.
Costs: 3 bp round trip (spread ~$6.40 + slippage) and 2 bp extra on stop entries; sensitivity at 10 bp.
Rules (new trials 6; 2 are re-measures of known passes):
 1 Williams breakout k=0.5, weekdays only (known lead)       2 = 1 but only when 12-month momentum is long
 3 = 1 but only when MACD(12,26,9) is above its signal      4 Buy the close after a day down > 5%, sell next close
 5 = 4 but only above the 200-day                           6 MACD long-only (known pass)
 7 12-month momentum long/flat, monthly (known pass)        8 MACD AND 12-month momentum both long
 9 12-month momentum long/short, monthly
Report: Sharpe 2014-19/2020-23/2024-now, $ at 0.01 lot 2024-now (fixed lot, real prices), worst $ drop 2024-now,
worst day $, full-history worst drop in % of exposure x today's $584 exposure, and that drop as % of $228.
PASS bar as famous2 (Sharpe > 0.3 all three periods, post-2014 > buy-and-hold, t >= 2).
"""
import sys, numpy as np, pandas as pd
sys.path.insert(0, sys.argv[2]); import famous2_lib as F
d = pd.read_csv(f"{sys.argv[1]}/BTC-USD.csv", parse_dates=["Date"], index_col="Date").dropna()
c, h, l, o = d.Close, d.High, d.Low, d.Open; ann = 365
def sh(x): x = x.dropna(); return x.mean() / x.std() * np.sqrt(ann) if len(x) > 30 and x.std() > 0 else np.nan
m = pd.Series(c.index.to_period("M"), index=c.index); me = m != m.shift(-1)
ts = pd.Series(np.where(me, np.sign(c / c.shift(365) - 1), np.nan), index=c.index).ffill().fillna(0)
ts_long = (ts > 0).astype(float)
macd = c.ewm(span=12, adjust=False).mean() - c.ewm(span=26, adjust=False).mean(); sig = macd.ewm(span=9, adjust=False).mean()
mac = (macd > sig).astype(float); s200 = c.rolling(200).mean()
def run(bp):
    cost = bp / 1e4; R = (h - l).shift(); trig = o + 0.5 * R; hit = h >= trig
    wr = pd.Series(np.where(hit, c / np.maximum(trig, o) * (1 - 2e-4) - 1 - cost, 0.0), index=c.index).fillna(0)
    wd = c.index.dayofweek < 5
    # $ version at 0.01 lot: 0.01 * (close - fill) - cost * notional
    wd_usd = pd.Series(np.where(hit, 0.01 * (c - np.maximum(trig, o) * (1 + 2e-4)) - cost * 0.01 * c, 0.0), index=c.index).fillna(0)
    def pos_ret(p):
        p = p.fillna(0); r = c.pct_change().fillna(0)
        turn = p.diff().abs().fillna(0)
        pct = p.shift().fillna(0) * r - turn.shift().fillna(0) * cost / 2
        usd = p.shift().fillna(0) * 0.01 * c.diff().fillna(0) - turn.shift().fillna(0) * cost / 2 * 0.01 * c.shift()
        return pct, usd.fillna(0)
    S = {}
    S["1 Williams weekdays"] = (wr.where(wd, 0), wd_usd.where(wd, 0))
    f = ts_long.shift().fillna(0) > 0; S["2 Williams weekdays + 12m momentum"] = (wr.where(wd & f, 0), wd_usd.where(wd & f, 0))
    f = mac.shift().fillna(0) > 0; S["3 Williams weekdays + MACD"] = (wr.where(wd & f, 0), wd_usd.where(wd & f, 0))
    big = c.pct_change() < -0.05
    S["4 Buy after -5% day, 1 day"] = pos_ret(big.astype(float))
    S["5 Buy after -5% day above 200-day"] = pos_ret((big & (c > s200)).astype(float))
    S["6 MACD long-only"] = pos_ret(mac)
    S["7 12m momentum long/flat"] = pos_ret(ts_long)
    S["8 MACD and 12m momentum"] = pos_ret(mac * ts_long)
    S["9 12m momentum long/short"] = pos_ret(ts)
    S["Buy and hold"] = pos_ret(pd.Series(1.0, index=c.index))
    rows = []
    for nm, (x, u) in S.items():
        x = x.loc["2014":]; u = u.loc["2014":]
        eq = (1 + x).cumprod(); dd = (eq / eq.cummax() - 1).min()
        ur = u.loc["2024":]; ue = ur.cumsum(); udd = (ue - ue.cummax()).min()
        rows.append(dict(rule=nm, s14_19=sh(x.loc[:"2019"]), s20_23=sh(x.loc["2020":"2023"]), s24=sh(x.loc["2024":]),
                         post14=sh(x), t=sh(x) * np.sqrt(len(x) / ann), usd24=ur.sum(), usd_dd24=udd, worst_day=ur.min(),
                         hist_dd_usd=dd * 584, hist_dd_pct228=dd * 584 / 228 * 100, days_in=(x != 0).mean()))
    df = pd.DataFrame(rows); bh = df.loc[df.rule == "Buy and hold", "post14"].iloc[0]
    df["PASS"] = (df.s14_19 > .3) & (df.s20_23 > .3) & (df.s24 > .3) & (df.post14 > bh) & (df.t >= 2)
    return df
for bp in (3, 10):
    print(f"\n## cost {bp} bp round trip"); print(run(bp).round(2).to_string(index=False))
