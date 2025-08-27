"""Tests for ranking modules."""
import pytest
from unittest.mock import Mock, patch
import json
from pathlib import Path
import tempfile

from her.rank.heuristics import heuristic_score, rank_by_heuristics, explain_heuristic_score
from her.rank.fusion import FusionConfig, RankFusion


class TestHeuristics:
    """Test heuristic ranking."""
    
    def test_heuristic_score_button(self):
        """Test heuristic scoring for button element."""
        descriptor = {
            "tag": "button",
            "text": "Submit Form",
            "role": "button",
            "id": "submit-btn"
        }
        
        # High score for button-related query
        score = heuristic_score(descriptor, "submit button", "click")
        assert score > 0.5
        
        # Lower score for unrelated query
        score = heuristic_score(descriptor, "email input", "type")
        assert score < 0.3
    
    def test_heuristic_score_input(self):
        """Test heuristic scoring for input element."""
        descriptor = {
            "tag": "input",
            "type": "email",
            "placeholder": "Enter your email",
            "name": "user-email"
        }
        
        # High score for input-related query
        score = heuristic_score(descriptor, "email field", "type")
        assert score > 0.4
        
        # Lower score for button query
        score = heuristic_score(descriptor, "submit button", "click")
        assert score < 0.3
    
    def test_heuristic_score_text_matching(self):
        """Test text matching in heuristic scoring."""
        descriptor = {
            "tag": "a",
            "text": "Click here to login",
            "href": "/login"
        }
        
        # Exact match
        score = heuristic_score(descriptor, "Click here to login")
        assert score > 0.5
        
        # Partial match
        score = heuristic_score(descriptor, "login")
        assert score > 0.2
        
        # No match
        score = heuristic_score(descriptor, "logout")
        assert score < 0.2
    
    def test_rank_by_heuristics(self):
        """Test ranking multiple elements."""
        descriptors = [
            {"tag": "button", "text": "Submit"},
            {"tag": "button", "text": "Cancel"},
            {"tag": "input", "placeholder": "Enter text"},
            {"tag": "div", "text": "Submit your form"}
        ]
        
        ranked = rank_by_heuristics(descriptors, "submit", "click", top_k=2)
        
        assert len(ranked) == 2
        assert ranked[0][0]["text"] == "Submit"  # Best match
        assert ranked[0][1] > ranked[1][1]  # Descending order
    
    def test_explain_heuristic_score(self):
        """Test score explanation."""
        descriptor = {
            "tag": "button",
            "text": "Login",
            "name": "login-btn"
        }
        
        explanation = explain_heuristic_score(descriptor, "login button", "click")
        
        assert "score" in explanation
        assert "reasons" in explanation
        assert len(explanation["reasons"]) > 0
        assert "matched_properties" in explanation


class TestFusion:
    """Test fusion ranking."""
    
    def test_fusion_config(self):
        """Test fusion configuration."""
        config = FusionConfig(alpha=0.5, beta=0.3, gamma=0.2)
        
        # Should normalize to sum to 1.0
        assert abs(config.alpha + config.beta + config.gamma - 1.0) < 0.01
    
    def test_rank_fusion_init(self):
        """Test fusion ranker initialization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fusion = RankFusion(promotion_store_path=Path(tmpdir) / "promotions.json")
            assert fusion.config.alpha > 0
            assert fusion.config.beta > 0
            assert fusion.config.gamma > 0
    
    def test_fuse_rankings(self):
        """Test fusing multiple ranking signals."""
        fusion = RankFusion()
        
        # Mock semantic scores
        semantic_scores = [
            ({"backendNodeId": 1, "tag": "button"}, 0.8),
            ({"backendNodeId": 2, "tag": "input"}, 0.6),
            ({"backendNodeId": 3, "tag": "div"}, 0.4)
        ]
        
        # Mock heuristic scores
        heuristic_scores = [
            ({"backendNodeId": 1, "tag": "button"}, 0.5),
            ({"backendNodeId": 2, "tag": "input"}, 0.9),
            ({"backendNodeId": 3, "tag": "div"}, 0.3)
        ]
        
        fused = fusion.fuse(semantic_scores, heuristic_scores, context="test", top_k=3)
        
        assert len(fused) == 3
        assert all(len(item) == 3 for item in fused)  # (descriptor, score, reasons)
        
        # Check reasons structure
        for desc, score, reasons in fused:
            assert "semantic_score" in reasons
            assert "heuristic_score" in reasons
            assert "promotion_score" in reasons
            assert "fused_score" in reasons
            assert "explanation" in reasons
    
    def test_promotion(self):
        """Test promotion functionality."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fusion = RankFusion(promotion_store_path=Path(tmpdir) / "promotions.json")
            
            descriptor = {"backendNodeId": 1, "tag": "button", "id": "test"}
            
            # Initial score should be 0
            initial_score = fusion.promotions.get(
                fusion._get_promotion_key(descriptor, "test_context"), 0
            )
            assert initial_score == 0
            
            # Promote element
            fusion.promote(descriptor, "test_context", boost=0.2)
            
            # Score should increase
            new_score = fusion.promotions.get(
                fusion._get_promotion_key(descriptor, "test_context"), 0
            )
            assert new_score == 0.2
            
            # Promote again
            fusion.promote(descriptor, "test_context", boost=0.3)
            final_score = fusion.promotions.get(
                fusion._get_promotion_key(descriptor, "test_context"), 0
            )
            assert final_score == 0.5
    
    def test_demote(self):
        """Test demotion functionality."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fusion = RankFusion(promotion_store_path=Path(tmpdir) / "promotions.json")
            
            descriptor = {"backendNodeId": 1, "tag": "button", "id": "test"}
            
            # Start with some promotion
            fusion.promote(descriptor, "test_context", boost=0.5)
            
            # Demote
            fusion.demote(descriptor, "test_context", penalty=0.2)
            
            score = fusion.promotions.get(
                fusion._get_promotion_key(descriptor, "test_context"), 0
            )
            assert score == 0.3
    
    def test_update_weights(self):
        """Test updating fusion weights."""
        fusion = RankFusion()
        
        fusion.update_weights(alpha=0.6, beta=0.3, gamma=0.1)
        
        assert fusion.config.alpha == 0.6
        assert fusion.config.beta == 0.3
        assert fusion.config.gamma == 0.1
        assert abs(fusion.config.alpha + fusion.config.beta + fusion.config.gamma - 1.0) < 0.01