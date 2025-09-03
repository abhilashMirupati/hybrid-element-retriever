import pytest

from her.embeddings.normalization import element_to_text


def test_button_canonicalization_basic():
    el = {
        "tag": "button",
        "text": "  Click   Me  ",
        "attributes": {
            "id": "cta",
            "class": "btn primary  large",
            "aria-label": "Submit order",
            "title": "Click to submit",
        },
    }
    s = element_to_text(el)
    # Deterministic signals order
    assert "Submit order" in s  # aria-label
    assert "Click to submit" in s  # title
    # TAG uppercased and id/classes compact
    assert "BUTTON" in s
    assert "#cta" in s
    assert ".btn" in s and ".primary" in s and ".large" in s
    # Collapsed whitespace and includes text
    assert "Click Me" in s


def test_link_includes_host_path_and_strips_query_fragment():
    el = {
        "tag": "a",
        "text": "Home",
        "attributes": {"href": "https://example.com/path/to/page?x=1#section"},
    }
    s = element_to_text(el)
    assert "EXAMPLE.COM/path/to/page" not in s  # not uppercased
    assert "example.com/path/to/page" in s
    assert "?" not in s and "#" not in s


def test_input_prefers_semantic_attrs():
    el = {
        "tag": "input",
        "attributes": {
            "placeholder": "Email address",
            "name": "email",
            "value": "",
            "type": "email",
        },
    }
    s = element_to_text(el)
    # Includes placeholder then name then value (if any)
    assert s.startswith("Email address")
    assert "name" not in s  # name value, not literal 'name:'
    assert "email" in s
    assert "INPUT" in s


def test_aria_only_and_empty_cases():
    aria_only = {"attributes": {"role": "button", "aria-label": "Close dialog"}}
    s1 = element_to_text(aria_only)
    assert s1.startswith("button") or s1.startswith("Button")
    assert "Close dialog" in s1

    empty = {}
    s2 = element_to_text(empty)
    assert s2 == ""


def test_length_cap_and_no_control_chars():
    long_text = "A" * 2048
    el = {"tag": "div", "text": long_text}
    s = element_to_text(el, max_length=128)
    assert len(s) == 128
    # Inject control chars and ensure they are stripped
    s2 = element_to_text({"text": "hi\x00\x07there"})
    assert "\x00" not in s2 and "\x07" not in s2

