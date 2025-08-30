"""Tests for recovery modules."""

import pytest
from unittest.mock import Mock, patch
# from pathlib import Path
import tempfile
import json
from datetime import datetime

from her.recovery.self_heal import SelfHealer, HealingStrategy
from her.recovery.promotion import PromotionStore, PromotionRecord


class TestSelfHealer:
    """Test self-healing functionality."""

    def test_init(self):
        """Test healer initialization."""
        healer = SelfHealer()
        assert len(healer.strategies) > 0
        assert len(healer.healing_history) == 0

    def test_healing_strategies(self):
        """Test individual healing strategies."""
        healer = SelfHealer()

        # Test relax exact match
        assert (
            healer._relax_exact_match("//button[text()='Submit']")
            == "//button[contains(text(),'Submit']"
        )
        assert healer._relax_exact_match("[@id='test']") == "[contains(@id, 'test')]"
        assert '[id*="test"]' in healer._relax_exact_match('[id="test"]')

        # Test remove index
        assert healer._remove_index("//button[1]") == "//button"
        assert healer._remove_index("//*[@id='test'][2]") == "//*[@id='test']"

        # Test ID to contains
        assert "contains(@id" in healer._id_to_contains("[@id='submit']")
        assert "[id*=" in healer._id_to_contains("#submit-btn")

        # Test class to contains
        assert "contains(@class" in healer._class_to_contains("[@class='btn primary']")

        # Test text to partial
        result = healer._text_to_partial("//button[text()='Click here to submit']")
        assert "contains(text()" in result or "Click" in result

        # Test remove attributes
        assert "data-" not in healer._remove_attributes("[data-testid='123']")
        assert "aria-" not in healer._remove_attributes("[aria-label='test']")

        # Test tag only
        assert healer._tag_only("//button[@id='test']") == "//button"
        assert healer._tag_only("div.class") == "div"

    @patch("her.recovery.self_heal.PLAYWRIGHT_AVAILABLE", True)
    def test_heal_with_page(self):
        """Test healing with page verification."""
        healer = SelfHealer()

        mock_page = Mock()
        mock_locator = Mock()
        mock_locator.count.return_value = 1
        mock_page.locator = Mock(return_value=mock_locator)

        healed = healer.heal("//button[@id='exact']", mock_page)

        assert len(healed) > 0
        assert all(isinstance(item, tuple) for item in healed)
        assert all(len(item) == 2 for item in healed)

    def test_heal_without_page(self):
        """Test healing without page verification."""
        healer = SelfHealer()

        healed = healer.heal("#submit-btn")

        assert len(healed) > 0
        # Should return transformed locators even without verification

    def test_add_custom_strategy(self):
        """Test adding custom healing strategy."""
        healer = SelfHealer()

        custom_strategy = HealingStrategy(
            name="custom",
            description="Custom strategy",
            transform_func=lambda x: x.upper(),
            priority=0,
        )

        healer.add_strategy(custom_strategy)
        assert custom_strategy in healer.strategies

    def test_healing_stats(self):
        """Test healing statistics."""
        healer = SelfHealer()

        # Perform some healing attempts
        healer.heal("#test1")
        healer.heal("#test2")

        stats = healer.get_healing_stats()

        assert stats["total_attempts"] == 2
        assert "successful_heals" in stats
        assert "success_rate" in stats
        assert "most_used_strategies" in stats


class TestPromotionStore:
    """Test promotion store functionality."""

    def test_init_sqlite(self):
        """Test SQLite store initialization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = PromotionStore(
                store_path=Path(tmpdir) / "promotions.db", use_sqlite=True
            )
            assert store.use_sqlite == True
            assert len(store.cache) == 0

    def test_init_json(self):
        """Test JSON store initialization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = PromotionStore(
                store_path=Path(tmpdir) / "promotions.json", use_sqlite=False
            )
            assert store.use_sqlite == False

    def test_promote(self):
        """Test promoting a locator."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = PromotionStore(store_path=Path(tmpdir) / "test.db")

            record = store.promote("#submit", "https://example.com", boost=0.2)

            assert record.locator == "#submit"
            assert record.context == "https://example.com"
            assert record.success_count == 1
            assert record.score == 0.2

            # Promote again
            record = store.promote("#submit", "https://example.com", boost=0.3)
            assert record.success_count == 2
            assert record.score == 0.5

    def test_demote(self):
        """Test demoting a locator."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = PromotionStore(store_path=Path(tmpdir) / "test.db")

            # Start with promotion
            store.promote("#submit", "test", boost=0.5)

            # Demote
            record = store.demote("#submit", "test", penalty=0.2)
            assert record.failure_count == 1
            assert record.score == 0.3

    def test_get_score(self):
        """Test getting promotion score."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = PromotionStore(store_path=Path(tmpdir) / "test.db")

            # No promotion yet
            assert store.get_score("#submit", "test") == 0.0

            # After promotion
            store.promote("#submit", "test", boost=0.4)
            assert store.get_score("#submit", "test") == 0.4

    def test_get_best_locators(self):
        """Test getting best promoted locators."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = PromotionStore(store_path=Path(tmpdir) / "test.db")

            store.promote("#submit", "example.com", boost=0.8)
            store.promote("#cancel", "example.com", boost=0.3)
            store.promote("#delete", "example.com", boost=0.5)

            best = store.get_best_locators("example.com", top_k=2)

            assert len(best) == 2
            assert best[0][0] == "#submit"
            assert best[0][1] == 0.8
            assert best[1][0] == "#delete"
            assert best[1][1] == 0.5

    def test_persistence_sqlite(self):
        """Test SQLite persistence."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"

            # Create and populate store
            store1 = PromotionStore(store_path=db_path, use_sqlite=True)
            store1.promote("#submit", "test", boost=0.7)

            # Load in new store instance
            store2 = PromotionStore(store_path=db_path, use_sqlite=True)
            assert store2.get_score("#submit", "test") == 0.7

    def test_persistence_json(self):
        """Test JSON persistence."""
        with tempfile.TemporaryDirectory() as tmpdir:
            json_path = Path(tmpdir) / "test.json"

            # Create and populate store
            store1 = PromotionStore(store_path=json_path, use_sqlite=False)
            store1.promote("#submit", "test", boost=0.6)

            # Load in new store instance
            store2 = PromotionStore(store_path=json_path, use_sqlite=False)
            assert store2.get_score("#submit", "test") == 0.6

    def test_clear(self):
        """Test clearing promotions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = PromotionStore(store_path=Path(tmpdir) / "test.db")

            store.promote("#submit", "example.com", boost=0.5)
            store.promote("#cancel", "other.com", boost=0.3)

            # Clear specific context
            count = store.clear("example.com")
            assert count == 1
            assert store.get_score("#submit", "example.com") == 0.0
            assert store.get_score("#cancel", "other.com") == 0.3

            # Clear all
            count = store.clear()
            assert count == 1
            assert len(store.cache) == 0

    def test_get_stats(self):
        """Test getting statistics."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = PromotionStore(store_path=Path(tmpdir) / "test.db")

            # Empty stats
            stats = store.get_stats()
            assert stats["total_records"] == 0

            # Add some data
            store.promote("#submit", "test", boost=0.8)
            store.promote("#cancel", "test", boost=0.4)
            store.demote("#cancel", "test", penalty=0.1)

            stats = store.get_stats()
            assert stats["total_records"] == 2
            assert stats["total_successes"] == 2
            assert stats["total_failures"] == 1
            assert "avg_score" in stats
            assert "success_rate" in stats
            assert "top_performers" in stats
