import sys
src=open(sys.argv[1]+'/replicate.py').read().split('data = {c')[0]
exec(src)
import pandas as pd, numpy as np
rows=[];allt=[]
for c in 'EOS ETC XTZ BSV FTT ZEC DASH NEO XMR WAVES'.split():
    d=load(c); fi=max(WARM,d.index.searchsorted(WIN0)); tr=run_rule(d,fi)
    R=np.array([t['R'] for t in tr]); dr=np.array([t['dir'] for t in tr]); st=stats(R)
    p,pm=placebo(d,fi,len(R),st['avg'])
    rows.append(dict(coin=c,n=st['n'],avg=st['avg'],t=st['t'],nL=(dr==1).sum(),avgL=R[dr==1].mean(),nS=(dr==-1).sum(),avgS=R[dr==-1].mean(),p=p,bh_chg=d.Close.iloc[-1]/d.Close.iloc[fi]-1))
    allt+=[dict(coin=c,**t) for t in tr]
df=pd.DataFrame(rows); print(df.round(3).to_string())
a=pd.DataFrame(allt)
for nm,s in [('all',a),('long',a[a.dir==1]),('short',a[a.dir==-1])]: print(nm,{k:round(float(v),3) for k,v in stats(s.R.values).items()})
df.to_csv(sys.argv[1]+'/fallen_coins.csv',index=False)
