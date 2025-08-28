#!/usr/bin/env python3
"""Test runner for edge case examples."""

import json
import time
from pathlib import Path
from typing import Dict, List, Any
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logger.warning("Playwright not available - tests will be limited")

# Import HER components
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.her.session.enhanced_manager import EnhancedSessionManager
from src.her.locator.enhanced_verify import EnhancedLocatorVerifier, PopupHandler
from src.her.recovery.enhanced_promotion import EnhancedPromotionStore
from src.her.cli_api import HER


class EdgeCaseTestRunner:
    """Runner for edge case tests."""
    
    def __init__(self):
        self.results = []
        self.session_manager = None
        self.verifier = None
        self.promotion_store = None
        
    def setup(self):
        """Setup test environment."""
        logger.info("Setting up test environment...")
        
        # Initialize enhanced components
        self.session_manager = EnhancedSessionManager(
            enable_incremental=True,
            enable_spa_tracking=True
        )
        
        self.verifier = EnhancedLocatorVerifier(auto_handle_popups=True)
        self.promotion_store = EnhancedPromotionStore(auto_fallback=True)
        
        logger.info("Test environment ready")
    
    def test_cold_start(self, page) -> Dict[str, Any]:
        """Test cold start scenario."""
        logger.info("Testing cold start...")
        results = {
            "test": "cold_start",
            "passed": False,
            "details": {}
        }
        
        try:
            # Navigate to test page
            test_file = Path(__file__).parent / "cold_start.html"
            page.goto(f"file://{test_file}")
            page.wait_for_load_state("networkidle")
            
            # Create session (cold start)
            session = self.session_manager.create_session("cold_start_test", page)
            
            # Verify cold start behavior
            results["details"]["is_cold_start"] = session.is_cold_start
            results["details"]["elements_indexed"] = len(session.element_descriptors)
            results["details"]["cache_created"] = Path(".cache/her_cache.db").exists()
            
            # Test element resolution
            her = HER(page=page)
            
            # Test various intents
            test_intents = [
                "Search for products",
                "Add Wireless Headphones to cart",
                "Filter by electronics"
            ]
            
            intent_results = []
            for intent in test_intents:
                try:
                    result = her.resolve(intent)
                    intent_results.append({
                        "intent": intent,
                        "success": result.get("ok", False),
                        "selector": result.get("selector", "")
                    })
                except Exception as e:
                    intent_results.append({
                        "intent": intent,
                        "success": False,
                        "error": str(e)
                    })
            
            results["details"]["intent_resolution"] = intent_results
            
            # Check if all intents resolved
            results["passed"] = all(r["success"] for r in intent_results)
            
            logger.info(f"Cold start test: {'PASSED' if results['passed'] else 'FAILED'}")
            
        except Exception as e:
            results["error"] = str(e)
            logger.error(f"Cold start test failed: {e}")
        
        return results
    
    def test_incremental_update(self, page) -> Dict[str, Any]:
        """Test incremental update scenario."""
        logger.info("Testing incremental updates...")
        results = {
            "test": "incremental_update",
            "passed": False,
            "details": {}
        }
        
        try:
            # Navigate to test page
            test_file = Path(__file__).parent / "incremental_update.html"
            page.goto(f"file://{test_file}")
            page.wait_for_load_state("networkidle")
            
            # Create session and initial index
            session = self.session_manager.create_session("incremental_test", page)
            initial_count = len(session.element_descriptors)
            initial_ids = session.indexed_element_ids.copy()
            
            results["details"]["initial_elements"] = initial_count
            
            # Add new todo item
            page.fill("#new-todo-input", "Test incremental update")
            page.click("button[type='submit']")
            page.wait_for_timeout(500)
            
            # Force re-index
            self.session_manager._index_page_enhanced("incremental_test", page)
            
            # Check incremental update
            new_count = len(session.element_descriptors)
            new_ids = session.indexed_element_ids
            added_ids = new_ids - initial_ids
            
            results["details"]["new_elements"] = new_count
            results["details"]["elements_added"] = len(added_ids)
            results["details"]["incremental"] = len(added_ids) < new_count  # Should only index new elements
            
            # Test batch addition
            page.click("#add-batch")
            page.wait_for_timeout(500)
            
            self.session_manager._index_page_enhanced("incremental_test", page)
            batch_count = len(session.element_descriptors)
            
            results["details"]["batch_elements"] = batch_count
            results["details"]["batch_added"] = batch_count - new_count
            
            results["passed"] = results["details"]["incremental"]
            
            logger.info(f"Incremental update test: {'PASSED' if results['passed'] else 'FAILED'}")
            
        except Exception as e:
            results["error"] = str(e)
            logger.error(f"Incremental update test failed: {e}")
        
        return results
    
    def test_spa_routing(self, page) -> Dict[str, Any]:
        """Test SPA route change detection."""
        logger.info("Testing SPA routing...")
        results = {
            "test": "spa_routing",
            "passed": False,
            "details": {}
        }
        
        try:
            # Navigate to test page
            test_file = Path(__file__).parent / "spa_route_change.html"
            page.goto(f"file://{test_file}")
            page.wait_for_load_state("networkidle")
            
            # Create session with SPA tracking
            session = self.session_manager.create_session("spa_test", page)
            initial_route = page.url
            
            results["details"]["spa_tracking_enabled"] = session.spa_route_tracking
            
            # Navigate to different routes
            routes_tested = []
            
            # Click Products link
            page.click('[data-route="/products"]')
            page.wait_for_timeout(500)
            products_url = page.url
            routes_tested.append({
                "route": "/products",
                "url_changed": products_url != initial_route
            })
            
            # Click Users link
            page.click('[data-route="/users"]')
            page.wait_for_timeout(500)
            users_url = page.url
            routes_tested.append({
                "route": "/users",
                "url_changed": users_url != products_url
            })
            
            # Test browser back button
            page.go_back()
            page.wait_for_timeout(500)
            back_url = page.url
            routes_tested.append({
                "route": "back",
                "url_changed": back_url != users_url
            })
            
            results["details"]["routes_tested"] = routes_tested
            results["details"]["route_changes_detected"] = session.last_route is not None
            
            # Test element visibility on different routes
            visibility_tests = []
            
            # Go to products page
            page.click('[data-route="/products"]')
            page.wait_for_timeout(500)
            product_search_visible = page.is_visible("#product-search")
            visibility_tests.append({
                "route": "/products",
                "element": "#product-search",
                "visible": product_search_visible
            })
            
            # Go to contact page
            page.click('[data-route="/contact"]')
            page.wait_for_timeout(500)
            contact_form_visible = page.is_visible("#contact-form")
            visibility_tests.append({
                "route": "/contact",
                "element": "#contact-form",
                "visible": contact_form_visible
            })
            
            results["details"]["visibility_tests"] = visibility_tests
            
            results["passed"] = all(t["visible"] for t in visibility_tests)
            
            logger.info(f"SPA routing test: {'PASSED' if results['passed'] else 'FAILED'}")
            
        except Exception as e:
            results["error"] = str(e)
            logger.error(f"SPA routing test failed: {e}")
        
        return results
    
    def test_popup_handling(self, page) -> Dict[str, Any]:
        """Test popup and overlay handling."""
        logger.info("Testing popup handling...")
        results = {
            "test": "popup_handling",
            "passed": False,
            "details": {}
        }
        
        try:
            # Navigate to test page
            test_file = Path(__file__).parent / "overlay_popup.html"
            page.goto(f"file://{test_file}")
            
            # Wait for cookie banner to appear
            page.wait_for_timeout(2500)
            
            # Check if popup is detected
            popup_detected = PopupHandler.detect_popup(page)
            results["details"]["popup_detected"] = popup_detected is not None
            
            # Try to click target button (should be occluded)
            target_selector = "#target-button-1"
            
            # Verify without popup handling
            result_occluded = self.verifier.verify(target_selector, page)
            results["details"]["initially_accessible"] = result_occluded[0]
            
            # Close popup
            if popup_detected:
                closed = PopupHandler.close_popup(page, popup_detected)
                results["details"]["popup_closed"] = closed
                page.wait_for_timeout(500)
            
            # Verify after popup handling
            result_clear = self.verifier.verify(target_selector, page)
            results["details"]["accessible_after_close"] = result_clear[0]
            
            # Test multiple popups
            page.click("button[onclick='showAllPopups()']")
            page.wait_for_timeout(2000)
            
            # Test ESC key handling
            page.keyboard.press("Escape")
            page.wait_for_timeout(500)
            
            # Verify all cleared
            result_final = self.verifier.verify(target_selector, page)
            results["details"]["accessible_after_esc"] = result_final[0]
            
            results["passed"] = (
                results["details"]["popup_detected"] and
                results["details"]["accessible_after_close"] and
                results["details"]["accessible_after_esc"]
            )
            
            logger.info(f"Popup handling test: {'PASSED' if results['passed'] else 'FAILED'}")
            
        except Exception as e:
            results["error"] = str(e)
            logger.error(f"Popup handling test failed: {e}")
        
        return results
    
    def test_recovery_promotion(self, page) -> Dict[str, Any]:
        """Test recovery and promotion system."""
        logger.info("Testing recovery/promotion...")
        results = {
            "test": "recovery_promotion",
            "passed": False,
            "details": {}
        }
        
        try:
            # Navigate to cold start page (simpler for testing)
            test_file = Path(__file__).parent / "cold_start.html"
            page.goto(f"file://{test_file}")
            page.wait_for_load_state("networkidle")
            
            # Test successful locator promotion
            test_selector = "#product-search"
            test_context = page.url
            
            # Record success
            element = page.query_selector(test_selector)
            element_attrs = {
                "id": "product-search",
                "type": "text",
                "placeholder": "Search products..."
            }
            
            record = self.promotion_store.record_success(
                test_selector,
                test_context,
                element_attrs
            )
            
            results["details"]["promotion_recorded"] = record is not None
            results["details"]["promotion_score"] = record.score
            
            # Test fallback retrieval
            fallback = self.promotion_store.get_best_fallback(test_context)
            results["details"]["fallback_found"] = fallback is not None
            
            if fallback:
                results["details"]["fallback_selector"] = fallback.locator
                results["details"]["fallback_confidence"] = fallback.confidence
            
            # Test failure recording
            bad_selector = "#non-existent-element"
            self.promotion_store.record_failure(bad_selector, test_context)
            
            # Get stats
            stats = self.promotion_store.get_stats(test_context)
            results["details"]["stats"] = stats
            
            results["passed"] = (
                results["details"]["promotion_recorded"] and
                results["details"]["fallback_found"]
            )
            
            logger.info(f"Recovery/promotion test: {'PASSED' if results['passed'] else 'FAILED'}")
            
        except Exception as e:
            results["error"] = str(e)
            logger.error(f"Recovery/promotion test failed: {e}")
        
        return results
    
    def run_all_tests(self):
        """Run all edge case tests."""
        if not PLAYWRIGHT_AVAILABLE:
            logger.error("Playwright not available - cannot run tests")
            return
        
        self.setup()
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()
            
            try:
                # Run each test
                tests = [
                    self.test_cold_start,
                    self.test_incremental_update,
                    self.test_spa_routing,
                    self.test_popup_handling,
                    self.test_recovery_promotion
                ]
                
                for test_func in tests:
                    result = test_func(page)
                    self.results.append(result)
                    time.sleep(1)  # Brief pause between tests
                
            finally:
                browser.close()
        
        # Generate report
        self.generate_report()
    
    def generate_report(self):
        """Generate test report."""
        logger.info("\n" + "="*60)
        logger.info("EDGE CASE TEST REPORT")
        logger.info("="*60)
        
        passed = 0
        failed = 0
        
        for result in self.results:
            status = "✅ PASSED" if result.get("passed") else "❌ FAILED"
            logger.info(f"\n{result['test']}: {status}")
            
            if "details" in result:
                for key, value in result["details"].items():
                    logger.info(f"  - {key}: {value}")
            
            if "error" in result:
                logger.info(f"  ERROR: {result['error']}")
            
            if result.get("passed"):
                passed += 1
            else:
                failed += 1
        
        logger.info("\n" + "="*60)
        logger.info(f"SUMMARY: {passed} passed, {failed} failed")
        logger.info("="*60)
        
        # Save results to file
        report_path = Path(__file__).parent / "test_results.json"
        with open(report_path, "w") as f:
            json.dump(self.results, f, indent=2)
        
        logger.info(f"\nDetailed results saved to: {report_path}")


if __name__ == "__main__":
    runner = EdgeCaseTestRunner()
    runner.run_all_tests()