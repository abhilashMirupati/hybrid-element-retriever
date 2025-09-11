#!/usr/bin/env python3
"""
English-to-UI Automation Framework
==================================

A robust framework that converts plain English instructions into UI automation
with real XPath validation and comprehensive error handling.

Features:
- Natural language step parsing
- Real XPath validation on live websites
- Comprehensive error handling and retry logic
- Detailed logging and debugging
- Universal compatibility across different websites
"""

import os
import sys
import time
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
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
        logging.FileHandler('automation.log')
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

class EnglishStepParser:
    """Parses natural English instructions into structured automation steps."""
    
    def __init__(self):
        self.patterns = {
            # Navigation patterns
            'navigate': [
                r'open\s+(?:the\s+)?(?:website\s+)?(https?://[^\s]+)',
                r'go\s+to\s+(?:the\s+)?(?:website\s+)?(https?://[^\s]+)',
                r'visit\s+(?:the\s+)?(?:website\s+)?(https?://[^\s]+)',
                r'navigate\s+to\s+(?:the\s+)?(?:website\s+)?(https?://[^\s]+)',
            ],
            
            # Click patterns
            'click': [
                r'click\s+(?:on\s+)?(?:the\s+)?["\']([^"\']+)["\']',
                r'click\s+(?:on\s+)?(?:the\s+)?([^"\']+?)(?:\s+button|\s+link|\s+element)',
                r'press\s+(?:on\s+)?(?:the\s+)?["\']([^"\']+)["\']',
                r'tap\s+(?:on\s+)?(?:the\s+)?["\']([^"\']+)["\']',
                r'select\s+(?:the\s+)?["\']([^"\']+)["\']',
            ],
            
            # Type patterns
            'type': [
                r'type\s+["\']([^"\']+)["\']\s+(?:in\s+)?(?:the\s+)?["\']([^"\']+)["\']',
                r'enter\s+["\']([^"\']+)["\']\s+(?:in\s+)?(?:the\s+)?["\']([^"\']+)["\']',
                r'input\s+["\']([^"\']+)["\']\s+(?:in\s+)?(?:the\s+)?["\']([^"\']+)["\']',
                r'fill\s+(?:the\s+)?["\']([^"\']+)["\']\s+(?:with\s+)?["\']([^"\']+)["\']',
            ],
            
            # Validation patterns
            'validate': [
                r'validate\s+(?:that\s+)?(?:it\s+)?(?:landed\s+on\s+|navigated\s+to\s+)?(https?://[^\s]+)',
                r'verify\s+(?:that\s+)?(?:it\s+)?(?:landed\s+on\s+|navigated\s+to\s+)?(https?://[^\s]+)',
                r'check\s+(?:that\s+)?(?:it\s+)?(?:landed\s+on\s+|navigated\s+to\s+)?(https?://[^\s]+)',
                r'ensure\s+(?:that\s+)?(?:it\s+)?(?:landed\s+on\s+|navigated\s+to\s+)?(https?://[^\s]+)',
                r'validate\s+(?:that\s+)?["\']([^"\']+)["\']\s+(?:is\s+)?(?:visible|exists)',
                r'verify\s+(?:that\s+)?["\']([^"\']+)["\']\s+(?:is\s+)?(?:visible|exists)',
            ],
            
            # Wait patterns
            'wait': [
                r'wait\s+(?:for\s+)?(\d+)\s*(?:seconds?|secs?|s)',
                r'pause\s+(?:for\s+)?(\d+)\s*(?:seconds?|secs?|s)',
                r'delay\s+(?:for\s+)?(\d+)\s*(?:seconds?|secs?|s)',
            ]
        }
    
    def parse_step(self, step_text: str) -> Dict[str, Any]:
        """Parse a single English step into structured data."""
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
        
        # If no pattern matches, treat as click action
        return {
            'action': 'click',
            'target': step_text,
            'original_text': step_text
        }

class XPathValidator:
    """Validates XPath selectors on real web pages."""
    
    def __init__(self, page: Page):
        self.page = page
    
    def validate_xpath(self, xpath: str) -> Tuple[bool, int, str]:
        """
        Validate an XPath selector on the current page.
        
        Returns:
            (is_valid, match_count, error_message)
        """
        try:
            # Count elements matching the XPath
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

