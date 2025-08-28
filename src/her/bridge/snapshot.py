from __future__ import annotations
import hashlib
from typing import Any, Dict

def _sha1(s:str)->str:
    return hashlib.sha1(s.encode('utf-8')).hexdigest()

def get_flat_snapshot(page:Any)->Dict:
    frames=[]; total_nodes=0
    try:
        for fr in page.frames:
            try:
                cdp = page.context.new_cdp_session(fr)
            except Exception:
                cdp=None
            dom_nodes=[]; ax_nodes=[]
            if cdp:
                try:
                    dom = cdp.send('DOM.getFlattenedDocument', {'depth': -1, 'pierce': True}); dom_nodes = dom.get('nodes', [])
                except Exception:
                    dom_nodes=[]
                try:
                    ax = cdp.send('Accessibility.getFullAXTree', {}); ax_nodes = ax if isinstance(ax, list) else ax.get('nodes', [])
                except Exception:
                    ax_nodes=[]
            html=fr.content(); dom_hash=_sha1(html)
            frames.append({'frame_id': getattr(fr,'name','') if isinstance(getattr(fr,'name',None), str) else getattr(fr,'name',''), 'url': fr.url, 'dom_hash': dom_hash, 'dom_nodes': len(dom_nodes), 'ax_nodes': len(ax_nodes)})
            total_nodes += len(dom_nodes)+len(ax_nodes)
    except Exception:
        return {'frames': [], 'total_nodes': 0}
    return {'frames': frames, 'total_nodes': total_nodes}
