"""Typer CLI entry point for the routing daemon."""

import typer

app = typer.Typer(help="Routing daemon for experiment orchestration.")


@app.command()
def daemon(
    scenario: str = typer.Option("s3-hybrid-reactive", help="Scenario name"),
    interval: int = typer.Option(15, help="Decision interval in seconds"),
    prometheus_url: str = typer.Option("http://localhost:9090", help="Prometheus server URL"),
    haproxy_host: str = typer.Option("localhost", help="HAProxy admin socket host"),
    haproxy_port: int = typer.Option(9999, help="HAProxy admin socket port"),
    haproxy_stats: str = typer.Option("http://localhost:18404/stats;csv", help="HAProxy stats URL"),
    gru_url: str = typer.Option("http://localhost:8090", help="GRU prediction server URL"),
    api_port: int = typer.Option(9104, help="HTTP API port"),
):
    """Start the routing daemon."""
    import signal

    from routing.daemon.service import RoutingDaemon

    daemon_instance = RoutingDaemon(
        scenario=scenario,
        decision_interval=interval,
        prometheus_url=prometheus_url,
        haproxy_socket_host=haproxy_host,
        haproxy_socket_port=haproxy_port,
        haproxy_stats_url=haproxy_stats,
        gru_server_url=gru_url,
        api_port=api_port,
    )

    def signal_handler(signum, frame):
        import structlog

        logger = structlog.get_logger(__name__)
        logger.info("Received shutdown signal")
        daemon_instance.stop()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    daemon_instance.run()


if __name__ == "__main__":
    app()
