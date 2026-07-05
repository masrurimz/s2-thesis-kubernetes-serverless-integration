from __future__ import annotations

"""Experiment orchestration CLI.

Provides typer commands for running, analyzing, and validating experiments.
Entry point: thesis-experiment (via pyproject.toml [project.scripts]).
"""

import json
import os
import random
import time
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Optional

import typer
import structlog

from shared.models.experiment import ExperimentConfig, ExperimentResult

if TYPE_CHECKING:
    from shared.models.pipeline import PipelineContext

app = typer.Typer(help="Experiment orchestration")
logger = structlog.get_logger(__name__)

SCENARIOS = [
    "s1-k8s-only",
    "s2-serverless-only",
    "s3-hybrid-reactive",
    "s4-hybrid-predictive",
]

WARMUP_SEC = 30
COOLDOWN_SEC = 60
INTER_RUN_PAUSE_SEC = 60


@app.command()
def run(
    phase: str = typer.Option("full", help="Phase: preflight, experiments, analysis, or full"),
    runs: int = typer.Option(5, help="Runs per scenario"),
    duration: int = typer.Option(300, help="Workload duration in seconds"),
    seed: int = typer.Option(42, help="Random seed for run order"),
    scenarios: Optional[str] = typer.Option(None, help="Comma-separated scenario list (default: all 4)"),
    output: Optional[str] = typer.Option(None, help="Output directory"),
    dry_run: bool = typer.Option(False, help="Simulate pipeline without side effects"),
    controller: str = typer.Option("v2", help="Controller version for S4"),
) -> None:
    """Run experiment phase through the full pipeline."""
    from rich.console import Console
    from rich.panel import Panel

    console = Console()

    datestamp = datetime.now().strftime("%Y-%m-%d")
    output_dir = output or f"results/experiments/phase-b/{datestamp}_clarknet-replay"
    scenario_list = scenarios.split(",") if scenarios else SCENARIOS

    console.print(
        Panel.fit(
            f"[bold]Phase B Experiments[/bold]\n"
            f"Runs: {runs} × Scenarios: {len(scenario_list)}\n"
            f"Controller: {controller}  |  Seed: {seed}\n"
            f"Output: {output_dir}",
            border_style="cyan",
        )
    )
    os.environ["CONTROLLER_VERSION"] = controller

    config = ExperimentConfig(
        phase=phase,
        runs=runs,
        duration_sec=duration,
        seed=seed,
    )

    if phase in ("preflight", "full"):
        console.print("\n[bold cyan]Preflight Checks[/bold cyan]")
        from experiment.stages.preflight import PreflightStage

        stage = PreflightStage()
        ctx_result = stage.execute(_make_ctx(config, scenario_list[0], 0, output_dir))
        if not ctx_result.success:
            console.print(f"[red]Preflight failed: {ctx_result.error}[/red]")
            if phase == "full":
                raise typer.Exit(1)
        else:
            console.print("[green]All preflight checks passed[/green]")

    if phase in ("experiments", "full"):
        console.print(f"\n[bold cyan]Running {runs * len(scenario_list)} experiments...[/bold cyan]")
        results = _run_replicated(config, scenario_list, output_dir, dry_run)
        console.print(f"\n[green]✅ {len(results)} runs completed[/green]")

        if phase in ("analysis", "full"):
            console.print("\n[bold cyan]Statistical Analysis[/bold cyan]")
            from experiment.stages.analyze import AnalyzeStage
            from experiment.stages.report import ReportStage

            analyzer = AnalyzeStage()
            clean, excluded, comparisons = analyzer.analyze_batch(results)

            report_stage = ReportStage()
            analysis_set = [r for r in clean if r.stress_validity_passed or r.scenario == "s2-serverless-only"]
            report = report_stage.generate_report(clean, analysis_set, excluded, comparisons)

            report_path = Path(output_dir) / "report.md"
            report_path.write_text(report)
            console.print(f"\n{report}")


@app.command()
def analyze(
    results_file: str = typer.Argument(..., help="Path to results JSON file"),
    output: Optional[str] = typer.Option(None, help="Output directory for report"),
) -> None:
    """Statistical analysis of existing results."""
    from rich.console import Console

    console = Console()

    path = Path(results_file)
    if not path.exists():
        console.print(f"[red]File not found: {results_file}[/red]")
        raise typer.Exit(1)

    with open(path) as f:
        raw = json.load(f)
    results = [ExperimentResult(**r) for r in raw]

    from experiment.stages.analyze import AnalyzeStage
    from experiment.stages.report import ReportStage

    analyzer = AnalyzeStage()
    clean, excluded, comparisons = analyzer.analyze_batch(results)

    report_stage = ReportStage()
    analysis_set = [r for r in clean if r.stress_validity_passed or r.scenario == "s2-serverless-only"]
    report = report_stage.generate_report(clean, analysis_set, excluded, comparisons)

    if output:
        out_dir = Path(output)
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "report.md").write_text(report)
        console.print(f"[green]Report saved to {out_dir / 'report.md'}[/green]")

    console.print(f"\n{report}")


