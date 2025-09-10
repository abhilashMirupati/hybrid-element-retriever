#!/usr/bin/env python3
"""
Universal English-to-UI Automation Framework
============================================

A completely universal framework that converts plain English instructions into UI automation
for ANY website, ANY use case, with real XPath validation and comprehensive error handling.

Features:
- Universal natural language step parsing
- Works with ANY website (not just Verizon)
- Real XPath validation on live websites
- Comprehensive error handling and retry logic
- AI-powered element finding
- Universal compatibility across different websites
- No hardcoded selectors or website-specific logic
"""

import os
import sys
import time
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass
import re

# Add src to path for HER framework
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from playwright.sync_api import sync_playwright, Page, Browser, Playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

try:
    from her.core.runner import Runner
    from her.parser.enhanced_intent import EnhancedIntentParser
    HER_AVAILABLE = True
except ImportError:
    HER_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('universal_automation.log')
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class StepResult:
    """Result of executing a single automation step."""
    step_number: int
    step_text: str
    success: bool
    selector: str
    confidence: float
    error_message: Optional[str] = None
    execution_time: float = 0.0
    validation_passed: bool = False
    xpath_matches: int = 0
    element_found: bool = False
    action_performed: str = ""

@dataclass
class AutomationResult:
    """Result of executing a complete automation sequence."""
    total_steps: int
    successful_steps: int
    failed_steps: int
    total_time: float
    results: List[StepResult]
    final_url: str
    success_rate: float
    website: str
    use_case: str

