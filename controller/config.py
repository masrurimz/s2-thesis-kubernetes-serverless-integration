from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """
    Centralized configuration for the hybrid controller system.
    Reads from environment variables and .env file.
    """

    # HAProxy Configuration
    HAPROXY_HOST: str = Field(default="localhost", description="HAProxy host")
    HAPROXY_SOCKET_PORT: int = Field(default=19999, description="HAProxy admin socket port")
    HAPROXY_STATS_PORT: int = Field(default=18404, description="HAProxy stats port")
    HAPROXY_HTTP_PORT: int = Field(default=18082, description="HAProxy main HTTP traffic port")
    HAPROXY_STATS_URL_PATH: str = Field(default="/stats;csv", description="HAProxy stats URL path")

    @property
    def HAPROXY_STATS_URL(self) -> str:
        return f"http://{self.HAPROXY_HOST}:{self.HAPROXY_STATS_PORT}{self.HAPROXY_STATS_URL_PATH}"

    # GRU Prediction Service
    GRU_HOST: str = Field(default="localhost", description="GRU prediction service host")
    GRU_PORT: int = Field(default=8090, description="GRU prediction service port")

    @property
    def GRU_SERVICE_URL(self) -> str:
        return f"http://{self.GRU_HOST}:{self.GRU_PORT}"

    # Prometheus
    PROMETHEUS_HOST: str = Field(default="localhost", description="Prometheus host")
    PROMETHEUS_PORT: int = Field(default=9090, description="Prometheus port")

    @property
    def PROMETHEUS_URL(self) -> str:
        return f"http://{self.PROMETHEUS_HOST}:{self.PROMETHEUS_PORT}"

    # Routing Daemon
    DAEMON_API_PORT: int = Field(default=9104, description="Routing daemon API port")
    DAEMON_DECISION_INTERVAL: int = Field(default=15, description="Routing decision interval in seconds")

    # Scenario
    DEFAULT_SCENARIO: str = Field(default="s3-hybrid-reactive", description="Default experiment scenario")

    # Kubernetes / Serverless
    K3S_NODE_IP: str = Field(default="127.0.0.1", description="K3s Node IP")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()
