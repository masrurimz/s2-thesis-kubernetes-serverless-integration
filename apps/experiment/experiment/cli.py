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
    from rich.console import Console

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
    controller: str = typer.Option("v3", help="Controller version for S3/S4"),
    workload: str = typer.Option("clarknet", help="Workload trace: clarknet|spike|periodic|ramp|stationary"),
    calibration: Optional[str] = typer.Option(None, help="Path to CalibrationConfig JSON overrides"),
) -> None:
    """Run experiment phase through the full pipeline."""
    from rich.console import Console
    from rich.panel import Panel

    # Set env early so all subprocess children (daemon) inherit it
    if calibration:
        os.environ["CALIBRATION_OVERRIDE"] = calibration

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
    os.environ["WORKLOAD"] = workload

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


@app.command(name="calibrate")
def calibrate(
    scenarios: str = typer.Option("s1-k8s-only,s3-hybrid-reactive", help="Comma-separated scenarios to test"),
    rps_levels: str = typer.Option("50,100,150,200", help="Comma-separated RPS levels to test"),
    duration: int = typer.Option(180, help="Duration per test in seconds"),
    output: Optional[str] = typer.Option(None, help="Output file for calibration results"),
) -> None:
    """Workload calibration: find the Goldilocks RPS for experiments."""
    from rich.console import Console

    from experiment.calibration import analyze_results, run_full_calibration

    console = Console()
    scenario_list = [s.strip() for s in scenarios.split(",")]
    rps_list = [int(r.strip()) for r in rps_levels.split(",")]

    console.print("[bold cyan]Workload Calibration[/bold cyan]")
    console.print(f"Scenarios: {scenario_list}  |  RPS: {rps_list}  |  Duration: {duration}s")

    results = run_full_calibration(scenario_list, rps_list, duration)
    analysis = analyze_results(results)

    out_path = Path(output) if output else Path("results/calibration/analysis.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(analysis, f, indent=2)

    for r in results:
        console.print(
            f"  {r.scenario} @ {r.rps} RPS: p99={r.p99_ms:.1f}ms "
            f"err={r.error_rate:.2%} [{r.stress_level}]"
            f" {'✅' if r.recommended else '❌'}"
        )
    console.print(f"\n[green]Goldilocks load: {analysis['goldilocks_rps']} RPS[/green]")
    console.print(f"[dim]Results: {out_path}[/dim]")


@app.command(name="dynamic")
def dynamic(
    runs: int = typer.Option(3, help="Replicates per scenario"),
    scenarios: str = typer.Option("s3-hybrid-reactive,s4-hybrid-predictive", help="Comma-separated scenarios"),
    cooldown: int = typer.Option(30, help="Cooldown seconds between runs"),
    manage_daemon: bool = typer.Option(
        True, "--manage-daemon/--no-manage-daemon", help="Start/stop routing daemon per run"
    ),
    results_dir: Optional[str] = typer.Option(None, help="Override results directory"),
    dry_run: bool = typer.Option(False, help="Show schedule only"),
) -> None:
    """Phase C dynamic ramp/burst workload experiment (S3 vs S4)."""
    import random as _random

    from rich.console import Console

    from experiment.dynamic import RESULTS_BASE, K6_SCRIPT, run_dynamic_experiment

    console = Console()
    scenario_list = [s.strip() for s in scenarios.split(",")]

    if dry_run:
        schedule = [(s, r) for s in scenario_list for r in range(1, runs + 1)]
        _random.shuffle(schedule)
        console.print("[bold cyan]Phase C: Dynamic Workload (DRY RUN)[/bold cyan]")
        console.print(f"Scenarios: {scenario_list}  |  Runs: {runs}  |  k6: {K6_SCRIPT}")
        for i, (s, r) in enumerate(schedule, 1):
            console.print(f"  {i}. {s} run {r}")
        return

    rd = Path(results_dir) if results_dir else None
    results = run_dynamic_experiment(
        scenarios=scenario_list,
        num_runs=runs,
        cooldown_sec=cooldown,
        manage_daemon=manage_daemon,
        results_dir=rd,
    )
    console.print(f"\n[green]✅ {len(results)} runs completed[/green]")
    final_dir = rd or (RESULTS_BASE / f"{datetime.now().strftime('%Y-%m-%d')}_dynamic-workload")
    console.print(f"[dim]Results: {final_dir}[/dim]")
    for s in scenario_list:
        total = sum(r.predictive_count for r in results if r.scenario == s)
        console.print(f"  {s}: PREDICTIVE={total}")


@app.command(name="validate-realtime")
def validate_realtime(
    results_dir: Optional[str] = typer.Option(None, help="Override results directory"),
) -> None:
    """Real-time hypothesis validation (H3 GRU check; H1/H2 pending live runs)."""
    from rich.console import Console
    from rich.panel import Panel

    from experiment.validation import run_realtime_validation

    console = Console()
    console.print(Panel.fit("[bold]Real-Time Hypothesis Validation[/bold]", border_style="cyan"))

    rd = Path(results_dir) if results_dir else None
    results = run_realtime_validation(results_dir=rd)

    h3 = results["h3"]
    console.print(f"\n[bold]H3 (GRU prediction adequacy):[/bold] {'✅ VALIDATED' if h3['proven'] else '❌ FAILED'}")
    console.print(f"Confidence: {h3['confidence']}")
    console.print(f"Evidence: {json.dumps(h3['evidence'], indent=2)}")
    for lim in h3.get("limitations", []):
        console.print(f"  [dim]- {lim}[/dim]")

    console.print("\n[yellow]H1/H2: pending live experiments[/yellow]")
    console.print(f"[dim]Report: {results['report_path']}[/dim]")


@app.command(name="trace-replay")
def trace_replay(
    duration_min: int = typer.Option(20, help="Replay duration in minutes"),
    dry_run: bool = typer.Option(False, help="Print stages without writing files"),
    window_start_idx: int = typer.Option(14470, help="Start index in 30s-bucketed data"),
    scaling_factor: float = typer.Option(33.0, help="RPS scaling factor g"),
    dataset: str = typer.Option("clarknet", help="Dataset: clarknet|calgary"),
) -> None:
    """Generate k6 trace-replay artifacts (stages JSON + JS) from ClarkNet parquet."""
    from rich.console import Console

    from experiment.trace_replay import generate_trace_replay

    console = Console()
    console.print(f"[bold cyan]Trace-Replay Generation[/bold cyan]  dataset={dataset} duration={duration_min}min")
    rc = generate_trace_replay(
        dataset=dataset,
        window_start=window_start_idx,
        scale_factor=scaling_factor,
        duration_min=duration_min,
        dry_run=dry_run,
    )
    if rc != 0:
        raise typer.Exit(rc)


@app.command(name="paired-run")
def paired_run(
    pairs: int = typer.Option(5, help="Number of counterbalanced S3/S4 pairs"),
    duration: int = typer.Option(300, help="Workload duration in seconds per run"),
    seed: int = typer.Option(42, help="Random seed for pair ordering"),
    workload: str = typer.Option("clarknet", help="Workload trace"),
    controller: str = typer.Option("v3", help="Controller version"),
    calibration: Optional[str] = typer.Option(None, help="Path to CalibrationConfig JSON overrides"),
    output: Optional[str] = typer.Option(None, help="Output directory"),
    dry_run: bool = typer.Option(False, help="Print schedule without running"),
) -> None:
    """Run paired S3/S4 experiment for H2 decision (counterbalanced design).

    Each pair runs S3 and S4 back-to-back under identical conditions.
    Pair order alternates (S3→S4, S4→S3) to control for temporal drift.
    The primary endpoint is paired p99 latency difference (S4 < S3).
    """
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table

    from shared.progress import countdown

    console = Console()

    if calibration:
        os.environ["CALIBRATION_OVERRIDE"] = calibration

    datestamp = datetime.now().strftime("%Y-%m-%d")
    output_dir = output or f"results/experiments/phase-b/{datestamp}_paired-h2"

    os.environ["CONTROLLER_VERSION"] = controller
    os.environ["WORKLOAD"] = workload

    # Build counterbalanced schedule
    rng = random.Random(seed)
    pair_order = []
    for i in range(pairs):
        if i % 2 == 0:
            pair_order.append((i + 1, "s3-hybrid-reactive", "s4-hybrid-predictive"))
        else:
            pair_order.append((i + 1, "s4-hybrid-predictive", "s3-hybrid-reactive"))
    rng.shuffle(pair_order)

    console.print(
        Panel.fit(
            f"[bold]Paired H2 Experiment[/bold]\n"
            f"Pairs: {pairs}  |  Workload: {workload}\n"
            f"Controller: {controller}  |  Seed: {seed}\n"
            f"Output: {output_dir}",
            border_style="cyan",
        )
    )

    if dry_run:
        table = Table(show_header=True, header_style="bold")
        table.add_column("Pair", justify="right")
        table.add_column("First")
        table.add_column("Second")
        for pid, first, second in pair_order:
            table.add_row(str(pid), first, second)
        console.print(table)
        return

    config = ExperimentConfig(
        phase="experiments",
        runs=1,
        duration_sec=duration,
        seed=seed,
    )

    # Collect paired results
    s3_results: list[ExperimentResult] = []
    s4_results: list[ExperimentResult] = []
    pair_ids: list[str] = []

    for idx, (pair_id, first_scenario, second_scenario) in enumerate(pair_order):
        console.print(f"\n[bold cyan]Pair {pair_id}/{pairs}[/bold cyan]")
        pid = f"pair_{pair_id:03d}"

        # Run first scenario
        console.print(f"  [dim]Running {first_scenario}...[/dim]")
        r1 = _run_single(first_scenario, pair_id, idx * 2, config, output_dir, console=console)
        if r1 is None:
            console.print(f"  [red]First scenario {first_scenario} failed[/red]")
            continue

        if idx < len(pair_order) - 1:
            with countdown(console, INTER_RUN_PAUSE_SEC, "Inter-run pause"):
                pass

        # Run second scenario
        console.print(f"  [dim]Running {second_scenario}...[/dim]")
        r2 = _run_single(second_scenario, pair_id, idx * 2 + 1, config, output_dir, console=console)
        if r2 is None:
            console.print(f"  [red]Second scenario {second_scenario} failed[/red]")
            continue

        # Record pair
        if first_scenario == "s3-hybrid-reactive":
            s3_results.append(r1)
            s4_results.append(r2)
        else:
            s3_results.append(r2)
            s4_results.append(r1)
        pair_ids.append(pid)

        console.print(
            f"  [green]Pair {pair_id} complete: "
            f"S3 p99={s3_results[-1].p99_latency_ms:.0f}ms, "
            f"S4 p99={s4_results[-1].p99_latency_ms:.0f}ms[/green]"
        )

        if idx < len(pair_order) - 1:
            with countdown(console, INTER_RUN_PAUSE_SEC, "Inter-pair pause"):
                pass

    # Paired statistical analysis
    n_valid = len(pair_ids)
    console.print(f"\n[bold green]✅ {n_valid} valid pairs completed[/bold green]")

    if n_valid < 3:
        console.print("[yellow]Too few valid pairs for statistical analysis (need ≥3)[/yellow]")
        return

    from analysis.comparison import run_paired_comparison, apply_holm_paired

    # Primary endpoint: paired p99 latency
    s3_p99 = [r.p99_latency_ms for r in s3_results]
    s4_p99 = [r.p99_latency_ms for r in s4_results]
    primary = run_paired_comparison(s3_p99, s4_p99, metric="p99_latency_ms", pair_ids=pair_ids, label="H2-primary")

    # Secondary endpoints
    secondaries = []
    for metric_name, attr in [
        ("p95_latency_ms", "p95_latency_ms"),
        ("slo_violations_k6", "slo_violations_k6"),
        ("throughput_rps", "throughput_rps"),
        ("error_rate", "error_rate"),
    ]:
        s3_vals = [getattr(r, attr) for r in s3_results]
        s4_vals = [getattr(r, attr) for r in s4_results]
        secondaries.append(
            run_paired_comparison(
                s3_vals, s4_vals, metric=metric_name, pair_ids=pair_ids, label=f"H2-secondary-{metric_name}"
            )
        )

    apply_holm_paired(secondaries)

    # Report
    console.print("\n[bold cyan]H2 Paired Analysis[/bold cyan]")
    console.print("\n  [bold]Primary: p99 latency[/bold]")
    console.print(f"    S3 mean: {primary.baseline_mean:.1f}ms  |  S4 mean: {primary.comparison_mean:.1f}ms")
    console.print(f"    Mean diff: {primary.mean_difference:+.1f}ms")
    console.print(f"    95% CI: [{primary.paired_ci_lower:+.1f}, {primary.paired_ci_upper:+.1f}]")
    console.print(f"    Permutation p: {primary.permutation_p_value:.4f}")
    console.print(f"    Cohen's d (paired): {primary.cohens_d_paired:.3f} ({primary.effect_size_interpretation})")
    verdict = "✅ H2 SUPPORTED" if primary.h2_supported else "⚠️ H2 NOT SUPPORTED"
    console.print(f"    Verdict: {verdict}")

    console.print("\n  [bold]Secondary endpoints (Holm-corrected)[/bold]")
    for s in secondaries:
        sig = "✅" if s.permutation_p_corrected < 0.05 else "⚠️"
        console.print(f"    {s.metric}: diff={s.mean_difference:+.2f}, p={s.permutation_p_corrected:.4f} {sig}")

    # Save paired analysis
    import json

    analysis_path = Path(output_dir) / "paired_analysis.json"
    analysis = {
        "primary": primary.model_dump(),
        "secondaries": [s.model_dump() for s in secondaries],
        "n_pairs": n_valid,
        "pair_ids": pair_ids,
        "s3_p99_values": s3_p99,
        "s4_p99_values": s4_p99,
        "timestamp": datetime.now().isoformat(),
    }
    analysis_path.write_text(json.dumps(analysis, indent=2, default=str))
    console.print(f"\n[dim]Paired analysis: {analysis_path}[/dim]")


@app.command(name="gru-hpo")
def gru_hpo(
    data: str = typer.Option("clarknet", help="Dataset: clarknet or calgary"),
    trials: int = typer.Option(30, help="Number of Optuna trials"),
    output_dir: str = typer.Option("results/models/gru/hpo", help="Output directory"),
    seed: int = typer.Option(42, help="Random seed"),
) -> None:
    """GRU hyperparameter optimization with temporal cross-validation.

    Expanding-window temporal CV on the first 80% of data, with a promotion
    gate comparing the best GRU against persistence and linear-trend baselines
    on the untouched final 20% holdout.
    """
    from rich.console import Console

    from experiment.tuning.gru_hpo import run_gru_hpo

    console = Console()
    console.print(f"[bold cyan]GRU HPO[/bold cyan]  data={data}  trials={trials}  seed={seed}")

    result = run_gru_hpo(
        data_source=data,
        n_trials=trials,
        output_dir=output_dir,
        seed=seed,
    )

    console.print("\n[green]✅ HPO complete[/green]")
    console.print(f"  Best trial:    #{result['best_trial']}")
    console.print(f"  Best objective: {result['best_objective']:.4f}")
    console.print(f"  Promoted:       {result['promoted_model'] or 'NONE (gate failed)'}")
    console.print(f"[dim]Results: {result['output_dir']}[/dim]")


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

    from shared.progress import (
        countdown,
        create_progress,
        elapsed_str,
        print_run_failure,
        print_run_header,
        print_run_result,
    )

    console = Console()
    schedule = [(s, r) for s in scenarios for r in range(1, config.runs + 1)]
    rng = random.Random(config.seed)
    rng.shuffle(schedule)

    results: list[ExperimentResult] = []
    run_durations: list[float] = []
    total = len(schedule)

    with create_progress(console) as progress:
        batch_task = progress.add_task("[bold]Batch[/bold]", total=total)

        for idx, (scenario, run_id) in enumerate(schedule):
            print_run_header(console, idx + 1, total, scenario, run_id)

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
                progress.advance(batch_task)
                continue

            # Full run: execute the per-run protocol
            t0 = time.time()
            result = _run_single(scenario, run_id, idx, config, output_dir, console=console)
            run_dur = time.time() - t0
            run_durations.append(run_dur)

            if result:
                results.append(result)
                print_run_result(console, result, run_dur)
            else:
                print_run_failure(console, scenario, "run failed — see logs above")

            progress.advance(batch_task)

            # Update ETA description with rolling average
            if run_durations:
                avg = sum(run_durations) / len(run_durations)
                remaining = (total - idx - 1) * avg
                progress.update(
                    batch_task,
                    description=f"[bold]Batch[/bold] • ~{elapsed_str(remaining)} remaining",
                )

            # Inter-run pause
            if idx < total - 1:
                with countdown(console, INTER_RUN_PAUSE_SEC, "Inter-run pause"):
                    pass

    return results


def _run_single(
    scenario: str,
    run_id: int,
    run_order_idx: int,
    config: ExperimentConfig,
    output_dir: str,
    *,
    console: "Console | None" = None,
) -> Optional[ExperimentResult]:
    """Execute a single experiment run with full protocol."""
    from datetime import datetime

    from rich.console import Console

    from shared.progress import countdown, run_phase

    if console is None:
        console = Console()

    from shared.models.experiment import ExperimentResult, RunManifest
    from experiment.stages.reset import ResetStage
    from experiment.stages.daemon import DaemonStage
    from experiment.stages.workload import WorkloadStage
    from experiment.stages.collect import CollectStage
    from infra.cluster.k3d.autoscaler import K3dAutoscalerAdapter

    run_dir = Path(output_dir) / f"{scenario}_run{run_id}"
    run_dir.mkdir(parents=True, exist_ok=True)

    logger.info("run_start", scenario=scenario, run_id=run_id, order=run_order_idx)
    import shutil

    _k3d_path = shutil.which("k3d") or os.environ.get("K3D_PATH", "")
    _k3s_image = os.environ.get("K3S_IMAGE", "rancher/k3s:v1.28.5-k3s1")
    _cluster_name = os.environ.get("K3D_CLUSTER_NAME", "thesis-hybrid")
    provisioner = K3dAutoscalerAdapter(
        cluster_name=_cluster_name,
        k3d_path=_k3d_path,
        kubectl_path=os.environ.get("KUBECTL_PATH", "kubectl"),
        k3s_image=_k3s_image,
        min_nodes=0,
        max_nodes=2,
        provision_delay_min_sec=45,
        provision_delay_max_sec=120,
        node_memory="1g",
    )
    resetter = ResetStage(provisioner=provisioner)
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
        with countdown(console, WARMUP_SEC, "Warmup"):
            pass

        # Record t_start and begin resource polling
        t_start = time.time()
        collect_stage.start_resource_polling()
        if scenario != "s2-serverless-only":
            provisioner.clear_log()
            provisioner.start_background()
        # (C.2) Execute k6 trace replay
        workload_ctx = _make_ctx(config, scenario, run_id, output_dir)
        with run_phase(console, "k6 workload") as phase:
            phase_task = phase.tasks[0].id if phase.tasks else None

            def _on_k6_progress(line: str) -> None:
                # k6 emits lines like: running (0m30.0s), 0/100 VUs, 234 complete, 0 failed
                if "running" in line and phase_task is not None:
                    phase.update(phase_task, description=f"[cyan]k6: {line}[/cyan]")

            workload_stage._run(workload_ctx, on_progress=_on_k6_progress)

        # (C.3) Post-k6 cooldown
        logger.info("cooldown_start", seconds=COOLDOWN_SEC)
        with countdown(console, COOLDOWN_SEC, "Cooldown"):
            pass

        # Stop resource polling
        collect_stage.stop_resource_polling()
        if scenario != "s2-serverless-only":
            provisioner.stop()
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
            slo_violations_k6=k6m.get("slo_violations", 0),
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
        # Set node provisioning data
        if scenario != "s2-serverless-only":
            prov_log = provisioner.get_log()
            prov_success_events = {"node_created", "node_provisioned"}
            result.nodes_provisioned = sum(1 for _, et, _ in prov_log if et in prov_success_events)
            result.total_provision_events = len(prov_log)
            first_pending = next((ts for ts, et, _ in prov_log if et == "pending_detected"), None)
            first_created = next((ts for ts, et, _ in prov_log if et in prov_success_events), None)
            if first_pending and first_created:
                result.first_provision_delay_sec = first_created - first_pending
            with open(run_dir / "provision_events.json", "w") as f:
                json.dump([{"ts": ts, "event": et, "data": d} for ts, et, d in prov_log], f, indent=2)
            result.provision_log_path = str(run_dir / "provision_events.json")
        result.predictive_count = daemon_status.get("predictive_count", 0)
        result.optimize_cost_count = daemon_status.get("optimize_cost_count", 0)

        # Save result
        with open(run_dir / "result.json", "w") as f:
            json.dump(result.model_dump(), f, indent=2)

        logger.info("run_complete", scenario=scenario, run_id=run_id, p99=result.p99_latency_ms)
        return result

    finally:
        collect_stage.stop_resource_polling()
        provisioner.stop()
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
