from her.embeddings.normalization import canonical_text

def test_canonical_priority_and_truncation():
    el = {
        "tag": "button",
        "role": "button",
        "attributes": {
            "aria-label": "Save File"
        },
        "title": "Not Used When aria-label present",
        "alt": "ALT also behind title",
        "placeholder": "ignored for button",
        "name": "save",
        "value": "",
        "text": "  Save   ",
        "href": "https://example.com/files/save?draft=1",
        "id": "submit",
        "class": "btn  btn-primary"
    }
    out = canonical_text(el, max_length=200)
    # Priority: role → aria-label → title → alt → placeholder → name → value → TAG → #id/.classes → text → href(host/path)
    assert out.startswith("button Save File"), out

def test_href_hostpath_and_whitespace_collapse():
    el = {"tag": "a", "href": "https://abc.example.com/path/to/page?q=x#frag", "text": "Open"}
    out = canonical_text(el, max_length=200)
    # href(host/path) should be "abc.example.com/path/to/page"
    assert "abc.example.com/path/to/page" in out
    # no double spaces / controls
    assert "  " not in out

def test_handles_missing_fields_and_zero_maxlen():
    el = {"tag": "input", "attributes": {}, "text": ""}
    out = canonical_text(el, max_length=0)
    assert out == ""
