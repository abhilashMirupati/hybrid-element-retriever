"""Test NLP scoring for product disambiguation and form fields."""

import pytest
from her.pipeline import HERPipeline, PipelineConfig
from her.rank.fusion import FusionScorer


class TestNLPScoring:
    """Test NLP scoring accuracy and disambiguation."""
    
    @pytest.fixture
    def scorer(self):
        """Create a fusion scorer instance."""
        return FusionScorer()
    
    @pytest.fixture
    def pipeline(self):
        """Create pipeline with optimized scoring."""
        config = PipelineConfig(
            use_minilm=True,
            use_markuplm=True,
            enable_optimized_scoring=True
        )
        return HERPipeline(config=config)
    
    def test_product_disambiguation_phone_vs_laptop(self, scorer):
        """Test disambiguation between phone and laptop products."""
        elements = [
            {
                "text": "iPhone 14 Pro",
                "tag": "div",
                "attributes": {"class": "product-title"},
                "xpath": "//div[@class='product-title'][1]"
            },
            {
                "text": "MacBook Pro 16-inch",
                "tag": "div", 
                "attributes": {"class": "product-title"},
                "xpath": "//div[@class='product-title'][2]"
            },
            {
                "text": "Samsung Galaxy S23",
                "tag": "div",
                "attributes": {"class": "product-title"},
                "xpath": "//div[@class='product-title'][3]"
            }
        ]
        
        # Test phone query
        phone_scores = scorer.score_elements("select phone", elements)
        phone_winner = max(phone_scores, key=lambda x: x["score"])
        assert "iPhone" in phone_winner["element"]["text"] or "Galaxy" in phone_winner["element"]["text"]
        
        # Test laptop query
        laptop_scores = scorer.score_elements("choose laptop", elements)
        laptop_winner = max(laptop_scores, key=lambda x: x["score"])
        assert "MacBook" in laptop_winner["element"]["text"]
    
    def test_product_disambiguation_tablet(self, scorer):
        """Test tablet product disambiguation."""
        elements = [
            {"text": "iPad Pro 12.9", "tag": "div", "xpath": "//div[1]"},
            {"text": "Surface Pro 9", "tag": "div", "xpath": "//div[2]"},
            {"text": "Galaxy Tab S9", "tag": "div", "xpath": "//div[3]"},
            {"text": "iPhone 14", "tag": "div", "xpath": "//div[4]"}
        ]
        
        scores = scorer.score_elements("buy tablet", elements)
        top_matches = sorted(scores, key=lambda x: x["score"], reverse=True)[:3]
        
        # Top 3 should be tablets, not phone
        tablet_keywords = ["iPad", "Surface", "Tab"]
        for match in top_matches:
            assert any(kw in match["element"]["text"] for kw in tablet_keywords)
    
    def test_form_field_disambiguation(self, scorer):
        """Test form field disambiguation (email/password/username)."""
        form_elements = [
            {
                "tag": "input",
                "attributes": {"type": "email", "name": "email", "id": "email-field"},
                "xpath": "//input[@id='email-field']"
            },
            {
                "tag": "input",
                "attributes": {"type": "password", "name": "password", "id": "pwd"},
                "xpath": "//input[@id='pwd']"
            },
            {
                "tag": "input",
                "attributes": {"type": "text", "name": "username", "placeholder": "Username"},
                "xpath": "//input[@name='username']"
            }
        ]
        
        # Test email field
        email_scores = scorer.score_elements("enter email address", form_elements)
        email_winner = max(email_scores, key=lambda x: x["score"])
        assert email_winner["element"]["attributes"]["type"] == "email"
        
        # Test password field
        pwd_scores = scorer.score_elements("type password", form_elements)
        pwd_winner = max(pwd_scores, key=lambda x: x["score"])
        assert pwd_winner["element"]["attributes"]["type"] == "password"
        
        # Test username field
        user_scores = scorer.score_elements("input username", form_elements)
        user_winner = max(user_scores, key=lambda x: x["score"])
        assert user_winner["element"]["attributes"]["name"] == "username"
    
    def test_action_verb_scoring(self, scorer):
        """Test action verb recognition and scoring."""
        buttons = [
            {"text": "Add to Cart", "tag": "button", "xpath": "//button[1]"},
            {"text": "Submit Order", "tag": "button", "xpath": "//button[2]"},
            {"text": "Search Products", "tag": "button", "xpath": "//button[3]"},
            {"text": "Cancel", "tag": "button", "xpath": "//button[4]"}
        ]
        
        # Test "add to cart" verb
        add_scores = scorer.score_elements("add item to cart", buttons)
        add_winner = max(add_scores, key=lambda x: x["score"])
        assert "Add to Cart" in add_winner["element"]["text"]
        
        # Test "submit" verb
        submit_scores = scorer.score_elements("submit the form", buttons)
        submit_winner = max(submit_scores, key=lambda x: x["score"])
        assert "Submit" in submit_winner["element"]["text"]
        
        # Test "search" verb
        search_scores = scorer.score_elements("search for items", buttons)
        search_winner = max(search_scores, key=lambda x: x["score"])
        assert "Search" in search_winner["element"]["text"]
    
    def test_no_double_counting(self, scorer):
        """Test that scoring doesn't double-count features."""
        element = {
            "text": "Submit Submit",  # Repeated word
            "tag": "button",
            "attributes": {"value": "Submit", "title": "Submit form"},
            "xpath": "//button"
        }
        
        scores = scorer.score_elements("click submit", [element])
        score = scores[0]["score"]
        
        # Score should not be artificially inflated by repetition
        # Should be reasonable, not > 1.0 or multiple times higher
        assert 0 <= score <= 1.0
        
        # Compare with single occurrence
        single_element = {
            "text": "Submit",
            "tag": "button",
            "xpath": "//button[2]"
        }
        
        single_scores = scorer.score_elements("click submit", [single_element])
        single_score = single_scores[0]["score"]
        
        # Repeated text shouldn't give significantly higher score
        assert score <= single_score * 1.5  # Allow small variance
    
    def test_penalty_application(self, scorer):
        """Test that penalties are correctly applied."""
        elements = [
            {
                "text": "Login",
                "tag": "button",
                "attributes": {"disabled": "true"},
                "is_visible": False,
                "xpath": "//button[@disabled]"
            },
            {
                "text": "Login",
                "tag": "button",
                "attributes": {},
                "is_visible": True,
                "xpath": "//button[not(@disabled)]"
            }
        ]
        
        scores = scorer.score_elements("click login", elements)
        
        # Visible, enabled button should score higher
        disabled_score = next(s["score"] for s in scores if "disabled" in s["element"]["xpath"])
        enabled_score = next(s["score"] for s in scores if "not(@disabled)" in s["element"]["xpath"])
        
        assert enabled_score > disabled_score
    
    def test_accuracy_on_test_set(self, pipeline):
        """Test overall accuracy on a test set."""
        test_cases = [
            # (query, elements, expected_index)
            ("click phone", [
                {"text": "iPhone 14", "tag": "div"},
                {"text": "MacBook Pro", "tag": "div"},
                {"text": "iPad Mini", "tag": "div"}
            ], 0),
            
            ("select laptop", [
                {"text": "iPhone 14", "tag": "div"},
                {"text": "MacBook Pro", "tag": "div"},
                {"text": "iPad Mini", "tag": "div"}
            ], 1),
            
            ("enter email", [
                {"tag": "input", "attributes": {"type": "email"}},
                {"tag": "input", "attributes": {"type": "password"}},
                {"tag": "input", "attributes": {"type": "text"}}
            ], 0),
            
            ("type password", [
                {"tag": "input", "attributes": {"type": "email"}},
                {"tag": "input", "attributes": {"type": "password"}},
                {"tag": "input", "attributes": {"type": "text"}}
            ], 1),
            
            ("add to cart", [
                {"text": "Add to Cart", "tag": "button"},
                {"text": "Remove from Cart", "tag": "button"},
                {"text": "View Cart", "tag": "button"}
            ], 0),
        ]
        
        correct = 0
        total = len(test_cases)
        results = []
        
        for query, elements, expected_idx in test_cases:
            # Add xpaths
            for i, elem in enumerate(elements):
                elem["xpath"] = f"//element[{i+1}]"
            
            scores = pipeline.scorer.score_elements(query, elements)
            winner_idx = max(range(len(scores)), key=lambda i: scores[i]["score"])
            
            is_correct = winner_idx == expected_idx
            if is_correct:
                correct += 1
            
            results.append({
                "query": query,
                "expected": expected_idx,
                "predicted": winner_idx,
                "correct": is_correct
            })
        
        accuracy = correct / total
        
        # Print results
        print(f"\nNLP Scoring Accuracy: {accuracy:.1%}")
        print("\nPer-case results:")
        for r in results:
            status = "✅" if r["correct"] else "❌"
            print(f"  {status} '{r['query']}': expected={r['expected']}, got={r['predicted']}")
        
        # Require >95% accuracy
        assert accuracy >= 0.95, f"Accuracy {accuracy:.1%} is below 95% threshold"