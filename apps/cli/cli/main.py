"""Unified CLI entry point for the thesis hybrid system.

Aggregates subcommands from all apps:
    thesis experiment run --phase full --runs 5 --duration 300
    thesis experiment analyze --results-file path/to/results.json
    thesis experiment preflight
    thesis routing daemon --scenario s4-hybrid-predictive
    thesis prediction serve --port 8090
"""

import typer

app = typer.Typer(
    name="thesis",
    help="Hybrid k3s-serverless system with GRU workload prediction",
    no_args_is_help=True,
)


@app.command()
def version() -> None:
    """Show version information."""
    from rich import print as rprint

    rprint("[bold]thesis-hybrid-k3s-serverless[/bold] v0.1.0")


# Register sub-apps lazily to avoid import errors if a package isn't installed.
# Each sub-app is added when the corresponding command group is first used.
def _register_experiment() -> None:
    """Register the experiment sub-app."""
    try:
        from experiment.cli import app as experiment_app

        app.add_typer(experiment_app, name="experiment", help="Experiment orchestration")
    except ImportError:
        pass


def _register_routing() -> None:
    """Register the routing sub-app."""
    try:
        from routing.daemon.cli import app as routing_app

        app.add_typer(routing_app, name="routing", help="Routing daemon control")
    except ImportError:
        pass


def _register_prediction() -> None:
    """Register the prediction sub-app."""
    try:
        prediction_app = typer.Typer(help="GRU prediction service")

        @prediction_app.command()
        def serve(host: str = "0.0.0.0", port: int = 8090, model_path: str | None = None) -> None:
            """Start the GRU prediction server."""
            import uvicorn

            from prediction.server import create_app as create_fastapi_app

            uvicorn.run(create_fastapi_app(model_path), host=host, port=port)

        @prediction_app.command()
        def train(data: str = "synthetic") -> None:
            """Train a GRU model."""
            from rich import print as rprint

            rprint(f"[yellow]Training on {data} data...[/yellow]")
            if data == "synthetic":
                from prediction.training.train_gru import main as train_main

                train_main()
            else:
                from prediction.training.train_gru_real import main as train_main

                train_main()

        app.add_typer(prediction_app, name="prediction", help="GRU prediction service")
    except ImportError:
        pass


def _register_infra() -> None:
    """Register the infra sub-app."""
    try:
        from infra.cli import app as infra_app

        app.add_typer(infra_app, name="infra", help="Infrastructure management")
    except ImportError:
        pass


# Register all available sub-apps
_register_experiment()
_register_routing()
_register_prediction()
_register_infra()


if __name__ == "__main__":
    app()
