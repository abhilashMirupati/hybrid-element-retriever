"""Tests for the main CLI API."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json
import numpy as np

from her.cli_api import HybridElementRetrieverClient as HybridClient, QueryResult


class TestHybridClient:
    """Test the main HybridClient API."""

    @patch("her.cli_api.ActionExecutor")
    def test_init(self, mock_executor):
        """Test client initialization."""
        client = HybridClient(auto_index=True, headless=True)

        assert client.auto_index == True
        assert client.headless == True
        assert client.timeout_ms == 30000
        assert client.promotion_enabled == True
        assert client.current_session_id == "default"

    @patch("her.cli_api.ActionExecutor")
    def test_act_basic(self, mock_executor):
        """Test basic action execution."""
        # Setup mocks
        mock_page = Mock()
        mock_page.url = "https://example.com"
        mock_executor.return_value.page = mock_page

        client = HybridClient()

        # Mock components
        client.parser.parse = Mock(
            return_value=Mock(
                action="click", target_phrase="submit button", args=None, confidence=0.9
            )
        )

        client.session_manager.index_page = Mock(
            return_value=(
                [{"backendNodeId": 1, "tag": "button", "text": "Submit"}],
                "test_hash",
            )
        )

        client._find_candidates = Mock(
            return_value=[
                (
                    {"backendNodeId": 1, "tag": "button"},
                    0.8,
                    {"explanation": "Good match"},
                )
            ]
        )

        client.synthesizer.synthesize = Mock(return_value=["#submit"])
        client.verifier.find_unique_locator = Mock(return_value="#submit")

        client._execute_with_recovery = Mock(
            return_value=Mock(
                success=True,
                locator="#submit",
                overlay_events=["Cookie banner"],
                retries=1,
                verification={"method": "standard"},
            )
        )

        # Execute action
        result = client.act("Click the submit button", url="https://example.com")

        # Verify result structure
        assert result["status"] == "success"
        assert result["method"] == "click"
        assert result["confidence"] == 0.9
        assert result["dom_hash"] == "test_hash"
        assert result["used_locator"] == "#submit"
        assert "Cookie banner" in result["overlay_events"]
        assert result["retries"]["attempts"] == 1

    @patch("her.cli_api.ActionExecutor")
    def test_act_no_locator_found(self, mock_executor):
        """Test action when no locator is found."""
        mock_executor.return_value.page = Mock()

        client = HybridClient()

        client.parser.parse = Mock(
            return_value=Mock(
                action="click", target_phrase="nonexistent", args=None, confidence=0.5
            )
        )

        client.session_manager.index_page = Mock(return_value=([], ""))
        client._find_candidates = Mock(return_value=[])

        result = client.act("Click nonexistent element")

        assert result["status"] == "failure"
        assert result["used_locator"] is None
        assert "No valid locator found" in result["explanation"]

    @patch("her.cli_api.ActionExecutor")
    def test_query(self, mock_executor):
        """Test element querying."""
        mock_page = Mock()
        mock_page.url = "https://example.com"
        mock_executor.return_value.page = mock_page

        client = HybridClient()

        client.session_manager.index_page = Mock(
            return_value=(
                [
                    {"backendNodeId": 1, "tag": "button", "text": "Submit"},
                    {"backendNodeId": 2, "tag": "button", "text": "Cancel"},
                ],
                "test_hash",
            )
        )

        client._find_candidates = Mock(
            return_value=[
                (
                    {"backendNodeId": 1, "tag": "button", "text": "Submit"},
                    0.9,
                    {"explanation": "Best match"},
                ),
                (
                    {"backendNodeId": 2, "tag": "button", "text": "Cancel"},
                    0.3,
                    {"explanation": "Partial match"},
                ),
            ]
        )

        client.synthesizer.synthesize = Mock(
            side_effect=[["#submit-btn"], ["#cancel-btn"]]
        )

        client.verifier.find_unique_locator = Mock(
            side_effect=["#submit-btn", "#cancel-btn"]
        )

        results = client.query("button", url="https://example.com")

        assert len(results) == 2
        assert results[0]["selector"] == "#submit-btn"
        assert results[0]["score"] == 0.9
        assert results[0]["element"]["text"] == "Submit"
        assert results[1]["selector"] == "#cancel-btn"

    @patch("her.cli_api.ActionExecutor")
    def test_find_candidates(self, mock_executor):
        """Test finding element candidates."""
        mock_executor.return_value.page = None

        client = HybridClient()

        # Mock session with vector store
        mock_session = Mock()
        mock_session.vector_store.search = Mock(
            return_value=[({"backendNodeId": 1, "tag": "button"}, 0.8)]
        )
        client.session_manager.get_session = Mock(return_value=mock_session)

        # Mock embedder
        client.query_embedder.embed = Mock(return_value=np.array([1, 0, 0]))

        # Mock heuristic ranking
        with patch("her.cli_api.rank_by_heuristics") as mock_heuristics:
            mock_heuristics.return_value = [
                ({"backendNodeId": 1, "tag": "button"}, 0.6)
            ]

            # Mock fusion
            client.rank_fusion.fuse = Mock(
                return_value=[({"backendNodeId": 1}, 0.7, {"explanation": "Fused"})]
            )

            descriptors = [{"backendNodeId": 1, "tag": "button"}]
            candidates = client._find_candidates("button", descriptors)

            assert len(candidates) == 1
            assert candidates[0][1] == 0.7

    @patch("her.cli_api.ActionExecutor")
    def test_execute_with_recovery_success(self, mock_executor):
        """Test successful action execution."""
        mock_executor.return_value.click = Mock(
            return_value=Mock(
                success=True,
                locator="#submit",
                overlay_events=[],
                retries=0,
                verification={},
            )
        )

        client = HybridClient()

        result = client._execute_with_recovery("click", "#submit", None, [])

        assert result.success == True
        assert result.locator == "#submit"

    @patch("her.cli_api.ActionExecutor")
    def test_execute_with_recovery_self_heal(self, mock_executor):
        """Test self-healing on failure."""
        # First attempt fails
        mock_executor.return_value.click = Mock(
            side_effect=[
                Mock(success=False, locator="#submit", error="Not found"),
                Mock(success=True, locator="#submit-btn", verification={}),
            ]
        )
        mock_executor.return_value.page = Mock()

        client = HybridClient()

        # Mock healer
        client.healer.heal = Mock(return_value=[("#submit-btn", "relax_exact_match")])

        result = client._execute_with_recovery("click", "#submit", None, [])

        assert result.success == True
        assert result.locator == "#submit-btn"
        assert result.verification.get("healing_strategy") == "relax_exact_match"

    @patch("her.cli_api.ActionExecutor")
    def test_execute_with_recovery_alternative_candidate(self, mock_executor):
        """Test fallback to alternative candidates."""
        # All attempts with primary locator fail
        mock_executor.return_value.click = Mock(
            side_effect=[
                Mock(success=False, locator="#submit", error="Not found"),
                Mock(success=False, locator="#submit2", error="Not found"),
                Mock(success=True, locator="#alt-submit", verification={}),
            ]
        )
        mock_executor.return_value.page = Mock()

        client = HybridClient()

        # Mock healer returns nothing
        client.healer.heal = Mock(return_value=[])

        # Mock synthesizer for alternative candidates
        client.synthesizer.synthesize = Mock(return_value=["#alt-submit"])

        candidates = [({"backendNodeId": 1}, 0.8, {}), ({"backendNodeId": 2}, 0.6, {})]

        result = client._execute_with_recovery("click", "#submit", None, candidates)

        assert result.success == True
        assert result.locator == "#alt-submit"
        assert result.verification.get("recovery_method") == "alternative_candidate"

    @patch("her.cli_api.ActionExecutor")
    def test_close(self, mock_executor):
        """Test client cleanup."""
        mock_exec_instance = Mock()
        mock_executor.return_value = mock_exec_instance

        client = HybridClient()
        client.close()

        mock_exec_instance.close.assert_called_once()
