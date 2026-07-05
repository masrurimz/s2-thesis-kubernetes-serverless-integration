#!/usr/bin/env python3
"""
Sprint 2: HAProxy Weight Adjuster

This module handles real-time traffic weight adjustment through HAProxy's
admin socket interface for intelligent routing decisions.
"""

import socket
import time
from typing import Dict, Optional

import requests
import structlog

from shared.config import settings

logger = structlog.get_logger(__name__)


class HAProxyWeightAdjuster:
    """Manages HAProxy backend server weight adjustments via admin socket."""

    def __init__(
        self,
        tcp_socket_host: str = "localhost",
        tcp_socket_port: int = 9999,
        stats_url: str = "http://localhost:18404/stats;csv",
        backend_name: str = "servers",
    ):
        """
        Initialize HAProxy weight adjuster.

        Args:
            tcp_socket_host: HAProxy admin socket host
            tcp_socket_port: HAProxy admin socket port
            stats_url: HAProxy stats CSV URL
            backend_name: Name of the HAProxy backend
        """
        self.tcp_socket_host = tcp_socket_host
        self.tcp_socket_port = tcp_socket_port
        self.stats_url = stats_url
        self.backend_name = backend_name
        self.socket_available = False

        self._test_connection()

        logger.info(
            "HAProxyWeightAdjuster initialized",
            host=tcp_socket_host,
            port=tcp_socket_port,
            backend=backend_name,
        )

    def _test_connection(self) -> bool:
        """Test connection to HAProxy admin socket."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            sock.connect((self.tcp_socket_host, self.tcp_socket_port))
            sock.close()
            self.socket_available = True
            return True
        except Exception as e:
            logger.warning("HAProxy socket not available", error=str(e))
            self.socket_available = False
            return False

    def _send_command(self, command: str) -> Optional[str]:
        """Send command to HAProxy admin socket.

        Args:
            command: HAProxy admin command

        Returns:
            Response string or None on failure
        """
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((self.tcp_socket_host, self.tcp_socket_port))

            sock.send(f"{command}\n".encode())
            response = sock.recv(4096).decode()
            sock.close()

            return response.strip()
        except Exception as e:
            logger.error("Failed to send HAProxy command", command=command, error=str(e))
            return None

    def set_weights(self, k3s_weight: int, knative_weight: int) -> bool:
        """
        Set backend weights directly via HAProxy socket.

        Args:
            k3s_weight: Weight for k3s backend (0-100)
            knative_weight: Weight for knative backend (0-100)

        Returns:
            True if weights were set successfully
        """
        if not self.socket_available:
            if not self._test_connection():
                return False

        try:
            # Set k3s weight
            k3s_cmd = f"set server {self.backend_name}/k3s weight {k3s_weight}"
            k3s_response = self._send_command(k3s_cmd)

            # Set knative weight
            knative_cmd = f"set server {self.backend_name}/knative weight {knative_weight}"
            knative_response = self._send_command(knative_cmd)

            # HAProxy socket returns empty string on success, error message on failure,
            # None on connection error. Only non-empty strings indicate failure.
            if k3s_response or knative_response:
                logger.error("Failed to set weights", k3s_response=k3s_response, knative_response=knative_response)
                return False

            logger.info(
                "Weights updated",
                k3s=k3s_weight,
                knative=knative_weight,
            )
            return True

        except Exception as e:
            logger.error("Failed to set weights", error=str(e))
            return False

    def set_weights_with_retry(
        self,
        k3s_weight: int,
        knative_weight: int,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ) -> bool:
        """
        Set weights with retry logic.

        Args:
            k3s_weight: Weight for k3s backend
            knative_weight: Weight for knative backend
            max_retries: Maximum number of retries
            retry_delay: Delay between retries in seconds

        Returns:
            True if weights were set successfully
        """
        for attempt in range(max_retries):
            if self.set_weights(k3s_weight, knative_weight):
                return True

            if attempt < max_retries - 1:
                logger.warning(
                    "Retrying weight adjustment",
                    attempt=attempt + 1,
                    max_retries=max_retries,
                )
                time.sleep(retry_delay)

        logger.error(
            "Failed to set weights after retries",
            max_retries=max_retries,
            k3s=k3s_weight,
            knative=knative_weight,
        )
        return False

    def get_current_weights(self) -> Dict[str, int]:
        """
        Get current backend weights from HAProxy stats.

        Returns:
            Dict with 'k3s' and 'knative' weights
        """
        try:
            response = requests.get(self.stats_url, timeout=5)
            response.raise_for_status()

            lines = response.text.strip().split("\n")
            weights = {"k3s": 0, "knative": 0}

            for line in lines:
                fields = line.split(",")
                if len(fields) < 2:
                    continue

                server_name = fields[1]
                if server_name == "k3s":
                    weights["k3s"] = int(fields[18]) if fields[18].isdigit() else 0
                elif server_name == "knative":
                    weights["knative"] = int(fields[18]) if fields[18].isdigit() else 0

            return weights

        except Exception as e:
            logger.error("Failed to get current weights", error=str(e))
            return {}

    def get_backend_status(self) -> Dict[str, str]:
        """
        Get backend server status.

        Returns:
            Dict mapping server names to status strings
        """
        try:
            response = requests.get(self.stats_url, timeout=5)
            response.raise_for_status()

            lines = response.text.strip().split("\n")
            status = {}

            for line in lines:
                fields = line.split(",")
                if len(fields) < 2:
                    continue

                server_name = fields[1]
                server_status = fields[17] if len(fields) > 17 else "UNKNOWN"
                status[server_name] = server_status

            return status

        except Exception as e:
            logger.error("Failed to get backend status", error=str(e))
            return {}

    def test_connection(self) -> bool:
        """Test connection to HAProxy."""
        return self._test_connection()


def main():
    """Test the HAProxy weight adjuster."""
    adjuster = HAProxyWeightAdjuster(
        tcp_socket_host=settings.HAPROXY_HOST,
        tcp_socket_port=settings.HAPROXY_SOCKET_PORT,
        stats_url=settings.HAPROXY_STATS_URL,
    )

    # Test connection
    if not adjuster.test_connection():
        print(f"HAProxy admin socket not available at {settings.HAPROXY_HOST}:{settings.HAPROXY_SOCKET_PORT}")
        return

    # Get current weights
    current = adjuster.get_current_weights()
    print(f"Current weights: {current}")

    # Test weight adjustment
    if current:
        # Swap weights for testing
        new_k3s = current["knative"]
        new_knative = current["k3s"]
        print(f"Setting weights: k3s={new_k3s}, knative={new_knative}")

        success = adjuster.set_weights(new_k3s, new_knative)
        if success:
            updated = adjuster.get_current_weights()
            print(f"Updated weights: {updated}")


if __name__ == "__main__":
    main()
