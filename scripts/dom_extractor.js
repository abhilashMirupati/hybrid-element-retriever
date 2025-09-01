
/**
 * dom_extractor.js
 * Collects canonical descriptors for actionable DOM elements.
 * Exposes:
 *   - extractDescriptors(): Array<Descriptor>
 *   - evaluateXPathCount(xpath): number
 *   - evaluateCssCount(css): number
 */
(function () {
  function normText(s) {
    if (!s) return "";
    return String(s).replace(/\s+/g, " ").trim();
  }

  function getXPathForElement(el) {
    if (el.id) return `//*[@id="${el.id}"]`;
    const parts = [];
    let node = el;
    while (node && node.nodeType === 1 && node !== document.body && node !== document.documentElement) {
      const tag = node.tagName.toLowerCase();
      let index = 1;
      let sib = node.previousElementSibling;
      while (sib) {
        if (sib.tagName === node.tagName) index++;
        sib = sib.previousElementSibling;
      }
      parts.unshift(`${tag}[${index}]`);
      node = node.parentElement;
    }
    return "//" + parts.join("/");
  }

  function isVisible(el) {
    const style = window.getComputedStyle(el);
    const rect = el.getBoundingClientRect();
    return (
      style &&
      style.visibility !== "hidden" &&
      style.display !== "none" &&
      rect.width > 0 &&
      rect.height > 0
    );
  }

  function collectActionable() {
    const q = [
      "button",
      "a[href]",
      "input",
      "textarea",
      "select",
      "[role='button']",
      "[role='link']",
      "[role='menuitem']",
      "[role='tab']",
      "[role='checkbox']",
      "[role='radio']",
      "[role='combobox']"
    ].join(",");

    const nodes = Array.from(document.querySelectorAll(q));
    const out = [];
    for (const el of nodes) {
      if (!isVisible(el)) continue;
      const tag = el.tagName.toLowerCase();
      const attrs = {
        id: el.getAttribute("id"),
        name: el.getAttribute("name"),
        type: el.getAttribute("type"),
        placeholder: el.getAttribute("placeholder"),
        title: el.getAttribute("title"),
        role: el.getAttribute("role"),
        "aria-label": el.getAttribute("aria-label"),
        "data-testid": el.getAttribute("data-testid"),
        "data-test": el.getAttribute("data-test"),
        "data-qa": el.getAttribute("data-qa"),
        "data-cy": el.getAttribute("data-cy"),
      };
      const text = normText(el.innerText || el.textContent || "");
      const descriptor = {
        tag,
        text,
        attributes: attrs,
        is_visible: true,
        computed_xpath: getXPathForElement(el),
      };
      out.push(descriptor);
    }
    return out;
  }

  window.extractDescriptors = function () {
    return collectActionable();
  };

  window.evaluateXPathCount = function (xpath) {
    try {
      const r = document.evaluate(xpath, document, null, XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null);
      return r.snapshotLength || 0;
    } catch (e) {
      return -1;
    }
  };

  window.evaluateCssCount = function (css) {
    try {
      return document.querySelectorAll(css).length;
    } catch (e) {
      return -1;
    }
  };
})();
