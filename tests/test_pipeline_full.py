"""Integration tests for full pipeline with sample HTML."""

import unittest
import time
from typing import List, Dict, Any

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from her.pipeline_production import ProductionPipeline


class TestPipelineIntegration(unittest.TestCase):
    """Test full pipeline integration."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.pipeline = ProductionPipeline()
    
    def get_ecommerce_dom(self) -> List[Dict[str, Any]]:
        """Get sample e-commerce DOM."""
        return [
            # Header
            {"tag": "a", "text": "Home", "href": "/", "dataTestId": "nav-home"},
            {"tag": "a", "text": "Products", "href": "/products", "dataTestId": "nav-products"},
            {"tag": "input", "type": "search", "placeholder": "Search...", "dataTestId": "search-bar"},
            {"tag": "button", "text": "", "ariaLabel": "Search", "dataTestId": "search-btn"},
            
            # Product cards
            {"tag": "h2", "text": "Laptop Pro", "dataTestId": "product-title-laptop"},
            {"tag": "button", "text": "Add to Cart", "dataTestId": "add-laptop-to-cart"},
            {"tag": "button", "text": "Buy Now", "dataTestId": "buy-laptop-now"},
            
            {"tag": "h2", "text": "Phone X", "dataTestId": "product-title-phone"},
            {"tag": "button", "text": "Add to Cart", "dataTestId": "add-phone-to-cart"},
            {"tag": "button", "text": "Buy Now", "dataTestId": "buy-phone-now"},
            
            {"tag": "h2", "text": "Tablet Plus", "dataTestId": "product-title-tablet"},
            {"tag": "button", "text": "Add to Cart", "dataTestId": "add-tablet-to-cart"},
            {"tag": "button", "text": "Buy Now", "dataTestId": "buy-tablet-now"},
            
            # Cart
            {"tag": "button", "text": "View Cart (3)", "dataTestId": "view-cart", "ariaLabel": "View shopping cart"},
            {"tag": "button", "text": "Checkout", "dataTestId": "checkout-btn"},
        ]
    
    def get_form_dom(self) -> List[Dict[str, Any]]:
        """Get sample form DOM."""
        return [
            {"tag": "h1", "text": "Create Account"},
            {"tag": "label", "text": "Email Address"},
            {"tag": "input", "type": "email", "name": "email", "placeholder": "you@example.com", "dataTestId": "email-field"},
            
            {"tag": "label", "text": "Username"},
            {"tag": "input", "type": "text", "name": "username", "placeholder": "Choose a username", "dataTestId": "username-field"},
            
            {"tag": "label", "text": "Password"},
            {"tag": "input", "type": "password", "name": "password", "placeholder": "Min 8 characters", "dataTestId": "password-field"},
            
            {"tag": "label", "text": "Confirm Password"},
            {"tag": "input", "type": "password", "name": "confirm", "placeholder": "Re-enter password", "dataTestId": "confirm-password"},
            
            {"tag": "input", "type": "checkbox", "id": "terms", "dataTestId": "terms-checkbox"},
            {"tag": "label", "text": "I agree to the terms", "for": "terms"},
            
            {"tag": "button", "text": "Create Account", "type": "submit", "dataTestId": "submit-btn"},
            {"tag": "button", "text": "Cancel", "dataTestId": "cancel-btn"},
            
            {"tag": "a", "text": "Already have an account? Sign in", "href": "/login", "dataTestId": "signin-link"}
        ]
    
    def test_ecommerce_queries(self):
        """Test e-commerce related queries."""
        dom = self.get_ecommerce_dom()
        
        test_cases = [
            ("search for products", "search-bar"),
            ("add laptop to cart", "add-laptop-to-cart"),
            ("buy phone now", "buy-phone-now"),
            ("add tablet to shopping cart", "add-tablet-to-cart"),
            ("view my cart", "view-cart"),
            ("proceed to checkout", "checkout-btn"),
            ("go to products page", "nav-products")
        ]
        
        for query, expected_testid in test_cases:
            with self.subTest(query=query):
                result = self.pipeline.process(query, dom)
                
                # Check if correct element was selected
                actual_testid = result.element.get("dataTestId", "")
                self.assertEqual(
                    actual_testid, expected_testid,
                    f"Query '{query}' selected '{actual_testid}' instead of '{expected_testid}'"
                )
                
                # Check confidence
                self.assertGreater(
                    result.confidence, 0.5,
                    f"Low confidence {result.confidence} for query '{query}'"
                )
                
                # Check XPath generation
                self.assertTrue(
                    result.xpath,
                    f"No XPath generated for query '{query}'"
                )
    
    def test_form_queries(self):
        """Test form-related queries."""
        dom = self.get_form_dom()
        
        test_cases = [
            ("enter my email address", "email-field"),
            ("type username", "username-field"),
            ("enter password", "password-field"),
            ("confirm my password", "confirm-password"),
            ("agree to terms", "terms-checkbox"),
            ("create my account", "submit-btn"),
            ("cancel registration", "cancel-btn"),
            ("sign in instead", "signin-link")
        ]
        
        for query, expected_testid in test_cases:
            with self.subTest(query=query):
                result = self.pipeline.process(query, dom)
                
                actual_testid = result.element.get("dataTestId", "")
                self.assertEqual(
                    actual_testid, expected_testid,
                    f"Query '{query}' selected '{actual_testid}' instead of '{expected_testid}'"
                )
                
                self.assertGreater(result.confidence, 0.5)
                self.assertTrue(result.xpath)
    
    def test_ambiguous_queries(self):
        """Test handling of ambiguous queries."""
        dom = self.get_ecommerce_dom()
        
        # "buy now" is ambiguous - multiple products have it
        result = self.pipeline.process("buy laptop", dom)
        self.assertIn("laptop", result.element.get("dataTestId", "").lower())
        
        result = self.pipeline.process("buy phone", dom)
        self.assertIn("phone", result.element.get("dataTestId", "").lower())
        
        # Generic "add to cart" should still work
        result = self.pipeline.process("add to cart", dom)
        self.assertIn("add", result.element.get("dataTestId", "").lower())
        self.assertIn("cart", result.element.get("dataTestId", "").lower())
    
    def test_caching(self):
        """Test that caching works correctly."""
        dom = self.get_form_dom()
        query = "enter email"
        
        # First call - should not be cached
        result1 = self.pipeline.process(query, dom)
        self.assertFalse(result1.cache_hit)
        time1 = result1.processing_time_ms
        
        # Second call - should be cached
        result2 = self.pipeline.process(query, dom)
        self.assertTrue(result2.cache_hit)
        time2 = result2.processing_time_ms
        
        # Cached call should be faster
        self.assertLess(time2, time1 * 0.5)
        
        # Results should be identical
        self.assertEqual(result1.xpath, result2.xpath)
        self.assertEqual(result1.element, result2.element)
    
    def test_incremental_updates(self):
        """Test incremental embedding updates."""
        # Initial DOM
        dom1 = [
            {"tag": "button", "text": "Button 1", "id": "btn1"},
            {"tag": "button", "text": "Button 2", "id": "btn2"}
        ]
        
        # Process first query (cold start)
        result1 = self.pipeline.process("click button 1", dom1)
        self.assertEqual(result1.element.get("id"), "btn1")
        
        # Modified DOM (added element)
        dom2 = dom1 + [{"tag": "button", "text": "Button 3", "id": "btn3"}]
        
        # Process with modified DOM (incremental update)
        result2 = self.pipeline.process("click button 3", dom2)
        self.assertEqual(result2.element.get("id"), "btn3")
        
        # Check that cached embeddings were reused for unchanged elements
        # (This would be verified by checking logs in production)
    
    def test_performance(self):
        """Test performance benchmarks."""
        dom = self.get_ecommerce_dom() + self.get_form_dom()
        
        # Warm up
        self.pipeline.process("test query", dom)
        
        # Measure average time
        times = []
        queries = [
            "add phone to cart",
            "enter email",
            "search products",
            "create account",
            "view cart"
        ]
        
        for query in queries:
            result = self.pipeline.process(query, dom)
            times.append(result.processing_time_ms)
        
        avg_time = sum(times) / len(times)
        
        # Should process most queries under 100ms
        self.assertLess(avg_time, 100)
        
        # No query should take more than 500ms
        self.assertLess(max(times), 500)
    
    def test_xpath_quality(self):
        """Test that generated XPaths are high quality."""
        dom = self.get_form_dom()
        
        result = self.pipeline.process("enter email", dom)
        
        # Should prioritize data-testid
        self.assertIn("data-testid", result.xpath.lower())
        
        # Should have fallbacks
        self.assertGreater(len(result.fallbacks), 0)
        
        # Fallbacks should be different strategies
        strategies = set()
        for xpath in [result.xpath] + result.fallbacks:
            if "data-testid" in xpath.lower():
                strategies.add("testid")
            elif xpath.startswith("#"):
                strategies.add("id")
            elif xpath.startswith("."):
                strategies.add("class")
            elif "//" in xpath:
                strategies.add("xpath")
        
        self.assertGreater(len(strategies), 1, "Should have multiple strategies")


if __name__ == "__main__":
    unittest.main()