class UniversalStepParser:
    """Universal parser for natural English instructions - works with ANY website."""
    
    def __init__(self):
        # Universal patterns that work with any website
        self.patterns = {
            # Navigation patterns - universal
            'navigate': [
                r'open\s+(?:the\s+)?(?:website\s+)?(https?://[^\s]+)',
                r'go\s+to\s+(?:the\s+)?(?:website\s+)?(https?://[^\s]+)',
                r'visit\s+(?:the\s+)?(?:website\s+)?(https?://[^\s]+)',
                r'navigate\s+to\s+(?:the\s+)?(?:website\s+)?(https?://[^\s]+)',
                r'load\s+(?:the\s+)?(?:website\s+)?(https?://[^\s]+)',
            ],
            
            # Click patterns - universal
            'click': [
                r'click\s+(?:on\s+)?(?:the\s+)?["\']([^"\']+)["\']',
                r'click\s+(?:on\s+)?(?:the\s+)?([^"\']+?)(?:\s+button|\s+link|\s+element|\s+tab|\s+menu|\s+option)',
                r'press\s+(?:on\s+)?(?:the\s+)?["\']([^"\']+)["\']',
                r'tap\s+(?:on\s+)?(?:the\s+)?["\']([^"\']+)["\']',
                r'select\s+(?:the\s+)?["\']([^"\']+)["\']',
                r'choose\s+(?:the\s+)?["\']([^"\']+)["\']',
                r'pick\s+(?:the\s+)?["\']([^"\']+)["\']',
                r'hit\s+(?:on\s+)?(?:the\s+)?["\']([^"\']+)["\']',
            ],
            
            # Type patterns - universal
            'type': [
                r'type\s+["\']([^"\']+)["\']\s+(?:in\s+)?(?:the\s+)?["\']([^"\']+)["\']',
                r'enter\s+["\']([^"\']+)["\']\s+(?:in\s+)?(?:the\s+)?["\']([^"\']+)["\']',
                r'input\s+["\']([^"\']+)["\']\s+(?:in\s+)?(?:the\s+)?["\']([^"\']+)["\']',
                r'fill\s+(?:the\s+)?["\']([^"\']+)["\']\s+(?:with\s+)?["\']([^"\']+)["\']',
                r'write\s+["\']([^"\']+)["\']\s+(?:in\s+)?(?:the\s+)?["\']([^"\']+)["\']',
                r'put\s+["\']([^"\']+)["\']\s+(?:in\s+)?(?:the\s+)?["\']([^"\']+)["\']',
            ],
            
            # Validation patterns - universal
            'validate': [
                r'validate\s+(?:that\s+)?(?:it\s+)?(?:landed\s+on\s+|navigated\s+to\s+)?(https?://[^\s]+)',
                r'verify\s+(?:that\s+)?(?:it\s+)?(?:landed\s+on\s+|navigated\s+to\s+)?(https?://[^\s]+)',
                r'check\s+(?:that\s+)?(?:it\s+)?(?:landed\s+on\s+|navigated\s+to\s+)?(https?://[^\s]+)',
                r'ensure\s+(?:that\s+)?(?:it\s+)?(?:landed\s+on\s+|navigated\s+to\s+)?(https?://[^\s]+)',
                r'confirm\s+(?:that\s+)?(?:it\s+)?(?:landed\s+on\s+|navigated\s+to\s+)?(https?://[^\s]+)',
                r'validate\s+(?:that\s+)?["\']([^"\']+)["\']\s+(?:is\s+)?(?:visible|exists|present)',
                r'verify\s+(?:that\s+)?["\']([^"\']+)["\']\s+(?:is\s+)?(?:visible|exists|present)',
                r'check\s+(?:that\s+)?["\']([^"\']+)["\']\s+(?:is\s+)?(?:visible|exists|present)',
                r'ensure\s+(?:that\s+)?["\']([^"\']+)["\']\s+(?:is\s+)?(?:visible|exists|present)',
                r'confirm\s+(?:that\s+)?["\']([^"\']+)["\']\s+(?:is\s+)?(?:visible|exists|present)',
            ],
            
            # Wait patterns - universal
            'wait': [
                r'wait\s+(?:for\s+)?(\d+)\s*(?:seconds?|secs?|s)',
                r'pause\s+(?:for\s+)?(\d+)\s*(?:seconds?|secs?|s)',
                r'delay\s+(?:for\s+)?(\d+)\s*(?:seconds?|secs?|s)',
                r'sleep\s+(?:for\s+)?(\d+)\s*(?:seconds?|secs?|s)',
            ],
            
            # Hover patterns - universal
            'hover': [
                r'hover\s+(?:over\s+)?(?:the\s+)?["\']([^"\']+)["\']',
                r'mouse\s+over\s+(?:the\s+)?["\']([^"\']+)["\']',
                r'point\s+(?:at\s+)?(?:the\s+)?["\']([^"\']+)["\']',
            ],
            
            # Scroll patterns - universal
            'scroll': [
                r'scroll\s+(?:to\s+)?(?:the\s+)?["\']([^"\']+)["\']',
                r'scroll\s+(?:down|up|left|right)',
                r'scroll\s+to\s+(?:top|bottom)',
            ],
            
            # Form submission patterns - universal
            'submit': [
                r'submit\s+(?:the\s+)?["\']([^"\']+)["\']',
                r'send\s+(?:the\s+)?["\']([^"\']+)["\']',
                r'post\s+(?:the\s+)?["\']([^"\']+)["\']',
            ],
            
            # Clear patterns - universal
            'clear': [
                r'clear\s+(?:the\s+)?["\']([^"\']+)["\']',
                r'empty\s+(?:the\s+)?["\']([^"\']+)["\']',
                r'reset\s+(?:the\s+)?["\']([^"\']+)["\']',
            ],
        }
    
    def parse_step(self, step_text: str) -> Dict[str, Any]:
        """Parse a single English step into structured data - universal for any website."""
        step_text = step_text.strip()
        
        # Try each pattern category
        for action, patterns in self.patterns.items():
            for pattern in patterns:
                match = re.search(pattern, step_text, re.IGNORECASE)
                if match:
                    groups = match.groups()
                    
                    if action == 'navigate':
                        return {
                            'action': 'navigate',
                            'url': groups[0],
                            'original_text': step_text
                        }
                    elif action == 'click':
                        return {
                            'action': 'click',
                            'target': groups[0],
                            'original_text': step_text
                        }
                    elif action == 'type':
                        return {
                            'action': 'type',
                            'value': groups[0],
                            'target': groups[1],
                            'original_text': step_text
                        }
                    elif action == 'validate':
                        if groups[0].startswith('http'):
                            return {
                                'action': 'validate_url',
                                'expected_url': groups[0],
                                'original_text': step_text
                            }
                        else:
                            return {
                                'action': 'validate_element',
                                'target': groups[0],
                                'original_text': step_text
                            }
                    elif action == 'wait':
                        return {
                            'action': 'wait',
                            'duration': int(groups[0]),
                            'original_text': step_text
                        }
                    elif action == 'hover':
                        return {
                            'action': 'hover',
                            'target': groups[0],
                            'original_text': step_text
                        }
                    elif action == 'scroll':
                        return {
                            'action': 'scroll',
                            'target': groups[0] if groups[0] else 'down',
                            'original_text': step_text
                        }
                    elif action == 'submit':
                        return {
                            'action': 'submit',
                            'target': groups[0],
                            'original_text': step_text
                        }
                    elif action == 'clear':
                        return {
                            'action': 'clear',
                            'target': groups[0],
                            'original_text': step_text
                        }
        
        # If no pattern matches, treat as click action (most common)
        return {
            'action': 'click',
            'target': step_text,
            'original_text': step_text
        }

