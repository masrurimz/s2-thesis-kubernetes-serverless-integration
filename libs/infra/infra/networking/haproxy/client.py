"""HAProxy raw client: socket communication and stats CSV parsing.

Provides low-level HAProxy admin socket interaction without algorithm logic.
Algorithm-level weight adjustment (retry, verification, fallback) stays in routing.
"""

import socket
from typing import Optional

import requests
import structlog

logger = structlog.get_logger(__name__)


class HAProxyClient:
    """Raw HAProxy admin socket and stats client."""

    def __init__(
        self,
        tcp_socket_host: str = "localhost",
        tcp_socket_port: int = 9999,
        socket_path: str = "/tmp/haproxy.sock",
        backend_name: str = "servers",
        stats_url: str = "http://localhost:8404/stats;csv",
    ):
        self.tcp_socket_host = tcp_socket_host
        self.tcp_socket_port = tcp_socket_port
        self.socket_path = socket_path
        self.backend_name = backend_name
        self.stats_url = stats_url
        self.socket_timeout = 5.0

        # Detect available transport
        self.tcp_socket_available = self._test_tcp_socket_connectivity()
        self.unix_socket_available = self._test_socket_connectivity()

        logger.info(
            "HAProxyClient initialized",
            tcp_socket=f"{tcp_socket_host}:{tcp_socket_port}",
            backend=backend_name,
            tcp_available=self.tcp_socket_available,
            unix_available=self.unix_socket_available,
        )

    def _test_socket_connectivity(self) -> bool:
        """Test if HAProxy Unix admin socket is accessible."""
        try:
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            sock.settimeout(2.0)
            sock.connect(self.socket_path)
            sock.close()
            return True
        except Exception:
            return False

    def _test_tcp_socket_connectivity(self) -> bool:
        """Test if HAProxy TCP admin socket is accessible."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2.0)
            sock.connect((self.tcp_socket_host, self.tcp_socket_port))
            sock.close()
            return True
        except Exception:
            return False

    def _send_command_tcp(self, command: str) -> Optional[str]:
        """Send command to HAProxy via TCP socket.

        Args:
            command: HAProxy admin command

        Returns:
            Command response or None if failed
        """
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.socket_timeout)
            sock.connect((self.tcp_socket_host, self.tcp_socket_port))
            sock.send((command + "\n").encode())
            response = sock.recv(4096).decode().strip()
            sock.close()

            logger.debug("HAProxy TCP command sent", command=command, response_length=len(response))
            return response

        except Exception as e:
            logger.error("TCP socket command failed", error=str(e))
            return None

    def _send_command_unix(self, command: str) -> Optional[str]:
        """Send command to HAProxy via Unix socket.

        Args:
            command: HAProxy admin command

        Returns:
            Command response or None if failed
        """
        try:
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            sock.settimeout(self.socket_timeout)
            sock.connect(self.socket_path)
            sock.send((command + "\n").encode())
            response = sock.recv(4096).decode().strip()
            sock.close()

            logger.debug(
                "HAProxy Unix socket command sent",
                command=command,
                response_length=len(response),
            )
            return response

        except FileNotFoundError:
            logger.error("HAProxy admin socket not found", path=self.socket_path)
            return None
        except socket.timeout:
            logger.error("HAProxy socket timeout", command=command)
            return None
        except Exception as e:
            logger.error("HAProxy command failed", command=command, error=str(e))
            return None

    def _send_command(self, command: str) -> Optional[str]:
        """Send command to HAProxy admin socket. Tries TCP first, then Unix.

        Args:
            command: HAProxy admin command

        Returns:
            Command response or None if failed
        """
        if self.tcp_socket_available:
            response = self._send_command_tcp(command)
            if response is not None:
                return response
            logger.warning("TCP socket failed, falling back to Unix socket", command=command)

        if self.unix_socket_available:
            return self._send_command_unix(command)

        return None

    def test_connection(self) -> bool:
        """Test HAProxy admin socket connection.

        Returns:
            True if connection working, False otherwise
        """
        try:
            response = self._send_command("show info")
            if response and "HAProxy" in response:
                logger.info("HAProxy admin socket connection successful")
                return True
            else:
                logger.warning("HAProxy admin socket test failed")
                return False

        except Exception as e:
            logger.error("HAProxy connection test failed", error=str(e))
            return False

    def get_stats_csv(self) -> Optional[str]:
        """Get raw HAProxy stats CSV via HTTP.

        Returns:
            Raw CSV text or None on failure
        """
        try:
            response = requests.get(self.stats_url, timeout=5)
            response.raise_for_status()
            return response.text

        except Exception as e:
            logger.error("Failed to get HAProxy stats CSV", error=str(e))
            return None

    def get_current_weights(self) -> Optional[dict[str, int]]:
        """Get current backend server weights from HAProxy.

        Returns:
            Dictionary mapping server names to their weight values, or None on failure
        """
        # Try socket first if available
        if self.tcp_socket_available or self.unix_socket_available:
            try:
                response = self._send_command("show stat")
                if response:
                    weights = self._parse_stats_response(response)
                    if weights:
                        logger.debug("Current weights retrieved via socket", weights=weights)
                        return weights
            except Exception as e:
                logger.warning("Socket stats failed, trying HTTP", error=str(e))

        # Fallback to HTTP stats
        try:
            response = requests.get(self.stats_url, timeout=5)
            response.raise_for_status()

            weights = self._parse_stats_response(response.text)
            if weights:
                logger.debug("Current weights retrieved via HTTP", weights=weights)
                return weights
            else:
                logger.warning("Could not parse current weights from HAProxy stats")
                return None

        except Exception as e:
            logger.error("Failed to get current weights", error=str(e))
            return None

    def _parse_stats_response(self, stats_text: str) -> Optional[dict[str, int]]:
        """Parse HAProxy stats response to extract backend server weights.

        Args:
            stats_text: Raw stats output (socket response or HTTP CSV)

        Returns:
            Dict mapping 'k3s'/'knative' to weight values, or None
        """
        try:
            lines = stats_text.strip().split("\n")
            weights: dict[str, int] = {}

            k3s_aliases = {"k3s", "k3s-cluster"}
            knative_aliases = {"knative", "serverless-sim"}

            for line in lines:
                if not line or line.startswith("#"):
                    continue

                fields = line.split(",")
                if len(fields) < 19:
                    continue

                pxname = fields[0]
                svname = fields[1]
                weight = fields[18]

                if pxname == self.backend_name:
                    parsed_weight = self._parse_weight(weight)
                    if svname in k3s_aliases:
                        weights["k3s"] = parsed_weight
                    elif svname in knative_aliases:
                        weights["knative"] = parsed_weight

            if "k3s" in weights and "knative" in weights:
                return weights
            else:
                return None

        except Exception as e:
            logger.error("Failed to parse stats response", error=str(e))
            return None

    @staticmethod
    def _parse_weight(weight: str) -> int:
        """Extract numeric weight from HAProxy stat fields."""
        token = (weight or "").strip().split("/")[0]
        return int(token) if token.isdigit() else 0

    def set_weight(self, server: str, weight: int) -> bool:
        """Set weight for a single backend server.

        Args:
            server: Server name ('k3s' or 'knative')
            weight: Weight value (0-100)

        Returns:
            True if weight set successfully
        """
        if not (0 <= weight <= 100):
            logger.error("Invalid weight", server=server, weight=weight)
            return False

        command = f"set server {self.backend_name}/{server} weight {weight}"
        response = self._send_command(command)

        if response is not None and "no such" not in response.lower():
            logger.debug("Weight set via socket", server=server, weight=weight)
            return True

        # Fallback: try HTTP stats admin interface
        try:
            stats_admin_url = self.stats_url.replace(";csv", "")
            params = {"action": "set", "s": f"{self.backend_name}/{server}", "weight": str(weight)}
            resp = requests.post(stats_admin_url, data=params, timeout=5)

            if resp.status_code in [200, 302, 303]:
                logger.debug("Weight set via HTTP", server=server, weight=weight)
                return True

            logger.error(
                "Failed to set weight via HTTP",
                status=resp.status_code,
                server=server,
                weight=weight,
            )
            return False

        except Exception as e:
            logger.error("HTTP weight setting failed", error=str(e))
            return False

    def enable_server(self, server: str) -> bool:
        """Enable a backend server (sets to READY state).

        Args:
            server: Server name ('k3s' or 'knative')

        Returns:
            True if server enabled successfully
        """
        try:
            response = self._send_command(f"enable server {self.backend_name}/{server}")

            if response is not None and "no such" not in response.lower():
                logger.info("Server enabled", server=server)
                return True

            logger.error("Failed to enable server", server=server)
            return False

        except Exception as e:
            logger.error("Server enable failed", server=server, error=str(e))
            return False

    def disable_server(self, server: str) -> bool:
        """Disable a backend server (sets to MAINT state).

        Args:
            server: Server name ('k3s' or 'knative')

        Returns:
            True if server disabled successfully
        """
        try:
            response = self._send_command(f"disable server {self.backend_name}/{server}")

            if response is not None and "no such" not in response.lower():
                logger.info("Server disabled", server=server)
                return True

            logger.error("Failed to disable server", server=server)
            return False

        except Exception as e:
            logger.error("Server disable failed", server=server, error=str(e))
            return False
