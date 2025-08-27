"""Locator verification for uniqueness and stability."""

from typing import Dict, Any, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

try:
    from playwright.sync_api import Page, Locator, TimeoutError as PlaywrightTimeout

    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    Page = Any
    Locator = Any
    PlaywrightTimeout = Exception
    PLAYWRIGHT_AVAILABLE = False


class LocatorVerifier:
    """Verifies locators for uniqueness and stability."""

    def __init__(self, timeout_ms: int = 5000):
        self.timeout_ms = timeout_ms

    def verify(
        self,
        locator: str,
        page: Optional[Page] = None,
        expected_element: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Verify a locator for uniqueness and correctness.

        Args:
            locator: Locator string to verify
            page: Playwright page for live verification
            expected_element: Expected element descriptor

        Returns:
            Tuple of (is_valid, reason, verification_details)
        """
        if not page or not PLAYWRIGHT_AVAILABLE:
            # Can't verify without a page
            return True, "No page available for verification", None

        try:
            # Convert string locator to Playwright locator
            pw_locator = self._string_to_locator(locator, page)

            # Check uniqueness
            count = pw_locator.count()

            if count == 0:
                return False, "Locator matches no elements", {"count": 0}
            elif count > 1:
                return (
                    False,
                    f"Locator matches {count} elements (not unique)",
                    {"count": count},
                )

            # Check if element is visible and enabled
            is_visible = pw_locator.is_visible()
            is_enabled = pw_locator.is_enabled()

            if not is_visible:
                return (
                    False,
                    "Element is not visible",
                    {"count": 1, "visible": False, "enabled": is_enabled},
                )

            if not is_enabled:
                # Warning but not failure - disabled elements can be valid targets
                logger.warning(f"Element matched by {locator} is disabled")

            # If we have expected element, verify it's the right one
            if expected_element:
                actual_text = pw_locator.text_content() or ""
                expected_text = expected_element.get("text", "")

                # Basic sanity check
                if expected_text and actual_text:
                    if expected_text.strip()[:50] != actual_text.strip()[:50]:
                        logger.warning(
                            f"Text mismatch: expected '{expected_text[:50]}...', "
                            f"got '{actual_text[:50]}...'"
                        )

            return (
                True,
                "Locator verified successfully",
                {
                    "count": 1,
                    "visible": is_visible,
                    "enabled": is_enabled,
                    "locator": locator,
                },
            )

        except PlaywrightTimeout:
            return False, "Locator timed out", {"timeout": self.timeout_ms}
        except Exception as e:
            return False, f"Verification failed: {str(e)}", None

    def verify_all(
        self,
        locators: List[str],
        page: Optional[Page] = None,
        expected_element: Optional[Dict[str, Any]] = None,
    ) -> List[Tuple[str, bool, str]]:
        """Verify multiple locators and return results.

        Args:
            locators: List of locator strings
            page: Playwright page
            expected_element: Expected element descriptor

        Returns:
            List of (locator, is_valid, reason) tuples
        """
        results = []
        for locator in locators:
            is_valid, reason, _ = self.verify(locator, page, expected_element)
            results.append((locator, is_valid, reason))
        return results

    def find_unique_locator(
        self,
        locators: List[str],
        page: Optional[Page] = None,
        expected_element: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """Find the first unique and valid locator from candidates.

        Args:
            locators: List of candidate locators
            page: Playwright page
            expected_element: Expected element descriptor

        Returns:
            First valid unique locator, or None if none found
        """
        for locator in locators:
            is_valid, reason, details = self.verify(locator, page, expected_element)
            if is_valid:
                logger.info(f"Found unique locator: {locator}")
                return locator
            else:
                logger.debug(f"Locator {locator} invalid: {reason}")

        return None

    def test_stability(
        self, locator: str, page: Page, num_tests: int = 3, action: Optional[str] = None
    ) -> Tuple[bool, float, List[str]]:
        """Test locator stability over multiple attempts.

        Args:
            locator: Locator to test
            page: Playwright page
            num_tests: Number of stability tests
            action: Optional action to perform between tests

        Returns:
            Tuple of (is_stable, success_rate, failure_reasons)
        """
        if not page or not PLAYWRIGHT_AVAILABLE:
            return True, 1.0, []

        successes = 0
        failures = []

        for i in range(num_tests):
            try:
                pw_locator = self._string_to_locator(locator, page)

                # Check if element exists and is unique
                count = pw_locator.count()
                if count != 1:
                    failures.append(f"Test {i+1}: Found {count} elements")
                    continue

                # Optionally perform action
                if action == "click":
                    pw_locator.click(timeout=self.timeout_ms)
                elif action == "fill":
                    pw_locator.fill("test", timeout=self.timeout_ms)

                successes += 1

            except Exception as e:
                failures.append(f"Test {i+1}: {str(e)}")

        success_rate = successes / num_tests
        is_stable = success_rate >= 0.8  # 80% success threshold

        return is_stable, success_rate, failures

    def _string_to_locator(self, locator_str: str, page: Page) -> Locator:
        """Convert string locator to Playwright Locator object.

        Args:
            locator_str: String representation of locator
            page: Playwright page

        Returns:
            Playwright Locator object
        """
        if not PLAYWRIGHT_AVAILABLE:
            raise RuntimeError("Playwright not available")

        # Handle different locator formats
        if locator_str.startswith("role="):
            # Parse role locator
            parts = locator_str[5:].split("[", 1)
            role = parts[0]
            if len(parts) > 1:
                # Extract name from role=button[name="..."]
                import re

                name_match = re.search(r'name="([^"]*)"', parts[1])
                if name_match:
                    name = name_match.group(1)
                    return page.get_by_role(role, name=name)
            return page.get_by_role(role)

        elif locator_str.startswith("text="):
            # Text selector
            text = locator_str[5:].strip('"')
            return page.get_by_text(text, exact=True)

        elif locator_str.startswith("//"):
            # XPath selector
            return page.locator(f"xpath={locator_str}")

        else:
            # CSS selector
            return page.locator(locator_str)