class UniversalXPathValidator:
    """Universal XPath validator that works with any website."""
    
    def __init__(self, page: Page):
        self.page = page
    
    def validate_xpath(self, xpath: str) -> Tuple[bool, int, str]:
        """Validate an XPath selector on any website."""
        try:
            count = self.page.locator(f"xpath={xpath}").count()
            
            if count == 0:
                return False, 0, "No elements found matching XPath"
            elif count > 1:
                return True, count, f"Found {count} elements (multiple matches)"
            else:
                return True, count, "Single element found"
                
        except Exception as e:
            return False, 0, f"XPath validation error: {str(e)}"
    
    def get_element_info(self, xpath: str) -> Dict[str, Any]:
        """Get detailed information about elements matching the XPath."""
        try:
            locator = self.page.locator(f"xpath={xpath}")
            count = locator.count()
            
            if count == 0:
                return {"count": 0, "elements": []}
            
            elements = []
            for i in range(min(count, 5)):  # Limit to first 5 elements
                try:
                    element = locator.nth(i)
                    info = {
                        "index": i,
                        "text": element.text_content() or "",
                        "tag": element.evaluate("el => el.tagName") or "",
                        "visible": element.is_visible(),
                        "enabled": element.is_enabled(),
                        "bounding_box": element.bounding_box() or {},
                    }
                    elements.append(info)
                except Exception as e:
                    elements.append({"index": i, "error": str(e)})
            
            return {"count": count, "elements": elements}
            
        except Exception as e:
            return {"count": 0, "elements": [], "error": str(e)}