class EnglishAutomationRunner:
    """Main automation runner that executes English instructions."""
    
    def __init__(self, headless: bool = True, timeout: int = 30):
        self.headless = headless
        self.timeout = timeout
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.parser = EnglishStepParser()
        self.validator: Optional[XPathValidator] = None
        
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
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )
        self.page = self.browser.new_page()
        self.page.set_default_timeout(self.timeout * 1000)
        self.validator = XPathValidator(self.page)
        
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
        """Execute a single automation step."""
        start_time = time.time()
        
        try:
            # Parse the step
            parsed = self.parser.parse_step(step_text)
            action = parsed['action']
            
            logger.info(f"Step {step_number}: {action} - {step_text}")
            
            if action == 'navigate':
                return self._execute_navigate(step_number, step_text, parsed)
            elif action == 'click':
                return self._execute_click(step_number, step_text, parsed)
            elif action == 'type':
                return self._execute_type(step_number, step_text, parsed)
            elif action == 'validate_url':
                return self._execute_validate_url(step_number, step_text, parsed)
            elif action == 'validate_element':
                return self._execute_validate_element(step_number, step_text, parsed)
            elif action == 'wait':
                return self._execute_wait(step_number, step_text, parsed)
            else:
                return StepResult(
                    step_number=step_number,
                    step_text=step_text,
                    success=False,
                    selector="",
                    confidence=0.0,
                    error_message=f"Unknown action: {action}",
                    execution_time=time.time() - start_time
                )
                
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
        """Execute navigation step."""
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
                validation_passed=True
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
        """Execute click step using HER framework."""
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
                    xpath_matches=match_count
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
        """Fallback click execution using basic Playwright selectors."""
        try:
            # Try different selector strategies
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
                            xpath_matches=1
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
        """Execute type step."""
        value = parsed['value']
        target = parsed['target']
        
        try:
            # Find input field
            selectors = [
                f"input[placeholder*='{target}']",
                f"input[aria-label*='{target}']",
                f"input[name*='{target}']",
                f"input[id*='{target}']",
                f"textarea[placeholder*='{target}']",
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
                            validation_passed=True
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
        """Execute URL validation step."""
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
                    validation_passed=True
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
        """Execute element validation step."""
        target = parsed['target']
        
        try:
            # Try to find the element
            selectors = [
                f"text={target}",
                f"[aria-label*='{target}']",
                f"[title*='{target}']",
                f"[data-testid*='{target}']",
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
                            validation_passed=True
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
        """Execute wait step."""
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
                validation_passed=True
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
    
    def _dismiss_overlays(self):
        """Dismiss common overlays and popups."""
        if not self.page:
            return
        
        overlay_selectors = [
            'button[aria-label="Close"]',
            'button[aria-label="Dismiss"]',
            'button:has-text("Accept")',
            'button:has-text("Accept all")',
            'button:has-text("Got it")',
            'button:has-text("OK")',
            '#onetrust-accept-btn-handler',
            '.cc-allow',
            '[data-testid="close"]',
        ]
        
        for selector in overlay_selectors:
            try:
                element = self.page.locator(selector).first
                if element.is_visible():
                    element.click()
                    time.sleep(0.5)
            except Exception:
                continue
    
    def run_automation(self, steps: List[str]) -> AutomationResult:
        """Run a complete automation sequence."""
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
                success_rate=success_rate
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
                success_rate=0.0
            )
        finally:
            # Always stop browser
            self.stop_browser()

def run_english_automation(steps: List[str], headless: bool = True) -> AutomationResult:
    """
    Run automation from English steps.
    
    Args:
        steps: List of English automation steps
        headless: Whether to run browser in headless mode
    
    Returns:
        AutomationResult with detailed execution information
    """
    runner = EnglishAutomationRunner(headless=headless)
    return runner.run_automation(steps)

# Example usage and testing
if __name__ == "__main__":
    # Test the framework with the Verizon example
    test_steps = [
        "Open https://www.verizon.com/",
        "Click on 'Phones' button",
        "Click on 'Apple' filter button", 
        "Click on 'Apple iPhone 16 Pro Max'",
        "Validate that it landed on https://www.verizon.com/smartphones/apple-iphone-16-pro-max/",
        "Click on '512 GB'"
    ]
    
    print("🚀 Starting English Automation Framework Test")
    print("=" * 60)
    
    result = run_english_automation(test_steps, headless=False)
    
    print("\n📊 AUTOMATION RESULTS")
    print("=" * 60)
    print(f"Total Steps: {result.total_steps}")
    print(f"Successful: {result.successful_steps}")
    print(f"Failed: {result.failed_steps}")
    print(f"Success Rate: {result.success_rate:.1f}%")
    print(f"Total Time: {result.total_time:.2f}s")
    print(f"Final URL: {result.final_url}")
    
    print("\n📋 DETAILED RESULTS")
    print("=" * 60)
    for i, step_result in enumerate(result.results, 1):
        status = "✅ PASS" if step_result.success else "❌ FAIL"
        print(f"{i}. {status} - {step_result.step_text}")
        if step_result.selector:
            print(f"   Selector: {step_result.selector}")
            print(f"   Confidence: {step_result.confidence:.3f}")
            print(f"   XPath Matches: {step_result.xpath_matches}")
        if step_result.error_message:
            print(f"   Error: {step_result.error_message}")
        print()