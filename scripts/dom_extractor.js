// Enterprise-grade DOM extractor for HER.
(() => {
  function getUniqueXPath(el) {
    if (!el || el.nodeType !== Node.ELEMENT_NODE) return "";
    if (el.id) {
      const same = el.ownerDocument.querySelectorAll(`#${CSS.escape(el.id)}`);
      if (same.length === 1) return `//*[@id="${el.id}"]`;
    }
    const parts = [];
    let node = el;
    while (node && node.nodeType === Node.ELEMENT_NODE) {
      const tag = node.nodeName.toLowerCase();
      let idx = 1;
      let sib = node.previousElementSibling;
      while (sib) { if (sib.nodeName.toLowerCase() === tag) idx++; sib = sib.previousElementSibling; }
      parts.unshift(`${tag}[${idx}]`);
      node = node.parentNode;
    }
    return "/" + parts.join("/");
  }
  function isVisible(el) {
    try {
      const style = window.getComputedStyle(el);
      const rect = el.getBoundingClientRect();
      return style.display !== "none" && style.visibility !== "hidden" && parseFloat(style.opacity || "1") > 0 && rect.width > 0 && rect.height > 0;
    } catch { return false; }
  }
  function sortedAttrs(el) {
    const out = {};
    if (!el.hasAttributes()) return out;
    const arr = Array.from(el.attributes).sort((a,b)=>a.name.localeCompare(b.name));
    for (const a of arr) out[a.name] = a.value;
    return out;
  }
  function canonicalize(el, framePath = []) {
    return {
      tag: el.tagName.toLowerCase(),
      text: (el.innerText || "").trim().slice(0,256),
      attributes: sortedAttrs(el),
      is_visible: isVisible(el),
      computed_xpath: getUniqueXPath(el),
      frame_path: framePath,
      in_shadow_dom: !!el.getRootNode().host,
      cross_origin: false
    };
  }
  function traverse(root, acc, framePath = []) {
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT, null, false);
    let node;
    while ((node = walker.nextNode())) {
      acc.push(canonicalize(node, framePath));
      if (node.shadowRoot) traverse(node.shadowRoot, acc, framePath);
      if (node.tagName === "IFRAME") {
        try {
          const doc = node.contentDocument;
          if (doc) traverse(doc, acc, framePath.concat(getUniqueXPath(node)));
        } catch {
          acc.push({
            tag: "iframe",
            text: "",
            attributes: sortedAttrs(node),
            is_visible: isVisible(node),
            computed_xpath: getUniqueXPath(node),
            frame_path: framePath,
            in_shadow_dom: false,
            cross_origin: true
          });
        }
      }
    }
  }
  function extractDescriptors() {
    const acc = [];
    traverse(document, acc);
    const seen = new Set();
    return acc.filter(d => {
      const key = (d.frame_path||[]).join("::") + "::" + d.computed_xpath;
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    });
  }
  window.extractDescriptors = extractDescriptors;
})();
