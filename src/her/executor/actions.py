from __future__ import annotations
import time
from typing import Any, Optional
class ActionError(Exception):
    """Exception raised when an action fails to execute."""
    pass

def _scroll_into_view(el: Any) -> None:
    try:
        h = el.element_handle() if hasattr(el, 'element_handle') else el
        if h: h.scroll_into_view_if_needed()
    except Exception as e: raise ActionError(f'scroll failed: {e}') from e

def _overlay_guard(page: Any) -> None:
    try:
        for sel in ['text=Accept','text=Close','text=Dismiss','role=dialog >> text=×']:
            try:
                el = page.query_selector(sel)
                if el and el.is_visible(): el.click(timeout=1000)
            except Exception: continue
    except Exception: return

def _occlusion_guard(el: Any) -> None:
    try:
        h = el.element_handle() if hasattr(el,'element_handle') else el
        if not h: return
        occ = h.evaluate('(e)=>{const r=e.getBoundingClientRect();const cx=Math.floor(r.left+r.width/2);const cy=Math.floor(r.top+r.height/2);const top=document.elementFromPoint(cx,cy);return !(top===e||top.contains(e));}')
        if occ: raise ActionError('occluded')
    except Exception as e: raise ActionError(f'occlusion: {e}') from e

def _verify_post_action(el: Any, action: str, expected: Optional[str]=None) -> None:
    try:
        if action=='fill' and expected is not None:
            if el.input_value()!=expected: raise ActionError('fill verify failed')
        elif action=='click':
            if not el.is_enabled(): raise ActionError('disabled after click')
        elif action=='check':
            if not el.is_checked(): raise ActionError('check failed')
    except Exception as e: raise ActionError(f'post verify: {e}') from e

def click(page: Any, el: Any) -> None:
    _scroll_into_view(el); _overlay_guard(page); _occlusion_guard(el); el.click(); _verify_post_action(el,'click')

def fill(page: Any, el: Any, text: str) -> None:
    _scroll_into_view(el); _overlay_guard(page); _occlusion_guard(el); el.fill(text); _verify_post_action(el,'fill',text)

def check(page: Any, el: Any) -> None:
    _scroll_into_view(el); _overlay_guard(page); _occlusion_guard(el); el.check(); _verify_post_action(el,'check')

def wait_for_idle(page: Any, timeout: float=5.0) -> None:
    deadline=time.time()+timeout
    while time.time()<deadline:
        try:
            if page.evaluate('() => document.readyState')=='complete': return
        except Exception:
            # Page might be navigating or closed, continue waiting
            continue
        time.sleep(0.1)
__all__=['ActionError','click','fill','check','wait_for_idle']
