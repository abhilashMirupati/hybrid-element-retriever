"""Py4J gateway server for Java integration."""

import logging
import sys
try:
    from py4j.java_gateway import JavaGateway, CallbackServerParameters
    from py4j.java_gateway import GatewayParameters
    from py4j.java_server import JavaServer as GatewayServer
except ImportError:
    # Fallback for older py4j versions
    try:
        from py4j.java_gateway import JavaGateway, CallbackServerParameters, GatewayParameters
        from py4j import GatewayServer
    except ImportError:
        # Mock for testing when py4j is not available
        JavaGateway = None
        CallbackServerParameters = None
        GatewayParameters = None
        GatewayServer = None
from .cli_api import HybridClient

logger = logging.getLogger(__name__)


class PythonGateway:
    """Python gateway for Java integration."""

    def __init__(self):
        self.client = HybridClient(auto_index=True, headless=True)

    def act(self, step, url=None):
        """Execute an action."""
        return self.client.act(step, url)

    def query(self, phrase, url=None):
        """Query for elements."""
        return self.client.query(phrase, url)

    def findXPaths(self, phrase, url=None):
        """Find XPath selectors for a phrase."""
        results = self.client.query(phrase, url)
        return [r.get("selector", "") for r in results if r.get("selector")]

    def close(self):
        """Close the client."""
        self.client.close()

    class Java:
        implements = ["com.example.her.HybridClientInterface"]


def start_gateway_server(port=25333):
    """Start the Py4J gateway server.

    Args:
        port: Port to listen on
    """
    gateway = PythonGateway()
    server = GatewayServer(
        gateway,
        port=port,
        gateway_parameters=GatewayParameters(auto_convert=True),
        callback_server_parameters=CallbackServerParameters(),
    )

    server.start()
    logger.info(f"Gateway server started on port {port}")

    try:
        # Keep server running
        import time

        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down gateway server")
        gateway.close()
        server.shutdown()


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Start server
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 25333
    start_gateway_server(port)
