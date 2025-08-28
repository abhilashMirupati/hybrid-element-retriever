# src/her/locator/verify.py
# Verifies that a locator uniquely identifies a visible, interactable element
# in the given frame (or page) and is not occluded. Designed to work with
# Playwright's Python API without importing its types directly to avoid hard deps
# at import time. All logic is self-contained; no placeholders.

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List, Optional, Tuple


@dataclass(frozen=True)
class VerificationResult:
    ok: bool
    unique: bool
    count: int
    visible: bool
    occluded: bool
    disabled: bool
    strategy: str
    used_selector: str
    explanation: str


def _normalize_strategy(strategy: str) -> str:
    s = (strategy or "").strip().lower()
    if s in {"css", "selector", "sel"}:
        return "css"
    if s in {"xpath", "xp"}:
        return "xpath"
    if s in {"role", "byrole"}:
        return "role"
    if s in {"text", "bytext"}:
        return "text"
    # default to css
    return "css"


def _pick_frame(page_or_frame: Any) -> Any:
    """
    Accept either a Page or a Frame-like object and return a Frame-like object
    that exposes query_selector_all / locator / evaluate methods.
    """
    # Heuristic: Page has .main_frame, Frame doesn't.
    if hasattr(page_or_frame, "main_frame"):
        return page_or_frame.main_frame
    return page_or_frame


def _query_all(frame: Any, selector: str, strategy: str) -> List[Any]:
    """
    Query elements using Playwright engines. We prefer native engines without
    extra dependencies. Supports css/xpath/text/role.
    """
    st = _normalize_strategy(strategy)

    # Playwright supports engine prefixes via "engine=selector" syntax.
    if st == "css":
        return list(frame.query_selector_all(selector))
    if st == "xpath":
        return list(frame.query_selector_all(f"xpath={selector}"))
    if st == "text":
        # exact=false by default (case sensitive). Users can craft their own if needed.
        return list(frame.query_selector_all(f"text={selector}"))
    if st == "role":
        # Use the role engine if available via locator; fallback to role= engine prefix otherwise.
        try:
            # Playwright >=1.28 exposes get_by_role; prefer it if present.
            if hasattr(frame, "get_by_role"):
                # selector may come as "button[name=\"Submit\"]" or "button"
                role, name = _parse_role_selector(selector)
                if name:
                    return [frame.get_by_role(role=role, name=name)]
                return [frame.get_by_role(role=role)]
        except Exception:
            pass
        # Fallback to engine prefix (works with locator()):
        try:
            loc = frame.locator(f"role={selector}")
            n = loc.count()
            return [loc.nth(0)] if n == 1 else [loc.nth(i) for i in range(n)]
        except Exception:
            return []
    # default
    return list(frame.query_selector_all(selector))


def _parse_role_selector(sel: str) -> Tuple[str, Optional[str]]:
    """
    Accepts strings like:
      - "button"
      - "button[name=\"Submit\"]"
      - "textbox[name='Email']"
    Returns (role, name?) normalized for get_by_role.
    """
    s = sel.strip()
    name: Optional[str] = None
    role = s
    # Very lightweight parse for name=
    if "[" in s and "]" in s:
        role, rest = s.split("[", 1)
        rest = rest.rstrip("]")
        # allow forms: name="X" or name='X'
        if rest.startswith("name="):
            v = rest[len("name="):].strip()
            if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
                v = v[1:-1]
            name = v
    return role.strip(), name


def _is_visible(el: Any) -> bool:
    try:
        return bool(el.is_visible())
    except Exception:
        # Fallback: consider present == visible if API not available
        return True


def _is_disabled(el: Any) -> bool:
    # Try Playwright convenience first if exposed via locator
    try:
        # For Locator, we can evaluate on the element handle:
        handle = _to_element_handle(el)
        if handle:
            return bool(
                handle.evaluate(
                    """(e) => !!(e.disabled || e.getAttribute('aria-disabled') === 'true')"""
                )
            )
    except Exception:
        pass
    # Best-effort fallback: treat as enabled
    return False


