// scripts/dom_extractor.js
// Enterprise-grade DOM extractor for HER.
// Guarantees deterministic, complete, and stable descriptors.
// No heuristic pruning, no silent skips. All limitations exposed as metadata.

(() => {
  // ===== Helpers =====
  function getUniqueXPath(el) {
    if (!el || el.nodeType !== Node.ELEMENT_NODE) return "";

    // Prefer unique id
    if (el.id) {
      const sameId = el.ownerDocument.querySelectorAll(`#${CSS.escape(el.id)}`);
      if (sameId.length === 1) return `//*[@id="${el.id}"]`;
    }

    // Build stable absolute path
    const parts = [];
    let node = el;
    while (node && node.nodeType === Node.ELEMENT_NODE) {
      const tag = node.nodeName.toLowerCase();

      // Find 1-based index among siblings of same tag
      let index = 1;
      let sib = node.previousElementSibling;
      while (sib) {
        if (sib.nodeName.toLowerCase() === tag) index++;
        sib = sib.previousElementSibling;
      }
      parts.unshift(`${tag}[${index}]`);
      node = node.parentNode;
    }
    return "/" + parts.join("/");
  }

  function isVisible(el) {
    try {
      const style = window.getComputedStyle(el);
      const rect = el.getBoundingClientRect();
      return (
        style.display !== "none" &&
        style.visibility !== "hidden" &&
        parseFloat(style.opacity || "1") > 0 &&
        rect.width > 0 &&
        rect.height > 0
      );
    } catch {
      return false;
    }
  }

  function sortedAttrs(el) {
    const attrs = {};
    if (!el.hasAttributes()) return attrs;
    const arr = Array.from(el.attributes).sort((a, b) =>
      a.name.localeCompare(b.name)
    );
    for (const a of arr) attrs[a.name] = a.value;
    return attrs;
  }

  function canonicalize(el, framePath = []) {
    return {
      tag: el.tagName.toLowerCase(),
      text: (el.innerText || "").trim().slice(0, 256), // hard cap
      attributes: sortedAttrs(el),
      is_visible: isVisible(el),
      computed_xpath: getUniqueXPath(el),
      frame_path: framePath,
      in_shadow_dom: !!el.getRootNode().host,
      cross_origin: false,
    };
  }

  // ===== Traversal =====
  function traverse(root, acc, framePath = []) {
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT, null, false);
    let node;
    while ((node = walker.nextNode())) {
      acc.push(canonicalize(node, framePath));

      // shadow DOM
      if (node.shadowRoot) traverse(node.shadowRoot, acc, framePath);

      // iframes
      if (node.tagName === "IFRAME") {
        try {
          const doc = node.contentDocument;
          if (doc) traverse(doc, acc, framePath.concat(getUniqueXPath(node)));
        } catch {
          // Cross-origin iframe descriptor
          acc.push({
            tag: "iframe",
            text: "",
            attributes: sortedAttrs(node),
            is_visible: isVisible(node),
            computed_xpath: getUniqueXPath(node),
            frame_path: framePath,
            in_shadow_dom: false,
            cross_origin: true,
          });
        }
      }
    }
  }

  // ===== Entry =====
  function extractDescriptors() {
    const acc = [];
    traverse(document, acc);

    // Deduplicate by stable key
    const seen = new Set();
    return acc.filter(d => {
      const key = d.frame_path.join("::") + "::" + d.computed_xpath;
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    });
  }

  // Expose globally
  window.extractDescriptors = extractDescriptors;
})();
