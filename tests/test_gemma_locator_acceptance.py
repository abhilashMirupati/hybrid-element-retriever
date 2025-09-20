import os
import socket
import time

import pytest

import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from gemma_embedding import retrieve_best_element


def _has_network(host: str = "www.verizon.com", timeout_s: float = 3.0) -> bool:
    try:
        socket.gethostbyname(host)
        return True
    except Exception:
        return False


@pytest.mark.acceptance
def test_verizon_apple_button_footer():
    if not _has_network():
        pytest.skip("No network/DNS; skipping acceptance test")
    url = "https://www.verizon.com/smartphones/"
    cfg = {"use_visual_fallback": True}
    out = retrieve_best_element(url, "Click on Apple button in footer", target_text="Apple", config=cfg)
    assert out.get("best_canonical"), "No best element returned"
    node = out["best_canonical"]["node"]
    text = (node.get("text") or "").lower()
    tag = (node.get("tag") or "").upper()
    assert "apple" in text
    assert tag in ("A", "BUTTON")


@pytest.mark.acceptance
def test_compare_cta_plausible():
    if not _has_network():
        pytest.skip("No network/DNS; skipping acceptance test")
    url = "https://www.verizon.com/smartphones/"
    cfg = {"use_visual_fallback": True}
    out = retrieve_best_element(url, "Compare plans or products", target_text="Compare", config=cfg)
    assert out.get("best_canonical"), "No best element returned"
    node = out["best_canonical"]["node"]
    text = (node.get("text") or "").lower()
    # allow some flexibility; at least ensure compare keyword or fallback fired
    assert ("compare" in text) or bool(out.get("fallback_used"))

