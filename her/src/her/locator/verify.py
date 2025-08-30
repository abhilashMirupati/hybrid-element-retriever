"""Locator verification for validating selectors."""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

from playwright.async_api import Page, Frame, Locator, ElementHandle

logger = logging.getLogger(__name__)


@dataclass
class VerificationResult:
    """Result of locator verification."""
    ok: bool
    unique: bool
    count: int
    visible: bool
    occluded: bool
    disabled: bool
    used_selector: str
    strategy: str
    frame_path: List[str]
    explanation: str
    bounding_box: Optional[Dict[str, float]] = None
    alternatives_tried: List[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
        

class LocatorVerifier:
    """Verifies locators against live page."""
    
    def __init__(self, page: Page):
        self.page = page
        
    async def verify(
        self,
        selector: str,
        strategy: str = 'css',
        frame_path: Optional[List[str]] = None,
        alternatives: Optional[List[str]] = None
    ) -> VerificationResult:
        """Verify a locator on the page.
        
        Args:
            selector: Selector to verify
            strategy: Selector strategy ('css', 'xpath', 'text', 'aria')
            frame_path: Frame path if in iframe
            alternatives: Alternative selectors to try
            
        Returns:
            VerificationResult with detailed information
        """
        # Get target frame
        target_frame = await self._get_frame(frame_path)
        if not target_frame:
            return VerificationResult(
                ok=False,
                unique=False,
                count=0,
                visible=False,
                occluded=False,
                disabled=False,
                used_selector=selector,
                strategy=strategy,
                frame_path=frame_path or [],
                explanation="Frame not found"
            )
            
        # Try primary selector
        result = await self._verify_single(
            target_frame,
            selector,
            strategy,
            frame_path or []
        )
        
        # Try alternatives if primary failed
        alternatives_tried = []
        if not result.ok and alternatives:
            for alt_selector in alternatives:
                alternatives_tried.append(alt_selector)
                
                # Determine strategy from alternative format
                alt_strategy = self._detect_strategy(alt_selector)
                
                alt_result = await self._verify_single(
                    target_frame,
                    alt_selector,
                    alt_strategy,
                    frame_path or []
                )
                
                if alt_result.ok:
                    alt_result.alternatives_tried = alternatives_tried
                    return alt_result
                    
        result.alternatives_tried = alternatives_tried
        return result
        
    async def _get_frame(self, frame_path: Optional[List[str]]) -> Optional[Frame]:
        """Get frame by path.
        
        Args:
            frame_path: List of frame names/URLs
            
        Returns:
            Frame object or None
        """
        if not frame_path:
            return self.page.main_frame
            
        current_frame = self.page.main_frame
        
        for frame_spec in frame_path:
            # Find child frame by name or URL
            found = False
            for child_frame in current_frame.child_frames:
                if (child_frame.name == frame_spec or 
                    frame_spec in child_frame.url):
                    current_frame = child_frame
                    found = True
                    break
                    
            if not found:
                logger.warning(f"Frame not found: {frame_spec}")
                return None
                
        return current_frame
        
    async def _verify_single(
        self,
        frame: Frame,
        selector: str,
        strategy: str,
        frame_path: List[str]
    ) -> VerificationResult:
        """Verify a single selector.
        
        Args:
            frame: Target frame
            selector: Selector to verify
            strategy: Selector strategy
            frame_path: Frame path
            
        Returns:
            VerificationResult
        """
        try:
            # Create locator based on strategy
            locator = self._create_locator(frame, selector, strategy)
            
            # Count matches
            count = await locator.count()
            
            if count == 0:
                return VerificationResult(
                    ok=False,
                    unique=False,
                    count=0,
                    visible=False,
                    occluded=False,
                    disabled=False,
                    used_selector=selector,
                    strategy=strategy,
                    frame_path=frame_path,
                    explanation="No elements found"
                )
                
            # Check uniqueness
            unique = count == 1
            
            # Get first element for detailed checks
            element = locator.first
            
            # Check visibility
            visible = await element.is_visible()
            
            # Check if disabled
            disabled = await element.is_disabled()
            
            # Check occlusion
            occluded = await self._check_occlusion(element)
            
            # Get bounding box
            bbox = None
            try:
                bbox = await element.bounding_box()
            except:
                pass
                
            # Determine if OK
            ok = unique and visible and not disabled and not occluded
            
            # Create explanation
            issues = []
            if not unique:
                issues.append(f"found {count} elements")
            if not visible:
                issues.append("not visible")
            if disabled:
                issues.append("disabled")
            if occluded:
                issues.append("occluded")
                
            explanation = "OK" if ok else f"Issues: {', '.join(issues)}"
            
            return VerificationResult(
                ok=ok,
                unique=unique,
                count=count,
                visible=visible,
                occluded=occluded,
                disabled=disabled,
                used_selector=selector,
                strategy=strategy,
                frame_path=frame_path,
                explanation=explanation,
                bounding_box=bbox
            )
            
        except Exception as e:
            logger.error(f"Verification error: {e}")
            return VerificationResult(
                ok=False,
                unique=False,
                count=0,
                visible=False,
                occluded=False,
                disabled=False,
                used_selector=selector,
                strategy=strategy,
                frame_path=frame_path,
                explanation=f"Error: {str(e)}"
            )
            
    def _create_locator(self, frame: Frame, selector: str, strategy: str) -> Locator:
        """Create Playwright locator based on strategy.
        
        Args:
            frame: Target frame
            selector: Selector string
            strategy: Selector strategy
            
        Returns:
            Playwright Locator
        """
        if strategy == 'css':
            # Remove jQuery-style :contains if present
            if ':contains(' in selector:
                base_selector = selector.split(':contains(')[0]
                text = selector.split(":contains('")[1].split("')")[0] if ":contains('" in selector else ""
                if text:
                    return frame.locator(f"{base_selector}:has-text('{text}')")
                return frame.locator(base_selector)
            return frame.locator(selector)
            
        elif strategy == 'xpath':
            return frame.locator(f"xpath={selector}")
            
        elif strategy == 'text':
            # Extract text from text=value format
            if selector.startswith('text='):
                text_value = selector[5:]
                return frame.locator(f"text={text_value}")
            return frame.locator(f"text={selector}")
            
        elif strategy == 'aria':
            # Extract aria-label from aria-label=value format
            if selector.startswith('aria-label='):
                aria_value = selector[11:]
                return frame.locator(f"[aria-label='{aria_value}']")
            return frame.locator(f"[aria-label='{selector}']")
            
        elif strategy == 'role':
            # Extract role from role=value format
            if selector.startswith('role='):
                role_value = selector[5:]
                return frame.get_by_role(role_value)
            return frame.get_by_role(selector)
            
        else:
            # Default to CSS
            return frame.locator(selector)
            
    async def _check_occlusion(self, element: Locator) -> bool:
        """Check if element is occluded by another element.
        
        Args:
            element: Element to check
            
        Returns:
            True if occluded
        """
        try:
            # Get element's bounding box
            bbox = await element.bounding_box()
            if not bbox:
                return True  # No bounding box means not visible
                
            # Check element at center point
            center_x = bbox['x'] + bbox['width'] / 2
            center_y = bbox['y'] + bbox['height'] / 2
            
            # Use elementFromPoint to check what's at the center
            result = await element.evaluate(
                """(el) => {
                    const rect = el.getBoundingClientRect();
                    const centerX = rect.left + rect.width / 2;
                    const centerY = rect.top + rect.height / 2;
                    const topElement = document.elementFromPoint(centerX, centerY);
                    return topElement === el || el.contains(topElement);
                }"""
            )
            
            return not result  # Occluded if different element at center
            
        except Exception as e:
            logger.debug(f"Occlusion check failed: {e}")
            return False  # Assume not occluded if check fails
            
    def _detect_strategy(self, selector: str) -> str:
        """Detect strategy from selector format.
        
        Args:
            selector: Selector string
            
        Returns:
            Detected strategy
        """
        if selector.startswith('text='):
            return 'text'
        elif selector.startswith('aria-label='):
            return 'aria'
        elif selector.startswith('role='):
            return 'role'
        elif selector.startswith('/') or selector.startswith('//'):
            return 'xpath'
        else:
            return 'css'
            
    async def batch_verify(
        self,
        selectors: List[Dict[str, Any]]
    ) -> List[VerificationResult]:
        """Verify multiple selectors.
        
        Args:
            selectors: List of selector dicts with 'selector', 'strategy', etc.
            
        Returns:
            List of VerificationResults
        """
        results = []
        
        for selector_info in selectors:
            result = await self.verify(
                selector=selector_info['selector'],
                strategy=selector_info.get('strategy', 'css'),
                frame_path=selector_info.get('frame_path'),
                alternatives=selector_info.get('alternatives')
            )
            results.append(result)
            
        return results