import numpy as np, sys
HERE = '/tmp/claude-0/-home-user/8b993c28-efa9-5855-8d47-a8a3f974ffea/scratchpad/oil/oil-brain/btc_research/risk'
R = np.load(f'{HERE}/r2019.npy'); N = len(R)
TPY = 10  # 80 trades / 7.9 yrs = 10.1 per year
rng = np.random.default_rng(42); SIMS = 10000; BLOCK = 5
haircut = float(sys.argv[1]) if len(sys.argv) > 1 else 0.0  # subtract from every R (stress)
R = R - haircut

def iid(n): return R[rng.integers(0, N, size=(SIMS, n))]
def block(n):
    nb = -(-n // BLOCK); starts = rng.integers(0, N, size=(SIMS, nb))
    idx = (starts[:, :, None] + np.arange(BLOCK)) % N
    return R[idx.reshape(SIMS, -1)[:, :n]]

def streak(x):
    out = np.zeros(len(x), int)
    for i, row in enumerate(x <= 0):
        cur = best = 0
        for v in row:
            cur = cur + 1 if v else 0; best = max(best, cur)
        out[i] = best
    return out

def stats(paths, rk):
    eq = np.cumprod(1 + rk * paths, axis=1)
    peak = np.maximum.accumulate(np.hstack([np.ones((len(eq), 1)), eq]), axis=1)[:, 1:]
    dd = (1 - eq / peak).max(axis=1)
    return eq[:, -1] - 1, dd

print(f'R list n={N} mean={R.mean():.3f} (haircut {haircut})')
# Kelly: maximise mean log(1+fR)
fs = np.linspace(0.001, 0.6, 600); g = [np.mean(np.log1p(f * R)) for f in fs]
fk = fs[int(np.argmax(g))]
print(f'Kelly (empirical log-optimal) f*={fk*100:.1f}%  half={fk*50:.1f}%  quarter={fk*25:.1f}%  approx mean/var={R.mean()/R.var()*100:.1f}%')
for name, gen in [('IID', iid), (f'BLOCK{BLOCK}', block)]:
    p1 = gen(TPY); p3 = gen(3 * TPY)
    s1 = streak(p1); s3 = streak(p3)
    print(f'\n### {name} bootstrap, {TPY} trades/yr')
    print(f'losing streak (consecutive losers) 1y: median {np.median(s1):.0f}, p95 {np.percentile(s1,95):.0f}, p99 {np.percentile(s1,99):.0f} | 3y: median {np.median(s3):.0f}, p95 {np.percentile(s3,95):.0f}, p99 {np.percentile(s3,99):.0f}')
    print('| risk | 1y ret p5 | 1y median | 1y p95 | P(1y loss) | 3y ret p5 | 3y median | 3y p95 | P(3y loss) | 3y maxDD median | p95 | p99 | P(DD>20%) | P(DD>30%) | P(DD>50%) | 1y maxDD median | 1y p95 |')
    print('|' + '---|' * 17)
    for rk in [0.005, 0.01, 0.02, 0.03]:
        r1, d1 = stats(p1, rk); r3, d3 = stats(p3, rk)
        pc = lambda a, q: f'{np.percentile(a, q)*100:+.0f}%'
        print(f'| {rk*100:.1f}% | {pc(r1,5)} | {pc(r1,50)} | {pc(r1,95)} | {(r1<0).mean()*100:.0f}% | {pc(r3,5)} | {pc(r3,50)} | {pc(r3,95)} | {(r3<0).mean()*100:.1f}% | '
              f'{np.median(d3)*100:.0f}% | {np.percentile(d3,95)*100:.0f}% | {np.percentile(d3,99)*100:.0f}% | {(d3>.2).mean()*100:.1f}% | {(d3>.3).mean()*100:.1f}% | {(d3>.5).mean()*100:.2f}% | '
              f'{np.median(d1)*100:.0f}% | {np.percentile(d1,95)*100:.0f}% |')
