"""Simple HTTP server for serving sample pages.

This script runs a basic HTTP server that serves files from the same
directory.  It is used by the end‑to‑end tests to host pages such as
``test_complex.html``.  You can run it with ``python -m samples.site.server``.
"""

import http.server
import os
import socketserver


def run_server(port: int = 8000) -> None:
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", port), handler) as httpd:
        print(f"Serving sample site on http://localhost:{port}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("Stopping server")


if __name__ == "__main__":
    run_server()