@app.command()
def preflight() -> None:
    """Validate infrastructure readiness."""
    from rich.console import Console
    from rich.table import Table

    console = Console()

    from experiment.stages.preflight import PreflightStage
    from shared.models.pipeline import ExperimentConfig, PipelineContext

    stage = PreflightStage()
    config = ExperimentConfig()
    ctx = PipelineContext(
        batch_id="preflight-check",
        scenario="s1-k8s-only",
        run_id=0,
        config=config,
    )
    result = stage.execute(ctx)

    if ctx.preflight:
        table = Table(show_header=True, header_style="bold")
        table.add_column("Check")
        table.add_column("Status", justify="center")
        for k, v in ctx.preflight.checks.items():
            table.add_row(k, "[green]✅[/green]" if v else "[red]❌[/red]")
        console.print(table)

    if result.success:
        console.print("\n[green]All preflight checks passed[/green]")
    else:
        console.print(f"\n[red]Preflight failed: {result.error}[/red]")
        raise typer.Exit(1)


@app.command()
def validate(
    results_dir: str = typer.Argument(..., help="Path to experiment result bundle"),
) -> None:
    """Validate experiment result bundle against schema."""
    from rich.console import Console

    console = Console()

    bundle_path = Path(results_dir)
    if not bundle_path.exists():
        console.print(f"[red]Bundle not found: {results_dir}[/red]")
        raise typer.Exit(1)

    # Check for required files
    required_files = ["experiment_schedule.json"]
    for f in required_files:
        if not (bundle_path / f).exists():
            console.print(f"[yellow]Missing: {f}[/yellow]")

    # Check for result files
    result_files = list(bundle_path.glob("*/result.json"))
    if not result_files:
        console.print("[yellow]No run result files found[/yellow]")
    else:
        console.print(f"[green]Found {len(result_files)} run results[/green]")

    # Validate each result against ExperimentResult schema
    valid_count = 0
    for rf in result_files:
        try:
            with open(rf) as f:
                data = json.load(f)
            ExperimentResult(**data)
            valid_count += 1
        except Exception as e:
            console.print(f"[red]Invalid result {rf}: {e}[/red]")

    console.print(f"\n[green]{valid_count}/{len(result_files)} results validated[/green]")


def _make_ctx(
    config: ExperimentConfig,
    scenario: str,
    run_id: int,
    output_dir: str,
) -> "PipelineContext":  # noqa: F821
    """Create a PipelineContext for a single run."""
    from shared.models.pipeline import PipelineContext

    run_dir = Path(output_dir) / f"{scenario}_run{run_id}"
    run_dir.mkdir(parents=True, exist_ok=True)

    return PipelineContext(
        batch_id=f"batch-{datetime.now().strftime('%Y%m%d')}",
        scenario=scenario,
        run_id=run_id,
        config=config,
        output_dir=str(run_dir),
    )


def _run_replicated(
    config: ExperimentConfig,
    scenarios: list[str],
    output_dir: str,
    dry_run: bool,
) -> list[ExperimentResult]:
    """Run replicated experiments with randomized order."""
    from rich.console import Console

    console = Console()
    schedule = [(s, r) for s in scenarios for r in range(1, config.runs + 1)]
    rng = random.Random(config.seed)
    rng.shuffle(schedule)

    results: list[ExperimentResult] = []

    for idx, (scenario, run_id) in enumerate(schedule):
        console.print(f"  [cyan]Run {idx + 1}/{len(schedule)}:[/cyan] {scenario} run {run_id}")

        ctx = _make_ctx(config, scenario, run_id, output_dir)

        if dry_run:
            from experiment.pipeline import Pipeline
            from experiment.stages.reset import ResetStage
            from experiment.stages.daemon import DaemonStage
            from experiment.stages.workload import WorkloadStage
            from experiment.stages.collect import CollectStage

            stages = [ResetStage(), DaemonStage(), WorkloadStage(), CollectStage()]
            pipeline = Pipeline(stages, ctx)
            pipeline.dry_run()
            console.print(f"    [yellow]Dry run: {pipeline.summary()}[/yellow]")
            continue

        # Full run: execute the per-run protocol
        result = _run_single(scenario, run_id, idx, config, output_dir)
        if result:
            results.append(result)

        # Inter-run pause
        if idx < len(schedule) - 1:
            console.print(f"    [dim]Pausing {INTER_RUN_PAUSE_SEC}s...[/dim]")
            time.sleep(INTER_RUN_PAUSE_SEC)

    return results


