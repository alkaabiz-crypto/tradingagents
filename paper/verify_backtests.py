import sys, random, datetime as dt
sys.path.insert(0, '/home/user/tradingagents/paper')
import anomaly_study as A
from anomaly_study2 import common, trend_rule_positions
from anomaly_study3 import vol_managed, CRYPTO_START
from anomaly_study4 import sma_filter
import statistics as st

def delay(pos, k=1):          # execute k extra days late
    return [0.0]*k + pos[:-k]

def run(name, r, pos, bench, cost, py):
    e  = A.evaluate(name, r, pos, bench, cost, py)
    e2 = A.evaluate(name, r, delay(pos), bench, cost, py)
    print(f"{name}: Sharpe {e['all']['sharpe']:.2f} (bench {e['b']['sharpe']:.2f}) | 1 day late: {e2['all']['sharpe']:.2f}, "
          f"halves {e2['h1']['sharpe']:.2f}/{e2['h2']['sharpe']:.2f} vs {e2['b1']['sharpe']:.2f}/{e2['b2']['sharpe']:.2f}, pass={e2['passed']}")

# 1) sanity: buy-and-hold numbers
for s, start in (("SPY", 946684800), ("BTC-USD", int(dt.datetime(2014,9,17,tzinfo=dt.timezone.utc).timestamp()))):
    d, ds, R = common([s], start)
    c0, c1 = d[s][ds[0]]["c"], d[s][ds[-1]]["c"]
    yrs = (ds[-1]-ds[0]).days/365.25
    print(f"sanity {s}: {ds[0]} {c0:.2f} -> {ds[-1]} {c1:.2f} = {((c1/c0)**(1/yrs)-1)*100:+.1f}%/yr")

# 2) one-day-late execution (catches look-ahead / same-bar cheating)
d, ds, R = common(["SPY"]); r = R["SPY"]
run("#8 vol-managed SPY", r, vol_managed(r, ds, .15, 252), r, .0005, 252)
vm = vol_managed(r, ds, .15, 252); f = sma_filter(d, ds, "SPY")
run("#10 vol+200d SPY", r, [a*b for a,b in zip(vm,f)], r, .0005, 252)
d, ds, R = common(["QQQ"]); r = R["QQQ"]
run("#9 vol-managed QQQ", r, vol_managed(r, ds, .15, 252), r, .0005, 252)
d, ds, R = common(["GLD"]); r = R["GLD"]
run("#11 vol-managed GLD", r, vol_managed(r, ds, .15, 252), r, .0005, 252)
for s in ("BTC-USD", "ETH-USD"):
    d, ds, R = common([s], CRYPTO_START if s=="ETH-USD" else int(dt.datetime(2014,9,17,tzinfo=dt.timezone.utc).timestamp()))
    p, r = trend_rule_positions(d, ds, s, 365)
    run(f"#{6 if s=='BTC-USD' else 7} trend {s}", r, p, r, .001, 365)

# 3) risk parity: fair luck check (all weights slid together, so they still add to 100%)
d, ds, R = common(["SPY","TLT","GLD"]); F=("SPY","TLT","GLD")
me=set(A.month_ends(ds)); cur={}; W=[]
for i in range(len(ds)):
    W.append(dict(cur))
    if i in me and i>=63:
        inv={s:1/st.pstdev(R[s][i-62:i+1]) for s in F}; t=sum(inv.values()); cur={s:inv[s]/t for s in F}
P=[[w.get(s,0.) for w in W] for s in F]
def port(P):
    cols=[A.strat_returns(R[s],p,.0005) for s,p in zip(F,P)]; return [sum(x) for x in zip(*cols)]
real=A.metrics(port(P),252)["sharpe"]; rng=random.Random(1); beat=0
for _ in range(500):
    k=rng.randrange(1,len(ds)); beat+= real > A.metrics(port([p[k:]+p[:k] for p in P]),252)["sharpe"]
eq=[[1/3]*len(ds) for _ in F]
print(f"#12 risk parity Sharpe {real:.2f}; fair luck check {beat/500:.0%}; equal 1/3 each (no vol weighting) Sharpe {A.metrics(port(eq),252)['sharpe']:.2f}")
d2=[[0.]+p[:-1] for p in P]
print(f"#12 risk parity 1 day late Sharpe {A.metrics(port(d2),252)['sharpe']:.2f}")
