"""Unit tests for NLP scoring with mock DOMs."""

import unittest
from typing import List, Dict, Any

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from her.pipeline import HERPipeline as ProductionPipeline
from her.scoring.fusion_scorer_v2 import FusionScorerV2


class TestNLPScoring(unittest.TestCase):
    """Test NLP scoring accuracy."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.pipeline = ProductionPipeline()
        self.scorer = FusionScorerV2()
    
    def test_product_disambiguation(self):
        """Test: Products - phone vs laptop vs tablet."""
        descriptors = [
            {
                "tag": "button",
                "text": "Add to Cart",
                "dataTestId": "add-laptop-to-cart",
                "id": "laptop-btn",
                "attributes": {"data-product": "laptop"}
            },
            {
                "tag": "button",
                "text": "Add to Cart",
                "dataTestId": "add-phone-to-cart",
                "id": "phone-btn",
                "attributes": {"data-product": "phone"}
            },
            {
                "tag": "button",
                "text": "Add to Cart",
                "dataTestId": "add-tablet-to-cart",
                "id": "tablet-btn",
                "attributes": {"data-product": "tablet"}
            }
        ]
        
        # Test 1: "add phone to cart" should select phone
        result = self.pipeline.process("add phone to cart", descriptors)
        self.assertIn("phone", result.element.get("dataTestId", "").lower())
        self.assertGreater(result.confidence, 0.7)
        
        # Test 2: "add laptop to cart" should select laptop
        result = self.pipeline.process("add laptop to cart", descriptors)
        self.assertIn("laptop", result.element.get("dataTestId", "").lower())
        self.assertGreater(result.confidence, 0.7)
        
        # Test 3: "add tablet to cart" should select tablet
        result = self.pipeline.process("add tablet to cart", descriptors)
        self.assertIn("tablet", result.element.get("dataTestId", "").lower())
        self.assertGreater(result.confidence, 0.7)
    
    def test_form_field_disambiguation(self):
        """Test: Forms - email vs password vs username."""
        descriptors = [
            {
                "tag": "input",
                "type": "email",
                "name": "email",
                "placeholder": "Enter your email",
                "dataTestId": "email-input"
            },
            {
                "tag": "input",
                "type": "password",
                "name": "password",
                "placeholder": "Enter your password",
                "dataTestId": "password-input"
            },
            {
                "tag": "input",
                "type": "text",
                "name": "username",
                "placeholder": "Enter your username",
                "dataTestId": "username-input"
            }
        ]
        
        # Test 1: "enter email" should select email input
        result = self.pipeline.process("enter email", descriptors)
        self.assertEqual(result.element.get("type"), "email")
        self.assertIn("email", result.element.get("dataTestId", "").lower())
        self.assertGreater(result.confidence, 0.8)
        
        # Test 2: "type password" should select password input
        result = self.pipeline.process("type password", descriptors)
        self.assertEqual(result.element.get("type"), "password")
        self.assertIn("password", result.element.get("dataTestId", "").lower())
        self.assertGreater(result.confidence, 0.8)
        
        # Test 3: "enter username" should select username input
        result = self.pipeline.process("enter username", descriptors)
        self.assertEqual(result.element.get("type"), "text")
        self.assertIn("username", result.element.get("dataTestId", "").lower())
        self.assertGreater(result.confidence, 0.7)
    
    def test_action_disambiguation(self):
        """Test: Actions - add-to-cart, search, submit."""
        descriptors = [
            {
                "tag": "button",
                "text": "Add to Cart",
                "dataTestId": "add-to-cart-btn",
                "classes": ["btn", "btn-primary"]
            },
            {
                "tag": "input",
                "type": "search",
                "placeholder": "Search products...",
                "dataTestId": "search-input"
            },
            {
                "tag": "button",
                "text": "Submit",
                "dataTestId": "submit-form-btn",
                "type": "submit"
            }
        ]
        
        # Test 1: "add to cart" should select add to cart button
        result = self.pipeline.process("add to cart", descriptors)
        self.assertEqual(result.element.get("text"), "Add to Cart")
        self.assertGreater(result.confidence, 0.8)
        
        # Test 2: "search for products" should select search input
        result = self.pipeline.process("search for products", descriptors)
        self.assertEqual(result.element.get("type"), "search")
        self.assertGreater(result.confidence, 0.7)
        
        # Test 3: "submit the form" should select submit button
        result = self.pipeline.process("submit the form", descriptors)
        self.assertEqual(result.element.get("text"), "Submit")
        self.assertGreater(result.confidence, 0.7)
    
    def test_scoring_signals(self):
        """Test that scoring signals are computed correctly."""
        element = {
            "tag": "button",
            "text": "Sign In",
            "dataTestId": "login-button",
            "id": "signin-btn"
        }
        
        score, signals = self.scorer.score(
            query="click sign in button",
            element=element,
            intent={"action": "click", "target": "sign in button"}
        )
        
        # Check individual signals
        self.assertGreater(signals.text_similarity, 0.5)
        self.assertGreater(signals.attribute_match, 0.0)
        self.assertGreater(signals.structural_relevance, 0.8)
        self.assertEqual(signals.penalty, 0.0)  # No penalty for correct match
        
        # Check final score
        self.assertGreater(score, 1.0)  # Should be high for good match
    
    def test_penalty_application(self):
        """Test that penalties are applied correctly."""
        # Wrong product should get penalty
        laptop_element = {
            "tag": "button",
            "text": "Add to Cart",
            "dataTestId": "add-laptop-to-cart"
        }
        
        score, signals = self.scorer.score(
            query="add phone to cart",  # Asking for phone
            element=laptop_element,     # But element is laptop
            intent={"action": "add", "target": "phone to cart"}
        )
        
        # Should have penalty for wrong product
        self.assertGreater(signals.penalty, 0.3)
        self.assertLess(score, 2.0)  # Score should be lower due to penalty
    
    def test_no_double_counting(self):
        """Test that text matches aren't double counted."""
        element = {
            "tag": "button",
            "text": "Submit Form"
        }
        
        score1, signals1 = self.scorer.score(
            query="submit form",
            element=element,
            intent={"action": "submit"}
        )
        
        # Text similarity should be high
        self.assertGreater(signals1.text_similarity, 0.8)
        
        # Keyword/phrase match should be low (avoided double counting)
        self.assertLess(signals1.keyword_match, 0.2)
        
        # Total score should be reasonable, not inflated
        self.assertLess(score1, 5.0)
    
    def test_edge_cases(self):
        """Test edge cases."""
        # Empty query
        result = self.pipeline.process("", [{"tag": "button", "text": "Click"}])
        self.assertEqual(result.confidence, 0.0)
        
        # Unicode in query
        result = self.pipeline.process(
            "click 提交",  # Chinese for "submit"
            [{"tag": "button", "text": "提交"}]
        )
        self.assertGreater(result.confidence, 0.5)
        
        # Duplicate labels
        descriptors = [
            {"tag": "button", "text": "Submit", "id": "form1-submit"},
            {"tag": "button", "text": "Submit", "id": "form2-submit"}
        ]
        
        result = self.pipeline.process("click form2 submit", descriptors)
        self.assertIn("form2", result.element.get("id", ""))


if __name__ == "__main__":
    unittest.main()