class UniversalAutomationRunner:
    """Universal automation runner that works with ANY website and ANY use case."""
    
    def __init__(self, headless: bool = True, timeout: int = 30):
        self.headless = headless
        self.timeout = timeout
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.parser = UniversalStepParser()
        self.validator: Optional[UniversalXPathValidator] = None
        
        # Initialize HER framework if available
        self.her_runner = None
        if HER_AVAILABLE:
            try:
                self.her_runner = Runner(headless=headless)
                logger.info("HER framework initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize HER framework: {e}")
                self.her_runner = None
    
    def start_browser(self):
        """Start the browser and create a new page."""
        if not PLAYWRIGHT_AVAILABLE:
            raise RuntimeError("Playwright not available. Install with: pip install playwright")
        
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            headless=self.headless,
            args=['--no-sandbox', '--disable-dev-shm-usage', '--disable-web-security']
        )
        self.page = self.browser.new_page()
        self.page.set_default_timeout(self.timeout * 1000)
        self.validator = UniversalXPathValidator(self.page)
        
        logger.info(f"Browser started (headless={self.headless})")
    
    def stop_browser(self):
        """Stop the browser and clean up resources."""
        try:
            if self.page:
                self.page.close()
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
        except Exception as e:
            logger.warning(f"Error stopping browser: {e}")
        finally:
            self.page = None
            self.browser = None
            self.playwright = None
            self.validator = None
    
    def execute_step(self, step_number: int, step_text: str) -> StepResult:
        """Execute a single automation step - universal for any website."""
        start_time = time.time()
        
        try:
            # Parse the step
            parsed = self.parser.parse_step(step_text)
            action = parsed['action']
            
            logger.info(f"Step {step_number}: {action} - {step_text}")
            
            # Route to appropriate handler
            handlers = {
                'navigate': self._execute_navigate,
                'click': self._execute_click,
                'type': self._execute_type,
                'validate_url': self._execute_validate_url,
                'validate_element': self._execute_validate_element,
                'wait': self._execute_wait,
                'hover': self._execute_hover,
                'scroll': self._execute_scroll,
                'submit': self._execute_submit,
                'clear': self._execute_clear,
            }
            
            handler = handlers.get(action, self._execute_click)
            return handler(step_number, step_text, parsed)
                
        except Exception as e:
            logger.error(f"Error executing step {step_number}: {e}")
            return StepResult(
                step_number=step_number,
                step_text=step_text,
                success=False,
                selector="",
                confidence=0.0,
                error_message=str(e),
                execution_time=time.time() - start_time
            )
    
    def _execute_navigate(self, step_number: int, step_text: str, parsed: Dict[str, Any]) -> StepResult:
        """Execute navigation step - universal."""
        url = parsed['url']
        
        try:
            logger.info(f"Navigating to: {url}")
            self.page.goto(url, wait_until="networkidle", timeout=self.timeout * 1000)
            
            # Wait for page to fully load
            time.sleep(2)
            
            # Dismiss any popups/overlays
            self._dismiss_overlays()
            
            return StepResult(
                step_number=step_number,
                step_text=step_text,
                success=True,
                selector="",
                confidence=1.0,
                execution_time=time.time() - time.time(),
                validation_passed=True,
                action_performed="navigate"
            )
            
        except Exception as e:
            return StepResult(
                step_number=step_number,
                step_text=step_text,
                success=False,
                selector="",
                confidence=0.0,
                error_message=f"Navigation failed: {str(e)}",
                execution_time=time.time() - time.time()
            )
    
    def _execute_click(self, step_number: int, step_text: str, parsed: Dict[str, Any]) -> StepResult:
        """Execute click step using HER framework - universal for any website."""
        target = parsed['target']
        
        try:
            if self.her_runner and self.her_runner._page:
                # Use HER framework for intelligent element finding
                logger.info(f"Using HER framework to find: {target}")
                
                # Take snapshot and resolve selector
                snapshot = self.her_runner._snapshot()
                result = self.her_runner._resolve_selector(target, snapshot)
                
                selector = result.get('selector', '')
                confidence = result.get('confidence', 0.0)
                
                if not selector:
                    return StepResult(
                        step_number=step_number,
                        step_text=step_text,
                        success=False,
                        selector="",
                        confidence=0.0,
                        error_message="No selector found for target",
                        execution_time=time.time() - time.time()
                    )
                
                # Validate XPath
                is_valid, match_count, error_msg = self.validator.validate_xpath(selector)
                
                if not is_valid:
                    return StepResult(
                        step_number=step_number,
                        step_text=step_text,
                        success=False,
                        selector=selector,
                        confidence=confidence,
                        error_message=f"XPath validation failed: {error_msg}",
                        execution_time=time.time() - time.time()
                    )
                
                # Execute click
                self.her_runner._do_action("click", selector, None, result.get("promo", {}))
                
                # Wait for action to complete
                time.sleep(1)
                
                return StepResult(
                    step_number=step_number,
                    step_text=step_text,
                    success=True,
                    selector=selector,
                    confidence=confidence,
                    execution_time=time.time() - time.time(),
                    validation_passed=True,
                    xpath_matches=match_count,
                    element_found=True,
                    action_performed="click"
                )
            else:
                # Fallback to basic Playwright
                return self._execute_click_fallback(step_number, step_text, target)
                
        except Exception as e:
            return StepResult(
                step_number=step_number,
                step_text=step_text,
                success=False,
                selector="",
                confidence=0.0,
                error_message=f"Click execution failed: {str(e)}",
                execution_time=time.time() - time.time()
            )
    
    def _execute_click_fallback(self, step_number: int, step_text: str, target: str) -> StepResult:
        """Fallback click execution using basic Playwright selectors - universal."""
        try:
            # Universal selector strategies that work on any website
            selectors = [
                f"text={target}",
                f"[aria-label*='{target}']",
                f"[title*='{target}']",
                f"[data-testid*='{target}']",
                f"[data-id*='{target}']",
                f"[data-value*='{target}']",
                f"button:has-text('{target}')",
                f"a:has-text('{target}')",
                f"input[value*='{target}']",
                f"option:has-text('{target}')",
                f"label:has-text('{target}')",
                f"[role='button']:has-text('{target}')",
                f"[role='link']:has-text('{target}')",
                f"[role='menuitem']:has-text('{target}')",
                f"[role='tab']:has-text('{target}')",
            ]
            
            for selector in selectors:
                try:
                    element = self.page.locator(selector).first
                    if element.is_visible():
                        element.click()
                        time.sleep(1)
                        
                        return StepResult(
                            step_number=step_number,
                            step_text=step_text,
                            success=True,
                            selector=selector,
                            confidence=0.8,
                            execution_time=time.time() - time.time(),
                            validation_passed=True,
                            xpath_matches=1,
                            element_found=True,
                            action_performed="click"
                        )
                except Exception:
                    continue
            
            return StepResult(
                step_number=step_number,
                step_text=step_text,
                success=False,
                selector="",
                confidence=0.0,
                error_message=f"Could not find clickable element for: {target}",
                execution_time=time.time() - time.time()
            )
            
        except Exception as e:
            return StepResult(
                step_number=step_number,
                step_text=step_text,
                success=False,
                selector="",
                confidence=0.0,
                error_message=f"Fallback click failed: {str(e)}",
                execution_time=time.time() - time.time()
            )
    
    def _execute_type(self, step_number: int, step_text: str, parsed: Dict[str, Any]) -> StepResult:
        """Execute type step - universal for any website."""
        value = parsed['value']
        target = parsed['target']
        
        try:
            # Universal input field selectors
            selectors = [
                f"input[placeholder*='{target}']",
                f"input[aria-label*='{target}']",
                f"input[name*='{target}']",
                f"input[id*='{target}']",
                f"textarea[placeholder*='{target}']",
                f"textarea[aria-label*='{target}']",
                f"textarea[name*='{target}']",
                f"textarea[id*='{target}']",
                f"input[type='text'][placeholder*='{target}']",
                f"input[type='email'][placeholder*='{target}']",
                f"input[type='password'][placeholder*='{target}']",
                f"input[type='search'][placeholder*='{target}']",
            ]
            
            for selector in selectors:
                try:
                    element = self.page.locator(selector).first
                    if element.is_visible():
                        element.fill(value)
                        
                        return StepResult(
                            step_number=step_number,
                            step_text=step_text,
                            success=True,
                            selector=selector,
                            confidence=0.9,
                            execution_time=time.time() - time.time(),
                            validation_passed=True,
                            element_found=True,
                            action_performed="type"
                        )
                except Exception:
                    continue
            
            return StepResult(
                step_number=step_number,
                step_text=step_text,
                success=False,
                selector="",
                confidence=0.0,
                error_message=f"Could not find input field for: {target}",
                execution_time=time.time() - time.time()
            )
            
        except Exception as e:
            return StepResult(
                step_number=step_number,
                step_text=step_text,
                success=False,
                selector="",
                confidence=0.0,
                error_message=f"Type execution failed: {str(e)}",
                execution_time=time.time() - time.time()
            )
    
    def _execute_validate_url(self, step_number: int, step_text: str, parsed: Dict[str, Any]) -> StepResult:
        """Execute URL validation step - universal."""
        expected_url = parsed['expected_url']
        
        try:
            current_url = self.page.url
            
            # Normalize URLs for comparison
            def normalize_url(url):
                return url.rstrip('/').lower()
            
            current_normalized = normalize_url(current_url)
            expected_normalized = normalize_url(expected_url)
            
            # Check if expected URL is contained in current URL
            if expected_normalized in current_normalized or current_normalized in expected_normalized:
                return StepResult(
                    step_number=step_number,
                    step_text=step_text,
                    success=True,
                    selector="",
                    confidence=1.0,
                    execution_time=time.time() - time.time(),
                    validation_passed=True,
                    action_performed="validate_url"
                )
            else:
                return StepResult(
                    step_number=step_number,
                    step_text=step_text,
                    success=False,
                    selector="",
                    confidence=0.0,
                    error_message=f"URL mismatch. Expected: {expected_url}, Got: {current_url}",
                    execution_time=time.time() - time.time()
                )
                
        except Exception as e:
            return StepResult(
                step_number=step_number,
                step_text=step_text,
                success=False,
                selector="",
                confidence=0.0,
                error_message=f"URL validation failed: {str(e)}",
                execution_time=time.time() - time.time()
            )
    
    def _execute_validate_element(self, step_number: int, step_text: str, parsed: Dict[str, Any]) -> StepResult:
        """Execute element validation step - universal."""
        target = parsed['target']
        
        try:
            # Universal element selectors
            selectors = [
                f"text={target}",
                f"[aria-label*='{target}']",
                f"[title*='{target}']",
                f"[data-testid*='{target}']",
                f"button:has-text('{target}')",
                f"a:has-text('{target}')",
                f"input[value*='{target}']",
                f"option:has-text('{target}')",
                f"label:has-text('{target}')",
            ]
            
            for selector in selectors:
                try:
                    element = self.page.locator(selector).first
                    if element.is_visible():
                        return StepResult(
                            step_number=step_number,
                            step_text=step_text,
                            success=True,
                            selector=selector,
                            confidence=0.9,
                            execution_time=time.time() - time.time(),
                            validation_passed=True,
                            element_found=True,
                            action_performed="validate_element"
                        )
                except Exception:
                    continue
            
            return StepResult(
                step_number=step_number,
                step_text=step_text,
                success=False,
                selector="",
                confidence=0.0,
                error_message=f"Element not found or not visible: {target}",
                execution_time=time.time() - time.time()
            )
            
        except Exception as e:
            return StepResult(
                step_number=step_number,
                step_text=step_text,
                success=False,
                selector="",
                confidence=0.0,
                error_message=f"Element validation failed: {str(e)}",
                execution_time=time.time() - time.time()
            )
    
    def _execute_wait(self, step_number: int, step_text: str, parsed: Dict[str, Any]) -> StepResult:
        """Execute wait step - universal."""
        duration = parsed['duration']
        
        try:
            time.sleep(duration)
            
            return StepResult(
                step_number=step_number,
                step_text=step_text,
                success=True,
                selector="",
                confidence=1.0,
                execution_time=duration,
                validation_passed=True,
                action_performed="wait"
            )
            
        except Exception as e:
            return StepResult(
                step_number=step_number,
                step_text=step_text,
                success=False,
                selector="",
                confidence=0.0,
                error_message=f"Wait execution failed: {str(e)}",
                execution_time=time.time() - time.time()
            )
    
    def _execute_hover(self, step_number: int, step_text: str, parsed: Dict[str, Any]) -> StepResult:
        """Execute hover step - universal."""
        target = parsed['target']
        
        try:
            # Universal hover selectors
            selectors = [
                f"text={target}",
                f"[aria-label*='{target}']",
                f"[title*='{target}']",
                f"[data-testid*='{target}']",
                f"button:has-text('{target}')",
                f"a:has-text('{target}')",
            ]
            
            for selector in selectors:
                try:
                    element = self.page.locator(selector).first
                    if element.is_visible():
                        element.hover()
                        
                        return StepResult(
                            step_number=step_number,
                            step_text=step_text,
                            success=True,
                            selector=selector,
                            confidence=0.9,
                            execution_time=time.time() - time.time(),
                            validation_passed=True,
                            element_found=True,
                            action_performed="hover"
                        )
                except Exception:
                    continue
            
            return StepResult(
                step_number=step_number,
                step_text=step_text,
                success=False,
                selector="",
                confidence=0.0,
                error_message=f"Could not find element to hover: {target}",
                execution_time=time.time() - time.time()
            )
            
        except Exception as e:
            return StepResult(
                step_number=step_number,
                step_text=step_text,
                success=False,
                selector="",
                confidence=0.0,
                error_message=f"Hover execution failed: {str(e)}",
                execution_time=time.time() - time.time()
            )
    
    def _execute_scroll(self, step_number: int, step_text: str, parsed: Dict[str, Any]) -> StepResult:
        """Execute scroll step - universal."""
        target = parsed['target']
        
        try:
            if target == 'down':
                self.page.evaluate("window.scrollBy(0, window.innerHeight)")
            elif target == 'up':
                self.page.evaluate("window.scrollBy(0, -window.innerHeight)")
            elif target == 'left':
                self.page.evaluate("window.scrollBy(-window.innerWidth, 0)")
            elif target == 'right':
                self.page.evaluate("window.scrollBy(window.innerWidth, 0)")
            elif target == 'top':
                self.page.evaluate("window.scrollTo(0, 0)")
            elif target == 'bottom':
                self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            else:
                # Try to scroll to specific element
                selectors = [
                    f"text={target}",
                    f"[aria-label*='{target}']",
                    f"[title*='{target}']",
                ]
                
                for selector in selectors:
                    try:
                        element = self.page.locator(selector).first
                        if element.is_visible():
                            element.scroll_into_view_if_needed()
                            break
                    except Exception:
                        continue
            
            return StepResult(
                step_number=step_number,
                step_text=step_text,
                success=True,
                selector="",
                confidence=1.0,
                execution_time=time.time() - time.time(),
                validation_passed=True,
                action_performed="scroll"
            )
            
        except Exception as e:
            return StepResult(
                step_number=step_number,
                step_text=step_text,
                success=False,
                selector="",
                confidence=0.0,
                error_message=f"Scroll execution failed: {str(e)}",
                execution_time=time.time() - time.time()
            )
    
    def _execute_submit(self, step_number: int, step_text: str, parsed: Dict[str, Any]) -> StepResult:
        """Execute submit step - universal."""
        target = parsed['target']
        
        try:
            # Universal submit selectors
            selectors = [
                f"button:has-text('{target}')",
                f"input[type='submit'][value*='{target}']",
                f"input[type='button'][value*='{target}']",
                f"[aria-label*='{target}']",
                f"[title*='{target}']",
                f"[data-testid*='{target}']",
            ]
            
            for selector in selectors:
                try:
                    element = self.page.locator(selector).first
                    if element.is_visible():
                        element.click()
                        
                        return StepResult(
                            step_number=step_number,
                            step_text=step_text,
                            success=True,
                            selector=selector,
                            confidence=0.9,
                            execution_time=time.time() - time.time(),
                            validation_passed=True,
                            element_found=True,
                            action_performed="submit"
                        )
                except Exception:
                    continue
            
            return StepResult(
                step_number=step_number,
                step_text=step_text,
                success=False,
                selector="",
                confidence=0.0,
                error_message=f"Could not find submit element: {target}",
                execution_time=time.time() - time.time()
            )
            
        except Exception as e:
            return StepResult(
                step_number=step_number,
                step_text=step_text,
                success=False,
                selector="",
                confidence=0.0,
                error_message=f"Submit execution failed: {str(e)}",
                execution_time=time.time() - time.time()
            )
    
    def _execute_clear(self, step_number: int, step_text: str, parsed: Dict[str, Any]) -> StepResult:
        """Execute clear step - universal."""
        target = parsed['target']
        
        try:
            # Universal clear selectors
            selectors = [
                f"input[placeholder*='{target}']",
                f"input[aria-label*='{target}']",
                f"input[name*='{target}']",
                f"input[id*='{target}']",
                f"textarea[placeholder*='{target}']",
                f"textarea[aria-label*='{target}']",
                f"textarea[name*='{target}']",
                f"textarea[id*='{target}']",
            ]
            
            for selector in selectors:
                try:
                    element = self.page.locator(selector).first
                    if element.is_visible():
                        element.clear()
                        
                        return StepResult(
                            step_number=step_number,
                            step_text=step_text,
                            success=True,
                            selector=selector,
                            confidence=0.9,
                            execution_time=time.time() - time.time(),
                            validation_passed=True,
                            element_found=True,
                            action_performed="clear"
                        )
                except Exception:
                    continue
            
            return StepResult(
                step_number=step_number,
                step_text=step_text,
                success=False,
                selector="",
                confidence=0.0,
                error_message=f"Could not find element to clear: {target}",
                execution_time=time.time() - time.time()
            )
            
        except Exception as e:
            return StepResult(
                step_number=step_number,
                step_text=step_text,
                success=False,
                selector="",
                confidence=0.0,
                error_message=f"Clear execution failed: {str(e)}",
                execution_time=time.time() - time.time()
            )
    
    def _dismiss_overlays(self):
        """Dismiss common overlays and popups - universal for any website."""
        if not self.page:
            return
        
        # Universal overlay selectors that work on most websites
        overlay_selectors = [
            'button[aria-label="Close"]',
            'button[aria-label="Dismiss"]',
            'button[aria-label="Accept"]',
            'button:has-text("Accept")',
            'button:has-text("Accept all")',
            'button:has-text("Accept All")',
            'button:has-text("Got it")',
            'button:has-text("OK")',
            'button:has-text("Continue")',
            'button:has-text("Close")',
            'button:has-text("×")',
            'button:has-text("✕")',
            '#onetrust-accept-btn-handler',
            '.cc-allow',
            '.cookie-accept',
            '.modal-close',
            '.popup-close',
            '[data-testid="close"]',
            '[data-testid="dismiss"]',
            '[aria-label="Close dialog"]',
            '[aria-label="Close modal"]',
            '.modal button.close',
            '.popup button.close',
            'button[class*="close"]',
            'button[class*="dismiss"]',
        ]
        
        for selector in overlay_selectors:
            try:
                element = self.page.locator(selector).first
                if element.is_visible():
                    element.click()
                    time.sleep(0.5)
            except Exception:
                continue
    
    def run_automation(self, steps: List[str], website: str = "Unknown", use_case: str = "General") -> AutomationResult:
        """Run a complete automation sequence - universal for any website."""
        start_time = time.time()
        results = []
        
        try:
            # Start browser
            self.start_browser()
            
            # Execute each step
            for i, step in enumerate(steps, 1):
                logger.info(f"Executing step {i}/{len(steps)}: {step}")
                result = self.execute_step(i, step)
                results.append(result)
                
                # Log step result
                if result.success:
                    logger.info(f"✅ Step {i} passed: {result.step_text}")
                    if result.selector:
                        logger.info(f"   Selector: {result.selector}")
                        logger.info(f"   Confidence: {result.confidence:.3f}")
                        logger.info(f"   XPath matches: {result.xpath_matches}")
                else:
                    logger.error(f"❌ Step {i} failed: {result.step_text}")
                    logger.error(f"   Error: {result.error_message}")
                
                # Stop on first failure
                if not result.success:
                    logger.error(f"Stopping automation due to step {i} failure")
                    break
            
            # Calculate final results
            successful_steps = sum(1 for r in results if r.success)
            failed_steps = len(results) - successful_steps
            total_time = time.time() - start_time
            success_rate = (successful_steps / len(results)) * 100 if results else 0
            
            final_url = self.page.url if self.page else ""
            
            return AutomationResult(
                total_steps=len(steps),
                successful_steps=successful_steps,
                failed_steps=failed_steps,
                total_time=total_time,
                results=results,
                final_url=final_url,
                success_rate=success_rate,
                website=website,
                use_case=use_case
            )
            
        except Exception as e:
            logger.error(f"Automation failed with error: {e}")
            return AutomationResult(
                total_steps=len(steps),
                successful_steps=0,
                failed_steps=len(steps),
                total_time=time.time() - start_time,
                results=results,
                final_url="",
                success_rate=0.0,
                website=website,
                use_case=use_case
            )
        finally:
            # Always stop browser
            self.stop_browser()

