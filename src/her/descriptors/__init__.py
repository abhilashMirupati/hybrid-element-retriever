"""Descriptors package for element description and merging."""

from .merge import merge_dom_ax
from typing import Dict, Any


def normalize_descriptor(node: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize a raw node dict to a standard descriptor shape for tests."""
    out = {}
    out['tagName'] = (node.get('tag') or node.get('tagName') or node.get('nodeName') or '').lower()
    attrs = node.get('attributes') or {}
    if isinstance(attrs, list):
        # Convert [name,value,...] to dict
        attrs_dict = {}
        for i in range(0, len(attrs), 2):
            if i+1 < len(attrs):
                attrs_dict[str(attrs[i])] = attrs[i+1]
        attrs = attrs_dict
    out['attributes'] = attrs
    out['id'] = (attrs.get('id') if isinstance(attrs, dict) else None) or None
    classes = attrs.get('class','') if isinstance(attrs, dict) else ''
    out['classes'] = classes.split() if isinstance(classes, str) else []
    # normalize text - trim whitespace
    raw_text = node.get('text','') or node.get('nodeValue','') or ''
    out['text'] = str(raw_text).strip()
    out['type'] = attrs.get('type','') if isinstance(attrs, dict) else ''
    out['placeholder'] = attrs.get('placeholder','') if isinstance(attrs, dict) else ''
    # mirror class in className for convenience
    if isinstance(attrs, dict) and 'class' in attrs:
        out['className'] = attrs.get('class')
    # include value if present (for inputs)
    if isinstance(attrs, dict) and 'value' in attrs:
        out['value'] = attrs.get('value')
    # flatten data- attributes
    for k, v in (attrs.items() if isinstance(attrs, dict) else []):
        if k.startswith('data-'):
            out[k] = v
        if k.startswith('aria-') or k == 'role':
            out[k] = v
    return out


__all__ = ["merge_dom_ax", "normalize_descriptor"]