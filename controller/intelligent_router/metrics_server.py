#!/usr/bin/env python3
"""
HTTP server for Prometheus metrics endpoint.

Exposes /metrics on port 9103 for scraping.
"""

import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

import structlog

logger = structlog.get_logger(__name__)

DEFAULT_PORT = 9103


class MetricsHandler(BaseHTTPRequestHandler):
    """HTTP handler for /metrics endpoint."""

    def do_GET(self):
        if self.path == "/metrics":
            self.send_response(200)
            self.send_header("Content-Type", CONTENT_TYPE_LATEST)
            self.end_headers()
            self.wfile.write(generate_latest())
        elif self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"OK")
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        logger.debug("metrics_request", message=format % args)


class MetricsServer:
    """HTTP server for Prometheus metrics."""

    def __init__(self, port: int = DEFAULT_PORT):
        self.port = port
        self._server: HTTPServer | None = None
        self._thread: threading.Thread | None = None

    def start(self):
        """Start metrics server in background thread."""
        self._server = HTTPServer(("0.0.0.0", self.port), MetricsHandler)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()
        logger.info("metrics_server_started", port=self.port)

    def stop(self):
        """Stop metrics server."""
        if self._server:
            self._server.shutdown()
            self._server = None
        if self._thread:
            self._thread.join(timeout=5)
            self._thread = None
        logger.info("metrics_server_stopped")


_default_server: MetricsServer | None = None


def start_metrics_server(port: int = DEFAULT_PORT) -> MetricsServer:
    """Start the default metrics server."""
    global _default_server
    if _default_server is None:
        _default_server = MetricsServer(port=port)
        _default_server.start()
    return _default_server


def stop_metrics_server():
    """Stop the default metrics server."""
    global _default_server
    if _default_server:
        _default_server.stop()
        _default_server = None


if __name__ == "__main__":
    import time

    server = start_metrics_server()
    print(f"Metrics server running on http://localhost:{DEFAULT_PORT}/metrics")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        stop_metrics_server()
