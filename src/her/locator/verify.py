from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

try:
    from playwright.sync_api import Page
    PLAYWRIGHT_AVAILABLE = True
except Exception:  # pragma: no cover
    Page = Any  # type: ignore
    PLAYWRIGHT_AVAILABLE = False


@dataclass(frozen=True)
class VerificationResult:
    ok: bool
    unique: bool
    count: int
    visible: bool
    occluded: bool
    enabled: bool
    strategy: str
    used_selector: str
    explanation: str


def _normalize_strategy(strategy: str) -> str:
    s = (strategy or "xpath").lower()
    if s in ("xpath", "css", "text", "role"):
        return s
    return "xpath"


def offline_verify_unique(xpath: str, descriptors: List[Dict[str, Any]]) -> Tuple[bool, int]:
    if not xpath:
        return False, 0
    try:
        hits = 0
        import re
        attr_pairs = re.findall(r'@([\\w:-]+)=\\"([^\\"]+)\\"', xpath)
        tag = None
        mtag = re.match(r"//([\\w*]+)\\[", xpath)
        if mtag:
            tag = mtag.group(1).lower()
        for d in descriptors:
            attrs = d.get("attributes") or {}
            if attr_pairs:
                if not all(str(attrs.get(k)) == v for k, v in attr_pairs):
                    continue
            if tag and tag != "*" and (d.get("tag") or "").lower() != tag:
                continue
            if d.get("computed_xpath") == xpath:
                hits += 1
            else:
                hits += 1  # attribute match surrogate
        return (hits == 1), hits
    except Exception:
        return False, 0


def verify_selector(page: Optional[Page], selector: str, strategy: str = "xpath",
                    descriptors: Optional[List[Dict[str, Any]]] = None) -> VerificationResult:
    st = _normalize_strategy(strategy)
    if page is None or not PLAYWRIGHT_AVAILABLE:
        unique, count = offline_verify_unique(selector, descriptors or [])
        return VerificationResult(
            ok=unique, unique=unique, count=count, visible=True, occluded=False, enabled=True,
            strategy=st, used_selector=selector,
            explanation="offline-verify" if unique else "offline-verify-failed"
        )
    try:
        if st == "xpath":
            h = page.query_selector_all(f"xpath={selector}")
        elif st == "css":
            h = page.query_selector_all(selector)
        elif st == "text":
            h = page.query_selector_all(f"text={selector}")
        else:
            h = page.query_selector_all(selector)
        count = len(h)
        unique = count == 1
        return VerificationResult(
            ok=unique, unique=unique, count=count,
            visible=True, occluded=False, enabled=True,
            strategy=st, used_selector=selector, explanation="online-verify"
        )
    except Exception as e:
        return VerificationResult(
            ok=False, unique=False, count=0, visible=False, occluded=False, enabled=False,
            strategy=st, used_selector=selector, explanation=f"error:{e}"
        )
