import pytest

from her.cli_api import HybridClient


def test_act_output_contract() -> None:
    """Ensure that the JSON returned by act() contains all required fields.

    The Hybrid Element Retriever must include a standard set of keys in its
    response.  This test verifies that each key is present and that values
    have the expected basic type.  The actual semantics of the values are
    validated by higher‑level tests.
    """
    client = HybridClient()
    result = client.act("Click the login button", url="about:blank")

    required_keys = {
        "status": str,
        "method": str,
        "confidence": float,
        "dom_hash": str,
        "framePath": str,
        "semantic_locator": (str, type(None)),
        "used_locator": (str, type(None)),
        "n_best": list,
        "overlay_events": list,
        "retries": dict,
        "explanation": str,
    }
    for key, expected_type in required_keys.items():
        assert key in result, f"Missing key '{key}' in act result"
        value = result[key]
        if isinstance(expected_type, tuple):
            assert isinstance(value, expected_type), f"Key '{key}' has wrong type"
        else:
            assert isinstance(value, expected_type), f"Key '{key}' has wrong type"

    # retries must include attempts and final_method
    assert "attempts" in result["retries"]
    assert "final_method" in result["retries"]
