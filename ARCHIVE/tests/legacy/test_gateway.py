"""Tests for gateway server module."""

from unittest.mock import Mock, patch, MagicMock
import pytest
# import sys
class TestGatewayServer:
    """Test gateway server functions."""

    def test_gateway_import(self):
        """Test that gateway module can be imported."""
        # Mock py4j if not available
        with patch.dict(
            sys.modules,
            {
                "py4j": Mock(),
                "py4j.java_gateway": Mock(
                    JavaGateway=Mock,
                    CallbackServerParameters=Mock,
                    GatewayParameters=Mock,
                ),
                "py4j.java_server": Mock(JavaServer=Mock),
            },
        ):
            from her import gateway_server

            assert gateway_server is not None

    @patch("her.gateway_server.GatewayServer")
    @patch("her.gateway_server.JavaGateway")
    @patch("her.gateway_server.HybridClient")
    def test_start_gateway_server(self, mock_client, mock_gateway, mock_server):
        """Test gateway server startup."""
        # Skip if py4j not available
        if mock_server is None:
            pytest.skip("py4j not available")

        # Mock the gateway and server
        mock_gateway_instance = Mock()
        mock_gateway.return_value = mock_gateway_instance

        mock_server_instance = Mock()
        mock_server.return_value = mock_server_instance

        # Import after mocking
        from her.gateway_server import start_gateway_server

        # Test with default parameters
        with patch("builtins.print") as mock_print:
            # Simulate KeyboardInterrupt to exit
            mock_server_instance.start.side_effect = KeyboardInterrupt()

            start_gateway_server()

            # Verify server was started
            mock_server_instance.start.assert_called_once()

            # Verify shutdown was called
            mock_gateway_instance.shutdown.assert_called_once()

    @patch("her.gateway_server.GatewayServer")
    @patch("her.gateway_server.JavaGateway")
    def test_start_gateway_server_with_port(self, mock_gateway, mock_server):
        """Test gateway server with custom port."""
        if mock_server is None:
            pytest.skip("py4j not available")

        mock_gateway_instance = Mock()
        mock_gateway.return_value = mock_gateway_instance

        mock_server_instance = Mock()
        mock_server.return_value = mock_server_instance
        mock_server_instance.start.side_effect = KeyboardInterrupt()

        from her.gateway_server import start_gateway_server

        start_gateway_server(port=12345)

        # Check that custom port was used
        call_args = mock_server.call_args
        assert call_args is not None

    @patch("her.gateway_server.GatewayServer")
    @patch("her.gateway_server.JavaGateway")
    def test_start_gateway_server_error(self, mock_gateway, mock_server):
        """Test gateway server error handling."""
        if mock_server is None:
            pytest.skip("py4j not available")

        mock_gateway_instance = Mock()
        mock_gateway.return_value = mock_gateway_instance

        mock_server_instance = Mock()
        mock_server.return_value = mock_server_instance
        mock_server_instance.start.side_effect = Exception("Connection failed")

        from her.gateway_server import start_gateway_server

        with pytest.raises(Exception) as exc_info:
            start_gateway_server()

        assert "Connection failed" in str(exc_info.value)
