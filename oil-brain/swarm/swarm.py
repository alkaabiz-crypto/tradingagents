"""The swarm: 1,000+ rule-brains generated in code and tested together (pre-registered 2026-11-24).

Every rule is fixed by its family and parameters below BEFORE the run. Nothing is tuned.
Each rule makes a daily position in -1..+1 known at the close of day t; it earns close t -> t+1.
Costs: 5 bp per unit of turnover (10 bp for BTC/ETH). Post-2014 = OOS + HOLDOUT (engine.py splits).

Families x instruments x parameters:
  TS   time-series momentum: sign(ret over L), L in {5,10,21,42,63,126,252}, long/flat and long/short
  MA   price above its L-day average, L in {10,20,50,100,200}, long/flat and long/short
  X    fast/slow average cross (f,s) in {(5,20),(10,50),(20,100),(50,200)}, long/flat and long/short
  MR   mean reversion: z of the L-day return vs its 252-day spread, buy z < -k / sell z > k,
       L in {1,2,5}, k in {1,1.5,2}, long/flat and long/short
  BO   breakout: close above the L-day high -> long until close below the L/2-day low, L in {20,55,100}
  DOW  long only on one weekday (5 rules) per instrument
  TOM  turn of month: long last n and first m trading days, (n,m) in {(1,3),(3,3),(2,0),(0,3)}
  CA   cross-asset signal S -> trade instrument I: sign of S's L-day return (or minus it),
       S in {VIX, HYG/LQD, TLT, GLD, UUP, USO, SPY, DBB/GLD, TNX}, L in {5,21,63}
Instruments: SPY QQQ IWM DIA USO XLE XOP UNG GLD SLV TLT IEF HYG DBC XLF XLK XLU XLV XLP XLY XLI XLB BTC ETH

Multiple testing (the point of the swarm): White's (2000) Reality Check / Romano & Wolf (2005)
max statistic. For B = 300 random circular time shifts k (the SAME k for every rule, so the
dependence between rules is kept), compute every rule's post-2014 t-stat and keep the MAXIMUM.
The 95th percentile of that maximum is the luck bar for "best of N rules". A rule is a swarm
winner only if its real post-2014 t beats that bar AND OOS > 0 AND HOLDOUT > 0 AND it beats its
instrument's buy-and-hold Sharpe. Also reported: Bailey & López de Prado (2014) expected maximum
Sharpe under the null for N trials.
"""
import os, glob, itertools, json
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
B = os.path.dirname(HERE)
paths = {}
for f in glob.glob(os.path.join(B, "data", "*.csv")) + glob.glob(os.path.join(B, "brains", "*", "data", "*.csv")):
    paths.setdefault(os.path.basename(f)[:-4], f)

def px(sym):
    df = pd.read_csv(paths[sym], index_col=0, parse_dates=True)
    s = df["Close"] if "Close" in df else df.iloc[:, 0]
    s.index = pd.to_datetime(s.index).tz_localize(None).normalize()
    return s[~s.index.duplicated()].astype(float)

INSTR = ["SPY","QQQ","IWM","DIA","USO","XLE","XOP","UNG","GLD","SLV","TLT","IEF","HYG","DBC",
         "XLF","XLK","XLU","XLV","XLP","XLY","XLI","XLB","BTC-USD","ETH-USD"]
INSTR = [s for s in INSTR if s in paths]
# Common NYSE calendar from SPY; crypto is sampled on it too (weekend moves land on Monday).
cal = px("SPY").loc["2003-01-01":].index
P = pd.DataFrame({s: px(s).reindex(cal, method="ffill", limit=5) for s in INSTR})
R = P.pct_change()
SIG = {}
for k in ["VIX","TLT","GLD","UUP","USO","SPY","TNX"]:
    if k in paths: SIG[k] = px(k).reindex(cal, method="ffill", limit=5)
if "HYG" in paths and "LQD" in paths:
    SIG["HYG/LQD"] = (px("HYG") / px("LQD")).reindex(cal, method="ffill", limit=5)
if "DBB" in paths:
    SIG["DBB/GLD"] = (px("DBB") / px("GLD")).reindex(cal, method="ffill", limit=5)

rules = {}  # name -> (instrument, position series)
def add(name, inst, pos):
    rules[name] = (inst, pos.reindex(cal).fillna(0).clip(-1, 1))

dow = pd.Series(cal.day_of_week, index=cal)
mon = pd.Series(cal.to_period("M"), index=cal)
rank_in_month = pd.Series(1, index=cal).groupby(mon).cumsum()
left_in_month = pd.Series(1, index=cal).groupby(mon).transform("sum") - rank_in_month

