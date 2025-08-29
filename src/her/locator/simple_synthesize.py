"""Simple locator synthesis wrapper for compatibility."""

from typing import Dict, Any, List
from .synthesize import LocatorSynthesizer as _LocatorSynthesizer


class LocatorSynthesizer(_LocatorSynthesizer):
    """Enhanced locator synthesizer with simpler interface."""

    def synthesize(self, descriptor: Dict[str, Any]) -> List[str]:
        """Synthesize locators from a simple descriptor.

        Handles both simple descriptors (tagName, attributes, text)
        and complex ones (tag, role, classes, etc.)
        """
        # Convert simple descriptor to complex format if needed
        element = self._normalize_descriptor(descriptor)

        # Call parent synthesize and convert to simple list of selector strings
        locs = super().synthesize(element)
        out: List[str] = []
        for loc in locs:
            if isinstance(loc, dict) and 'selector' in loc:
                out.append(loc['selector'])
            elif isinstance(loc, str):
                out.append(loc)
        return out

    def _normalize_descriptor(self, descriptor: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize descriptor to expected format."""
        element = {}

        # Handle tag/tagName
        element["tag"] = descriptor.get("tag") or descriptor.get("tagName", "*")

        # Handle attributes
        attrs = descriptor.get("attributes", {})
        if attrs:
            element["id"] = attrs.get("id")
            element["attributes"] = attrs
            element["type"] = attrs.get("type")
            element["placeholder"] = attrs.get("placeholder")

            # Extract classes
            if attrs.get("class"):
                element["classes"] = attrs["class"].split()

            # Extract data attributes
            element["data"] = {}
            for key, value in attrs.items():
                if key.startswith("data-"):
                    element["data"][key[5:]] = value

        # Handle text
        element["text"] = descriptor.get("text", "")

        # Handle accessibility
        element["role"] = descriptor.get("role")
        element["name"] = descriptor.get("name")
        if attrs:
            element["aria"] = {"label": attrs.get("aria-label")}

        return element
