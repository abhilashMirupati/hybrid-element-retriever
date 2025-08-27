"""Element descriptor definitions.

This module defines the data structures used to describe actionable elements
extracted from the DOM and accessibility tree.  These descriptors are
consumed by the embedding layer to compute semantic vectors and by the
locator synthesiser to generate robust selectors.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


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
