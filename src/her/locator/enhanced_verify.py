"""Enhanced locator verification with popup/overlay handling."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any, List, Optional, Tuple, Dict
import logging
import time

logger = logging.getLogger(__name__)

try:
    from playwright.sync_api import Page
    PLAYWRIGHT_AVAILABLE = True
except Exception:
    Page = Any
    PLAYWRIGHT_AVAILABLE = False


@dataclass(frozen=True)
class EnhancedVerificationResult:
    """Enhanced verification result with additional metadata."""
    ok: bool
    unique: bool
    count: int
    visible: bool
    occluded: bool
    disabled: bool
    strategy: str
    used_selector: str
    explanation: str
    # Enhanced fields
    popup_detected: bool = False
    popup_closed: bool = False
    retry_count: int = 0
    element_rect: Optional[Dict[str, float]] = None


class PopupHandler:
    """Handles popup and overlay detection/dismissal."""
    
    # Common popup selectors
    POPUP_SELECTORS = [
        # Cookie banners
        '[class*="cookie"]',
        '[id*="cookie"]',
        '[aria-label*="cookie"]',
        # General modals
        '[role="dialog"]',
        '[role="alertdialog"]',
        '.modal',
        '.popup',
        '.overlay',
        # Notifications
        '[role="alert"]',
        '.notification',
        '.toast',
        # Newsletter/subscription
        '[class*="newsletter"]',
        '[class*="subscribe"]',
        # GDPR/Privacy
        '[class*="gdpr"]',
        '[class*="privacy"]',
        '[class*="consent"]',
    ]
    
    # Common close button selectors
    CLOSE_SELECTORS = [
        '[aria-label*="close"]',
        '[aria-label*="dismiss"]',
        '[title*="close"]',
        'button:has-text("Accept")',
        'button:has-text("OK")',
        'button:has-text("Got it")',
        'button:has-text("Close")',
        'button:has-text("X")',
        '.close',
        '.dismiss',
        '[class*="close"]',
        '[class*="dismiss"]',
    ]
    
    @classmethod
    def detect_popup(cls, page: Page) -> Optional[str]:
        """Detect if a popup/overlay is present."""
        if not page or not PLAYWRIGHT_AVAILABLE:
            return None
            
        try:
            for selector in cls.POPUP_SELECTORS:
                try:
                    elements = page.query_selector_all(selector)
                    for el in elements:
                        if el.is_visible():
                            # Check if it's actually overlaying content
                            rect = el.bounding_box()
                            if rect:
                                # Check if it covers significant area
                                viewport = page.viewport_size
                                if viewport:
                                    coverage = (rect['width'] * rect['height']) / (viewport['width'] * viewport['height'])
                                    if coverage > 0.2:  # Covers >20% of viewport
                                        logger.debug(f"Detected popup with selector: {selector}")
                                        return selector
                except Exception:
                    continue
                    
        except Exception as e:
            logger.warning(f"Error detecting popup: {e}")
            
        return None
    
    @classmethod
    def close_popup(cls, page: Page, popup_selector: Optional[str] = None) -> bool:
        """Attempt to close a detected popup."""
        if not page or not PLAYWRIGHT_AVAILABLE:
            return False
            
        try:
            # If specific popup selector provided, try to close it
            if popup_selector:
                try:
                    popup = page.query_selector(popup_selector)
                    if popup:
                        # Look for close button within popup
                        for close_sel in cls.CLOSE_SELECTORS:
                            try:
                                close_btn = popup.query_selector(close_sel)
                                if close_btn and close_btn.is_visible():
                                    close_btn.click()
                                    page.wait_for_timeout(500)  # Wait for animation
                                    logger.info(f"Closed popup using {close_sel}")
                                    return True
                            except Exception:
                                continue
                                
                        # Try clicking outside popup (for modal overlays)
                        try:
                            page.mouse.click(10, 10)  # Click top-left corner
                            page.wait_for_timeout(300)
                            if not page.query_selector(popup_selector).is_visible():
                                logger.info("Closed popup by clicking outside")
                                return True
                        except Exception:
                            pass
                            
                except Exception as e:
                    logger.debug(f"Error closing specific popup: {e}")
            
            # Try generic close attempts
            for close_sel in cls.CLOSE_SELECTORS:
                try:
                    close_btns = page.query_selector_all(close_sel)
                    for btn in close_btns:
                        if btn.is_visible():
                            btn.click()
                            page.wait_for_timeout(500)
                            logger.info(f"Closed popup using generic {close_sel}")
                            return True
                except Exception:
                    continue
                    
            # Try ESC key
            try:
                page.keyboard.press("Escape")
                page.wait_for_timeout(300)
                logger.info("Attempted popup close with ESC key")
                return True
            except Exception:
                pass
                
        except Exception as e:
            logger.warning(f"Error closing popup: {e}")
            
        return False


def check_element_occlusion(page: Page, element: Any) -> Tuple[bool, Optional[str]]:
    """Check if element is occluded and identify occluding element."""
    if not element:
        return False, None
        
    try:
        # Get element center point
        box = element.bounding_box()
        if not box:
            return False, None
            
        cx = box['x'] + box['width'] / 2
        cy = box['y'] + box['height'] / 2
        
        # Check what element is at center point
        result = page.evaluate("""
            ({x, y, element}) => {
                const topEl = document.elementFromPoint(x, y);
                if (!topEl) return { occluded: false };
                
                // Check if top element is our target or contains it
                const targetEl = element;
                if (topEl === targetEl || topEl.contains(targetEl) || targetEl.contains(topEl)) {
                    return { occluded: false };
                }
                
                // Element is occluded - get info about occluder
                const occluder = {
                    tag: topEl.tagName.toLowerCase(),
                    id: topEl.id || null,
                    classes: Array.from(topEl.classList),
                    role: topEl.getAttribute('role'),
                    zIndex: window.getComputedStyle(topEl).zIndex
                };
                
                return { occluded: true, occluder };
            }
        """, {'x': cx, 'y': cy, 'element': element})
        
        if result['occluded']:
            occluder = result.get('occluder', {})
            occluder_desc = f"{occluder.get('tag', 'unknown')}"
            if occluder.get('id'):
                occluder_desc += f"#{occluder['id']}"
            if occluder.get('classes'):
                occluder_desc += f".{'.'.join(occluder['classes'][:2])}"
            return True, occluder_desc
            
    except Exception as e:
        logger.debug(f"Error checking occlusion: {e}")
        
    return False, None


def enhanced_verify_locator(
    page: Page,
    selector: str,
    strategy: str = 'css',
    require_unique: bool = True,
    auto_handle_popups: bool = True,
    max_retries: int = 3
) -> EnhancedVerificationResult:
    """Enhanced locator verification with popup handling and retries."""
    
    if not page or not PLAYWRIGHT_AVAILABLE:
        return EnhancedVerificationResult(
            False, False, 0, False, False, False, strategy, selector,
            "Page not available", False, False, 0
        )
    
    retry_count = 0
    popup_detected = False
    popup_closed = False
    
    while retry_count <= max_retries:
        try:
            # Check for popups if enabled
            if auto_handle_popups and retry_count == 0:
                popup_sel = PopupHandler.detect_popup(page)
                if popup_sel:
                    popup_detected = True
                    logger.info(f"Detected popup: {popup_sel}")
                    if PopupHandler.close_popup(page, popup_sel):
                        popup_closed = True
                        logger.info("Successfully closed popup")
                        time.sleep(0.5)  # Wait for DOM to stabilize
            
            # Query elements
            if strategy == 'css':
                elements = page.query_selector_all(selector)
            elif strategy == 'xpath':
                elements = page.query_selector_all(f"xpath={selector}")
            elif strategy == 'text':
                elements = page.query_selector_all(f"text={selector}")
            else:
                elements = page.query_selector_all(selector)
            
            count = len(elements)
            
            if count == 0:
                if retry_count < max_retries:
                    retry_count += 1
                    time.sleep(0.5)
                    continue
                return EnhancedVerificationResult(
                    False, False, 0, False, False, False, strategy, selector,
                    "No elements matched", popup_detected, popup_closed, retry_count
                )
            
            if require_unique and count != 1:
                return EnhancedVerificationResult(
                    False, False, count, False, False, False, strategy, selector,
                    f"Matched {count} elements; expected 1", 
                    popup_detected, popup_closed, retry_count
                )
            
            target = elements[0]
            
            # Check visibility
            if not target.is_visible():
                if retry_count < max_retries:
                    retry_count += 1
                    time.sleep(0.5)
                    continue
                return EnhancedVerificationResult(
                    False, count == 1, count, False, False, False, strategy, selector,
                    "Element not visible", popup_detected, popup_closed, retry_count
                )
            
            # Check occlusion
            is_occluded, occluder = check_element_occlusion(page, target)
            if is_occluded:
                # If occluded and we haven't tried closing popups yet
                if auto_handle_popups and not popup_closed and retry_count == 0:
                    # Try to close any overlay
                    if PopupHandler.close_popup(page):
                        popup_closed = True
                        retry_count += 1
                        time.sleep(0.5)
                        continue
                        
                if retry_count < max_retries:
                    retry_count += 1
                    time.sleep(0.5)
                    continue
                    
                return EnhancedVerificationResult(
                    False, count == 1, count, True, True, False, strategy, selector,
                    f"Element occluded by {occluder or 'unknown'}",
                    popup_detected, popup_closed, retry_count
                )
            
            # Check if disabled
            is_disabled = False
            try:
                is_disabled = not target.is_enabled()
            except Exception:
                pass
            
            if is_disabled:
                return EnhancedVerificationResult(
                    False, count == 1, count, True, False, True, strategy, selector,
                    "Element is disabled", popup_detected, popup_closed, retry_count
                )
            
            # Get element rect for additional info
            element_rect = None
            try:
                box = target.bounding_box()
                if box:
                    element_rect = {
                        'x': box['x'],
                        'y': box['y'],
                        'width': box['width'],
                        'height': box['height']
                    }
            except Exception:
                pass
            
            # Success!
            return EnhancedVerificationResult(
                True, count == 1, count, True, False, False, strategy, selector,
                "Element verified successfully",
                popup_detected, popup_closed, retry_count, element_rect
            )
            
        except Exception as e:
            if retry_count < max_retries:
                retry_count += 1
                time.sleep(0.5)
                continue
                
            return EnhancedVerificationResult(
                False, False, 0, False, False, False, strategy, selector,
                f"Verification error: {e}", popup_detected, popup_closed, retry_count
            )
    
    return EnhancedVerificationResult(
        False, False, 0, False, False, False, strategy, selector,
        f"Max retries ({max_retries}) exceeded", popup_detected, popup_closed, retry_count
    )


class EnhancedLocatorVerifier:
    """Enhanced verifier with popup handling."""
    
    def __init__(self, timeout_ms: int = 5000, auto_handle_popups: bool = True):
        self.timeout_ms = timeout_ms
        self.auto_handle_popups = auto_handle_popups
    
    def verify(self, selector: str, page: Optional[Page]) -> Tuple[bool, str, Dict]:
        """Verify a locator with enhanced features."""
        if not page:
            return False, "No page available", {"count": 0}
            
        result = enhanced_verify_locator(
            page, selector, 
            auto_handle_popups=self.auto_handle_popups
        )
        
        details = {
            "count": result.count,
            "unique": result.unique,
            "visible": result.visible,
            "enabled": not result.disabled,
            "occluded": result.occluded,
            "popup_handled": result.popup_closed,
            "retries": result.retry_count
        }
        
        return result.ok, result.explanation, details
    
    def verify_uniqueness(self, page: Optional[Page], selector: str) -> bool:
        """Check if selector matches exactly one element."""
        ok, _, details = self.verify(selector, page)
        return ok and details.get("unique", False)
    
    def find_unique_locator(
        self, 
        locators: List[str], 
        page: Optional[Page]
    ) -> Optional[str]:
        """Find first unique locator from list."""
        for loc in locators:
            if self.verify_uniqueness(page, loc):
                return loc
        return None


__all__ = [
    'EnhancedVerificationResult',
    'EnhancedLocatorVerifier',
    'enhanced_verify_locator',
    'PopupHandler',
    'check_element_occlusion'
]