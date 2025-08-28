"""Locator synthesis for generating robust XPath and CSS selectors."""

from __future__ import annotations
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class LocatorSynthesizer:
    """Synthesizes multiple locator strategies for elements."""
    
    def __init__(self):
        """Initialize the locator synthesizer."""
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
    
    def synthesize(self, descriptor: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate multiple locators for an element descriptor.
        
        Args:
            descriptor: Element descriptor with tag, attributes, text, etc.
            
        Returns:
            List of locator dictionaries with 'selector' and 'strategy' keys
        """
        locators = []
        
        for strategy in self.strategies:
            try:
                result = strategy(descriptor)
                if result:
                    if isinstance(result, list):
                        locators.extend(result)
                    else:
                        locators.append(result)
            except Exception as e:
                logger.debug(f"Strategy {strategy.__name__} failed: {e}")
        
        # Remove duplicates while preserving order
        seen = set()
        unique_locators = []
        for loc in locators:
            key = (loc["selector"], loc["strategy"])
            if key not in seen:
                seen.add(key)
                unique_locators.append(loc)
        
        return unique_locators[:10]  # Return top 10 locators
    
    def _by_id(self, desc: Dict) -> Optional[Dict]:
        """Generate locator by ID."""
        element_id = desc.get("id")
        if element_id:
            return [
                {"selector": f"#{element_id}", "strategy": "css"},
                {"selector": f"//*[@id='{element_id}']", "strategy": "xpath"}
            ]
        return None
    
    def _by_data_testid(self, desc: Dict) -> Optional[List[Dict]]:
        """Generate locator by data-testid attributes."""
        locators = []
        attrs = desc.get("attributes", {})
        
        for attr in ["data-testid", "data-test", "data-qa", "data-cy"]:
            if attr in attrs:
                value = attrs[attr]
                locators.append({
                    "selector": f"[{attr}='{value}']",
                    "strategy": "css"
                })
                locators.append({
                    "selector": f"//*[@{attr}='{value}']",
                    "strategy": "xpath"
                })
        
        return locators if locators else None
    
    def _by_name(self, desc: Dict) -> Optional[Dict]:
        """Generate locator by name attribute."""
        name = desc.get("name") or desc.get("attributes", {}).get("name")
        if name:
            tag = desc.get("tag", "*")
            return [
                {"selector": f"{tag}[name='{name}']", "strategy": "css"},
                {"selector": f"//{tag}[@name='{name}']", "strategy": "xpath"}
            ]
        return None
    
    def _by_class(self, desc: Dict) -> Optional[Dict]:
        """Generate locator by class."""
        classes = desc.get("classes", [])
        if classes and len(classes) > 0:
            # Use the most specific class
            class_name = classes[0]
            return [
                {"selector": f".{class_name}", "strategy": "css"},
                {"selector": f"//*[contains(@class, '{class_name}')]", "strategy": "xpath"}
            ]
        return None
    
    def _by_text(self, desc: Dict) -> Optional[Dict]:
        """Generate locator by text content."""
        text = desc.get("text", "").strip()
        if text and len(text) > 2:  # Avoid too short text
            tag = desc.get("tag", "*")
            # Escape quotes in text
            text_escaped = text.replace("'", "\\'")
            return [
                {"selector": f"{tag}:has-text('{text_escaped}')", "strategy": "css"},
                {"selector": f"//{tag}[text()='{text}']", "strategy": "xpath"},
                {"selector": f"//{tag}[contains(text(), '{text}')]", "strategy": "xpath"}
            ]
        return None
    
    def _by_role(self, desc: Dict) -> Optional[Dict]:
        """Generate locator by ARIA role."""
        role = desc.get("role") or desc.get("attributes", {}).get("role")
        if role:
            name = desc.get("name") or desc.get("text", "")
            if name:
                return [{
                    "selector": f"[role='{role}'][aria-label='{name}']",
                    "strategy": "css"
                }]
            return [{"selector": f"[role='{role}']", "strategy": "css"}]
        return None
    
    def _by_aria_label(self, desc: Dict) -> Optional[Dict]:
        """Generate locator by aria-label."""
        attrs = desc.get("attributes", {})
        aria_label = attrs.get("aria-label") or desc.get("aria", {}).get("label")
        if aria_label:
            return [
                {"selector": f"[aria-label='{aria_label}']", "strategy": "css"},
                {"selector": f"//*[@aria-label='{aria_label}']", "strategy": "xpath"}
            ]
        return None
    
    def _by_xpath_text(self, desc: Dict) -> Optional[Dict]:
        """Generate XPath locator by text."""
        text = desc.get("text", "").strip()
        tag = desc.get("tag", "*")
        if text:
            return [{
                "selector": f"//{tag}[normalize-space()='{text}']",
                "strategy": "xpath"
            }]
        return None
    
    def _by_xpath_contains(self, desc: Dict) -> Optional[Dict]:
        """Generate XPath contains locator."""
        text = desc.get("text", "").strip()
        if text and len(text) > 5:
            # Use first few words for partial match
            words = text.split()[:3]
            partial = " ".join(words)
            return [{
                "selector": f"//*[contains(normalize-space(), '{partial}')]",
                "strategy": "xpath"
            }]
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
                    locators.append({
                        "selector": f"{tag}[{attr}='{value}']",
                        "strategy": "css"
                    })
                else:
                    locators.append({
                        "selector": f"[{attr}='{value}']",
                        "strategy": "css"
                    })
        
        return locators if locators else None


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