for s in INSTR:
    p = P[s]; r = R[s]
    for L in (5,10,21,42,63,126,252):
        sg = np.sign(p.pct_change(L))
        add(f"TS{L} LF {s}", s, (sg > 0).astype(float)); add(f"TS{L} LS {s}", s, sg)
    for L in (10,20,50,100,200):
        up = (p > p.rolling(L).mean())
        add(f"MA{L} LF {s}", s, up.astype(float)); add(f"MA{L} LS {s}", s, up.astype(float)*2-1)
    for f_, s_ in ((5,20),(10,50),(20,100),(50,200)):
        up = p.rolling(f_).mean() > p.rolling(s_).mean()
        add(f"X{f_}/{s_} LF {s}", s, up.astype(float)); add(f"X{f_}/{s_} LS {s}", s, up.astype(float)*2-1)
    for L in (1,2,5):
        rr = p.pct_change(L); z = rr / rr.rolling(252).std()
        for k in (1,1.5,2):
            lf = (z < -k).astype(float); ls = lf - (z > k).astype(float)
            add(f"MR{L} k{k} LF {s}", s, lf); add(f"MR{L} k{k} LS {s}", s, ls)
    for L in (20,55,100):
        hi = p.rolling(L).max().shift(1); lo = p.rolling(L//2).min().shift(1)
        st = pd.Series(np.nan, index=cal); st[p > hi] = 1; st[p < lo] = 0
        add(f"BO{L} {s}", s, st.ffill().fillna(0))
    for d in range(5):  # long on weekday d: hold from the previous close
        add(f"DOW{d} {s}", s, (dow.shift(-1) == d).astype(float))
    for n, m in ((1,3),(3,3),(2,0),(0,3)):
        hold = ((left_in_month.shift(-1) < n) | (rank_in_month.shift(-1) <= m)).astype(float)
        add(f"TOM{n}/{m} {s}", s, hold)
    for k, S in SIG.items():
        for L in (5,21,63):
            sg = np.sign(S.pct_change(L))
            add(f"CA {k}{L}+ -> {s}", s, sg); add(f"CA {k}{L}- -> {s}", s, -sg)

names = list(rules)
N = len(names)
inst_idx = np.array([INSTR.index(rules[n][0]) for n in names])
POS = np.column_stack([rules[n][1].values for n in names])          # T x N
RET = R.fillna(0).values[:, inst_idx]                               # T x N
cost = np.where(np.isin(inst_idx, [INSTR.index(c) for c in ("BTC-USD","ETH-USD") if c in INSTR]), 10, 5) / 1e4
TURN = np.abs(np.diff(POS, axis=0, prepend=0))
post = cal >= "2014-01-01"; oos = (cal >= "2014-01-01") & (cal <= "2019-12-31"); ho = cal >= "2020-01-01"
avail = ~np.isnan(R.values[:, inst_idx])                            # instrument trading yet?

def pnl(pos):
    pl = np.zeros_like(pos)
    pl[1:] = pos[:-1] * RET[1:] - TURN[:-1] * cost
    return np.where(avail, pl, np.nan)

def stats(pl, mask):
    x = pl[mask]
    m = np.nanmean(x, 0); sd = np.nanstd(x, 0); n = np.sum(~np.isnan(x), 0)
    with np.errstate(invalid="ignore", divide="ignore"):
        return m / sd * np.sqrt(252), m / sd * np.sqrt(n)

PL = pnl(POS)
sh_post, t_post = stats(PL, post); sh_oos, _ = stats(PL, oos); sh_ho, _ = stats(PL, ho)
BH = np.where(avail, RET, np.nan); bh_post, _ = stats(BH, post)

rng = np.random.default_rng(2026)
T = len(cal); maxt = []
for _ in range(300):
    k = int(rng.integers(T // 10, T - T // 10))
    _, tt = stats(pnl(np.roll(POS, k, axis=0)), post)
    maxt.append(np.nanmax(tt))
bar = float(np.quantile(maxt, 0.95))

# Bailey & Lopez de Prado (2014): expected max Sharpe of N independent null trials (approx).
from math import e
g = 0.5772
sd_sh = np.nanstd(sh_post)
exp_max_sh = sd_sh * ((1 - g) * np.sqrt(2 * np.log(N)) + g * np.sqrt(2 * np.log(N * e)) / np.sqrt(2 * np.log(N))) if N > 1 else np.nan

df = pd.DataFrame(dict(rule=names, inst=[rules[n][0] for n in names], OOS=sh_oos, HOLDOUT=sh_ho,
                       post=sh_post, bh_post=bh_post, t_post=t_post)).set_index("rule")
df["swarm_winner"] = (df.t_post > bar) & (df.OOS > 0) & (df.HOLDOUT > 0) & (df.post > df.bh_post)
df["passes_t3_only"] = (df.t_post >= 3) & (df.OOS > 0) & (df.HOLDOUT > 0) & (df.post > df.bh_post)
df.sort_values("t_post", ascending=False).round(3).to_csv(os.path.join(HERE, "swarm_results.csv"))
summary = dict(rules=N, instruments=len(INSTR), luck_bar_t95=round(bar, 2),
               luck_max_t_median=round(float(np.median(maxt)), 2),
               expected_max_sharpe_null=round(float(exp_max_sh), 2),
               n_t3_and_beats_bh=int(df.passes_t3_only.sum()), n_swarm_winners=int(df.swarm_winner.sum()))
json.dump(summary, open(os.path.join(HERE, "swarm_summary.json"), "w"), indent=1)
print(json.dumps(summary, indent=1))
print("\nTop 15 by post-2014 t (after costs):")
print(df.sort_values("t_post", ascending=False).head(15).round(2).to_string())
print("\nSwarm winners:"); print(df[df.swarm_winner].round(2).to_string() if df.swarm_winner.any() else "none")
