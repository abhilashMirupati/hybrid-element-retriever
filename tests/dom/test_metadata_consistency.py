# tests/dom/test_metadata_consistency.py
"""
Verifies the pipeline carries correct frame/shadow metadata:
- used_frame_id and frame_path reflect the chosen element's context
- metadata['in_shadow_dom'] is always present and correct
- Fields are never missing in the output JSON
"""

from src.her.compat import HERPipeline


def _framey_descriptors():
    # Two frames A/B; target is in B and inside shadow DOM
    return [
        {
            "tag": "button",
            "text": "Send",
            "attributes": {"role": "button", "id": "sendA"},
            "is_visible": True,
            "computed_xpath": "//*[@id='sendA']",
            "frame_path": ["root", "frame-A"],
            "in_shadow_dom": False,
        },
        {
            "tag": "button",
            "text": "Shadow Thing",
            "attributes": {"role": "button", "id": "shadowB"},
            "is_visible": True,
            "computed_xpath": "//*[@id='shadowB']",
            "frame_path": ["root", "frame-B"],
            "in_shadow_dom": True,
        },
    ]


def test_metadata_fields_and_values(tmp_path):
    p = HERPipeline(cache_dir=tmp_path)
    elements = _framey_descriptors()

    out = p.process("click shadow thing", {"elements": elements})
    assert isinstance(out, dict)

    # Required top-level fields always present
    for k in ("xpath", "strategy", "metadata", "used_frame_id", "frame_path"):
        assert k in out, f"missing field: {k}"

    # Metadata invariants
    md = out["metadata"]
    assert isinstance(md, dict)
    assert "in_shadow_dom" in md and isinstance(md["in_shadow_dom"], bool)

    # Frame selection should pick frame-B target
    assert out["used_frame_id"] in ("frame-B", "root/frame-B", "B")  # allow naming variance
    assert out["frame_path"] == ["root", "frame-B"]
    assert md["in_shadow_dom"] is True
