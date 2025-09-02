import pytest
from src.her.compat import HERPipeline  # type: ignore


def test_frame_and_shadow_metadata_fields_present_and_correct():
    p = HERPipeline()  # type: ignore[call-arg]

    # Two frames; one shadow element in frame B
    elements = [
        {
            "tag": "button",
            "text": "Send",
            "attributes": {"role": "button"},
            "is_visible": True,
            "computed_xpath": "//button[@id='sendA']",
            "frame_id": "frame-A",
            "frame_path": [0, 1],
        },
        {
            "tag": "button",
            "text": "Shadow Thing",
            "attributes": {"role": "button"},
            "is_visible": True,
            "computed_xpath": "//button[@id='shadowB']",
            "frame_id": "frame-B",
            "frame_path": [0, 2],
            "in_shadow_dom": True,  # hint for metadata
        },
    ]

    out = p.process("click shadow thing", {"elements": elements})  # type: ignore[attr-defined]
    assert isinstance(out, dict)
    # Must always include these fields
    assert "used_frame_id" in out
    assert "frame_path" in out
    assert "metadata" in out and isinstance(out["metadata"], dict)
    assert "in_shadow_dom" in out["metadata"]

    assert out["used_frame_id"] == "frame-B"
    assert out["frame_path"] == [0, 2]
    assert out["metadata"]["in_shadow_dom"] is True
