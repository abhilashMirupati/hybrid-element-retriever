"""Enhanced locator verification with frame support and self-healing."""

import logging
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from ..vectordb.sqlite_cache import SQLiteKV
from .synthesize import LocatorSynthesizer
from .verify import verify_selector as verify_locator

logger = logging.getLogger(__name__)


@dataclass
class VerificationResult:
    """Result of locator verification."""
    success: bool
    selector: str
    frame_path: str = "main"
    frame_id: Optional[str] = None
    frame_url: Optional[str] = None
    unique_in_frame: bool = False
    element_count: int = 0
    strategy_used: str = "primary"
    promoted_from: Optional[str] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "selector": self.selector,
            "frame": {
                "used_frame_id": self.frame_id or "",
                "frame_url": self.frame_url or "",
                "frame_path": self.frame_path
            },
            "unique_in_frame": self.unique_in_frame,
            "element_count": self.element_count,
            "strategy_used": self.strategy_used,
            "promoted_from": self.promoted_from or "",
            "error": self.error or ""
        }


class EnhancedLocatorVerifier:
    """Enhanced locator verifier with self-healing and frame support."""
    
    STRATEGY_ORDER = ["semantic", "css", "xpath_contextual", "xpath_text"]
    
    def __init__(self, cache_path: Optional[str] = None, auto_handle_popups: bool = True):
        """Initialize enhanced verifier.
        
        Args:
            cache_path: Path to SQLite cache for promotions
        """
        self.synthesizer = LocatorSynthesizer()
        self.promotion_cache = SQLiteKV(cache_path) if cache_path else None
        self.auto_handle_popups = auto_handle_popups
    
    def verify_with_healing(
        self,
        selector: str,
        descriptor: Dict[str, Any],
        page: Any,
        frame_path: Optional[str] = None,
        max_attempts: int = 3
    ) -> VerificationResult:
        """Verify locator with self-healing fallbacks.
        
        Args:
            selector: Primary selector to verify
            descriptor: Element descriptor
            page: Page or frame object
            frame_path: Optional frame path
            max_attempts: Maximum healing attempts
            
        Returns:
            VerificationResult with comprehensive metadata
        """
        result = VerificationResult(
            success=False,
            selector=selector,
            frame_path=frame_path or "main"
        )
        
        # Switch to frame if needed
        target = self._switch_to_frame(page, frame_path) if frame_path else page
        if not target:
            result.error = f"Failed to switch to frame: {frame_path}"
            return result
        
        # Get frame metadata
        result.frame_id = self._get_frame_id(target)
        result.frame_url = self._get_frame_url(target)
        
        # Try primary selector
        if self._verify_unique_in_frame(selector, descriptor, target):
            result.success = True
            result.unique_in_frame = True
            result.element_count = self._count_elements(selector, target)
            return result
        
        # Check for promoted selector
        if self.promotion_cache:
            promoted = self.promotion_cache.get_promotion(selector)
            if promoted and self._verify_unique_in_frame(promoted, descriptor, target):
                result.success = True
                result.selector = promoted
                result.unique_in_frame = True
                result.element_count = self._count_elements(promoted, target)
                result.strategy_used = "promoted"
                result.promoted_from = selector
                
                # Record successful promotion
                self.promotion_cache.record_promotion(selector, promoted, True)
                return result
        
        # Try self-healing with different strategies
        for attempt in range(max_attempts):
            for strategy in self.STRATEGY_ORDER:
                healed_selector = self._generate_selector(descriptor, strategy)
                
                if healed_selector and healed_selector != selector:
                    if self._verify_unique_in_frame(healed_selector, descriptor, target):
                        result.success = True
                        result.selector = healed_selector
                        result.unique_in_frame = True
                        result.element_count = self._count_elements(healed_selector, target)
                        result.strategy_used = strategy
                        result.promoted_from = selector
                        
                        # Record successful healing
                        if self.promotion_cache:
                            self.promotion_cache.record_promotion(selector, healed_selector, True)
                        
                        return result
        
        # All attempts failed
        result.error = "No unique selector found after healing attempts"
        return result
    
    def verify_uniqueness_per_frame(
        self,
        selector: str,
        page: Any,
        include_frames: bool = True
    ) -> Dict[str, VerificationResult]:
        """Verify selector uniqueness in each frame.
        
        Args:
            selector: Selector to verify
            page: Page object
            include_frames: Whether to check child frames
            
        Returns:
            Dictionary of frame_path to VerificationResult
        """
        results = {}
        
        # Check main frame
        main_result = VerificationResult(
            success=False,
            selector=selector,
            frame_path="main"
        )
        
        try:
            count = self._count_elements(selector, page)
            main_result.element_count = count
            main_result.unique_in_frame = (count == 1)
            main_result.success = main_result.unique_in_frame
        except Exception as e:
            main_result.error = str(e)
        
        results["main"] = main_result
        
        # Check child frames
        if include_frames:
            try:
                iframes = page.query_selector_all("iframe")
                
                for i, iframe in enumerate(iframes):
                    try:
                        frame = iframe.content_frame()
                        if frame:
                            frame_id = iframe.get_attribute("id") or f"frame_{i}"
                            frame_path = f"iframe[id='{frame_id}']" if frame_id != f"frame_{i}" else f"iframe:nth-of-type({i+1})"
                            
                            frame_result = VerificationResult(
                                success=False,
                                selector=selector,
                                frame_path=frame_path,
                                frame_id=frame_id,
                                frame_url=self._get_frame_url(frame)
                            )
                            
                            count = self._count_elements(selector, frame)
                            frame_result.element_count = count
                            frame_result.unique_in_frame = (count == 1)
                            frame_result.success = frame_result.unique_in_frame
                            
                            results[frame_path] = frame_result
                            
                    except Exception as e:
                        logger.debug(f"Failed to check frame {i}: {e}")
                        
            except Exception as e:
                logger.warning(f"Failed to check frames: {e}")
        
        return results
    
    def verify(self, selector: str, page: Any):
        """Compatibility API used in examples: returns tuple (ok, reason, details).

        Falls back to simple uniqueness/visibility checks. If auto popups enabled,
        attempts a soft close before final verification.
        """
        try:
            if self.auto_handle_popups and hasattr(PopupHandler, 'close_any'):
                try:
                    PopupHandler.close_any(page)
                except Exception:
                    pass
            ok = False; reason = ""; details = {"unique": False, "count": 0, "visible": False}
            cnt = self._count_elements(selector, page)
            details["count"] = cnt
            if cnt == 0:
                return (False, "No elements matched.", details)
            if cnt != 1:
                return (False, f"Matched {cnt} elements; not unique.", details)
            el = page.query_selector(selector)
            vis = True
            try:
                vis = bool(el.is_visible()) if el else False
            except Exception:
                vis = True
            details["visible"] = vis
            if not vis:
                return (False, "Not visible.", details)
            return (True, "successfully verified", details)
        except Exception as e:
            return (False, f"Verify error: {e}", {"unique": False, "count": 0, "visible": False})

    def _verify_unique_in_frame(
        self,
        selector: str,
        descriptor: Dict[str, Any],
        frame: Any
    ) -> bool:
        """Verify selector is unique in frame.
        
        Args:
            selector: Selector to verify
            descriptor: Expected element descriptor
            frame: Frame object
            
        Returns:
            True if selector uniquely identifies element
        """
        try:
            # First check basic verification
            if not verify_locator(selector, descriptor, frame):
                return False
            
            # Check uniqueness
            count = self._count_elements(selector, frame)
            if count != 1:
                return False
            
            # Verify it matches expected element
            element = frame.query_selector(selector)
            if element:
                # Check key attributes match
                elem_tag = element.evaluate("el => el.tagName.toLowerCase()")
                expected_tag = descriptor.get('tag', '').lower()
                
                if expected_tag and elem_tag != expected_tag:
                    return False
                
                # Check ID if present
                elem_id = element.get_attribute("id")
                expected_id = descriptor.get('id')
                
                if expected_id and elem_id != expected_id:
                    return False
                
                return True
            
            return False
            
        except Exception as e:
            logger.debug(f"Verification failed: {e}")
            return False
    
    def _generate_selector(self, descriptor: Dict[str, Any], strategy: str) -> Optional[str]:
        """Generate selector using specific strategy.
        
        Args:
            descriptor: Element descriptor
            strategy: Strategy to use
            
        Returns:
            Generated selector or None
        """
        try:
            if strategy == "semantic":
                # Prioritize semantic attributes
                if descriptor.get('dataTestId'):
                    return f"[data-testid='{descriptor['dataTestId']}']"
                elif descriptor.get('ariaLabel'):
                    return f"[aria-label='{descriptor['ariaLabel']}']"
                elif descriptor.get('id'):
                    return f"#{descriptor['id']}"
            
            elif strategy == "css":
                # Generate CSS selector
                tag = descriptor.get('tag', '*')
                classes = descriptor.get('classes', [])
                
                if classes:
                    class_selector = ''.join(f'.{c}' for c in classes[:2])  # Limit classes
                    return f"{tag}{class_selector}"
            
            elif strategy == "xpath_contextual":
                # Generate contextual XPath
                tag = descriptor.get('tag', '*')
                text = descriptor.get('text', '')
                
                if text:
                    # Find parent with ID and use relative path
                    return f"//{tag}[contains(text(), '{text[:30]}')]"
            
            elif strategy == "xpath_text":
                # Generate text-based XPath
                text = descriptor.get('text', '')
                if text:
                    return f"//*[normalize-space()='{text[:50]}']"
            
            # Fall back to synthesizer
            locators = self.synthesizer.synthesize(descriptor)
            for loc in locators:
                if strategy == "css" and not loc.startswith('/'):
                    return loc
                elif strategy.startswith("xpath") and loc.startswith('/'):
                    return loc
            
            return locators[0] if locators else None
            
        except Exception as e:
            logger.debug(f"Selector generation failed for {strategy}: {e}")
            return None
    
    def _switch_to_frame(self, page: Any, frame_path: str) -> Optional[Any]:
        """Switch to specified frame.
        
        Args:
            page: Page object
            frame_path: Frame path
            
        Returns:
            Frame object or None
        """
        try:
            if not frame_path or frame_path == "main":
                return page
            
            # Handle nested frames
            frames = frame_path.split("/")
            current = page
            
            for frame_selector in frames:
                if frame_selector:
                    frame_element = current.query_selector(frame_selector)
                    if frame_element:
                        current = frame_element.content_frame()
                    else:
                        return None
            
            return current
            
        except Exception as e:
            logger.warning(f"Failed to switch to frame {frame_path}: {e}")
            return None
    
    def _count_elements(self, selector: str, frame: Any) -> int:
        """Count elements matching selector.
        
        Args:
            selector: Selector
            frame: Frame object
            
        Returns:
            Number of matching elements
        """
        try:
            elements = frame.query_selector_all(selector)
            return len(elements)
        except Exception:
            return 0
    
    def _get_frame_id(self, frame: Any) -> Optional[str]:
        """Get frame ID.
        
        Args:
            frame: Frame object
            
        Returns:
            Frame ID or None
        """
        try:
            return frame.evaluate("window.frameElement ? window.frameElement.id : null")
        except Exception:
            return None


