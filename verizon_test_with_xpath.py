#!/usr/bin/env python3
"""
Verizon Test with XPath Capture
Runs the Verizon test suite and captures XPath selectors for each step.
"""

import os
import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Set environment variables
os.environ["HER_E2E"] = "1"
os.environ["HER_DEBUG"] = "1"
os.environ["HER_LOG_LEVEL"] = "DEBUG"

try:
    from her.core.runner import Runner
    from her.core.pipeline import HybridPipeline
    PLAYWRIGHT_AVAILABLE = True
except Exception as e:
    print(f"❌ Import error: {e}")
    PLAYWRIGHT_AVAILABLE = False

class VerizonTestWithXPath:
    """Test Verizon page interactions and capture XPath selectors."""
    
    def __init__(self):
        self.results = []
        self.runner = None
        
    def log_step(self, step_name, xpath, confidence, success=True, error=None):
        """Log a test step with XPath information."""
        result = {
            "step": step_name,
            "xpath": xpath,
            "confidence": confidence,
            "success": success,
            "error": error,
            "timestamp": time.time()
        }
        self.results.append(result)
        
        status = "✅" if success else "❌"
        print(f"{status} {step_name}")
        print(f"   XPath: {xpath}")
        print(f"   Confidence: {confidence:.3f}")
        if error:
            print(f"   Error: {error}")
        print()
    
    def test_verizon_phone_navigation_flow(self):
        """Test complete flow: navigate to Verizon, find phones, filter by Apple, select iPhone."""
        print("🚀 Starting Verizon Phone Navigation Flow Test")
        print("=" * 60)
        
        try:
            # Initialize runner
            self.runner = Runner(headless=True)
            
            # Step 1: Navigate to Verizon homepage
            print("📍 Step 1: Navigate to Verizon homepage")
            self.runner._snapshot("https://www.verizon.com/")
            self.runner._page.wait_for_timeout(3000)
            self.log_step("Navigate to Verizon", "N/A", 1.0, True)
            
            # Step 2: Click on Phones navigation
            print("📍 Step 2: Find and click 'Phones' navigation")
            shot = self.runner._snapshot()
            result = self.runner._resolve_selector("Phones", shot)
            
            if result['confidence'] > 0.5:
                self.runner._do_action("click", result["selector"], None, result.get("promo", {}))
                self.runner._page.wait_for_timeout(3000)
                self.log_step("Click Phones", result["selector"], result['confidence'], True)
                
                # Verify we're on phones page
                current_url = self.runner._page.url
                if "phones" in current_url.lower():
                    self.log_step("Verify phones page", "URL check", 1.0, True)
                else:
                    self.log_step("Verify phones page", "URL check", 0.0, False, f"Expected phones in URL, got: {current_url}")
            else:
                self.log_step("Click Phones", result["selector"], result['confidence'], False, f"Low confidence: {result['confidence']}")
                return False
            
            # Step 3: Apply Apple filter
            print("📍 Step 3: Find and click 'Apple' filter")
            shot = self.runner._snapshot()
            result = self.runner._resolve_selector("Apple", shot)
            
            if result['confidence'] > 0.5:
                self.runner._do_action("click", result["selector"], None, result.get("promo", {}))
                self.runner._page.wait_for_timeout(3000)
                self.log_step("Click Apple filter", result["selector"], result['confidence'], True)
            else:
                self.log_step("Click Apple filter", result["selector"], result['confidence'], False, f"Low confidence: {result['confidence']}")
                return False
            
            # Step 4: Select iPhone product
            print("📍 Step 4: Find and click 'iPhone' product")
            shot = self.runner._snapshot()
            result = self.runner._resolve_selector("iPhone", shot)
            
            if result['confidence'] > 0.5:
                self.runner._do_action("click", result["selector"], None, result.get("promo", {}))
                self.runner._page.wait_for_timeout(5000)
                self.log_step("Click iPhone", result["selector"], result['confidence'], True)
                
                # Verify we're on iPhone product page
                current_url = self.runner._page.url
                if "iphone" in current_url.lower():
                    self.log_step("Verify iPhone page", "URL check", 1.0, True)
                else:
                    self.log_step("Verify iPhone page", "URL check", 0.0, False, f"Expected iPhone in URL, got: {current_url}")
            else:
                self.log_step("Click iPhone", result["selector"], result['confidence'], False, f"Low confidence: {result['confidence']}")
                return False
            
            return True
            
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            self.log_step("Test Exception", "N/A", 0.0, False, str(e))
            return False
        finally:
            if self.runner:
                self.runner._close()
    
    def test_verizon_search_functionality(self):
        """Test search functionality on Verizon site."""
        print("\n🔍 Starting Verizon Search Functionality Test")
        print("=" * 60)
        
        try:
            # Initialize runner
            self.runner = Runner(headless=True)
            
            # Navigate to Verizon
            print("📍 Step 1: Navigate to Verizon homepage")
            self.runner._snapshot("https://www.verizon.com/")
            self.runner._page.wait_for_timeout(3000)
            self.log_step("Navigate to Verizon", "N/A", 1.0, True)
            
            # Find and use search box
            print("📍 Step 2: Find search box")
            shot = self.runner._snapshot()
            result = self.runner._resolve_selector("search", shot)
            
            if result['confidence'] > 0.3:
                self.log_step("Find search box", result["selector"], result['confidence'], True)
                
                # Type search query
                print("📍 Step 3: Type search query")
                self.runner._do_action("type", result["selector"], "iPhone 16", result.get("promo", {}))
                self.runner._page.wait_for_timeout(2000)
                self.log_step("Type search query", result["selector"], result['confidence'], True)
                
                # Submit search
                print("📍 Step 4: Submit search")
                self.runner._do_action("press", result["selector"], "Enter", result.get("promo", {}))
                self.runner._page.wait_for_timeout(5000)
                self.log_step("Submit search", result["selector"], result['confidence'], True)
                
                # Verify search results
                current_url = self.runner._page.url
                if "search" in current_url.lower() or "iphone" in current_url.lower():
                    self.log_step("Verify search results", "URL check", 1.0, True)
                else:
                    self.log_step("Verify search results", "URL check", 0.0, False, f"Expected search results, got: {current_url}")
            else:
                self.log_step("Find search box", result["selector"], result['confidence'], False, f"Low confidence: {result['confidence']}")
                return False
            
            return True
            
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            self.log_step("Test Exception", "N/A", 0.0, False, str(e))
            return False
        finally:
            if self.runner:
                self.runner._close()
    
    def test_verizon_element_detection_accuracy(self):
        """Test accuracy of element detection on Verizon pages."""
        print("\n🎯 Starting Verizon Element Detection Accuracy Test")
        print("=" * 60)
        
        try:
            # Initialize runner
            self.runner = Runner(headless=True)
            
            # Navigate to Verizon
            print("📍 Step 1: Navigate to Verizon homepage")
            self.runner._snapshot("https://www.verizon.com/")
            self.runner._page.wait_for_timeout(3000)
            self.log_step("Navigate to Verizon", "N/A", 1.0, True)
            
            # Test various element types
            test_queries = [
                "phones",
                "plans", 
                "shop",
                "login",
                "search",
                "menu"
            ]
            
            print("📍 Step 2: Test element detection for various queries")
            results = {}
            for query in test_queries:
                shot = self.runner._snapshot()
                result = self.runner._resolve_selector(query, shot)
                results[query] = {
                    'confidence': result['confidence'],
                    'selector': result['selector'],
                    'candidates_count': len(result.get('candidates', []))
                }
                self.log_step(f"Detect '{query}'", result["selector"], result['confidence'], result['confidence'] > 0.3)
            
            # Verify we found elements with reasonable confidence
            high_confidence_count = sum(1 for r in results.values() if r['confidence'] > 0.5)
            candidates_count = sum(1 for r in results.values() if r['candidates_count'] > 0)
            
            print(f"📊 Detection Summary:")
            print(f"   High confidence matches (>0.5): {high_confidence_count}/6")
            print(f"   Queries with candidates: {candidates_count}/6")
            
            if high_confidence_count >= 3 and candidates_count >= 4:
                self.log_step("Overall detection accuracy", "Summary", 1.0, True)
                return True
            else:
                self.log_step("Overall detection accuracy", "Summary", 0.0, False, f"Only {high_confidence_count} high-confidence matches")
                return False
            
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            self.log_step("Test Exception", "N/A", 0.0, False, str(e))
            return False
        finally:
            if self.runner:
                self.runner._close()
    
    def run_all_tests(self):
        """Run all Verizon tests and capture results."""
        print("🚀 Starting Verizon Test Suite with XPath Capture")
        print("=" * 80)
        
        if not PLAYWRIGHT_AVAILABLE:
            print("❌ Playwright not available. Cannot run tests.")
            return False
        
        test_results = []
        
        # Test 1: Phone Navigation Flow
        try:
            result1 = self.test_verizon_phone_navigation_flow()
            test_results.append(("Phone Navigation Flow", result1))
        except Exception as e:
            print(f"❌ Phone Navigation Flow failed: {e}")
            test_results.append(("Phone Navigation Flow", False))
        
        # Test 2: Search Functionality
        try:
            result2 = self.test_verizon_search_functionality()
            test_results.append(("Search Functionality", result2))
        except Exception as e:
            print(f"❌ Search Functionality failed: {e}")
            test_results.append(("Search Functionality", False))
        
        # Test 3: Element Detection Accuracy
        try:
            result3 = self.test_verizon_element_detection_accuracy()
            test_results.append(("Element Detection Accuracy", result3))
        except Exception as e:
            print(f"❌ Element Detection Accuracy failed: {e}")
            test_results.append(("Element Detection Accuracy", False))
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        
        passed = sum(1 for _, result in test_results if result)
        total = len(test_results)
        
        for test_name, result in test_results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {test_name}")
        
        print(f"\nOverall: {passed}/{total} tests passed")
        
        # XPath Summary
        print("\n" + "=" * 80)
        print("🔍 XPath SELECTORS CAPTURED")
        print("=" * 80)
        
        for result in self.results:
            if result['xpath'] != 'N/A':
                print(f"Step: {result['step']}")
                print(f"XPath: {result['xpath']}")
                print(f"Confidence: {result['confidence']:.3f}")
                print(f"Success: {result['success']}")
                print()
        
        return passed == total

if __name__ == "__main__":
    tester = VerizonTestWithXPath()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)