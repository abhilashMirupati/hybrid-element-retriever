"""Locator synthesis for generating robust XPath and CSS selectors."""

from __future__ import annotations
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class LocatorSynthesizer:
    """Synthesizes multiple locator strategies for elements."""
    
    def __init__(self):
        """Initialize the locator synthesizer."""
        self.prefer_css = True
        self.max_candidates = 5
        self.strategies = [
            self._by_id,
            self._by_data_testid,
            self._by_name,
            self._by_class,
            self._by_text,
            self._by_role,
            self._by_aria_label,
            self._by_xpath_text,
            self._by_xpath_contains,
            self._by_css_attribute,
        ]
    
    def synthesize(self, descriptor: Dict[str, Any]) -> List[str]:
        """Generate multiple locators for an element descriptor.
        
        Args:
            descriptor: Element descriptor with tag, attributes, text, etc.
            
        Returns:
            List of locator dictionaries with 'selector' and 'strategy' keys
        """
        locators: List[str] = []
        
        for strategy in self.strategies:
            try:
                result = strategy(descriptor)
                if result:
                    if isinstance(result, list):
                        for r in result:
                            sel = r["selector"] if isinstance(r, dict) else r
                            locators.append(sel)
                    else:
                        sel = result["selector"] if isinstance(result, dict) else result
                        locators.append(sel)
            except Exception as e:
                logger.debug(f"Strategy {strategy.__name__} failed: {e}")
        
        # Remove duplicates while preserving order
        seen = set()
        unique: List[str] = []
        for sel in locators:
            if sel not in seen:
                seen.add(sel)
                unique.append(sel)
        # Enforce max candidates
        return unique[: self.max_candidates]
    
    def _by_id(self, desc: Dict) -> Optional[Dict]:
        """Generate locator by ID."""
        element_id = desc.get("id")
        if element_id:
            return [f"#{element_id}", f"//*[@id='{element_id}']"]
        return None
    
    def _by_data_testid(self, desc: Dict) -> Optional[List[Dict]]:
        """Generate locator by data-testid attributes."""
        locators = []
        attrs = desc.get("attributes", {})
        
        for attr in ["data-testid", "data-test", "data-qa", "data-cy"]:
            if attr in attrs:
                value = attrs[attr]
                locators.append(f"[{attr}='{value}']")
                locators.append(f"//*[@{attr}='{value}']")
        
        return locators if locators else None
    
    def _by_name(self, desc: Dict) -> Optional[Dict]:
        """Generate locator by name attribute."""
        name = desc.get("name") or desc.get("attributes", {}).get("name")
        if name:
            tag = desc.get("tag", "*")
            return [f"{tag}[name='{name}']", f"//{tag}[@name='{name}']"]
        return None
    
    def _by_class(self, desc: Dict) -> Optional[Dict]:
        """Generate locator by class."""
        classes = desc.get("classes", [])
        if classes and len(classes) > 0:
            # Use the most specific class
            class_name = classes[0]
            return [f".{class_name}", f"//*[contains(@class, '{class_name}')]" ]
        return None
    
    def _by_text(self, desc: Dict) -> Optional[Dict]:
        """Generate locator by text content."""
        text = desc.get("text", "").strip()
        if text and len(text) > 2:  # Avoid too short text
            tag = desc.get("tag", "*")
            # Escape quotes in text
            text_escaped = text.replace("'", "\\'")
            return [f"{tag}:has-text('{text_escaped}')", f"//{tag}[text()='{text}']", f"//{tag}[contains(text(), '{text}')]" ]
        return None
    
    def _by_role(self, desc: Dict) -> Optional[Dict]:
        """Generate locator by ARIA role."""
        role = desc.get("role") or desc.get("attributes", {}).get("role")
        if role:
            name = desc.get("name") or desc.get("text", "")
            if name:
                return [f"role={role}[name=\"{name}\"]", f"[role='{role}'][aria-label='{name}']"]
            return [f"role={role}", f"[role='{role}']"]
        return None
    
    def _by_aria_label(self, desc: Dict) -> Optional[Dict]:
        """Generate locator by aria-label."""
        attrs = desc.get("attributes", {})
        aria_label = attrs.get("aria-label") or desc.get("aria", {}).get("label")
        if aria_label:
            return [f"[aria-label='{aria_label}']", f"//*[@aria-label='{aria_label}']"]
        return None
    
    def _by_xpath_text(self, desc: Dict) -> Optional[Dict]:
        """Generate XPath locator by text."""
        text = desc.get("text", "").strip()
        tag = desc.get("tag", "*")
        if text:
            return [f"//{tag}[normalize-space()='{text}']"]
        return None
    
    def _by_xpath_contains(self, desc: Dict) -> Optional[Dict]:
        """Generate XPath contains locator."""
        text = desc.get("text", "").strip()
        if text and len(text) > 5:
            # Use first few words for partial match
            words = text.split()[:3]
            partial = " ".join(words)
            return [f"//*[contains(normalize-space(), '{partial}')]"]
        return None
    
    def _by_css_attribute(self, desc: Dict) -> Optional[List[Dict]]:
        """Generate CSS attribute selectors."""
        locators = []
        attrs = desc.get("attributes", {})
        tag = desc.get("tag", "")
        
        # Common attributes to use for selection
        for attr in ["type", "placeholder", "value", "title", "alt"]:
            if attr in attrs and attrs[attr]:
                value = attrs[attr]
                if tag:
                    locators.append(f"{tag}[{attr}='{value}']")
                else:
                    locators.append(f"[{attr}='{value}']")
        
        return locators if locators else None

    # Test helpers
    def _is_stable_id(self, value: str) -> bool:
        v = value or ""
        if any(tok for tok in ["ember", "react-select", "__private"] if tok in v):
            return False
        # hex-like long strings
        import re
        if re.fullmatch(r"[a-fA-F0-9]{8,}", v):
            return False
        return True

    def _is_meaningful_class(self, value: str) -> bool:
        v = (value or "").lower()
        if len(v) < 3:
            return False
        utility_prefixes = ("mt-", "text-", "col-", "fa-")
        if v.startswith(utility_prefixes):
            return False
        return True

    def explain_locator(self, selector: str) -> str:
        s = selector or ""
        if s.startswith("role="):
            return "role-based selector"
        if s.startswith("#"):
            return "ID based selector"
        if s.startswith("text=") or ":has-text(" in s:
            return "text selector"
        if s.startswith("//"):
            return "XPath selector"
        return "CSS selector"


def choose_best(candidates: List[Dict]) -> Dict:
    """Choose the best candidate from a list of scored candidates.
    
    This is a compatibility function for the old API.
    """
    if not candidates:
        return {}
    
    # Sort by score if available
    if candidates and "score" in candidates[0]:
        sorted_candidates = sorted(candidates, key=lambda x: x.get("score", 0), reverse=True)
        return sorted_candidates[0]
    
    # Otherwise return first with a selector
    for candidate in candidates:
        if candidate.get("selector"):
            return candidate
    
    return candidates[0] if candidates else {}


__all__ = ["LocatorSynthesizer", "choose_best"]