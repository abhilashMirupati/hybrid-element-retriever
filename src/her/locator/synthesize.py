from __future__ import annotations

from typing import Dict, List, Tuple


def synthesize_xpath(desc: Dict) -> List[Tuple[str, str]]:
    """
    Returns a list of (kind, xpath) in precedence order.
    Precedence: data-testid > aria-label > id > role[name] > text exact > text contains
    """
    tag = (desc.get("tag") or "*").lower()
    text = " ".join((desc.get("text") or "").split())
    attrs = desc.get("attributes") or {}

    out: List[Tuple[str, str]] = []
    def add(kind: str, xp: str):
        out.append((kind, xp))

    dtid = attrs.get("data-testid")
    if dtid:
        add("data-testid", f'//*[@data-testid="{dtid}"]')

    aria = attrs.get("aria-label")
    if aria:
        add("aria-label", f'//*[@aria-label="{aria}"]')

    elid = attrs.get("id")
    if elid:
        add("id", f'//*[@id="{elid}"]')

    role = attrs.get("role")
    if role and text:
        add("role+name", f'//*[@role="{role}" and (normalize-space(@aria-label)="{text}" or normalize-space()="{text}")]')

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
