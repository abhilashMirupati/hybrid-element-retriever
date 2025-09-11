# 🔍 HTML Processing Analysis in HER Framework

## 📋 **Summary**
The HER framework processes HTML in **TEXT FORMAT**, not as raw HTML strings. Here's the complete flow:

## 🔄 **HTML Processing Flow**

### **1. DOM Snapshot (Browser Level)**
```javascript
// In src/her/browser/snapshot.py (lines 241-242)
const textRaw = (el.innerText || '').replace(/\s+/g, ' ').trim();
const text = textRaw.length > cfg.maxText ? textRaw.slice(0, cfg.maxText) : textRaw;
```

**Key Points:**
- Uses `el.innerText` (not `innerHTML` or `outerHTML`)
- Extracts **visible text content only**
- Collapses whitespace and trims
- Limits text length to prevent memory issues

### **2. Element Structure Captured**
```javascript
// Elements captured with these properties:
{
  text: "Click here",           // ← TEXT FORMAT (not HTML)
  tag: "BUTTON",               // ← Tag name only
  role: "button",              // ← ARIA role
  attrs: {                     // ← Attributes as key-value pairs
    "id": "submit-btn",
    "class": "btn-primary",
    "aria-label": "Submit form"
  },
  xpath: "/HTML[1]/BODY[1]/BUTTON[1]",
  bbox: { x: 100, y: 200, width: 80, height: 30 },
  visible: true
}
```

### **3. Text Extraction Functions**

#### **A. Basic Text Extraction**
```python
# src/her/descriptors/merge.py (lines 11-62)
def extract_text_content(node: Dict[str, Any]) -> str:
    """Extract text content from DOM node, including child text nodes."""
    text_parts = []
    
    # Get direct text content
    node_value = node.get('nodeValue', '').strip()
    if node_value:
        text_parts.append(node_value)
    
    # Get text from accessibility tree
    if 'accessibility' in node:
        ax_name = node['accessibility'].get('name', '')
        if ax_name:
            clean_name = extract_clean_text(ax_name)
            if clean_name:
                text_parts.append(clean_name)
    
    # Get text from attributes (aria-label, title, value, etc.)
    # ... priority order for text content
```

#### **B. Comprehensive Text Extraction**
```python
# src/her/descriptors/merge.py (lines 324-370)
def extract_comprehensive_text(node: Dict[str, Any]) -> str:
    """Extract comprehensive text content from a node, trying multiple sources."""
    text_parts = []
    
    # 1. Direct text content
    # 2. Text from accessibility tree
    # 3. Text from attributes (aria-label, title, value, alt, placeholder)
    # 4. Text from children nodes
    # 5. Fallback to tag name if no text found
```

### **4. MarkupLM Processing (HTML Reconstruction)**

#### **A. Query Processing**
```python
# src/her/core/pipeline.py (lines 506-524)
def _embed_query_markup(self, text: str) -> np.ndarray:
    """Embed query using MarkupLM for reranking (768-d)."""
    # Create proper HTML structure for MarkupLM embedding
    if "click" in text.lower():
        html_text = f"<button type='button'>{text}</button>"
    elif "enter" in text.lower() or "type" in text.lower():
        html_text = f"<input type='text' placeholder='{text}'>"
    elif "select" in text.lower():
        html_text = f"<select>{text}</select>"
    else:
        html_text = f"<div>{text}</div>"
    
    html_element = {"text": html_text, "tag": "html", "attributes": {}}
    q = self.element_embedder.encode(html_element)
```

#### **B. Element Processing for MarkupLM**
```python
# src/her/core/pipeline.py (lines 677-717)
# Create enhanced elements with proper HTML structure for MarkupLM
for (_, meta) in shortlist[:10]:
    enhanced_meta = meta.copy()
    
    # Convert element to proper HTML structure
    tag = meta.get('tag', '').lower()
    text = meta.get('text', '')
    attrs = meta.get('attributes', {})
    
    # Build attribute string
    attr_str = ""
    for key, value in attrs.items():
        attr_str += f' {key}="{value}"'
    
    # Create HTML structure based on element type
    if tag in ['a', 'button', 'input', 'select', 'option']:
        if tag == 'a':
            html_text = f'<a{attr_str}>{text}</a>'
        elif tag == 'button':
            html_text = f'<button{attr_str}>{text}</button>'
        elif tag == 'input':
            html_text = f'<input{attr_str} value="{text}">'
        else:
            html_text = f'<{tag}{attr_str}>{text}</{tag}>'
    else:
        html_text = f'<{tag}{attr_str}>{text}</{tag}>'
    
    enhanced_meta["text"] = html_text  # ← HTML RECONSTRUCTED HERE
    enhanced_meta["tag"] = "html"      # ← Mark as HTML for MarkupLM
```

