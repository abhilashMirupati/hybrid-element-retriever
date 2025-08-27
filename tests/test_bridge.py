"""Tests for bridge modules."""
import pytest
from unittest.mock import Mock, patch, MagicMock
import json

from her.bridge.cdp_bridge import (
    get_flattened_document,
    get_full_ax_tree,
    get_frame_tree,
    execute_cdp_command,
    get_document_with_styles
)
from her.bridge.snapshot import (
    compute_dom_hash,
    index_by_backend_id,
    merge_dom_and_ax,
    capture_snapshot,
    detect_dom_change
)


class TestCDPBridge:
    """Test CDP bridge functions."""
    
    def test_get_flattened_document_no_page(self):
        """Test get_flattened_document with no page."""
        result = get_flattened_document(None)
        assert result == []
    
    @patch('her.bridge.cdp_bridge.PLAYWRIGHT_AVAILABLE', True)
    def test_get_flattened_document_with_page(self):
        """Test get_flattened_document with mocked page."""
        mock_page = Mock()
        mock_client = Mock()
        mock_page.context.new_cdp_session.return_value = mock_client
        
        mock_nodes = [
            {"nodeId": 1, "nodeName": "HTML"},
            {"nodeId": 2, "nodeName": "BODY"}
        ]
        mock_client.send.return_value = {"nodes": mock_nodes}
        
        result = get_flattened_document(mock_page)
        assert result == mock_nodes
        mock_client.send.assert_any_call("DOM.enable")
        mock_client.send.assert_any_call("DOM.getFlattenedDocument", {"depth": -1, "pierce": True})
    
    def test_get_full_ax_tree_no_page(self):
        """Test get_full_ax_tree with no page."""
        result = get_full_ax_tree(None)
        assert result == []
    
    @patch('her.bridge.cdp_bridge.PLAYWRIGHT_AVAILABLE', True)
    def test_get_full_ax_tree_with_page(self):
        """Test get_full_ax_tree with mocked page."""
        mock_page = Mock()
        mock_client = Mock()
        mock_page.context.new_cdp_session.return_value = mock_client
        
        mock_nodes = [
            {"nodeId": 1, "role": {"value": "document"}},
            {"nodeId": 2, "role": {"value": "button"}}
        ]
        mock_client.send.return_value = {"nodes": mock_nodes}
        
        result = get_full_ax_tree(mock_page)
        assert result == mock_nodes
    
    @patch('her.bridge.cdp_bridge.PLAYWRIGHT_AVAILABLE', True)
    def test_execute_cdp_command(self):
        """Test execute_cdp_command."""
        mock_page = Mock()
        mock_client = Mock()
        mock_page.context.new_cdp_session.return_value = mock_client
        mock_client.send.return_value = {"result": "success"}
        
        result = execute_cdp_command(mock_page, "Page.navigate", {"url": "https://example.com"})
        assert result == {"result": "success"}
        mock_client.send.assert_called_with("Page.navigate", {"url": "https://example.com"})


class TestSnapshot:
    """Test snapshot functions."""
    
    def test_compute_dom_hash(self):
        """Test DOM hash computation."""
        descriptors = [
            {"backendNodeId": 1, "tag": "div", "text": "Hello"},
            {"backendNodeId": 2, "tag": "button", "text": "Click"}
        ]
        
        hash1 = compute_dom_hash(descriptors)
        assert isinstance(hash1, str)
        assert len(hash1) == 64  # SHA256 hex digest
        
        # Same descriptors should produce same hash
        hash2 = compute_dom_hash(descriptors)
        assert hash1 == hash2
        
        # Different descriptors should produce different hash
        descriptors[0]["text"] = "World"
        hash3 = compute_dom_hash(descriptors)
        assert hash1 != hash3
    
    def test_index_by_backend_id(self):
        """Test indexing nodes by backend ID."""
        nodes = [
            {"backendNodeId": 1, "tag": "div"},
            {"backendNodeId": 2, "tag": "button"},
            {"backendDOMNodeId": 3, "role": "link"}  # Alternative field name
        ]
        
        indexed = index_by_backend_id(nodes)
        assert len(indexed) == 3
        assert indexed[1]["tag"] == "div"
        assert indexed[2]["tag"] == "button"
        assert indexed[3]["role"] == "link"
    
    def test_merge_dom_and_ax(self):
        """Test merging DOM and AX nodes."""
        dom_nodes = [
            {
                "backendNodeId": 1,
                "nodeName": "BUTTON",
                "nodeType": 1,
                "attributes": ["id", "submit-btn", "class", "btn primary"]
            },
            {
                "backendNodeId": 2,
                "nodeName": "INPUT",
                "nodeType": 1,
                "attributes": ["type", "text", "placeholder", "Enter text"]
            }
        ]
        
        ax_nodes = [
            {
                "backendDOMNodeId": 1,
                "role": {"value": "button"},
                "name": {"value": "Submit"},
                "properties": [
                    {"name": "disabled", "value": {"value": False}}
                ]
            }
        ]
        
        merged = merge_dom_and_ax(dom_nodes, ax_nodes)
        
        assert len(merged) == 2
        assert merged[0]["tag"] == "button"
        assert merged[0]["role"] == "button"
        assert merged[0]["name"] == "Submit"
        assert merged[0]["id"] == "submit-btn"
        assert merged[0]["classes"] == ["btn", "primary"]
        assert merged[0]["disabled"] == False
        
        assert merged[1]["tag"] == "input"
        assert merged[1]["type"] == "text"
        assert merged[1]["placeholder"] == "Enter text"
    
    def test_detect_dom_change(self):
        """Test DOM change detection."""
        hash1 = "abc123"
        hash2 = "def456"
        
        assert detect_dom_change(hash1, hash2) == True
        assert detect_dom_change(hash1, hash1) == False
        assert detect_dom_change("", hash1) == True
        assert detect_dom_change(hash1, "") == True
    
    @patch('her.bridge.snapshot.get_flattened_document')
    @patch('her.bridge.snapshot.get_full_ax_tree')
    def test_capture_snapshot(self, mock_ax, mock_dom):
        """Test snapshot capture."""
        mock_dom.return_value = [
            {
                "backendNodeId": 1,
                "nodeName": "DIV",
                "nodeType": 1,
                "attributes": []
            }
        ]
        mock_ax.return_value = []
        
        mock_page = Mock()
        descriptors, dom_hash = capture_snapshot(mock_page)
        
        assert len(descriptors) == 1
        assert descriptors[0]["tag"] == "div"
        assert descriptors[0]["framePath"] == "main"
        assert isinstance(dom_hash, str)