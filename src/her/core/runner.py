from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from ..parser.enhanced_intent import EnhancedIntentParser
from ..promotion.promotion_adapter import compute_label_key
from .hashing import page_signature, dom_hash, frame_hash as compute_frame_hash
from .pipeline import HybridPipeline

try:
    from playwright.sync_api import sync_playwright
    _PLAYWRIGHT = True
except Exception:  # pragma: no cover
    _PLAYWRIGHT = False

try:
    from ..executor.main import Executor  # type: ignore
except Exception:
    Executor = None  # type: ignore


logger = logging.getLogger("her.runner")
_DEBUG_CANDS = os.getenv("HER_DEBUG_CANDIDATES", "0") == "1"


@dataclass
class StepResult:
    step: str
    selector: str
    confidence: float
    ok: bool
    info: Dict[str, Any]


class Runner:
    _shared_pipeline = None
    _pipeline_lock = None
    
    def __init__(self, headless: bool = True, intent_parser: Optional[EnhancedIntentParser] = None, pipeline: Optional[HybridPipeline] = None) -> None:
        """Initialize Runner with optional dependency injection.
        
        Args:
            headless: Whether to run browser in headless mode.
            intent_parser: Optional intent parser instance. If None, creates default.
            pipeline: Optional pipeline instance. If None, uses shared pipeline.
        """
        self.headless = headless
        self.intent = intent_parser or EnhancedIntentParser()
        
        # Use provided pipeline or shared pipeline to avoid reloading models
        if pipeline is not None:
            # Validate that the provided pipeline is compatible
            if not hasattr(pipeline, 'query') or not callable(getattr(pipeline, 'query')):
                raise ValueError("Provided pipeline must have a 'query' method")
            self.pipeline = pipeline
        else:
            if Runner._shared_pipeline is None:
                import threading
                if Runner._pipeline_lock is None:
                    Runner._pipeline_lock = threading.Lock()
                
                with Runner._pipeline_lock:
                    if Runner._shared_pipeline is None:
                        print("📦 Loading models (one-time cost for all runners)...")
                        start_time = time.time()
                        Runner._shared_pipeline = HybridPipeline()
                        print(f"   ✅ Models loaded in {time.time() - start_time:.3f}s")
            
            self.pipeline = Runner._shared_pipeline
        self._page = None
        self._browser = None
        self._playwright = None

    def _normalize_url(self, url: str) -> str:
        from urllib.parse import urlparse
        try:
            u = urlparse(url or "")
            path = u.path.rstrip("/")
            parts = [p for p in path.split("/") if p]
            if parts and len(parts[0]) in (2, 5) and parts[0].isalpha():
                parts = parts[1:]
            norm = f"{u.scheme}://{u.netloc}/" + "/".join(parts)
            return norm.rstrip("/")
        except Exception:
            return (url or "").split("?")[0].rstrip("/")

    def _ensure_browser(self):
        if not _PLAYWRIGHT:
            return None
        if self._page is None:
            self._playwright = sync_playwright().start()
            self._browser = self._playwright.chromium.launch(headless=self.headless)
            self._page = self._browser.new_page()
            self._page.set_default_timeout(15000)
        return self._page

    def _generate_xpath_for_element(self, element: Dict[str, Any]) -> str:
        """Generate XPath only for top candidates to save processing time."""
        from ..utils.xpath_generator import generate_xpath_for_element
        return generate_xpath_for_element(element)
    
    def _is_element_interactive(self, tag: str, attrs: Dict[str, Any], role: str) -> bool:
        """
        Universal element interactivity detection - works for any website.
        
        Args:
            tag: Element tag name
            attrs: Element attributes
            role: Accessibility role
            
        Returns:
            True if element is interactive, False otherwise
        """
        # Text nodes are not interactive but are valid for validation
        if tag == '#text' or not tag:
            return False
        
        # Universal interactive tags (works across all websites)
        interactive_tags = ['button', 'a', 'input', 'select', 'textarea', 'option', 'label', 'form', 'fieldset', 'summary', 'details']
        if tag.lower() in interactive_tags:
            return True
        
        # Universal interactive roles (accessibility standard)
        interactive_roles = [
            'button', 'link', 'menuitem', 'tab', 'option', 'radio', 'checkbox', 'switch', 
            'textbox', 'combobox', 'listbox', 'menu', 'menubar', 'toolbar', 'slider', 
            'progressbar', 'scrollbar', 'tablist', 'tree', 'grid', 'cell', 'row', 
            'columnheader', 'rowheader', 'dialog', 'alertdialog', 'log', 'marquee', 
            'status', 'timer', 'tooltip', 'searchbox', 'spinbutton', 'tabpanel'
        ]
        if role and role.lower() in interactive_roles:
            return True
        
        # Check for universal click handlers
        click_handlers = ['onclick', 'onmousedown', 'onmouseup', 'ontouchstart', 'ontouchend']
        if any(attrs.get(handler) for handler in click_handlers):
            return True
        
        # Check for tabindex (focusable elements)
        tabindex = attrs.get('tabindex')
        if tabindex and str(tabindex).isdigit() and int(tabindex) >= 0:
            return True
        
        # Universal input type detection
        if tag.lower() == 'input':
            input_type = attrs.get('type', '').lower()
            # All input types are interactive except 'hidden'
            if input_type != 'hidden':
                return True
        
        # Universal data attributes indicating interactivity
        interactive_data_attrs = [
            'data-testid', 'data-id', 'data-value', 'data-action', 'data-click', 
            'data-toggle', 'data-target', 'data-controls', 'data-dismiss',
            'data-bs-toggle', 'data-bs-target', 'data-bs-dismiss'
        ]
        if any(attrs.get(attr) for attr in interactive_data_attrs):
            return True
        
        # Check for ARIA attributes indicating interactivity
        aria_interactive = ['aria-expanded', 'aria-selected', 'aria-checked', 'aria-pressed']
        if any(attrs.get(attr) for attr in aria_interactive):
            return True
        
        # Check for common interactive class patterns
        class_name = attrs.get('class', '').lower()
        interactive_class_patterns = [
            'btn', 'button', 'link', 'clickable', 'interactive', 'action',
            'nav', 'menu', 'tab', 'toggle', 'dropdown', 'accordion'
        ]
        if any(pattern in class_name for pattern in interactive_class_patterns):
            return True
        
        return False

    def _detect_universal_elements(self, page) -> Dict[str, Any]:
        """
        Universal element detection that works for any website structure.
        Detects common UI patterns without hardcoded assumptions.
        """
        if not _PLAYWRIGHT or not page:
            return {}
        
        try:
            # Detect common UI patterns universally
            patterns = {
                'filters': self._detect_filter_elements(page),
                'buttons': self._detect_button_elements(page),
                'forms': self._detect_form_elements(page),
                'navigation': self._detect_navigation_elements(page),
                'content': self._detect_content_elements(page)
            }
            
            print(f"🔍 Universal element detection:")
            for pattern_type, elements in patterns.items():
                print(f"   {pattern_type}: {len(elements)} elements")
            
            return patterns
        except Exception as e:
            print(f"⚠️  Universal element detection failed: {e}")
            return {}

    def _detect_filter_elements(self, page) -> List[Dict[str, Any]]:
        """Detect filter elements universally."""
        filter_selectors = [
            '[role="button"][aria-expanded]',  # Dropdown filters
            'button[data-testid*="filter"]',   # Test ID filters
            'button[class*="filter"]',         # Class-based filters
            'input[type="checkbox"]',          # Checkbox filters
            'input[type="radio"]',             # Radio filters
            'select',                          # Select filters
            '[aria-label*="filter" i]',        # Aria label filters
            'button:has-text("Filter")',       # Text-based filters
            'button:has-text("Sort")',         # Sort filters
            'button:has-text("Category")',     # Category filters
        ]
        
        elements = []
        for selector in filter_selectors:
            try:
                locators = page.locator(selector)
                for i in range(locators.count()):
                    element = locators.nth(i)
                    if element.is_visible():
                        elements.append({
                            'selector': selector,
                            'text': element.text_content() or '',
                            'type': 'filter'
                        })
            except:
                continue
        
        return elements

    def _detect_button_elements(self, page) -> List[Dict[str, Any]]:
        """Detect button elements universally."""
        button_selectors = [
            'button',
            'a[role="button"]',
            '[role="button"]',
            'input[type="button"]',
            'input[type="submit"]',
            '[data-testid*="button"]',
            '[class*="btn"]',
            '[class*="button"]'
        ]
        
        elements = []
        for selector in button_selectors:
            try:
                locators = page.locator(selector)
                for i in range(locators.count()):
                    element = locators.nth(i)
                    if element.is_visible():
                        elements.append({
                            'selector': selector,
                            'text': element.text_content() or '',
                            'type': 'button'
                        })
            except:
                continue
        
        return elements

    def _detect_form_elements(self, page) -> List[Dict[str, Any]]:
        """Detect form elements universally."""
        form_selectors = [
            'input[type="text"]',
            'input[type="email"]',
            'input[type="password"]',
            'input[type="search"]',
            'textarea',
            'select',
            'input[type="checkbox"]',
            'input[type="radio"]'
        ]
        
        elements = []
        for selector in form_selectors:
            try:
                locators = page.locator(selector)
                for i in range(locators.count()):
                    element = locators.nth(i)
                    if element.is_visible():
                        elements.append({
                            'selector': selector,
                            'text': element.get_attribute('placeholder') or element.text_content() or '',
                            'type': 'form'
                        })
            except:
                continue
        
        return elements

    def _detect_navigation_elements(self, page) -> List[Dict[str, Any]]:
        """Detect navigation elements universally."""
        nav_selectors = [
            'nav a',
            '[role="navigation"] a',
            '[role="menubar"] a',
            '[role="tablist"] a',
            '.nav a',
            '.menu a',
            '.breadcrumb a',
            'header a',
            'footer a'
        ]
        
        elements = []
        for selector in nav_selectors:
            try:
                locators = page.locator(selector)
                for i in range(locators.count()):
                    element = locators.nth(i)
                    if element.is_visible():
                        elements.append({
                            'selector': selector,
                            'text': element.text_content() or '',
                            'type': 'navigation'
                        })
            except:
                continue
        
        return elements

    def _detect_content_elements(self, page) -> List[Dict[str, Any]]:
        """Detect content elements universally."""
        content_selectors = [
            'h1, h2, h3, h4, h5, h6',  # Headings
            'p',                        # Paragraphs
            'div[class*="content"]',    # Content divs
            'article',                  # Articles
            'section',                  # Sections
            'main',                     # Main content
            '[role="main"]'             # Main role
        ]
        
        elements = []
        for selector in content_selectors:
            try:
                locators = page.locator(selector)
                for i in range(locators.count()):
                    element = locators.nth(i)
                    if element.is_visible():
                        text = element.text_content() or ''
                        if text and len(text.strip()) > 10:  # Only meaningful content
                            elements.append({
                                'selector': selector,
                                'text': text[:100] + '...' if len(text) > 100 else text,
                                'type': 'content'
                            })
            except:
                continue
        
        return elements

    def _close(self) -> None:
        try:
            if self._page:
                self._page.close()
        except Exception:
            pass
        try:
            if self._browser:
                self._browser.close()
        except Exception:
            pass
        try:
            if self._playwright:
                self._playwright.stop()
        except Exception:
            pass
        self._page = None
        self._browser = None
        self._playwright = None
    
    @classmethod
    def cleanup_models(cls) -> None:
        """Cleanup shared models (call at end of test suite)"""
        if cls._shared_pipeline is not None:
            print("🧹 Cleaning up shared models...")
            del cls._shared_pipeline
            cls._shared_pipeline = None
            print("✅ Models cleaned up")

    def _inline_snapshot(self) -> Dict[str, Any]:
        # Skip CDP entirely and use JavaScript fallback which we know works
        print("🔧 Using JavaScript fallback snapshot (CDP disabled for debugging)")
        return self._fallback_javascript_snapshot()
        
        # First try to get DOM + accessibility tree via CDP
        try:
            from ..bridge.cdp_bridge import capture_complete_snapshot
            from ..descriptors.merge import merge_dom_ax, enhance_element_descriptor
            from .config import get_config
            
            # Get configuration for canonical descriptor building
            config = get_config()
            print(f"🔧 Using canonical mode: {config.get_canonical_mode().value}")
            
            # Capture complete snapshot with accessibility tree
            snapshot = capture_complete_snapshot(self._page, include_frames=True)
            
            # Merge DOM and accessibility tree based on configuration
            merged_nodes = merge_dom_ax(snapshot.dom_nodes, snapshot.ax_nodes)
            print(f"✅ CDP Integration: Merged {len(merged_nodes)} nodes using {config.get_canonical_mode().value} mode")
            
            # Convert to the expected format
            elements = []
            for node in merged_nodes:
                # Extract attributes
                attrs = node.get('attributes', {})
                if isinstance(attrs, list):
                    attrs_dict = {}
                    for i in range(0, len(attrs), 2):
                        if i + 1 < len(attrs):
                            attrs_dict[str(attrs[i])] = attrs[i + 1]
                    attrs = attrs_dict
                
                # Get text content using comprehensive extraction
                from ..descriptors.merge import extract_comprehensive_text
                text = extract_comprehensive_text(node)
                
                # Get tag name
                tag = (node.get('tagName') or node.get('nodeName') or node.get('tag') or '').upper()
                
                # Get role from accessibility tree
                role = attrs.get('role', '')
                if not role and 'accessibility' in node:
                    role = node['accessibility'].get('role', '')
                if not role:
                    role = node.get('type', '')
                
                # Debug: Print element details
                print(f"🔍 Processing element: tag='{tag}', text='{text[:50]}{'...' if len(text) > 50 else ''}', attrs={len(attrs)}")
                
                # Don't generate XPath here - will be generated only for top K candidates
                # This saves processing time and memory
                xpath = node.get('xpath', '')  # Keep existing if present
                
                # Determine if element is interactive
                interactive = self._is_element_interactive(tag, attrs, role)
                
                # NO FILTERING - Let AI models see ALL elements
                # MiniLM and MarkupLM will decide relevance based on semantic similarity
                
                # Create element descriptor
                element = {
                    'text': text,
                    'tag': tag,
                    'role': role or None,
                    'attrs': attrs,
                    'xpath': xpath,
                    'bbox': node.get('bbox', {'x': 0, 'y': 0, 'width': 0, 'height': 0, 'w': 0, 'h': 0}),
                    'visible': node.get('visible', True),
                    'below_fold': node.get('below_fold', False),
                    'interactive': interactive,
                    'backendNodeId': node.get('backendNodeId'),
                    'accessibility': node.get('accessibility', {}),
                    'meta': {}  # Initialize meta field for frame_hash
                }
                
                # Enhance with accessibility information
                element = enhance_element_descriptor(element)
                elements.append(element)
            
            # Add hierarchical context if enabled
            from .config import get_config
            config = get_config()
            if config.should_use_hierarchy():
                try:
                    from ..descriptors.hierarchy import HierarchyContextBuilder
                    hierarchy_builder = HierarchyContextBuilder()
                    
                    # Debug: Show elements before adding context
                    print(f"🔍 Adding hierarchical context to {len(elements)} elements")
                    
                    # Add context to elements
                    elements = hierarchy_builder.add_context_to_elements(elements)
                    
                    # Debug: Show context was added
                    context_count = sum(1 for el in elements if el.get('context', {}).get('hierarchy_path', '') not in ['PENDING', 'ERROR', ''])
                    print(f"✅ Added hierarchical context to {context_count}/{len(elements)} elements")
                    
                    # Show sample context
                    for i, el in enumerate(elements[:3]):
                        context = el.get('context', {})
                        hierarchy_path = context.get('hierarchy_path', 'N/A')
                        print(f"   Element {i+1}: {hierarchy_path}")
                        
                except Exception as e:
                    print(f"⚠️  Failed to add hierarchical context: {e}")
                    import traceback
                    traceback.print_exc()
                    # Continue without hierarchy context
            
            # Return in expected format
            frame_url = getattr(self._page, "url", "")
            fh = compute_frame_hash(frame_url, elements)
            
            # Ensure frame_hash is properly set for all elements AFTER hierarchy context
            for it in elements:
                # Create meta dict if it doesn't exist
                if "meta" not in it:
                    it["meta"] = {}
                it["meta"]["frame_hash"] = fh
                it["frame_url"] = frame_url
                
                # Debug: Verify frame_hash is set
                if "meta" not in it or "frame_hash" not in it["meta"]:
                    print(f"⚠️  Element missing frame_hash: {it.get('tag', 'unknown')}")
                    it["meta"] = it.get("meta", {})
                    it["meta"]["frame_hash"] = fh
                
            frames = [{"frame_url": frame_url, "elements": elements, "frame_hash": fh}]
            return {"elements": elements, "dom_hash": dom_hash(frames), "url": frame_url}
                
        except Exception as e:
            print(f"⚠️  CDP accessibility integration failed: {e}")
            print("   Falling back to basic DOM snapshot...")
            import traceback
            traceback.print_exc()
            
            # Fallback to JavaScript approach
            return self._fallback_javascript_snapshot()
        
    def _fallback_javascript_snapshot(self) -> Dict[str, Any]:
        """Fallback JavaScript-based snapshot when CDP fails."""
        try:
            page = self._ensure_browser()
            if not page:
                return {"elements": [], "dom_hash": "", "url": ""}
            
            # Ensure page is fully loaded before running JavaScript
            print("🔄 Ensuring page is fully loaded before JavaScript...")
            page.wait_for_load_state("domcontentloaded", timeout=15000)
            page.wait_for_load_state("load", timeout=15000)
            page.wait_for_load_state("networkidle", timeout=15000)
            page.wait_for_timeout(5000)
            
            # Force re-render
            page.evaluate("() => { document.body.offsetHeight; }")
            page.wait_for_timeout(2000)
            
            print("✅ Page fully loaded, running JavaScript...")
            
            # Use JavaScript to get DOM elements
            elements_js = page.evaluate("""
                () => {
                    try {
                        console.log('JavaScript fallback starting...');
                        console.log('Document ready state:', document.readyState);
                        console.log('Body exists:', !!document.body);
                        console.log('Body children count:', document.body ? document.body.children.length : 'N/A');
                        
                        const elements = [];
                        
                        // Try simple querySelectorAll first
                        const allElements = document.querySelectorAll('*');
                        console.log('querySelectorAll found:', allElements.length);
                        
                        // Process first few elements from querySelectorAll
                        for (let i = 0; i < Math.min(10, allElements.length); i++) {
                            const node = allElements[i];
                            console.log('Element', i, ':', node.tagName, node.textContent?.substring(0, 50));
                        }
                        
                        // Use TreeWalker as backup
                        const walker = document.createTreeWalker(
                            document.body,
                            NodeFilter.SHOW_ELEMENT,
                            null,
                            false
                        );
                        
                        let node;
                        let count = 0;
                        while (node = walker.nextNode()) {
                            count++;
                            if (count <= 5) {
                                console.log('TreeWalker Node', count, ':', node.tagName, node.textContent?.substring(0, 50));
                            }
                            if (node.nodeType === Node.ELEMENT_NODE) {
                            const rect = node.getBoundingClientRect();
                            const style = window.getComputedStyle(node);
                            
                            // Get text content
                            let text = '';
                            if (node.textContent) {
                                text = node.textContent.trim().substring(0, 200);
                            }
                            
                            // Get attributes
                            const attrs = {};
                            for (let attr of node.attributes) {
                                attrs[attr.name] = attr.value;
                            }
                            
                            // Determine if interactive
                            const interactive = ['button', 'a', 'input', 'select', 'textarea'].includes(node.tagName.toLowerCase()) ||
                                              node.onclick || node.getAttribute('onclick') ||
                                              style.cursor === 'pointer' ||
                                              node.getAttribute('role') === 'button';
                            
                            elements.push({
                                text: text,
                                tag: node.tagName.toUpperCase(),
                                role: node.getAttribute('role') || '',
                                attrs: attrs,
                                bbox: {
                                    x: Math.round(rect.x),
                                    y: Math.round(rect.y),
                                    width: Math.round(rect.width),
                                    height: Math.round(rect.height),
                                    w: Math.round(rect.width),
                                    h: Math.round(rect.height)
                                },
                                visible: rect.width > 0 && rect.height > 0 && style.display !== 'none',
                                below_fold: rect.y > window.innerHeight,
                                interactive: interactive,
                                backendNodeId: Math.random().toString(36).substr(2, 9),  // Generate fake ID
                                meta: {}  // Initialize meta field for frame_hash
                            });
                        }
                    }
                    
                        console.log('Total elements found:', elements.length);
                        console.log('First few elements:', elements.slice(0, 3));
                        
                        return elements;
                    } catch (error) {
                        console.error('JavaScript error:', error);
                        return [];
                    }
                }
            """)
            
            # Convert to expected format and add frame_hash
            print(f"🔍 JavaScript returned {len(elements_js)} elements")
            elements = []
            frame_url = getattr(page, "url", "")
            fh = compute_frame_hash(frame_url, elements_js)
            
            for element in elements_js:
                # Create meta dict
                element["meta"] = {"frame_hash": fh}
                element["frame_url"] = frame_url
                elements.append(element)
            
            print(f"🔍 Processed {len(elements)} elements")
            frames = [{"frame_url": frame_url, "elements": elements, "frame_hash": fh}]
            return {"elements": elements, "dom_hash": dom_hash(frames), "url": frame_url}
            
        except Exception as e:
            print(f"⚠️  JavaScript fallback also failed: {e}")
            import traceback
            traceback.print_exc()
            return {"elements": [], "dom_hash": "", "url": ""}

    def snapshot(self, url: Optional[str] = None) -> Dict[str, Any]:
        """Take a snapshot of the current page or navigate to a URL.
        
        Args:
            url: Optional URL to navigate to. If None, captures current page.
            
        Returns:
            Dictionary containing elements, DOM hash, and URL.
        """
        return self._snapshot(url)
    
    def _snapshot(self, url: Optional[str] = None) -> Dict[str, Any]:
        page = self._ensure_browser()
        if not _PLAYWRIGHT or not page:
            return {"elements": [], "dom_hash": "", "url": url or ""}
        if url:
            try:
                print(f"🔍 Loading page: {url}")
                page.goto(url, wait_until="networkidle", timeout=30000)
                
                # Wait for page to be fully loaded
                print("⏳ Waiting for page stability...")
                page.wait_for_load_state("domcontentloaded", timeout=10000)
                page.wait_for_load_state("networkidle", timeout=10000)
                
                # Additional wait for dynamic content
                print("⏳ Waiting for dynamic content...")
                page.wait_for_timeout(5000)
                
                # Try to dismiss any initial popups/overlays
                print("🔧 Dismissing overlays...")
                self._dismiss_overlays()
                
                # Universal dynamic content loading - works for any website
                print("🔧 Loading dynamic content...")
                self._load_dynamic_content(page)
                
                # Final stability check
                print("⏳ Final stability check...")
                page.wait_for_timeout(2000)
                
                print("✅ Page loaded successfully")
                
            except Exception as e:
                print(f"❌ Page loading exception: {e}")
                pass
        
        print("📸 Taking snapshot...")
        snapshot = self._inline_snapshot()
        elements_count = len(snapshot.get('elements', []))
        print(f"📊 Captured {elements_count} elements")
        
        return snapshot

    def resolve_selector(self, phrase: str, snapshot: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve a natural language phrase to a CSS selector.
        
        Args:
            phrase: Natural language description of the element to find.
            snapshot: Page snapshot from snapshot() method.
            
        Returns:
            Dictionary containing selector, confidence, and metadata.
        """
        return self._resolve_selector(phrase, snapshot)
    
    def _resolve_selector(self, phrase: str, snapshot: Dict[str, Any]) -> Dict[str, Any]:
        elements = snapshot.get("elements", [])
        if not elements:
            return {"selector": "", "confidence": 0.0, "reason": "no-elements", "candidates": []}
        ps = page_signature(str(snapshot.get("url", "")))
        frame_hash = (elements[0].get("meta") or {}).get("frame_hash") or ps
        parsed = self.intent.parse(phrase)
        label_key = compute_label_key([w for w in (parsed.target_phrase or phrase).split()])
        # Use parsed target phrase for better MiniLM matching
        target_phrase = parsed.target_phrase or phrase
        
        # DETAILED LOGGING: Data Creation
        print(f"\n🔍 DETAILED DATA CREATION LOGGING:")
        print(f"   Original Step: '{phrase}'")
        print(f"   Parsed Action: '{parsed.action}'")
        print(f"   Parsed Target Phrase: '{parsed.target_phrase}'")
        print(f"   Label Key: '{label_key}'")
        print(f"   Page Signature: '{ps}'")
        print(f"   Frame Hash: '{frame_hash}'")
        print(f"   Elements Count: {len(elements)}")
        
        # DETAILED LOGGING: Parameters being passed
        print(f"\n🔍 PARAMETERS PASSED TO PIPELINE:")
        print(f"   Query (target only for MiniLM): '{target_phrase}'")
        print(f"   User Intent (action): '{parsed.action}'")
        print(f"   Target (target phrase): '{parsed.target_phrase}'")
        print(f"   Top K: 10")
        
        result = self.pipeline.query(
            target_phrase,  # Query: target phrase only for MiniLM semantic matching
            elements,
            top_k=10,
            page_sig=ps,
            frame_hash=frame_hash,
            label_key=label_key,
            user_intent=parsed.action,  # Intent: action only (e.g., "click", "select")
            target=parsed.target_phrase,  # Target: target phrase only (e.g., "Apple filter")
        )
        candidates = []
        for item in (result.get("results") or [])[:10]:
            candidates.append({
                "selector": item.get("selector", ""),
                "score": float(item.get("score", 0.0)),
                "meta": item.get("meta", {}),
                "reasons": item.get("reasons", []),
            })
        if _DEBUG_CANDS:
            top3 = [f"{c['score']:.3f}:{c['selector']}" for c in candidates[:3]]
            print(f"[HER DEBUG] candidates: {' | '.join(top3)}")
        best = candidates[:1]
        if not best:
            return {"selector": "", "confidence": 0.0, "reason": "no-results", "candidates": candidates, "promo": {"page_sig": ps, "frame_hash": frame_hash, "label_key": label_key}, "strategy": result.get("strategy", "unknown")}
        return {
            "selector": best[0].get("selector", ""),
            "confidence": float(result.get("confidence", 0.0)),
            "meta": best[0].get("meta", {}),
            "reasons": best[0].get("reasons", []),
            "candidates": candidates,
            "promo": {"page_sig": ps, "frame_hash": frame_hash, "label_key": label_key},
            "strategy": result.get("strategy", "unknown"),
        }

    def _load_dynamic_content(self, page) -> None:
        """Universal dynamic content loading that works for any website."""
        if not _PLAYWRIGHT or not page:
            return
        
        print("🔄 Loading dynamic content universally...")
        
        # Wait for initial page load
        try:
            page.wait_for_load_state("domcontentloaded", timeout=10000)
            page.wait_for_load_state("networkidle", timeout=10000)
        except:
            pass
        
        # Detect if page has infinite scroll or dynamic content
        has_infinite_scroll = self._detect_infinite_scroll(page)
        has_dynamic_forms = self._detect_dynamic_forms(page)
        has_lazy_images = self._detect_lazy_images(page)
        
        print(f"   Infinite scroll: {has_infinite_scroll}")
        print(f"   Dynamic forms: {has_dynamic_forms}")
        print(f"   Lazy images: {has_lazy_images}")
        
        # Universal scrolling strategy
        if has_infinite_scroll or has_dynamic_forms or has_lazy_images:
            self._universal_scroll_strategy(page)
        
        # Detect universal UI patterns
        detected_patterns = self._detect_universal_elements(page)
        
        # Wait for any remaining dynamic content
        page.wait_for_timeout(2000)
        print("✅ Dynamic content loading completed")

    def _detect_infinite_scroll(self, page) -> bool:
        """Detect if page has infinite scroll patterns."""
        try:
            # Check for common infinite scroll indicators
            indicators = [
                'button:has-text("Load more")',
                'button:has-text("Show more")',
                '[data-testid*="load"]',
                '[data-testid*="more"]',
                '.load-more',
                '.show-more',
                '.infinite-scroll'
            ]
            
            for indicator in indicators:
                if page.locator(indicator).count() > 0:
                    return True
            
            # Check if page height changes significantly on scroll
            initial_height = page.evaluate("document.body.scrollHeight")
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(1000)
            final_height = page.evaluate("document.body.scrollHeight")
            
            return final_height > initial_height * 1.2
        except:
            return False

    def _detect_dynamic_forms(self, page) -> bool:
        """Detect if page has dynamic form elements."""
        try:
            # Check for dynamic form patterns
            patterns = [
                'input[type="radio"]',
                'input[type="checkbox"]',
                'select',
                'option',
                '[role="radio"]',
                '[role="checkbox"]',
                '[role="option"]'
            ]
            
            for pattern in patterns:
                if page.locator(pattern).count() > 0:
                    return True
            
            return False
        except:
            return False

    def _detect_lazy_images(self, page) -> bool:
        """Detect if page has lazy-loaded images."""
        try:
            # Check for lazy loading indicators
            lazy_indicators = [
                'img[loading="lazy"]',
                'img[data-src]',
                'img[data-lazy]',
                '.lazy',
                '.lazy-load'
            ]
            
            for indicator in lazy_indicators:
                if page.locator(indicator).count() > 0:
                    return True
            
            return False
        except:
            return False

    def _universal_scroll_strategy(self, page) -> None:
        """Universal scrolling strategy that works for any website."""
        try:
            # Get initial page state
            initial_height = page.evaluate("document.body.scrollHeight")
            viewport_height = page.evaluate("window.innerHeight")
            
            # Progressive scrolling to load content
            scroll_positions = [
                0.25,  # 25% down
                0.5,   # 50% down
                0.75,  # 75% down
                1.0,   # Bottom
                0.5,   # Back to middle
                0.25   # Back to top area
            ]
            
            for position in scroll_positions:
                scroll_y = int(initial_height * position)
                page.evaluate(f"window.scrollTo(0, {scroll_y})")
                page.wait_for_timeout(1000)
                
                # Check if new content loaded
                current_height = page.evaluate("document.body.scrollHeight")
                if current_height > initial_height * 1.1:  # 10% increase
                    print(f"   New content detected at {position*100}% scroll")
                    initial_height = current_height
            
            # Final scroll to top for better element visibility
            page.evaluate("window.scrollTo(0, 0)")
            page.wait_for_timeout(500)
            
        except Exception as e:
            print(f"⚠️  Universal scroll strategy failed: {e}")

    def _dismiss_overlays(self) -> None:
        if not _PLAYWRIGHT or not self._page:
            return
        selectors = [
            'button[aria-label="Close"]',
            'button[aria-label="Dismiss"]',
            'button:has-text("Accept")',
            'button:has-text("Accept all")',
            'button:has-text("Accept All")',
            'button:has-text("Agree")',
            'button:has-text("I agree")',
            'button:has-text("Got it")',
            'button:has-text("OK")',
            '#onetrust-accept-btn-handler',
            '.cc-allow',
            '[data-testid="close"]',
            'button:has-text("No thanks")',
            'button:has-text("Continue")',
            '[aria-label="Close dialog"]',
            '[aria-label="Close modal"]',
            '.modal button.close',
            '.popup button.close',
        ]
        for sel in selectors:
            try:
                # Try to find all matching elements
                els = self._page.query_selector_all(sel)
                for el in els[:2]:  # Click max 2 of each type
                    try:
                        if el.is_visible():
                            el.click(timeout=500)
                            time.sleep(0.2)
                    except Exception:
                        continue
            except Exception:
                continue

    def _scroll_into_view(self, target) -> None:
        """Scroll element into view if it's not visible."""
        if not _PLAYWRIGHT or not self._page:
            return
        
        try:
            # Handle both selector string and element object
            if isinstance(target, str):
                # If it's a selector string, get the element first
                element = self._page.locator(f"xpath={target}").first
                element.scroll_into_view_if_needed(timeout=2000)
            else:
                # If it's an element object, check if it's in viewport
                if not hasattr(target, 'bounding_box'):
                    return
                    
                bbox = target.bounding_box()
                if not bbox:
                    return
                
                viewport = self._page.viewport_size
                if not viewport:
                    return
                
                # Check if element is already in viewport
                if (bbox['x'] >= 0 and bbox['y'] >= 0 and 
                    bbox['x'] + bbox['width'] <= viewport['width'] and 
                    bbox['y'] + bbox['height'] <= viewport['height']):
                    return
                
                # Scroll element into view
                target.scroll_into_view_if_needed(timeout=2000)
        except Exception:
            pass

    def do_action(self, action: str, selector: str, value: Optional[str] = None, promo: Optional[Dict[str, Any]] = None, user_intent: str = "") -> None:
        """Execute an action on a page element.
        
        Args:
            action: Action to perform (click, type, etc.).
            selector: CSS selector for the target element.
            value: Optional value for input actions.
            promo: Optional promotion metadata.
            user_intent: Optional user intent description.
        """
        return self._do_action(action, selector, value, promo or {}, user_intent)
    
    def wait_for_timeout(self, timeout: int) -> None:
        """Wait for a specified timeout.
        
        Args:
            timeout: Timeout in milliseconds.
        """
        if self._page:
            self._page.wait_for_timeout(timeout)
    
    def get_current_url(self) -> str:
        """Get the current page URL.
        
        Returns:
            Current page URL.
        """
        return self._page.url if self._page else ""
    
    def _do_action(self, action: str, selector: str, value: Optional[str], promo: Dict[str, Any], user_intent: str = "") -> None:
        if not _PLAYWRIGHT or not self._page:
            raise RuntimeError("Playwright unavailable for action execution")
        # Try scroll + overlay dismiss before attempting action
        self._scroll_into_view(selector)
        self._dismiss_overlays()
        # Strict executor if available
        if Executor is not None and action not in {"back", "refresh", "wait"}:
            try:
                ex = Executor(self._page)
                kw = dict(page_sig=promo.get("page_sig"), frame_hash=promo.get("frame_hash"), label_key=promo.get("label_key"))
                if action == "type" and value is not None:
                    ex.type(selector, str(value), **kw)
                    return
                if action == "press" and value:
                    ex.press(selector, str(value), **kw)
                    return
                if action == "hover":
                    self._page.locator(f"xpath={selector}").first.hover()
                    return
            except Exception as e:
                logger.warning(f"Executor failed for action '{action}': {e}, falling back to direct Playwright")
                # Fall through to direct Playwright implementation
        
        # Direct Playwright implementation
        if action in {"check", "uncheck"}:
            handle = self._page.locator(f"xpath={selector}").first
            try:
                if action == "check":
                    handle.check()
                else:
                    handle.uncheck()
                return
            except Exception:
                pass
        # Fallback raw Playwright and navigation/waits
        if action == "type" and value is not None:
            element = self._page.locator(f"xpath={selector}").first
            self._scroll_into_view(element)
            element.fill(value)
            return
        if action == "sendkeys" and value is not None:
            element = self._page.locator(f"xpath={selector}").first
            self._scroll_into_view(element)
            element.type(value)
            return
        if action == "press" and value:
            element = self._page.locator(f"xpath={selector}").first
            self._scroll_into_view(element)
            element.press(str(value))
            return
        if action == "hover":
            element = self._page.locator(f"xpath={selector}").first
            self._scroll_into_view(element)
            element.hover()
            return
        if action in {"check", "uncheck"}:
            handle = self._page.locator(f"xpath={selector}").first
            self._scroll_into_view(handle)
            try:
                if action == "check":
                    handle.check()
                else:
                    handle.uncheck()
                return
            except Exception:
                handle.click()
                return
        if action == "select":
            # For select actions, try to find the most visible/clickable element
            self._click_best_element(selector, user_intent)
            return
        if action == "back":
            try:
                self._page.go_back()
            except Exception:
                pass
            return
        if action == "refresh":
            try:
                self._page.reload()
            except Exception:
                pass
            return
        if action == "wait":
            try:
                secs = float(value or 1)
            except Exception:
                secs = 1.0
            self._page.wait_for_timeout(int(secs * 1000))
            return
        # For click actions, try to find the best element
        self._click_best_element(selector, user_intent)


    def _click_best_element(self, selector: str, user_intent: str = "") -> None:
        """Click the best element when there are multiple matches, using user intent."""
        if not _PLAYWRIGHT or not self._page:
            return
        
        try:
            # Get all matching elements
            locators = self._page.locator(f"xpath={selector}")
            count = locators.count()
            if count == 0:
                raise Exception(f"No elements found for selector: {selector}")
            elif count == 1:
                # Only one element, scroll into view and click it
                element = locators.first
                self._scroll_into_view(element)
                element.click()
                return
            
            # Multiple elements - find the best one using user intent
            print(f"🔍 Found {count} elements with selector: {selector}")
            print(f"🎯 User intent: '{user_intent}'")
            
            # Universal element processing - no hardcoded filtering
            print(f"   Action type: {user_intent} | Processing ALL elements universally")
            
            # Try to find the most suitable element based on universal criteria
            best_element = None
            best_score = -1
            element_details = []
            
            for i in range(count):
                try:
                    element = locators.nth(i)
                    
                    # Scroll into view for better interaction
                    try:
                        element.scroll_into_view_if_needed()
                        self._page.wait_for_timeout(500)
                    except:
                        pass
                    
                    # Get element properties
                    bbox = element.bounding_box()
                    
                    # Get element text and attributes for better scoring
                    try:
                        text = element.text_content() or ""
                        tag_name = element.evaluate("el => el.tagName.toLowerCase()") or ""
                        role = element.get_attribute("role") or ""
                        href = element.get_attribute("href") or ""
                        class_name = element.get_attribute("class") or ""
                        id_attr = element.get_attribute("id") or ""
                    except:
                        text = ""
                        tag_name = ""
                        role = ""
                        href = ""
                        class_name = ""
                        id_attr = ""
                    
                    # Calculate score based on multiple factors
                    score = bbox['width'] * bbox['height']  # Area as base score
                    
                    # Universal heuristics - work for any website
                    
                    # HEURISTIC 1: Skip completely off-screen elements
                    if bbox['y'] < -100 or bbox['x'] < -100:  # Far off-screen
                        continue
                    
                    # HEURISTIC 2: Skip extremely small elements (likely decorative)
                    if bbox['width'] < 5 or bbox['height'] < 5:
                        continue
                    
                    # HEURISTIC 3: Skip elements with no meaningful content (unless they have important attributes)
                    if not text.strip() and not href and not role and not id_attr and not class_name:
                        continue
                    
                    # HEURISTIC 4: Universal intent matching
                    intent_score = 0
                    if user_intent:
                        intent_lower = user_intent.lower()
                        text_lower = text.lower()
                        
                        # Exact text match gets highest score
                        if intent_lower in text_lower:
                            intent_score += 1000
                        
                        # Partial word matches (case-insensitive) - optimized
                        intent_words = set(w.strip() for w in intent_lower.split() if w.strip())
                        text_words = set(w.strip() for w in text_lower.split() if w.strip())
                        word_matches = len(intent_words.intersection(text_words))
                        intent_score += word_matches * 200
                        
                        # Check attributes for intent
                        all_attrs = f"{href} {id_attr} {class_name} {role}".lower()
                        if any(word in all_attrs for word in intent_words):
                            intent_score += 300
                    
                    # HEURISTIC 5: Universal position-based scoring
                    viewport = self._page.viewport_size
                    if viewport:
                        # Bonus for being visible in viewport
                        element_center_x = bbox['x'] + bbox['width'] / 2
                        element_center_y = bbox['y'] + bbox['height'] / 2
                        
                        # Check if element is in viewport
                        in_viewport = (
                            0 <= bbox['x'] < viewport['width'] and
                            0 <= bbox['y'] < viewport['height'] and
                            bbox['width'] > 0 and bbox['height'] > 0
                        )
                        
                        if in_viewport:
                            # Bonus for being in viewport
                            score += 500
                            
                            # Bonus for being in upper portion of viewport (more likely to be important)
                            if bbox['y'] < viewport['height'] * 0.5:
                                score += 300
                        else:
                            # Small penalty for off-screen elements
                            score -= 100
                    
                    # HEURISTIC 6: Universal interactive element detection
                    interactive_tags = ['a', 'button', 'input', 'select', 'textarea', 'option', 'label']
                    interactive_roles = ['button', 'link', 'menuitem', 'tab', 'option', 'radio', 'checkbox', 'switch']
                    
                    if tag_name in interactive_tags or role in interactive_roles:
                        score += 500
                    
                    # HEURISTIC 7: Content quality bonus
                    if text and len(text.strip()) > 0:
                        # Bonus for meaningful text length
                        text_length = len(text.strip())
                        if 5 <= text_length <= 100:  # Sweet spot for button text
                            score += 200
                        elif text_length > 100:  # Longer text might be less clickable
                            score += 100
                        else:  # Very short text
                            score += 50
                    
                    # HEURISTIC 8: Accessibility and identification bonus
                    if id_attr:
                        score += 300  # ID is very reliable
                    if role:
                        score += 200  # Role is good for accessibility
                    if href:
                        score += 150  # Href indicates navigation
                    if class_name and any(keyword in class_name.lower() for keyword in ['btn', 'button', 'link', 'nav', 'menu']):
                        score += 100  # Semantic class names
                    
                    # HEURISTIC 9: Universal element scoring - no hardcoded penalties
                    # All elements are potentially valid targets based on user intent and context
                    
                    # Add intent score
                    score += intent_score
                    
                    element_details.append({
                        'index': i,
                        'element': element,
                        'score': score,
                        'text': text[:50],
                        'tag': tag_name,
                        'bbox': bbox,
                        'href': href[:50] if href else '',
                        'intent_score': intent_score
                    })
                    
                    if score > best_score:
                        best_score = score
                        best_element = element
                        
                except Exception as e:
                    print(f"⚠️  Error evaluating element {i}: {e}")
                    continue
            
            # Log all elements for debugging
            print(f"📋 Element analysis (sorted by score):")
            for detail in sorted(element_details, key=lambda x: x['score'], reverse=True)[:5]:
                print(f"  {detail['index']+1}. Score: {detail['score']:.1f} | {detail['tag']} | '{detail['text']}' | Intent: {detail['intent_score']:.0f} | Pos: ({detail['bbox']['x']:.0f}, {detail['bbox']['y']:.0f})")
            
            # Show which element will be clicked
            if best_element:
                best_index = next(i for i, detail in enumerate(element_details) if detail['element'] == best_element)
                best_detail = element_details[best_index]
                print(f"🎯 SELECTED ELEMENT FOR CLICKING:")
                print(f"   Index: {best_index+1} (out of {count} total elements)")
                print(f"   Score: {best_detail['score']:.1f}")
                print(f"   Tag: {best_detail['tag']}")
                print(f"   Text: '{best_detail['text']}'")
                print(f"   Position: ({best_detail['bbox']['x']:.0f}, {best_detail['bbox']['y']:.0f})")
                print(f"   Intent Score: {best_detail['intent_score']:.0f}")
                print(f"   XPath: {selector}")
            
            if best_element:
                best_index = next(i for i, detail in enumerate(element_details) if detail['element'] == best_element)
                print(f"✅ Clicking best element #{best_index+1} (score: {best_score:.1f})")
                self._scroll_into_view(best_element)
                best_element.click()
            else:
                print(f"⚠️  No suitable element found, clicking first visible one")
                element = locators.first
                self._scroll_into_view(element)
                element.click()
                
        except Exception as e:
            print(f"❌ Error clicking element: {e}")
            # Fallback to first element
            try:
                element = self._page.locator(f"xpath={selector}").first
                self._scroll_into_view(element)
                element.click()
            except Exception as e2:
                print(f"❌ Fallback click also failed: {e2}")
                raise

    def _validate(self, step: str) -> bool:
        if not _PLAYWRIGHT or not self._page:
            return False
        low = step.lower()
        if low.startswith("validate it landed on ") or low.startswith("validate landed on "):
            expected = step.split(" on ", 1)[1].strip().strip(",")
            try:
                # Wait a bit for any redirects to complete
                self._page.wait_for_timeout(2000)
                current_url = self._page.url
                
                # Try exact match first
                current = self._normalize_url(current_url)
                exp_norm = self._normalize_url(expected)
                if current == exp_norm:
                    return True
                
                # Universal URL validation - check for key components
                expected_parts = [part.strip() for part in expected.lower().split('/') if part.strip()]
                current_parts = [part.strip() for part in current_url.lower().split('/') if part.strip()]
                
                # Check if key parts of expected URL are present in current URL - optimized
                current_parts_set = set(current_parts)
                matching_parts = sum(1 for part in expected_parts if part in current_parts_set)
                if matching_parts >= len(expected_parts) * 0.6:  # 60% match threshold
                    return True
                
                return False
            except Exception as e:
                print(f"Validation error: {e}")
                return False
        if low.startswith("validate ") and " is visible" in low:
            target = step[9:].rsplit(" is visible", 1)[0].strip()
            # Remove quotes from target text
            target = target.strip("'\"")
            
            try:
                # Try multiple strategies to find the text
                strategies = [
                    f"text={target}",  # Exact text match
                    f"text*={target}",  # Partial text match
                    f"[aria-label*='{target}']",  # Aria label
                    f"[title*='{target}']",  # Title attribute
                ]
                
                for strategy in strategies:
                    try:
                        locator = self._page.locator(strategy)
                        if locator.count() > 0:
                            # Check if any matching element is visible
                            for i in range(locator.count()):
                                if locator.nth(i).is_visible():
                                    return True
                    except Exception:
                        continue
                
                # Fallback: use snapshot-based search
                shot = self._snapshot()
                resolved = self._resolve_selector(target, shot)
                sel = resolved.get("selector", "")
                if sel:
                    try:
                        self._page.locator(f"xpath={sel}").first.wait_for(state="visible", timeout=2000)
                        return True
                    except Exception:
                        pass
                
                return False
            except Exception as e:
                print(f"Text validation error: {e}")
                return False
        if low.startswith("validate ") and " exists" in low:
            target = step[9:].rsplit(" exists", 1)[0].strip()
            shot = self._snapshot()
            resolved = self._resolve_selector(target, shot)
            sel = resolved.get("selector", "")
            if not sel:
                return False
            try:
                count = self._page.locator(f"xpath={sel}").count()
                return count > 0
            except Exception:
                return False
        if "validate page has text" in low:
            # Expect quoted text or plain text
            parts = step.lower().split("validate page has text", 1)
            if len(parts) > 1:
                wanted = parts[1].strip().strip('"').strip("'")
                try:
                    content = self._page.content()
                    return wanted.lower() in content.lower()
                except Exception:
                    return False
            return False
        if "validate it landed on" in low:
            # Validate URL navigation
            parts = step.lower().split("validate it landed on", 1)
            if len(parts) > 1:
                expected_url = parts[1].strip().strip('"').strip("'")
                try:
                    current_url = self._page.url
                    # Check if current URL contains the expected URL or vice versa
                    return expected_url in current_url or current_url in expected_url
                except Exception:
                    return False
            return False
        return False

    def run(self, steps: List[str]) -> List[StepResult]:
        logs: List[StepResult] = []
        try:
            for raw in steps:
                step = raw.strip()
                if not step:
                    continue
                if step.lower().startswith("open "):
                    url = step.split(" ", 1)[1].strip()
                    self._snapshot(url)
                    logs.append(StepResult(step=step, selector="", confidence=1.0, ok=True, info={"url": url}))
                    logger.info(json.dumps({"step": step, "selector": "", "confidence": 1.0, "ok": True}))
                    continue
                if step.lower().startswith("validate "):
                    ok = self._validate(step)
                    logs.append(StepResult(step=step, selector="", confidence=1.0, ok=ok, info={}))
                    logger.info(json.dumps({"step": step, "selector": "", "confidence": 1.0, "ok": ok}))
                    if not ok:
                        break
                    continue
                intent = self.intent.parse(step)
                
                # Debug: Print step JSON
                print(f"\n📋 STEP JSON:")
                print(f"  Raw Step: '{step}'")
                print(f"  Action: '{intent.action}'")
                print(f"  Target: '{intent.target_phrase}'")
                print(f"  Args: '{intent.args}'")
                print(f"  Constraints: {intent.constraints}")
                print(f"  Confidence: {intent.confidence}")
                
                attempts = 3
                selector = ""
                conf = 0.0
                last_err: Optional[str] = None
                candidates: List[Dict[str, Any]] = []
                for attempt in range(attempts):
                    shot = self._snapshot()
                    resolved = self._resolve_selector(intent.target_phrase or step, shot)
                    selector = resolved.get("selector", "")
                    conf = float(resolved.get("confidence", 0.0))
                    candidates = resolved.get("candidates", [])
                    if selector:
                        try:
                            # Use extracted value if available, otherwise use args
                            value = getattr(intent, 'value', None) or intent.args
                            self._do_action(intent.action, selector, value, resolved.get("promo", {}), step)
                            last_err = None
                            # Wait after successful action for page to update
                            if intent.action in ["click", "select"]:
                                time.sleep(2.0)  # Give page time to load after click
                            break
                        except Exception as e1:
                            last_err = str(e1)
                            self._dismiss_overlays()
                            time.sleep(1.0)  # Longer wait on failure
                            continue
                    else:
                        # No selector; try dismiss overlays, small wait, and retry
                        self._dismiss_overlays()
                        time.sleep(0.25)
                        continue
                ok = last_err is None
                info: Dict[str, Any] = {
                    "candidates": candidates,
                    "error": last_err,
                }
                logs.append(StepResult(step=step, selector=selector, confidence=conf, ok=ok, info=info))
                payload = {
                    "step": step,
                    "selector": selector,
                    "confidence": conf,
                    "ok": ok,
                    "candidates": candidates if _DEBUG_CANDS else None,
                    "info": {k: v for k, v in info.items() if k != "candidates"},
                }
                logger.info(json.dumps({k: v for k, v in payload.items() if v is not None}, ensure_ascii=False))
        finally:
            self._close()
        return logs


def run_steps(steps: List[str], *, headless: bool = True) -> None:
    runner = Runner(headless=headless)
    results = runner.run(steps)
    failed = [r for r in results if not r.ok]
    if failed:
        f = failed[0]
        raise AssertionError(f"Step failed: {f.step} | selector={f.selector} | info={f.info}")