import pytest
from her.browser import snapshot_sync

@pytest.mark.timeout(60)
def test_iframe_traversal_data_url():
    html_iframe = "data:text/html," \
                  "<html><body><h2>Inner</h2><a href='/x'>Go</a><button>Press</button></body></html>"
    outer = f"data:text/html,<html><body><iframe src=\"{html_iframe}\"></iframe></body></html>"
    items = snapshot_sync(outer, timeout_ms=8000, include_iframes=True, max_iframe_depth=2)
    assert any(it["text"].startswith("Inner") for it in items)
    assert any(it["tag"] == "BUTTON" for it in items)

@pytest.mark.timeout(60)
def test_shadow_dom_capture():
    shadow_html = (
        "data:text/html,<html><body>"
        "<div id='host'></div>"
        "<script>"
        "const host=document.getElementById('host');"
        "const root=host.attachShadow({mode:'open'});"
        "root.innerHTML='<button aria-label=\"Shadow OK\">Shadow Button</button>';"
        "</script>"
        "</body></html>"
    )
    items = snapshot_sync(shadow_html, timeout_ms=8000, include_shadow_dom=True)
    assert any('Shadow Button' in it["text"] or (it["attrs"] or {}).get("aria-label") == "Shadow OK" for it in items)

@pytest.mark.timeout(60)
def test_auto_scroll_lazy_content():
    # Simulate lazy growth by increasing body height after a delay
    lazy = (
        "data:text/html,<html><body style='height:2000px'>"
        "<div id='late'></div>"
        "<script>setTimeout(()=>{document.getElementById('late').innerText='Loaded later';}, 600);</script>"
        "</body></html>"
    )
    items = snapshot_sync(lazy, timeout_ms=8000, auto_scroll=True, scroll_steps=3, scroll_pause_ms=500)
    assert any('Loaded later' in it["text"] for it in items)
