from __future__ import annotations
from typing import Any, Dict, List, Tuple
from ..locator.verify import verify_locator
from .promotion import promote_locator

def try_fallbacks(page:Any, phrase:str, fallbacks:List[Tuple[str,str]], frame_hash:str)->Dict:
    for strategy, selector in fallbacks:
        vr = verify_locator(page, selector, strategy=strategy, require_unique=True)
        if vr.ok and vr.unique:
            promote_locator(frame_hash, phrase, selector, strategy, 0.5)
            return {'strategy': strategy, 'selector': selector, 'verification': vr.__dict__}
    return {'strategy': '', 'selector': '', 'verification': {'ok': False, 'unique': False, 'count': 0, 'visible': False, 'occluded': True, 'disabled': False, 'strategy': '', 'used_selector': '', 'explanation': 'No fallback succeeded.'}}
