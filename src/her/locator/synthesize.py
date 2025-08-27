"""Locator synthesis with role→CSS→XPath progression and uniqueness checks."""
from typing import Dict, Any, List, Optional, Tuple
import re
import logging

logger = logging.getLogger(__name__)


class LocatorSynthesizer:
    """Synthesizes robust locators with uniqueness and stability checks."""
    
    def __init__(self, prefer_css: bool = True, max_candidates: int = 5):
        self.prefer_css = prefer_css
        self.max_candidates = max_candidates
    
    def synthesize(
        self,
        element: Dict[str, Any],
        context: Optional[List[Dict[str, Any]]] = None
    ) -> List[str]:
        """Synthesize candidate locators for an element.
        
        Tries strategies in order:
        1. Accessibility role/name
        2. CSS selectors (ID, data attributes, classes)
        3. XPath (resilient with multiple attributes)
        
        Args:
            element: Element descriptor
            context: Optional list of all elements for uniqueness checking
        
        Returns:
            List of candidate locator strings, best first
        """
        candidates = []
        
        # Strategy 1: Accessibility-based locators
        role_locators = self._synthesize_role_locators(element)
        candidates.extend(role_locators)
        
        # Strategy 2: CSS selectors
        if self.prefer_css:
            css_locators = self._synthesize_css_locators(element)
            candidates.extend(css_locators)
        
        # Strategy 3: XPath selectors
        xpath_locators = self._synthesize_xpath_locators(element)
        candidates.extend(xpath_locators)
        
        # Strategy 4: CSS if not preferred initially
        if not self.prefer_css:
            css_locators = self._synthesize_css_locators(element)
            candidates.extend(css_locators)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_candidates = []
        for loc in candidates:
            if loc not in seen:
                seen.add(loc)
                unique_candidates.append(loc)
        
        # Return top candidates
        return unique_candidates[:self.max_candidates]
    
    def _synthesize_role_locators(self, element: Dict[str, Any]) -> List[str]:
        """Generate role-based locators using Playwright's getByRole."""
        locators = []
        
        role = element.get("role")
        name = element.get("name")
        
        if not role:
            return locators
        
        # Basic role locator
        if name:
            # getByRole with name
            locators.append(f"role={role}[name=\"{self._escape_quotes(name)}\"]")
        else:
            # Just role
            locators.append(f"role={role}")
        
        # Add aria-label variant if different from name
        aria_label = element.get("aria", {}).get("label")
        if aria_label and aria_label != name:
            locators.append(f"role={role}[name=\"{self._escape_quotes(aria_label)}\"]")
        
        return locators
    
    def _synthesize_css_locators(self, element: Dict[str, Any]) -> List[str]:
        """Generate CSS selectors."""
        locators = []
        tag = element.get("tag", "*")
        
        # ID selector (most specific)
        element_id = element.get("id")
        if element_id and self._is_stable_id(element_id):
            locators.append(f"#{self._escape_css_id(element_id)}")
            locators.append(f"{tag}#{self._escape_css_id(element_id)}")
        
        # Data attributes (usually stable)
        data_attrs = element.get("data", {})
        for key, value in data_attrs.items():
            if value:
                locators.append(f"{tag}[data-{key}=\"{self._escape_quotes(value)}\"]")
        
        # Name attribute (for form elements)
        name_attr = element.get("attributes", {}).get("name")
        if name_attr:
            locators.append(f"{tag}[name=\"{self._escape_quotes(name_attr)}\"]")
        
        # Placeholder (for inputs)
        placeholder = element.get("placeholder")
        if placeholder:
            locators.append(f"{tag}[placeholder=\"{self._escape_quotes(placeholder)}\"]")
        
        # Type attribute (for inputs)
        type_attr = element.get("type")
        if type_attr and tag == "input":
            locators.append(f"input[type=\"{type_attr}\"]")
        
        # Class combinations (less stable but sometimes necessary)
        classes = element.get("classes", [])
        if classes:
            # Single most specific class
            for cls in classes:
                if self._is_meaningful_class(cls):
                    locators.append(f"{tag}.{cls}")
                    break
            
            # Multiple classes for uniqueness
            if len(classes) >= 2:
                class_selector = "".join(f".{cls}" for cls in classes[:2])
                locators.append(f"{tag}{class_selector}")
        
        # Text content (using Playwright's text selector)
        text = element.get("text", "").strip()
        if text and len(text) < 50:  # Avoid long text
            locators.append(f"text=\"{self._escape_quotes(text)}\"")
        
        return locators
    
    def _synthesize_xpath_locators(self, element: Dict[str, Any]) -> List[str]:
        """Generate XPath selectors."""
        locators = []
        tag = element.get("tag", "*")
        
        # Build XPath with multiple conditions for resilience
        conditions = []
        
        # ID condition
        element_id = element.get("id")
        if element_id and self._is_stable_id(element_id):
            locators.append(f"//*[@id='{self._escape_xpath(element_id)}']")
            conditions.append(f"@id='{self._escape_xpath(element_id)}'")
        
        # Text content
        text = element.get("text", "").strip()
        if text and len(text) < 50:
            # Exact text match
            conditions.append(f"text()='{self._escape_xpath(text)}'")
            # Contains text (more flexible)
            locators.append(f"//{tag}[contains(text(), '{self._escape_xpath(text)}')]")
        
        # Name attribute
        name_attr = element.get("attributes", {}).get("name")
        if name_attr:
            conditions.append(f"@name='{self._escape_xpath(name_attr)}'")
        
        # Placeholder
        placeholder = element.get("placeholder")
        if placeholder:
            conditions.append(f"@placeholder='{self._escape_xpath(placeholder)}'")
        
        # Type
        type_attr = element.get("type")
        if type_attr:
            conditions.append(f"@type='{type_attr}'")
        
        # Classes
        classes = element.get("classes", [])
        for cls in classes:
            if self._is_meaningful_class(cls):
                conditions.append(f"contains(@class, '{cls}')")
                break
        
        # Build combined XPath
        if conditions:
            # Single condition
            if len(conditions) == 1:
                locators.append(f"//{tag}[{conditions[0]}]")
            # Multiple conditions (more specific)
            else:
                for i in range(min(3, len(conditions))):
                    combined = " and ".join(conditions[:i+1])
                    locators.append(f"//{tag}[{combined}]")
        
        # Fallback: position-based (least stable)
        # This would need the element's position among siblings
        # locators.append(f"(//{tag})[position()=1]")
        
        return locators
    
    def _is_stable_id(self, element_id: str) -> bool:
        """Check if an ID looks stable (not auto-generated)."""
        # Reject IDs that look auto-generated
        if re.match(r'^[a-f0-9]{8,}$', element_id):  # Hex hash
            return False
        if re.match(r'^ember\d+$', element_id):  # Ember.js
            return False
        if re.match(r'^react-select-\d+-\w+$', element_id):  # React
            return False
        if element_id.startswith("__"):  # Private/generated
            return False
        return True
    
    def _is_meaningful_class(self, class_name: str) -> bool:
        """Check if a class name is meaningful (not utility/framework)."""
        # Reject common utility classes
        utility_patterns = [
            r'^[mp][tlrbxy]?-\d+$',  # Tailwind spacing
            r'^text-\w+$',  # Tailwind text
            r'^bg-\w+$',  # Tailwind background
            r'^col-\w+-\d+$',  # Bootstrap grid
            r'^btn-\w+$',  # Bootstrap buttons (too generic)
            r'^fa-\w+$',  # Font Awesome
            r'^icon-\w+$',  # Icon classes
        ]
        
        for pattern in utility_patterns:
            if re.match(pattern, class_name):
                return False
        
        return len(class_name) > 2  # Not too short
    
    def _escape_quotes(self, text: str) -> str:
        """Escape quotes for use in selectors."""
        return text.replace('"', '\\"')
    
    def _escape_css_id(self, element_id: str) -> str:
        """Escape ID for CSS selector."""
        # CSS requires escaping special characters
        return re.sub(r'([!"#$%&\'()*+,./:;<=>?@\[\\\]^`{|}~])', r'\\\1', element_id)
    
    def _escape_xpath(self, text: str) -> str:
        """Escape text for XPath."""
        # XPath 1.0 doesn't have escape sequences for quotes
        # Use concat() for mixed quotes if needed
        if "'" in text and '"' in text:
            # This is complex, for now just replace single quotes
            return text.replace("'", "")
        elif "'" in text:
            return text
        else:
            return text
    
    def explain_locator(self, locator: str) -> str:
        """Explain what a locator does in plain English."""
        if locator.startswith("role="):
            return f"Find element by accessibility role: {locator}"
        elif locator.startswith("#"):
            return f"Find element by ID: {locator}"
        elif locator.startswith("text="):
            return f"Find element by text content: {locator}"
        elif "[" in locator and "]" in locator:
            return f"Find element by attributes: {locator}"
        elif locator.startswith("//"):
            return f"Find element by XPath: {locator}"
        else:
            return f"Find element by CSS selector: {locator}"