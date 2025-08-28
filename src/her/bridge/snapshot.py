"""Bridge module for capturing DOM and accessibility snapshots."""

from __future__ import annotations
import hashlib
import logging
from typing import Any, Dict, List, Tuple, Optional

logger = logging.getLogger(__name__)


def _sha1(s: str) -> str:
    """Generate SHA1 hash of a string."""
    return hashlib.sha1(s.encode('utf-8')).hexdigest()


def get_flat_snapshot(page: Any) -> Dict:
    """Get a flattened snapshot of all frames in the page.
    
    Args:
        page: Playwright page instance
        
    Returns:
        Dictionary with frame information and node counts
    """
    frames = []
    total_nodes = 0
    
    try:
        for fr in page.frames:
            try:
                cdp = page.context.new_cdp_session(fr)
            except Exception:
                cdp = None
            
            dom_nodes = []
            ax_nodes = []
            
            if cdp:
                try:
                    dom = cdp.send('DOM.getFlattenedDocument', {'depth': -1, 'pierce': True})
                    dom_nodes = dom.get('nodes', [])
                except Exception:
                    dom_nodes = []
                
                try:
                    ax = cdp.send('Accessibility.getFullAXTree', {})
                    ax_nodes = ax if isinstance(ax, list) else ax.get('nodes', [])
                except Exception:
                    ax_nodes = []
            
            html = fr.content()
            dom_hash = _sha1(html)
            
            frames.append({
                'frame_id': getattr(fr, 'name', '') if isinstance(getattr(fr, 'name', None), str) else getattr(fr, 'name', ''),
                'url': fr.url,
                'dom_hash': dom_hash,
                'dom_nodes': len(dom_nodes),
                'ax_nodes': len(ax_nodes)
            })
            
            total_nodes += len(dom_nodes) + len(ax_nodes)
    
    except Exception as e:
        logger.warning(f"Failed to get snapshot: {e}")
        return {'frames': [], 'total_nodes': 0}
    
    return {'frames': frames, 'total_nodes': total_nodes}


def capture_snapshot(page: Any, frame_path: Optional[str] = None) -> Tuple[List[Dict], str]:
    """Capture a snapshot of the page including DOM and accessibility tree.
    
    Args:
        page: Playwright page instance
        frame_path: Optional frame path to capture
        
    Returns:
        Tuple of (descriptors list, DOM hash string)
    """
    try:
        # Get the target frame
        if frame_path:
            frame = page.frame(name=frame_path) or page.frame(url=frame_path)
            if not frame:
                logger.warning(f"Frame not found: {frame_path}")
                frame = page.main_frame
        else:
            frame = page.main_frame
        
        # Get HTML content for hash
        html = frame.content()
        dom_hash = _sha1(html)
        
        # Try to get CDP session for detailed capture
        descriptors = []
        try:
            cdp = page.context.new_cdp_session(frame)
            
            # Get DOM nodes
            dom_result = cdp.send('DOM.getFlattenedDocument', {
                'depth': -1,
                'pierce': True
            })
            dom_nodes = dom_result.get('nodes', [])
            
            # Get accessibility tree
            ax_result = cdp.send('Accessibility.getFullAXTree', {})
            ax_nodes = ax_result.get('nodes', []) if isinstance(ax_result, dict) else ax_result
            
            # Merge and create descriptors
            from ..descriptors.merge import merge_dom_ax
            descriptors = merge_dom_ax(dom_nodes, ax_nodes)
            
        except Exception as e:
            logger.warning(f"CDP capture failed, using fallback: {e}")
            # Fallback to basic element extraction
            descriptors = _fallback_capture(frame)
        
        return descriptors, dom_hash
        
    except Exception as e:
        logger.error(f"Failed to capture snapshot: {e}")
        return [], ""


def detect_dom_change(old_hash: str, new_hash: str) -> bool:
    """Detect if the DOM has changed based on hashes.
    
    Args:
        old_hash: Previous DOM hash
        new_hash: Current DOM hash
        
    Returns:
        True if DOM has changed, False otherwise
    """
    if not old_hash or not new_hash:
        return True
    return old_hash != new_hash


def _fallback_capture(frame: Any) -> List[Dict]:
    """Fallback capture method using basic Playwright selectors.
    
    Args:
        frame: Playwright frame instance
        
    Returns:
        List of element descriptors
    """
    descriptors = []
    
    try:
        # Get all actionable elements
        selectors = [
            "button", "a", "input", "select", "textarea",
            "[role=button]", "[role=link]", "[role=textbox]",
            "[onclick]", "[ng-click]", "[data-click]"
        ]
        
        for selector in selectors:
            elements = frame.query_selector_all(selector)
            for element in elements[:100]:  # Limit to avoid too many elements
                try:
                    # Get element properties
                    props = element.evaluate("""(el) => {
                        const rect = el.getBoundingClientRect();
                        return {
                            tag: el.tagName.toLowerCase(),
                            id: el.id || '',
                            className: el.className || '',
                            text: el.innerText || el.value || '',
                            type: el.type || '',
                            name: el.name || '',
                            placeholder: el.placeholder || '',
                            href: el.href || '',
                            role: el.getAttribute('role') || '',
                            ariaLabel: el.getAttribute('aria-label') || '',
                            visible: rect.width > 0 && rect.height > 0,
                            bbox: {
                                x: rect.x,
                                y: rect.y,
                                width: rect.width,
                                height: rect.height
                            }
                        };
                    }""")
                    
                    # Convert to descriptor format
                    descriptor = {
                        "tag": props["tag"],
                        "id": props["id"],
                        "classes": props["className"].split() if props["className"] else [],
                        "text": props["text"][:200],  # Limit text length
                        "type": props["type"],
                        "name": props["name"],
                        "placeholder": props["placeholder"],
                        "href": props["href"],
                        "role": props["role"],
                        "attributes": {
                            "aria-label": props["ariaLabel"]
                        },
                        "visible": props["visible"],
                        "bbox": props["bbox"]
                    }
                    
                    descriptors.append(descriptor)
                    
                except Exception:
                    continue
                    
    except Exception as e:
        logger.warning(f"Fallback capture failed: {e}")
    
    return descriptors


__all__ = ["get_flat_snapshot", "capture_snapshot", "detect_dom_change"]