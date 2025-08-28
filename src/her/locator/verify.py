from __future__ import annotations
from dataclasses import dataclass
from typing import Any, List, Optional, Tuple
@dataclass(frozen=True)
class VerificationResult:
    ok: bool; unique: bool; count: int; visible: bool; occluded: bool; disabled: bool; strategy: str; used_selector: str; explanation: str

def _normalize_strategy(strategy:str)->str:
    s=(strategy or '').strip().lower()
    if s in {'css','selector','sel'}: return 'css'
    if s in {'xpath','xp'}: return 'xpath'
    if s in {'role','byrole'}: return 'role'
    if s in {'text','bytext'}: return 'text'
    return 'css'

def _pick_frame(page_or_frame:Any)->Any:
    if hasattr(page_or_frame,'main_frame'): return page_or_frame.main_frame
    return page_or_frame

def _query_all(frame:Any, selector:str, strategy:str)->List[Any]:
    st=_normalize_strategy(strategy)
    if st=='css': return list(frame.query_selector_all(selector))
    if st=='xpath': return list(frame.query_selector_all(f"xpath={selector}"))
    if st=='text': return list(frame.query_selector_all(f"text={selector}"))
    if st=='role':
        try:
            if hasattr(frame,'get_by_role'):
                role,name=_parse_role_selector(selector)
                if name: return [frame.get_by_role(role=role, name=name)]
                return [frame.get_by_role(role=role)]
        except Exception: pass
        try:
            loc=frame.locator(f"role={selector}"); n=loc.count(); return [loc.nth(0)] if n==1 else [loc.nth(i) for i in range(n)]
        except Exception: return []
    return list(frame.query_selector_all(selector))

def _parse_role_selector(sel:str)->Tuple[str, Optional[str]]:
    s=sel.strip(); name=None; role=s
    if '[' in s and ']' in s:
        role,rest=s.split('[',1); rest=rest.rstrip(']')
        if rest.startswith('name='):
            v=rest[len('name='):].strip()
            if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")): v=v[1:-1]
            name=v
    return role.strip(), name

def _to_element_handle(x:Any):
    try:
        if hasattr(x,'element_handle'):
            h=x.element_handle(); 
            if h: return h
        if hasattr(x,'evaluate'): return x
    except Exception: return None
    return None

def _is_visible(el:Any)->bool:
    try: return bool(el.is_visible())
    except Exception: return True

def _is_disabled(el:Any)->bool:
    try:
        h=_to_element_handle(el)
        if h: return bool(h.evaluate("""(e)=>!!(e.disabled || e.getAttribute('aria-disabled')==='true')"""))
    except Exception: return False
    return False

def _is_occluded(el:Any)->bool:
    h=_to_element_handle(el)
    if not h: return False
    try:
        return bool(h.evaluate("""(e)=>{const r=e.getBoundingClientRect();const cx=Math.floor(r.left+r.width/2);const cy=Math.floor(r.top+r.height/2);const top=document.elementFromPoint(cx,cy);return !(top===e||top.contains(e));}"""))
    except Exception: return True

def verify_locator(page_or_frame:Any, selector:str, strategy:str='css', require_unique:bool=True)->VerificationResult:
    frame=_pick_frame(page_or_frame); st=_normalize_strategy(strategy)
    try: candidates=_query_all(frame, selector, st)
    except Exception as e:
        return VerificationResult(False, False, 0, False, True, False, st, selector, f'Query error: {e}')
    count=len(candidates)
    if count==0:
        return VerificationResult(False, False, 0, False, True, False, st, selector, 'No elements matched.')
    if require_unique and count!=1:
        return VerificationResult(False, False, count, False, False, False, st, selector, f'Matched {count} elements; expected 1.')
    target=candidates[0]
    if not _is_visible(target):
        return VerificationResult(False, count==1, count, False, False, False, st, selector, 'Not visible.')
    if _is_occluded(target):
        return VerificationResult(False, count==1, count, True, True, False, st, selector, 'Occluded at center.')
    if _is_disabled(target):
        return VerificationResult(False, count==1, count, True, False, True, st, selector, 'Disabled/aria-disabled.')
    return VerificationResult(True, count==1, count, True, False, False, st, selector, 'OK')
__all__=['VerificationResult','verify_locator']
