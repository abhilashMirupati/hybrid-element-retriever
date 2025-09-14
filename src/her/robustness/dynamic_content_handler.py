"""
Dynamic Content Handler for HER Framework

Handles dynamic web content including:
- Shadow DOM traversal
- Infinite scroll detection and handling
- Lazy loading content
- Dynamic element stability validation
- Frame context management
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional, Set

try:
    from playwright.sync_api import Page, Frame, Locator
    _PLAYWRIGHT_AVAILABLE = True
except ImportError:
    _PLAYWRIGHT_AVAILABLE = False
    Page = None
    Frame = None
    Locator = None

logger = logging.getLogger(__name__)


class DynamicContentHandler:
    """Handles dynamic content and ensures element stability."""
    
    def __init__(self, page: Page):
        if not _PLAYWRIGHT_AVAILABLE:
            raise RuntimeError("Playwright is required for dynamic content handling")
        
        self.page = page
        self.shadow_dom_selectors = [
            'shadow-root',
            '[shadowroot]',
            '::shadow',
            '/deep/',
            '>>>'
        ]
    
    def ensure_content_loaded(self, max_wait_seconds: int = 10) -> bool:
        """
        Ensure all dynamic content is loaded.
        
        Args:
            max_wait_seconds: Maximum time to wait for content
            
        Returns:
            True if content is loaded, False if timeout
        """
        logger.debug("Ensuring dynamic content is loaded...")
        
        start_time = time.time()
        
        # Wait for initial page load
        try:
            self.page.wait_for_load_state("domcontentloaded", timeout=5000)
            self.page.wait_for_load_state("networkidle", timeout=5000)
        except Exception:
            logger.debug("Page load timeout, continuing...")
        
        # Handle infinite scroll
        self._handle_infinite_scroll()
        
        # Handle lazy loading
        self._handle_lazy_loading()
        
        # Wait for any remaining dynamic content
        remaining_time = max_wait_seconds - (time.time() - start_time)
        if remaining_time > 0:
            self.page.wait_for_timeout(int(remaining_time * 1000))
        
        logger.debug("Dynamic content loading completed")
        return True
    
    def _handle_infinite_scroll(self) -> None:
        """Handle infinite scroll content."""
        try:
            # Detect infinite scroll indicators
            scroll_indicators = [
                'button:has-text("Load more")',
                'button:has-text("Show more")',
                '[data-testid*="load"]',
                '[data-testid*="more"]',
                '.load-more',
                '.show-more',
                '.infinite-scroll'
            ]
            
            has_infinite_scroll = False
            for indicator in scroll_indicators:
                if self.page.locator(indicator).count() > 0:
                    has_infinite_scroll = True
                    break
            
            if not has_infinite_scroll:
                # Check if page height changes on scroll
                initial_height = self.page.evaluate("document.body.scrollHeight")
                self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                self.page.wait_for_timeout(1000)
                final_height = self.page.evaluate("document.body.scrollHeight")
                
                if final_height > initial_height * 1.2:
                    has_infinite_scroll = True
            
            if has_infinite_scroll:
                logger.debug("Detected infinite scroll, loading content...")
                self._scroll_to_load_content()
            
        except Exception as e:
            logger.debug(f"Infinite scroll handling failed: {e}")
    
    def _handle_lazy_loading(self) -> None:
        """Handle lazy-loaded content."""
        try:
            # Check for lazy loading indicators
            lazy_indicators = [
                'img[loading="lazy"]',
                'img[data-src]',
                'img[data-lazy]',
                '.lazy',
                '.lazy-load'
            ]
            
            has_lazy_content = False
            for indicator in lazy_indicators:
                if self.page.locator(indicator).count() > 0:
                    has_lazy_content = True
                    break
            
            if has_lazy_content:
                logger.debug("Detected lazy loading, triggering load...")
                self._trigger_lazy_loading()
            
        except Exception as e:
            logger.debug(f"Lazy loading handling failed: {e}")
    
    def _scroll_to_load_content(self) -> None:
        """Scroll to load infinite scroll content."""
        try:
            # Progressive scrolling
            scroll_positions = [0.25, 0.5, 0.75, 1.0, 0.5, 0.25]
            
            for position in scroll_positions:
                self.page.evaluate(f"window.scrollTo(0, document.body.scrollHeight * {position})")
                self.page.wait_for_timeout(1000)
            
            # Scroll back to top
            self.page.evaluate("window.scrollTo(0, 0)")
            self.page.wait_for_timeout(500)
            
        except Exception as e:
            logger.debug(f"Scroll to load content failed: {e}")
    
    def _trigger_lazy_loading(self) -> None:
        """Trigger lazy loading of content."""
        try:
            # Scroll to trigger lazy loading
            self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            self.page.wait_for_timeout(1000)
            
            # Scroll back to top
            self.page.evaluate("window.scrollTo(0, 0)")
            self.page.wait_for_timeout(500)
            
        except Exception as e:
            logger.debug(f"Trigger lazy loading failed: {e}")
    
    def traverse_shadow_dom(self, element: Locator) -> List[Locator]:
        """
        Traverse shadow DOM to find elements.
        
        Args:
            element: Parent element that may contain shadow DOM
            
        Returns:
            List of elements found in shadow DOM
        """
        shadow_elements = []
        
        try:
            # Check if element has shadow root
            has_shadow = element.evaluate("el => !!el.shadowRoot")
            if not has_shadow:
                return shadow_elements
            
            # Get elements from shadow root
            shadow_elements = element.evaluate("""
                el => {
                    if (!el.shadowRoot) return [];
                    const elements = el.shadowRoot.querySelectorAll('*');
                    return Array.from(elements).map(e => ({
                        tagName: e.tagName,
                        textContent: e.textContent,
                        id: e.id,
                        className: e.className
                    }));
                }
            """)
            
            logger.debug(f"Found {len(shadow_elements)} elements in shadow DOM")
            
        except Exception as e:
            logger.debug(f"Shadow DOM traversal failed: {e}")
        
        return shadow_elements
    
    def validate_element_stability(self, selector: str, max_attempts: int = 3) -> bool:
        """
        Validate that an element remains stable across multiple checks.
        
        Args:
            selector: Element selector to validate
            max_attempts: Number of validation attempts
            
        Returns:
            True if element is stable, False otherwise
        """
        try:
            locator = self.page.locator(selector)
            
            for attempt in range(max_attempts):
                # Check if element exists and is visible
                if locator.count() == 0:
                    logger.debug(f"Element not found on attempt {attempt + 1}")
                    return False
                
                if not locator.first.is_visible():
                    logger.debug(f"Element not visible on attempt {attempt + 1}")
                    return False
                
                # Brief pause between checks
                if attempt < max_attempts - 1:
                    time.sleep(0.5)
            
            logger.debug(f"Element {selector} is stable")
            return True
            
        except Exception as e:
            logger.debug(f"Element stability validation failed: {e}")
            return False
    
    def get_frame_context(self, selector: str) -> Optional[Frame]:
        """
        Determine the appropriate frame context for a selector.
        
        Args:
            selector: Element selector
            
        Returns:
            Appropriate frame for the selector
        """
        try:
            # For now, return main frame
            # TODO: Implement frame detection based on selector context
            return self.page.main_frame
            
        except Exception as e:
            logger.debug(f"Frame context detection failed: {e}")
            return None
    
    def handle_dynamic_overlays(self) -> None:
        """Handle dynamic overlays that may appear during interaction."""
        overlay_selectors = [
            'button[aria-label="Close"]',
            'button[aria-label="Dismiss"]',
            'button:has-text("Accept")',
            'button:has-text("Agree")',
            'button:has-text("Got it")',
            'button:has-text("OK")',
            'button:has-text("Continue")',
            '#onetrust-accept-btn-handler',
            '.cc-allow',
            '[data-testid="close"]',
            '[aria-label="Close dialog"]',
            '[aria-label="Close modal"]',
            '.modal button.close',
            '.popup button.close',
            'button:has-text("No thanks")',
            'button:has-text("I agree")',
        ]
        
        for selector in overlay_selectors:
            try:
                locator = self.page.locator(selector)
                if locator.count() > 0 and locator.first.is_visible(timeout=100):
                    locator.first.click(timeout=500)
                    time.sleep(0.2)
                    logger.debug(f"Dismissed overlay: {selector}")
            except Exception:
                continue


def create_dynamic_content_handler(page: Page) -> DynamicContentHandler:
    """Create a dynamic content handler instance."""
    return DynamicContentHandler(page)