### **5. Text Normalization for Embeddings**

#### **A. Element to Text Conversion**
```python
# src/her/embeddings/normalization.py (lines 32-62)
def element_to_text(el: Dict, max_length: int = 1024) -> str:
    """
    Canonical text for element embeddings (deterministic, attribute-aware).
    
    Order of signals (most informative first):
    [role] [aria-label] [title] [alt] [placeholder] [name] [value]
    [TAG] [#id .classes] [visible text] [href(host/path)]
    """
    attrs = (el.get("attrs") or {})
    tag   = _clean((el.get("tag") or "").upper())
    role  = _clean(attrs.get("role") or el.get("role") or "")
    label = _clean(attrs.get("aria-label") or "")
    title = _clean(attrs.get("title") or "")
    alt   = _clean(attrs.get("alt") or "")
    ph    = _clean(attrs.get("placeholder") or "")
    name  = _clean(attrs.get("name") or "")
    val   = _clean(attrs.get("value") or "")
    text  = _clean(el.get("text") or "")
    
    # Compact id + class
    idp   = f"#{_clean(attrs['id'])}" if attrs.get("id") else ""
    classes = _clean(attrs.get("class") or "")
    clsp  = ("." + ".".join([c for c in classes.split() if c])) if classes else ""
    
    hrefp = _href_hostpath(attrs.get("href") or "")
    
    parts = [
        role, label, title, alt, ph, name, val,
        tag, idp + clsp, text, hrefp
    ]
    return _join(parts, max_length)
```

## 🎯 **Key Findings**

### **✅ HTML is NOT passed as raw strings:**
1. **DOM Snapshot**: Uses `innerText` to extract visible text only
2. **Element Processing**: Captures structured data (tag, attributes, text) separately
3. **Text Extraction**: Multiple functions extract text from various sources
4. **MarkupLM Processing**: HTML is **reconstructed** from structured data for MarkupLM

### **🔄 Processing Flow:**
```
Raw HTML → DOM Snapshot → Structured Elements → Text Extraction → MarkupLM HTML Reconstruction
    ↓           ↓              ↓                    ↓                        ↓
  <button>   innerText      {tag, attrs, text}   "Click here"         <button>Click here</button>
```

### **📊 Data Formats:**

#### **Input (DOM Snapshot):**
- **Text**: `"Click here"` (extracted from `innerText`)
- **Tag**: `"BUTTON"`
- **Attributes**: `{"id": "submit", "class": "btn"}`

#### **Output (MarkupLM):**
- **HTML**: `"<button id='submit' class='btn'>Click here</button>"`
- **Tag**: `"html"`
- **Text**: `"<button id='submit' class='btn'>Click here</button>"`

## 🔍 **Code Evidence**

### **1. DOM Snapshot (Browser)**
```javascript
// src/her/browser/snapshot.py:241
const textRaw = (el.innerText || '').replace(/\s+/g, ' ').trim();
```
**Uses `innerText` (text only), not `innerHTML` (HTML markup)**

### **2. Text Extraction**
```python
# src/her/descriptors/merge.py:324
def extract_comprehensive_text(node: Dict[str, Any]) -> str:
    """Extract comprehensive text content from a node, trying multiple sources."""
```
**Extracts text from multiple sources, not HTML**

### **3. MarkupLM HTML Reconstruction**
```python
# src/her/core/pipeline.py:694-704
if tag == 'a':
    html_text = f'<a{attr_str}>{text}</a>'
elif tag == 'button':
    html_text = f'<button{attr_str}>{text}</button>'
```
**HTML is reconstructed from structured data for MarkupLM**

## 🏆 **Conclusion**

**The HER framework processes HTML in TEXT FORMAT, not as raw HTML strings.** The system:

1. **Captures** DOM elements as structured data (tag, attributes, text)
2. **Extracts** text content using `innerText` and various fallback methods
3. **Reconstructs** HTML only when needed for MarkupLM processing
4. **Uses** text-based embeddings for MiniLM and reconstructed HTML for MarkupLM

This approach is more robust and efficient than processing raw HTML strings, as it focuses on the semantic content rather than markup structure.