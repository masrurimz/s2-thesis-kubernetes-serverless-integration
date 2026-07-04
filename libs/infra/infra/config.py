"""Platform configuration — replaces deploy/config.env."""

from dataclasses import dataclass


@dataclass
class PlatformConfig:
    """Deployment-specific ports and hosts for the hybrid k3s-serverless platform.

    This replaces deploy/config.env as the single source of truth.
    Application-level config (e.g. GRU model paths) lives in shared.config.Settings.
    """

    haproxy_host: str = "localhost"
    haproxy_http_port: int = 18082
    haproxy_stats_port: int = 18404
    haproxy_socket_port: int = 19999

    prometheus_host: str = "localhost"
    prometheus_port: int = 9090

    gru_host: str = "localhost"
    gru_port: int = 8090

    daemon_api_port: int = 9104

    k3d_node_ip: str = "127.0.0.1"
    k3s_warm_nodeport: int = 30080
    k3s_activator_nodeport: int = 30081

    @property
    def haproxy_url(self) -> str:
        return f"http://{self.haproxy_host}:{self.haproxy_http_port}"

    @property
    def haproxy_stats_url(self) -> str:
        return f"http://{self.haproxy_host}:{self.haproxy_stats_port}/stats"

    @property
    def haproxy_stats_csv_url(self) -> str:
        return f"http://{self.haproxy_host}:{self.haproxy_stats_port}/stats;csv"

    @property
    def prometheus_url(self) -> str:
        return f"http://{self.prometheus_host}:{self.prometheus_port}"

    @property
    def gru_url(self) -> str:
        return f"http://{self.gru_host}:{self.gru_port}"

    @property
    def daemon_url(self) -> str:
        return f"http://localhost:{self.daemon_api_port}"

    @property
    def k3s_warm_url(self) -> str:
        return f"http://{self.k3d_node_ip}:{self.k3s_warm_nodeport}"

    @property
    def k3s_activator_url(self) -> str:
        return f"http://{self.k3d_node_ip}:{self.k3s_activator_nodeport}"