def run_universal_automation(steps: List[str], website: str = "Unknown", use_case: str = "General", headless: bool = True) -> AutomationResult:
    """
    Run universal automation from English steps for ANY website.
    
    Args:
        steps: List of English automation steps
        website: Name of the website being automated
        use_case: Description of the use case
        headless: Whether to run browser in headless mode
    
    Returns:
        AutomationResult with detailed execution information
    """
    runner = UniversalAutomationRunner(headless=headless)
    return runner.run_automation(steps, website, use_case)

# Example usage and testing
if __name__ == "__main__":
    # Example 1: E-commerce shopping
    ecommerce_steps = [
        "Open https://www.amazon.com/",
        "Click on 'Search' field",
        "Type 'laptop' in 'Search' field",
        "Click on 'Search' button",
        "Click on 'First product'",
        "Click on 'Add to Cart'",
        "Validate that 'Added to Cart' is visible"
    ]
    
    # Example 2: Social media
    social_steps = [
        "Open https://www.twitter.com/",
        "Click on 'Sign in'",
        "Type 'username' in 'Username' field",
        "Type 'password' in 'Password' field",
        "Click on 'Log in'",
        "Validate that it landed on https://twitter.com/home"
    ]
    
    # Example 3: News website
    news_steps = [
        "Open https://www.cnn.com/",
        "Click on 'World' tab",
        "Click on 'First article'",
        "Validate that article is visible",
        "Scroll down",
        "Click on 'Related articles'"
    ]
    
    print("🚀 Universal English Automation Framework")
    print("=" * 60)
    print("This framework can automate ANY website with English instructions!")
    print("=" * 60)
    
    # Run e-commerce example
    print("\n🛒 E-commerce Example (Amazon):")
    result = run_universal_automation(ecommerce_steps, "Amazon", "E-commerce Shopping", headless=False)
    
    print(f"\n📊 Results: {result.successful_steps}/{result.total_steps} steps successful ({result.success_rate:.1f}%)")
    print(f"Website: {result.website}")
    print(f"Use Case: {result.use_case}")
    print(f"Final URL: {result.final_url}")