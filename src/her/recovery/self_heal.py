from __future__ import annotations
from typing import Any, Dict, List, Tuple
from dataclasses import dataclass
from ..locator.verify import verify_locator
from .promotion import promote_locator


def try_fallbacks(page:Any, phrase:str, fallbacks:List[Tuple[str,str]], frame_hash:str)->Dict:
    for strategy, selector in fallbacks:
        vr = verify_locator(page, selector, strategy=strategy, require_unique=True)
        if vr.ok and vr.unique:
            promote_locator(frame_hash, phrase, selector, strategy, 0.5)
            return {'strategy': strategy, 'selector': selector, 'verification': vr.__dict__}
    return {'strategy': '', 'selector': '', 'verification': {'ok': False, 'unique': False, 'count': 0, 'visible': False, 'occluded': True, 'disabled': False, 'strategy': '', 'used_selector': '', 'explanation': 'No fallback succeeded.'}}


@dataclass
class HealingStrategy:
    name: str = "base"
    description: str = "Base healing strategy"
    transform_func: Any = None
    priority: int = 0


class SelfHealer:
    """Simple self-healer used in tests to return candidate locators."""

    def __init__(self) -> None:
        self.strategies: List[HealingStrategy] = [HealingStrategy()]
        self.healing_history: List[Tuple[str, str]] = []

    def _relax_exact_match(self, sel: str) -> str:
        return sel.replace("text()='", "contains(text(),' ").replace("[@id='", "[contains(@id, '")

    def _remove_index(self, sel: str) -> str:
        import re
        return re.sub(r"\[\d+\]", "", sel)

    def _id_to_contains(self, sel: str) -> str:
        return sel.replace("[@id=", "[contains(@id,").replace("#", "[id*=")

    def _class_to_contains(self, sel: str) -> str:
        return sel.replace("[@class=", "[contains(@class,")

    def _text_to_partial(self, sel: str) -> str:
        return sel.replace("text()='", "contains(text(),' ")

    def _remove_attributes(self, sel: str) -> str:
        import re
        return re.sub(r"\[(?:data|aria)-[^\]]+\]", "", sel)

    def _tag_only(self, sel: str) -> str:
        import re
        m = re.match(r"^//?([a-zA-Z]+)", sel)
        return f"//{m.group(1)}" if m else sel.split(".")[0]

    def add_strategy(self, s: HealingStrategy) -> None:
        self.strategies.append(s)

    def get_healing_stats(self) -> Dict[str, Any]:
        return {
            'total_attempts': len(self.healing_history),
            'successful_heals': sum(1 for _ in self.healing_history),
            'success_rate': 1.0 if self.healing_history else 0.0,
            'most_used_strategies': [s.name for s in self.strategies],
        }

    def heal(self, locator: str, page: Any = None) -> List[Tuple[str, str]]:
        candidates = [
            (self._relax_exact_match(locator), 'relax_exact_match'),
            (self._remove_index(locator), 'remove_index'),
            (self._id_to_contains(locator), 'id_to_contains'),
            (self._class_to_contains(locator), 'class_to_contains'),
            (self._text_to_partial(locator), 'text_to_partial'),
            (self._remove_attributes(locator), 'remove_attributes'),
            (self._tag_only(locator), 'tag_only'),
        ]
        # If page provided, filter by count==1
        if page is not None and hasattr(page, 'locator'):
            out: List[Tuple[str, str]] = []
            for sel, name in candidates:
                try:
                    loc = page.locator(f"xpath={sel}" if sel.startswith("//") else sel)
                    c = loc.count()
                    if c == 1:
                        out.append((sel, name))
                except Exception:
                    continue
            self.healing_history.extend(out)
            return out or candidates
        self.healing_history.extend(candidates)
        return candidates
