from __future__ import annotations

from typing import Dict, List, Tuple


def synthesize_xpath(desc: Dict) -> List[Tuple[str, str]]:
    """
    Returns a list of (kind, xpath) in precedence order.
    Precedence: data-testid > data-quick-link > href+text > aria-label > id > role[name] > text exact > text contains
    
    Focuses on RELATIVE, ROBUST selectors that work across multiple runs.
    """
    tag = (desc.get("tag") or "*").lower()
    text = " ".join((desc.get("text") or "").split())
    attrs = desc.get("attributes") or {}

    out: List[Tuple[str, str]] = []
    def add(kind: str, xp: str):
        out.append((kind, xp))

    # Highest priority: data-testid (most stable)
    dtid = attrs.get("data-testid")
    if dtid:
        add("data-testid", f'//*[@data-testid="{dtid}"]')

    # High priority: data-quick-link (navigation elements)
    data_quick_link = attrs.get("data-quick-link")
    if data_quick_link and text:
        add("data-quick-link", f'//*[@data-quick-link="{data_quick_link}" and normalize-space()="{text}"]')

    # High priority: href+text (for links) - more robust than absolute paths
    href = attrs.get("href")
    if href and text and tag == "a":
        add("href+text", f'//a[@href="{href}" and normalize-space()="{text}"]')

    # Medium priority: aria-label (accessibility-friendly)
    aria = attrs.get("aria-label")
    if aria:
        add("aria-label", f'//*[@aria-label="{aria}"]')

    # Medium priority: id + text (more specific than just id)
    elid = attrs.get("id")
    if elid and text:
        add("id+text", f'//*[@id="{elid}" and normalize-space()="{text}"]')
    elif elid:
        add("id", f'//*[@id="{elid}"]')

    # Medium priority: class + text (more robust than absolute paths)
    class_name = attrs.get("class")
    if class_name and text and tag:
        # Use first meaningful class name
        first_class = class_name.split()[0] if class_name else ""
        if first_class:
            add("class+text", f'//{tag}[contains(@class, "{first_class}") and normalize-space()="{text}"]')
    
    # High priority: id + class + text (most specific for buttons/filters)
    if elid and class_name and text and tag:
        first_class = class_name.split()[0] if class_name else ""
        if first_class:
            add("id+class+text", f'//{tag}[@id="{elid}" and contains(@class, "{first_class}") and normalize-space()="{text}"]')

    # Lower priority: role+text (accessibility-friendly)
    role = attrs.get("role")
    if role and text:
        add("role+name", f'//*[@role="{role}" and (normalize-space(@aria-label)="{text}" or normalize-space()="{text}")]')

    # Fallback: text-based selectors (most fragile but sometimes necessary)
    if text and tag:
        add("text-exact", f'//{tag}[normalize-space()="{text}"]')
    if text:
        add("text-contains", f'//*[contains(normalize-space(), "{text}")]')

    return out


class LocatorSynthesizer:
    """Minimal class wrapper used by cli_api and tests.

    synthesize(desc) -> List[Dict]: each dict has {'kind','selector'} keys
    """
    def synthesize(self, desc: Dict) -> List[Dict[str, str]]:
        cands: List[Dict[str, str]] = []
        for kind, xp in synthesize_xpath(desc):
            cands.append({"kind": kind, "selector": xp})
        return cands
