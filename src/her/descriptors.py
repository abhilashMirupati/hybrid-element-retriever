"""Element descriptor definitions.

This module defines the data structures used to describe actionable elements
extracted from the DOM and accessibility tree.  These descriptors are
consumed by the embedding layer to compute semantic vectors and by the
locator synthesiser to generate robust selectors.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


def normalize_descriptor(desc: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize a raw descriptor into a consistent format.

    Args:
        desc: Raw descriptor dictionary

    Returns:
        Normalized descriptor dictionary
    """
    normalized = {}

    # Normalize tag name
    tag = desc.get("tagName", "")
    normalized["tagName"] = tag.lower() if tag else ""

    # Normalize text
    text = desc.get("text", "")
    normalized["text"] = text.strip() if text else ""

    # Extract attributes
    attributes = desc.get("attributes", {}) or {}
    for key, value in attributes.items():
        if key == "class":
            normalized["className"] = value
        else:
            normalized[key] = value

    # Add common attributes directly
    if "value" in desc:
        normalized["value"] = desc["value"]

    return normalized


@dataclass
class ElementDescriptor:
    backendNodeId: int
    framePath: str
    tag: str
    type: Optional[str] = None
    id: Optional[str] = None
    classes: List[str] = field(default_factory=list)
    placeholder: Optional[str] = None
    aria: Dict[str, Any] = field(default_factory=dict)
    labels: List[str] = field(default_factory=list)
    ax_role: Optional[str] = None
    ax_name: Optional[str] = None
    ax_hidden: Optional[bool] = None
    ax_disabled: Optional[bool] = None
    visible: Optional[bool] = None
    bbox: Optional[Dict[str, float]] = None
    neighbors: List[str] = field(default_factory=list)
    dom_hash: Optional[str] = None
    shadowPath: Optional[str] = None