def _run_single(
    scenario: str,
    run_id: int,
    run_order_idx: int,
    config: ExperimentConfig,
    output_dir: str,
) -> Optional[ExperimentResult]:
    """Execute a single experiment run with full protocol."""
    from datetime import datetime

    from shared.models.experiment import ExperimentResult, RunManifest
    from experiment.stages.reset import ResetStage
    from experiment.stages.daemon import DaemonStage
    from experiment.stages.workload import WorkloadStage
    from experiment.stages.collect import CollectStage

    run_dir = Path(output_dir) / f"{scenario}_run{run_id}"
    run_dir.mkdir(parents=True, exist_ok=True)

    logger.info("run_start", scenario=scenario, run_id=run_id, order=run_order_idx)

    resetter = ResetStage()
    daemon_stage = DaemonStage()
    workload_stage = WorkloadStage()
    collect_stage = CollectStage()

    # (B) Per-run reset
    reset_ctx = _make_ctx(config, scenario, run_id, output_dir)
    reset_result = resetter.execute(reset_ctx)
    if not reset_result.success:
        logger.error("reset_failed", scenario=scenario, error=reset_result.error)
        return None

    # Start daemon
    daemon_ctx = _make_ctx(config, scenario, run_id, output_dir)
    daemon_result = daemon_stage.execute(daemon_ctx)
    if not daemon_result.success:
        logger.error("daemon_failed", scenario=scenario, error=daemon_result.error)
        return None

    try:
        # Save manifest
        manifest = RunManifest(
            scenario=scenario,
            run_id=run_id,
            run_order_idx=run_order_idx,
            random_seed=config.seed,
            git_commit=_git_commit_hash(),
            k6_script="",
            k6_stages_json="",
            replay_manifest=config.replay_manifest,
            daemon_config=config.daemon_config,
            scaling_config=config.scaling_config,
            timestamp=datetime.now().isoformat(),
        )
        with open(run_dir / "manifest.json", "w") as f:
            json.dump(manifest.model_dump(), f, indent=2)

        # (C.warm-up) 30s idle warm-up
        logger.info("warmup_start", seconds=WARMUP_SEC)
        time.sleep(WARMUP_SEC)

        # Record t_start and begin resource polling
        t_start = time.time()
        collect_stage.start_resource_polling()

        # (C.2) Execute k6 trace replay
        workload_ctx = _make_ctx(config, scenario, run_id, output_dir)
        workload_stage.execute(workload_ctx)

        # (C.3) Post-k6 cooldown
        logger.info("cooldown_start", seconds=COOLDOWN_SEC)
        time.sleep(COOLDOWN_SEC)

        # Stop resource polling
        collect_stage.stop_resource_polling()
        t_end = time.time()

        # Get daemon status before stopping
        daemon_status = daemon_stage.get_status() or {}

        # Build result
        k6m = workload_ctx.workload.model_dump() if workload_ctx.workload else {}
        result = ExperimentResult(
            scenario=scenario,
            run_id=run_id,
            timestamp=datetime.now().isoformat(),
            p50_latency_ms=k6m.get("p50_latency_ms", 0),
            p95_latency_ms=k6m.get("p95_latency_ms", 0),
            p99_latency_ms=k6m.get("p99_latency_ms", 0),
            error_rate=k6m.get("error_rate", 0),
            throughput_rps=k6m.get("throughput_rps", 0),
            total_requests=k6m.get("total_requests", 0),
            t_start=t_start,
            t_end=t_end,
            duration_sec=max(1, int(t_end - t_start)),
        )

        # Set result on context for collect stage
        collect_ctx = _make_ctx(config, scenario, run_id, output_dir)
        collect_ctx.result = result
        collect_stage.execute(collect_ctx)

        # Update result from collect stage
        if collect_ctx.result:
            result = collect_ctx.result

        # Set daemon metrics
        result.maintain_count = daemon_status.get("maintain_count", 0)
        result.scale_out_count = daemon_status.get("scale_out_count", 0)
        result.predictive_count = daemon_status.get("predictive_count", 0)
        result.optimize_cost_count = daemon_status.get("optimize_cost_count", 0)

        # Save result
        with open(run_dir / "result.json", "w") as f:
            json.dump(result.model_dump(), f, indent=2)

        logger.info("run_complete", scenario=scenario, run_id=run_id, p99=result.p99_latency_ms)
        return result

    finally:
        collect_stage.stop_resource_polling()
        daemon_stage.stop_daemon()


def _git_commit_hash() -> str:
    import subprocess

    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.stdout.strip()
    except Exception:
        return "unknown"


if __name__ == "__main__":
    app()
