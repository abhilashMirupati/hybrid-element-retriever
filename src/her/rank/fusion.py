from __future__ import annotations
from typing import List, Dict
ALPHA=1.0; BETA=0.5; GAMMA=0.2

def fuse(cands:List[Dict])->List[Dict]:
    out=[]
    for c in cands:
        s=ALPHA*float(c.get('semantic',0.0))+BETA*float(c.get('css',0.0))+GAMMA*float(c.get('promotion',0.0))
        x=dict(c); x['score']=s; out.append(x)
    out.sort(key=lambda d:d['score'], reverse=True); return out
