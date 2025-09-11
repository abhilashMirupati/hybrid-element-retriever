"""Comprehensive Verizon page test demonstrating the framework's capabilities."""

import pytest
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from playwright.sync_api import sync_playwright  # noqa: F401
    PLAYWRIGHT_AVAILABLE = True
except Exception:
    PLAYWRIGHT_AVAILABLE = False


@pytest.mark.skipif(not PLAYWRIGHT_AVAILABLE, reason="Playwright not available")
@pytest.mark.skipif(os.getenv("HER_E2E") != "1", reason="Set HER_E2E=1 to run live e2e test")
@pytest.mark.timeout(300)
class TestVerizonComprehensive:
    """Comprehensive test of Verizon page interactions using the framework."""
    
    def test_verizon_phone_navigation_flow(self):
        """Test complete flow: navigate to Verizon, find phones, filter by Apple, select iPhone."""
        from her.core.runner import Runner
        
        runner = Runner(headless=True)
        
        try:
            # Step 1: Navigate to Verizon homepage
            runner.snapshot("https://www.verizon.com/")
            runner._page.wait_for_timeout(3000)
            
            # Step 2: Click on Phones navigation
            shot = runner.snapshot()
            result = runner.resolve_selector("Phones", shot)
            
            assert result['confidence'] > 0.5, f"Low confidence for Phones selector: {result['confidence']}"
            
            runner.do_action("click", result["selector"], None, result.get("promo", {}))
            runner._page.wait_for_timeout(3000)
            
            # Verify we're on phones page
            current_url = runner._page.url
            assert "phones" in current_url.lower(), f"Expected phones in URL, got: {current_url}"
            
            # Step 3: Apply Apple filter
            shot = runner.snapshot()
            result = runner.resolve_selector("Apple", shot)
            
            assert result['confidence'] > 0.5, f"Low confidence for Apple filter: {result['confidence']}"
            
            runner.do_action("click", result["selector"], None, result.get("promo", {}))
            runner._page.wait_for_timeout(3000)
            
            # Step 4: Select iPhone product
            shot = runner.snapshot()
            result = runner.resolve_selector("iPhone", shot)
            
            assert result['confidence'] > 0.5, f"Low confidence for iPhone selector: {result['confidence']}"
            
            runner.do_action("click", result["selector"], None, result.get("promo", {}))
            runner._page.wait_for_timeout(5000)
            
            # Verify we're on iPhone product page
            current_url = runner._page.url
            assert "iphone" in current_url.lower(), f"Expected iPhone in URL, got: {current_url}"
            
        finally:
            runner._close()
    
    def test_verizon_search_functionality(self):
        """Test search functionality on Verizon site."""
        from her.core.runner import Runner
        
        runner = Runner(headless=True)
        
        try:
            # Navigate to Verizon
            runner.snapshot("https://www.verizon.com/")
            runner._page.wait_for_timeout(3000)
            
            # Find and use search box
            shot = runner.snapshot()
            result = runner.resolve_selector("search", shot)
            
            assert result['confidence'] > 0.3, f"Low confidence for search selector: {result['confidence']}"
            
            # Type search query
            runner.do_action("type", result["selector"], "iPhone 16", result.get("promo", {}))
            runner._page.wait_for_timeout(2000)
            
            # Submit search
            runner.do_action("press", result["selector"], "Enter", result.get("promo", {}))
            runner._page.wait_for_timeout(5000)
            
            # Verify search results
            current_url = runner._page.url
            assert "search" in current_url.lower() or "iphone" in current_url.lower(), \
                f"Expected search results, got: {current_url}"
            
        finally:
            runner._close()
    
    def test_verizon_menu_navigation(self):
        """Test menu navigation on Verizon site."""
        from her.core.runner import Runner
        
        runner = Runner(headless=True)
        
        try:
            # Navigate to Verizon
            runner.snapshot("https://www.verizon.com/")
            runner._page.wait_for_timeout(3000)
            
            # Find and click menu button
            shot = runner.snapshot()
            result = runner.resolve_selector("menu", shot)
            
            if result['confidence'] > 0.3:
                runner.do_action("click", result["selector"], None, result.get("promo", {}))
                runner._page.wait_for_timeout(2000)
                
                # Try to find a menu item
                shot = runner.snapshot()
                result = runner.resolve_selector("plans", shot)
                
                if result['confidence'] > 0.3:
                    runner.do_action("click", result["selector"], None, result.get("promo", {}))
                    runner._page.wait_for_timeout(3000)
                    
                    # Verify navigation
                    current_url = runner._page.url
                    assert "plan" in current_url.lower(), f"Expected plans in URL, got: {current_url}"
            
        finally:
            runner._close()
    
    def test_verizon_element_detection_accuracy(self):
        """Test accuracy of element detection on Verizon pages."""
        from her.core.runner import Runner
        
        runner = Runner(headless=True)
        
        try:
            # Navigate to Verizon
            runner.snapshot("https://www.verizon.com/")
            runner._page.wait_for_timeout(3000)
            
            # Test various element types
            test_queries = [
                "phones",
                "plans", 
                "shop",
                "login",
                "search",
                "menu"
            ]
            
            results = {}
            for query in test_queries:
                shot = runner.snapshot()
                result = runner.resolve_selector(query, shot)
                results[query] = {
                    'confidence': result['confidence'],
                    'selector': result['selector'],
                    'candidates_count': len(result.get('candidates', []))
                }
            
            # Verify we found elements with reasonable confidence
            high_confidence_count = sum(1 for r in results.values() if r['confidence'] > 0.5)
            assert high_confidence_count >= 3, f"Expected at least 3 high-confidence matches, got {high_confidence_count}"
            
            # Verify we have candidates for most queries
            candidates_count = sum(1 for r in results.values() if r['candidates_count'] > 0)
            assert candidates_count >= 4, f"Expected at least 4 queries with candidates, got {candidates_count}"
            
        finally:
            runner._close()
    
    def test_verizon_error_handling(self):
        """Test error handling with invalid selectors."""
        from her.core.runner import Runner
        
        runner = Runner(headless=True)
        
        try:
            # Navigate to Verizon
            runner.snapshot("https://www.verizon.com/")
            runner._page.wait_for_timeout(3000)
            
            # Test with non-existent element
            shot = runner.snapshot()
            result = runner.resolve_selector("nonexistent_element_xyz", shot)
            
            # Should return low confidence or empty results
            assert result['confidence'] < 0.5 or len(result.get('candidates', [])) == 0, \
                "Should handle non-existent elements gracefully"
            
            # Test with empty query
            result = runner.resolve_selector("", shot)
            assert result['confidence'] < 0.5, "Should handle empty queries gracefully"
            
        finally:
            runner._close()