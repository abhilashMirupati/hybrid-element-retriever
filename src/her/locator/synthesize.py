from __future__ import annotations
from typing import Dict, List
from ..rank.heuristics import robust_css_score
from ..rank.fusion import fuse

def _css_from_attrs(tag:str, attrs:Dict[str,str])->str:
    if attrs.get('id'): return f"{tag}#{attrs['id']}"
    for k in ('data-testid','data-test','data-qa'):
        if attrs.get(k): return f"{tag}[{k}='{attrs[k]}']"
    if attrs.get('name'): return f"{tag}[name='{attrs['name']}']"
    return tag

def choose_best(candidates:List[Dict])->Dict:
    scored=[]
    for c in candidates:
        css=robust_css_score(c.get('attrs',{}))
        sel=_css_from_attrs(c.get('tag','*'), c.get('attrs',{}))
        scored.append({'semantic':c.get('semantic',0.0),'css':css,'promotion':c.get('promotion',0.0),'selector':sel,'strategy':'css','meta':{'tag':c.get('tag'),'text':c.get('text','')}})
    fused=fuse(scored)
    return fused[0] if fused else {}
__all__=['choose_best']
