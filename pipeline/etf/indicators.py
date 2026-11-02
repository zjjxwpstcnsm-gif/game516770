import math
import numpy as np

def indicators(prices):
    c=np.array([p['close'] for p in prices],dtype=float)
    out={}
    for n in (5,10,20,60):out[f'ma{n}']=float(c[-n:].mean()) if len(c)>=n else None
    for n in (5,20,60):out[f'return{n}']=float(c[-1]/c[-n-1]-1) if len(c)>n else None
    if len(c)>=15:
        d=np.diff(c[-15:]);gain=np.maximum(d,0).mean();loss=np.maximum(-d,0).mean();out['rsi14']=float(100-100/(1+gain/loss)) if loss else (100.0 if gain else 50.0)
    else:out['rsi14']=None
    out['volatility20']=float(np.std(np.diff(np.log(c[-21:])),ddof=1)*np.sqrt(252)) if len(c)>=21 else None
    return out