class PopupHandler:
    """Minimal popup detector/closer used by examples.

    Implements detect_popup(page) -> locator|None and close_popup(page, locator)->bool
    and a convenience close_any(page).
    """

    @staticmethod
    def detect_popup(page: Any):
        try:
            # Common overlay patterns
            sels = [
                "[role='dialog']",
                ".modal, .modal-dialog, .overlay, .backdrop",
                "text=/cookie/i",
            ]
            for s in sels:
                try:
                    loc = page.locator(s)
                    if loc and loc.count() > 0 and loc.first.is_visible():
                        return loc.first
                except Exception:
                    continue
        except Exception:
            return None
        return None

    @staticmethod
    def close_popup(page: Any, locator: Any) -> bool:
        try:
            # Try common close patterns inside locator
            close_sels = ["button:has-text('Close')", "button[aria-label='Close']", "[data-test*='close']", "text=/accept|agree|ok/i"]
            for s in close_sels:
                try:
                    btn = locator.locator(s)
                    if btn and btn.count() > 0:
                        btn.first.click()
                        return True
                except Exception:
                    continue
            # Fallback: press Escape
            try:
                page.keyboard.press('Escape')
                return True
            except Exception:
                return False
        except Exception:
            return False

    @staticmethod
    def close_any(page: Any) -> bool:
        loc = PopupHandler.detect_popup(page)
        if loc is not None:
            return PopupHandler.close_popup(page, loc)
        return False
    
    def _get_frame_url(self, frame: Any) -> Optional[str]:
        """Get frame URL.
        
        Args:
            frame: Frame object
            
        Returns:
            Frame URL or None
        """
        try:
            return frame.url
        except Exception:
            return None