def _to_element_handle(el_or_locator: Any) -> Optional[Any]:
    """
    Convert a Locator to ElementHandle when possible.
    If it's already an ElementHandle, return as-is.
    """
    try:
        # Locator → element handle
        if hasattr(el_or_locator, "element_handle"):
            h = el_or_locator.element_handle()
            if h:
                return h
        # ElementHandle has .evaluate; return directly
        if hasattr(el_or_locator, "evaluate"):
            return el_or_locator
    except Exception:
        pass
    return None


def _is_occluded(el: Any) -> bool:
    """
    Returns True if the element appears to be occluded at its visual center.
    Uses document.elementFromPoint at the center of the element's bounding box.
    """
    handle = _to_element_handle(el)
    if handle is None:
        return False
    try:
        return bool(
            handle.evaluate(
                """(e) => {
                    const r = e.getBoundingClientRect();
                    const cx = Math.floor(r.left + r.width / 2);
                    const cy = Math.floor(r.top  + r.height / 2);
                    const top = document.elementFromPoint(cx, cy);
                    if (!top) return true; // nothing at center → treat as occluded
                    return !(top === e || top.contains(e));
                }"""
            )
        )
    except Exception:
        # If evaluation fails (detached or not visible), consider occluded.
        return True


def verify_locator(
    page_or_frame: Any,
    selector: str,
    strategy: str = "css",
    require_unique: bool = True,
) -> VerificationResult:
    """
    Verify that `selector` with given `strategy` resolves to exactly one
    visible, non-occluded, interactable element in the provided page/frame.

    Parameters
    ----------
    page_or_frame : Playwright Page or Frame
    selector      : selector string (css/xpath/text/role form depending on strategy)
    strategy      : one of {'css','xpath','text','role'}
    require_unique: if True, fail when multiple elements match

    Returns
    -------
    VerificationResult
    """
    frame = _pick_frame(page_or_frame)
    st = _normalize_strategy(strategy)

    try:
        candidates = _query_all(frame, selector, st)
    except Exception as e:
        return VerificationResult(
            ok=False,
            unique=False,
            count=0,
            visible=False,
            occluded=True,
            disabled=False,
            strategy=st,
            used_selector=selector,
            explanation=f"Query error: {e}",
        )

    count = len(candidates)
    if count == 0:
        return VerificationResult(
            ok=False,
            unique=False,
            count=0,
            visible=False,
            occluded=True,
            disabled=False,
            strategy=st,
            used_selector=selector,
            explanation="No elements matched the selector.",
        )

    if require_unique and count != 1:
        return VerificationResult(
            ok=False,
            unique=False,
            count=count,
            visible=False,
            occluded=False,
            disabled=False,
            strategy=st,
            used_selector=selector,
            explanation=f"Selector matched {count} elements; expected unique match.",
        )

    # If not enforcing uniqueness strictly, pick the first and validate it.
    target = candidates[0]

    visible = _is_visible(target)
    if not visible:
        return VerificationResult(
            ok=False,
            unique=(count == 1),
            count=count,
            visible=False,
            occluded=False,
            disabled=False,
            strategy=st,
            used_selector=selector,
            explanation="Element is not visible.",
        )

    occluded = _is_occluded(target)
    if occluded:
        return VerificationResult(
            ok=False,
            unique=(count == 1),
            count=count,
            visible=True,
            occluded=True,
            disabled=False,
            strategy=st,
            used_selector=selector,
            explanation="Element appears occluded at the visual center.",
        )

    disabled = _is_disabled(target)
    if disabled:
        return VerificationResult(
            ok=False,
            unique=(count == 1),
            count=count,
            visible=True,
            occluded=False,
            disabled=True,
            strategy=st,
            used_selector=selector,
            explanation="Element is disabled (or aria-disabled).",
        )

    return VerificationResult(
        ok=True,
        unique=(count == 1),
        count=count,
        visible=True,
        occluded=False,
        disabled=False,
        strategy=st,
        used_selector=selector,
        explanation="OK",
    )


__all__ = ["VerificationResult", "verify_locator"]
