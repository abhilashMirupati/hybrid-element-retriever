"""Enhanced snapshot management with frame support and delta tracking."""

import hashlib
import time
import logging
from typing import Any, Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class FrameSnapshot:
    """Snapshot of a single frame."""
    frame_path: str
    frame_id: Optional[str]
    frame_url: Optional[str]
    dom_hash: str
    elements: List[Dict[str, Any]]
    timestamp: float = field(default_factory=time.time)


@dataclass 
class PageSnapshot:
    """Complete page snapshot including all frames."""
    url: str
    main_frame: FrameSnapshot
    child_frames: List[FrameSnapshot] = field(default_factory=list)
    total_elements: int = 0
    timestamp: float = field(default_factory=time.time)
    
    def get_all_elements(self) -> List[Dict[str, Any]]:
        """Get all elements from all frames."""
        all_elements = self.main_frame.elements.copy()
        for frame in self.child_frames:
            all_elements.extend(frame.elements)
        return all_elements
    
    def get_frame_elements(self, frame_path: str) -> List[Dict[str, Any]]:
        """Get elements from specific frame."""
        if frame_path == "main":
            return self.main_frame.elements
        
        for frame in self.child_frames:
            if frame.frame_path == frame_path:
                return frame.elements
        
        return []


class SnapshotManager:
    """Manages page snapshots with delta tracking and frame support."""
    
    def __init__(self):
        self.snapshots: Dict[str, PageSnapshot] = {}
        self.element_hashes: Dict[str, Set[str]] = {}
        self.spa_listener_injected: Dict[str, bool] = {}
    
    def capture_snapshot(
        self,
        page: Any,
        session_id: str,
        include_frames: bool = True,
        include_shadow: bool = True
    ) -> Tuple[PageSnapshot, List[Dict[str, Any]]]:
        """Capture complete page snapshot including frames.
        
        Args:
            page: Playwright page
            session_id: Session identifier
            include_frames: Whether to include iframe content
            include_shadow: Whether to penetrate shadow DOM
            
        Returns:
            Tuple of (PageSnapshot, new_elements_needing_embedding)
        """
        # Inject SPA listeners if not already done
        if not self.spa_listener_injected.get(session_id):
            self._inject_spa_listeners(page)
            self.spa_listener_injected[session_id] = True
        
        # Capture main frame
        main_frame = self._capture_frame(
            page,
            "main",
            include_shadow=include_shadow
        )
        
        # Capture child frames
        child_frames = []
        if include_frames:
            child_frames = self._capture_child_frames(
                page,
                include_shadow=include_shadow
            )
        
        # Create snapshot
        snapshot = PageSnapshot(
            url=page.url,
            main_frame=main_frame,
            child_frames=child_frames,
            total_elements=len(main_frame.elements) + sum(len(f.elements) for f in child_frames)
        )
        
        # Detect new elements needing embedding
        new_elements = self._detect_new_elements(session_id, snapshot)
        
        # Store snapshot
        self.snapshots[session_id] = snapshot
        
        return snapshot, new_elements
    
    def _capture_frame(
        self,
        frame: Any,
        frame_path: str,
        include_shadow: bool = True
    ) -> FrameSnapshot:
        """Capture snapshot of a single frame."""
        elements = []
        
        try:
            # Extract elements with comprehensive attributes
            js_code = """
            () => {
                const elements = [];
                const seen = new Set();
                
                function extractElement(el, path = '') {
                    if (seen.has(el)) return;
                    seen.add(el);
                    
                    const tagName = el.tagName?.toLowerCase();
                    if (!tagName) return;
                    
                    // Skip script and style
                    if (tagName === 'script' || tagName === 'style') return;
                    
                    const elem = {
                        tag: tagName,
                        text: el.textContent?.trim().substring(0, 200) || '',
                        id: el.id || null,
                        classes: Array.from(el.classList || []),
                        attributes: {},
                        path: path,
                        isVisible: isElementVisible(el),
                        isInteractive: isElementInteractive(el),
                        boundingBox: el.getBoundingClientRect()
                    };
                    
                    // Collect all attributes
                    for (const attr of el.attributes || []) {
                        elem.attributes[attr.name] = attr.value;
                    }
                    
                    // Prioritize test IDs and ARIA
                    elem.dataTestId = el.getAttribute('data-testid') || el.getAttribute('data-test-id');
                    elem.ariaLabel = el.getAttribute('aria-label');
                    elem.ariaRole = el.getAttribute('role');
                    elem.ariaPressed = el.getAttribute('aria-pressed');
                    elem.ariaExpanded = el.getAttribute('aria-expanded');
                    
                    // Form-specific attributes
                    if (tagName === 'input' || tagName === 'textarea' || tagName === 'select') {
                        elem.type = el.type;
                        elem.name = el.name;
                        elem.value = el.value;
                        elem.placeholder = el.placeholder;
                        elem.disabled = el.disabled;
                        elem.ariaDisabled = el.getAttribute('aria-disabled') === 'true';
                        elem.required = el.required;
                        elem.pattern = el.pattern;
                        
                        // Label association
                        const label = document.querySelector(`label[for="${el.id}"]`);
                        elem.labelText = label?.textContent?.trim();
                    }
                    
                    // Handle contenteditable
                    elem.contentEditable = el.contentEditable === 'true';
                    
                    // SVG handling
                    if (tagName === 'svg' || el.closest('svg')) {
                        elem.isSvg = true;
                        elem.viewBox = el.getAttribute('viewBox');
                    }
                    
                    elements.push(elem);
                    
                    // Handle shadow DOM
                    if (el.shadowRoot && """ + str(include_shadow).lower() + """) {
                        const shadowElements = el.shadowRoot.querySelectorAll('*');
                        shadowElements.forEach(shadowEl => {
                            extractElement(shadowEl, path + '::shadow');
                        });
                    }
                    
                    // Process children
                    for (const child of el.children) {
                        extractElement(child, path);
                    }
                }
                
                function isElementVisible(el) {
                    const style = window.getComputedStyle(el);
                    const rect = el.getBoundingClientRect();
                    
                    return style.display !== 'none' &&
                           style.visibility !== 'hidden' &&
                           style.opacity !== '0' &&
                           rect.width > 0 &&
                           rect.height > 0;
                }
                
                function isElementInteractive(el) {
                    const tagName = el.tagName?.toLowerCase();
                    const role = el.getAttribute('role');
                    
                    return tagName === 'button' ||
                           tagName === 'a' ||
                           tagName === 'input' ||
                           tagName === 'select' ||
                           tagName === 'textarea' ||
                           role === 'button' ||
                           role === 'link' ||
                           el.onclick !== null ||
                           el.getAttribute('ng-click') ||
                           el.getAttribute('@click');
                }
                
                // Start extraction from body
                const body = document.body;
                if (body) {
                    extractElement(body);
                }
                
                return elements;
            }
            """
            
            elements = frame.evaluate(js_code)
            
            # Add frame context to elements
            for elem in elements:
                elem['frame_path'] = frame_path
            
        except Exception as e:
            logger.warning(f"Failed to capture frame {frame_path}: {e}")
        
        # Calculate DOM hash
        dom_hash = self._calculate_dom_hash(elements)
        
        # Get frame metadata
        frame_id = None
        frame_url = None
        try:
            frame_id = frame.evaluate("window.frameElement ? window.frameElement.id : null")
            frame_url = frame.url
        except Exception:
            pass
        
        return FrameSnapshot(
            frame_path=frame_path,
            frame_id=frame_id,
            frame_url=frame_url,
            dom_hash=dom_hash,
            elements=elements
        )
    
    def _capture_child_frames(
        self,
        page: Any,
        include_shadow: bool = True
    ) -> List[FrameSnapshot]:
        """Capture all child frames."""
        child_frames = []
        
        try:
            # Get all iframes
            iframe_handles = page.query_selector_all("iframe")
            
            for i, iframe_handle in enumerate(iframe_handles):
                try:
                    # Get frame attributes
                    frame_id = iframe_handle.get_attribute("id") or f"frame_{i}"
                    frame_src = iframe_handle.get_attribute("src")
                    
                    # Skip cross-origin frames
                    if frame_src and frame_src.startswith("http"):
                        origin = page.evaluate("window.location.origin")
                        frame_origin = frame_src.split("/")[0:3]
                        if len(frame_origin) >= 3 and "/".join(frame_origin) != origin:
                            logger.debug(f"Skipping cross-origin frame: {frame_src}")
                            continue
                    
                    # Get frame content
                    frame = iframe_handle.content_frame()
                    if frame:
                        frame_path = f"iframe[id='{frame_id}']" if frame_id != f"frame_{i}" else f"iframe:nth-of-type({i+1})"
                        frame_snapshot = self._capture_frame(
                            frame,
                            frame_path,
                            include_shadow=include_shadow
                        )
                        child_frames.append(frame_snapshot)
                        
                except Exception as e:
                    logger.debug(f"Failed to capture iframe {i}: {e}")
        
        except Exception as e:
            logger.warning(f"Failed to capture child frames: {e}")
        
        return child_frames
    
    def _inject_spa_listeners(self, page: Any) -> None:
        """Inject SPA route change listeners."""
        try:
            page.evaluate("""
                () => {
                    if (window.__herListenersInjected) return;
                    window.__herListenersInjected = true;
                    
                    // Store original methods
                    const originalPushState = history.pushState;
                    const originalReplaceState = history.replaceState;
                    
                    // Track route changes
                    window.__herRouteChanges = [];
                    
                    function notifyRouteChange(type, url) {
                        const event = new CustomEvent('__herRouteChange', {
                            detail: { type, url, timestamp: Date.now() }
                        });
                        window.dispatchEvent(event);
                        window.__herRouteChanges.push({ type, url, timestamp: Date.now() });
                    }
                    
                    // Wrap pushState
                    history.pushState = function(...args) {
                        const result = originalPushState.apply(history, args);
                        notifyRouteChange('pushState', window.location.href);
                        return result;
                    };
                    
                    // Wrap replaceState
                    history.replaceState = function(...args) {
                        const result = originalReplaceState.apply(history, args);
                        notifyRouteChange('replaceState', window.location.href);
                        return result;
                    };
                    
                    // Listen for popstate (back/forward)
                    window.addEventListener('popstate', () => {
                        notifyRouteChange('popstate', window.location.href);
                    });
                    
                    // Listen for hash changes
                    window.addEventListener('hashchange', () => {
                        notifyRouteChange('hashchange', window.location.href);
                    });
                }
            """)
        except Exception as e:
            logger.warning(f"Failed to inject SPA listeners: {e}")
    
    def check_route_changed(self, page: Any) -> bool:
        """Check if SPA route has changed."""
        try:
            changes = page.evaluate("window.__herRouteChanges || []")
            return len(changes) > 0
        except Exception:
            return False
    
    def clear_route_changes(self, page: Any) -> None:
        """Clear tracked route changes."""
        try:
            page.evaluate("window.__herRouteChanges = []")
        except Exception:
            pass
    
    def _calculate_dom_hash(self, elements: List[Dict[str, Any]]) -> str:
        """Calculate hash of DOM elements."""
        if not elements:
            return "0" * 64
        
        # Create stable hash from element signatures
        signatures = []
        for elem in elements:
            sig = f"{elem.get('tag')}|{elem.get('id')}|{elem.get('dataTestId')}|{len(elem.get('text', ''))}"
            signatures.append(sig)
        
        combined = "|".join(sorted(signatures))
        return hashlib.sha256(combined.encode()).hexdigest()
    
    def _detect_new_elements(
        self,
        session_id: str,
        snapshot: PageSnapshot
    ) -> List[Dict[str, Any]]:
        """Detect elements that need embedding."""
        new_elements = []
        current_hashes = set()
        
        # Get all elements
        all_elements = snapshot.get_all_elements()
        
        # Calculate element hashes
        for elem in all_elements:
            elem_hash = self._element_hash(elem)
            current_hashes.add(elem_hash)
            
            # Check if this element is new
            if session_id in self.element_hashes:
                if elem_hash not in self.element_hashes[session_id]:
                    new_elements.append(elem)
            else:
                # First snapshot, all elements are new
                new_elements.append(elem)
        
        # Update stored hashes
        self.element_hashes[session_id] = current_hashes
        
        return new_elements
    
    def _element_hash(self, element: Dict[str, Any]) -> str:
        """Calculate hash for a single element."""
        sig = f"{element.get('tag')}|{element.get('id')}|{element.get('dataTestId')}|{element.get('text', '')[:50]}"
        return hashlib.md5(sig.encode()).hexdigest()
    
    def needs_reindex(
        self,
        page: Any,
        session_id: str,
        threshold: float = 0.3
    ) -> bool:
        """Check if page needs reindexing."""
        # Check for route changes
        if self.check_route_changed(page):
            return True
        
        # Check for significant DOM changes
        if session_id in self.snapshots:
            old_snapshot = self.snapshots[session_id]
            
            # Quick hash comparison
            try:
                current_main_hash = hashlib.sha256(
                    page.content()[:5000].encode()
                ).hexdigest()
                
                if current_main_hash != old_snapshot.main_frame.dom_hash[:64]:
                    # Calculate change ratio
                    current_count = page.evaluate("document.querySelectorAll('*').length")
                    old_count = old_snapshot.total_elements
                    
                    if old_count > 0:
                        change_ratio = abs(current_count - old_count) / old_count
                        return change_ratio > threshold
            except Exception:
                return True
        
        return True  # Default to reindex if no previous snapshot