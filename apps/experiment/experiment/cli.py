from __future__ import annotations

"""Experiment orchestration CLI.

Provides typer commands for running, analyzing, and validating experiments.
Entry point: thesis-experiment (via pyproject.toml [project.scripts]).
"""

import json
import os
import random
import shutil
import tempfile
import time
from dataclasses import replace
from datetime import date, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Optional

import typer
import structlog

from shared.models.experiment import ExperimentConfig, ExperimentResult

from experiment.profiles import get_profile, profile_names

if TYPE_CHECKING:
    from rich.console import Console

    from experiment.conditions import RunConditions
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


def _bundle_dir(
    base_dir: str,
    slug: str,
    force: bool,
) -> str:
    """Resolve a unique experiment bundle directory.

    Default names are timestamped (YYYY-MM-DD_slug_HHMMSS) so re-triggering the
    same command can never collide with an earlier bundle. Explicit --output
    paths are honoured but refused if they already exist, unless --force is
    passed (which deletes the existing bundle first).
    """
    now = datetime.now()
    candidate = Path(base_dir) / f"{now.strftime('%Y-%m-%d')}_{slug}_{now.strftime('%H%M%S')}"
    if force and candidate.exists():
        shutil.rmtree(candidate)
    if candidate.exists():
        console = Console()
        console.print(
            f"[red]Bundle directory already exists: {candidate}[/red]\n"
            f"[red]Re-running would mix runs from two invocations. "
            f"Pass --force to delete it first, or choose a different --output.[/red]"
        )
        raise typer.Exit(1)
    return str(candidate)


def _write_bundle_metadata(output_dir: str, scenarios: list[str], runs: int, status: str) -> None:
    """Write bundle meta.yaml + a bundle-level events.jsonl (schema v2)."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    meta = out / "meta.yaml"
    if not meta.exists():
        meta.write_text(
            f"bundle_schema_version: 2\n"
            f"name: {out.name}\n"
            f"date: {datetime.now().strftime('%Y-%m-%d')}\n"
            f"scenarios: {scenarios}\n"
            f"runs: {runs}\n"
            f"status: {status}\n"
        )
    from shared.storage.journal import ExperimentJournal

    journal = ExperimentJournal(
        out / "events.jsonl",
        experiment_id=out.name,
        bundle_path=str(out),
        git_commit=_git_commit_hash(),
    )
    journal.record(
        journal.new_event(
            "bundle_created",
            payload={"scenarios": scenarios, "runs": runs, "status": status},
        )
    )


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
    force: bool = typer.Option(False, "--force", help="Delete an existing bundle dir before running"),
    no_preflight: bool = typer.Option(False, "--no-preflight", help="Skip preflight checks before experiments"),
    agents: int = typer.Option(1, help="Static agent nodes the testbed is converged to before each run"),
    allow_loaded_host: bool = typer.Option(
        False,
        "--allow-loaded-host",
        help="Take measurements on an oversubscribed host, recording it",
    ),
) -> None:
    """Run experiment phase through the full pipeline.

    Conditions the testbed before every run, the same way `reproduce` does: the
    node count is converged, residue cleared, and the sanity checks applied. A run
    only starts when they hold.
    """
    from rich.console import Console
    from rich.panel import Panel

    # Set env early so all subprocess children (daemon) inherit it
    if calibration:
        os.environ["CALIBRATION_OVERRIDE"] = calibration

    console = Console()

    from experiment.conditions import RunConditions

    scenario_list = [s.strip() for s in scenarios.split(",")] if scenarios else list(SCENARIOS)
    run_conditions = RunConditions.for_scenarios(
        scenario_list,
        agents=agents,
        cluster=os.environ.get("K3D_CLUSTER_NAME", "thesis-hybrid"),
    )
    if allow_loaded_host:
        run_conditions = replace(run_conditions, check_host_load=False)

    output_dir = output or _bundle_dir("results/experiments/phase-b", "clarknet-replay", force)
    if output and Path(output).exists() and not force:
        console.print(f"[red]Output bundle already exists: {output}. Pass --force to delete it first.[/red]")
        raise typer.Exit(1)
    if output and force and Path(output).exists():
        shutil.rmtree(output)

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

    # Preflight runs before experiments by default (and as --phase preflight);
    # --no-preflight opts out of the automatic gate only.
    if phase == "preflight" or (phase in ("experiments", "full") and not no_preflight):
        console.print("\n[bold cyan]Preflight Checks[/bold cyan]")
        from experiment.stages.preflight import PreflightStage

        stage = PreflightStage(s4_planned=any(s.startswith("s4") for s in scenario_list))
        # Preflight-only invocations must not create result-bundle dirs.
        ctx_out = output_dir if phase in ("experiments", "full") else tempfile.mkdtemp(prefix="thesis-preflight-")
        ctx_result = stage.execute(_make_ctx(config, scenario_list[0], 0, ctx_out))
        if not ctx_result.success:
            console.print(f"[red]Preflight failed: {ctx_result.error}[/red]")
            if phase != "preflight":
                raise typer.Exit(1)
        else:
            console.print("[green]All preflight checks passed[/green]")

    if phase in ("experiments", "full"):
        if not dry_run:
            _write_bundle_metadata(output_dir, scenario_list, runs, status="in_progress")
        console.print(f"\n[bold cyan]Running {runs * len(scenario_list)} experiments...[/bold cyan]")
        results = _run_replicated(config, scenario_list, output_dir, dry_run, conditions=run_conditions)
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
def preflight(
    profile: Optional[str] = typer.Option(
        None, "--profile", help=f"Check the conditions this profile declares: {', '.join(profile_names())}"
    ),
    agents: int = typer.Option(1, help="Static agent nodes to converge to when no profile is given"),
    converge: bool = typer.Option(
        True,
        "--converge/--no-converge",
        help="Converge the testbed and clear residue, or only report",
    ),
) -> None:
    """Validate the conditions an experiment will run under.

    The same battery the runner applies before every run, so a person can see the
    verdict before committing hours to it: testbed converged and cleared, nodes
    ready, both arms serving, the prediction server present when the design needs
    it, and the host quiet enough to measure on.
    """
    from rich.console import Console
    from rich.table import Table

    from experiment.conditions import ConditionsUnmet, RunConditions, apply as apply_conditions

    console = Console()

    if profile is not None:
        selected = get_profile(profile)
        conditions = RunConditions(
            agents=selected.k8s_agents,
            needs_prediction_server=selected.prediction_server,
            cluster=os.environ.get("K3D_CLUSTER_NAME", "thesis-hybrid"),
        )
    else:
        conditions = RunConditions(agents=agents, cluster=os.environ.get("K3D_CLUSTER_NAME", "thesis-hybrid"))

    conditions = replace(conditions, converge=converge)

    try:
        report = apply_conditions(conditions, scenario=profile or "", console=console)
    except ConditionsUnmet as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1) from exc

    table = Table(show_header=True, header_style="bold")
    table.add_column("Check")
    table.add_column("Status", justify="center")
    for name, ok in report["checks"].items():
        table.add_row(name, "[green]pass[/green]" if ok else "[red]fail[/red]")
    console.print(table)

    load = report["load"]
    console.print(
        f"nodes: {report['nodes']} | load {load['load1']:.1f} on {load['cores']:.0f} cores ({load['ratio']:.2f}x)"
    )
    for note in report["notes"]:
        console.print(f"  [yellow]note:[/yellow] {note}")
    console.print("\n[green]Every condition holds[/green]")


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
    force: bool = typer.Option(False, "--force", help="Delete an existing bundle dir before running"),
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

    rd = results_dir or _bundle_dir(str(RESULTS_BASE), "dynamic-workload", force)
    results = run_dynamic_experiment(
        scenarios=scenario_list,
        num_runs=runs,
        cooldown_sec=cooldown,
        manage_daemon=manage_daemon,
        results_dir=Path(rd),
    )
    console.print(f"\n[green]✅ {len(results)} runs completed[/green]")
    console.print(f"[dim]Results: {rd}[/dim]")
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


@app.command()
def summary(
    bundle: str = typer.Argument(..., help="Bundle directory containing per-run result.json files"),
    print_report: bool = typer.Option(True, "--print/--no-print", help="Print the summary after writing it"),
) -> None:
    """Write SUMMARY.md for a bundle: what ran, the headline table, the pair verdict."""
    from rich.console import Console

    from experiment.summary import write_summary

    console = Console()
    path = write_summary(Path(bundle))
    console.print(f"[green]Summary written: {path}[/green]")
    if print_report:
        console.print(path.read_text())


@app.command()
def reproduce(
    profile: str = typer.Option(..., "--profile", help=f"Experiment profile: {', '.join(profile_names())}"),
    pairs: Optional[int] = typer.Option(None, help="Override the profile's pair count"),
    runs: Optional[int] = typer.Option(None, help="Override the profile's run count"),
    duration: int = typer.Option(300, help="Workload duration in seconds per run"),
    seed: int = typer.Option(42, help="Random seed for schedule and ordering"),
    output: Optional[str] = typer.Option(None, help="Bundle directory (default: dated name from the profile)"),
    controller: str = typer.Option("v3", help="Controller version for S3/S4"),
    workload: str = typer.Option("clarknet", help="Workload trace"),
    resume: bool = typer.Option(True, "--resume/--no-resume", help="Continue an existing bundle instead of refusing"),
    force: bool = typer.Option(False, "--force", help="Delete an existing bundle before running"),
    dry_run: bool = typer.Option(False, help="Report what would happen without changing anything"),
    fresh_stack: bool = typer.Option(
        False,
        "--fresh-stack",
        help="Rebuild both clusters and redeploy the app before running",
    ),
) -> None:
    """Run an experiment under a named profile, end to end.

    Converges the testbed to the profile's shape, ensures the prediction server is
    the right artifact on CPU, runs the profile's design, writes the analysis and a
    human-readable summary, and exits nonzero when a run or pair failed its gate.

    Idempotent: a bundle that already holds every requested pair or run is left
    alone and only re-analysed, and a partial bundle continues from where it stopped
    rather than starting over.

    The testbed is re-converged before every run, and --fresh-stack additionally
    tears both clusters down and redeploys the application first, so a headline
    experiment does not inherit the nodes, pods, and objects earlier ones left.
    """
    from rich.console import Console
    from rich.panel import Panel

    console = Console()

    selected = get_profile(profile)
    pair_count = pairs if pairs is not None else selected.pairs
    run_count = runs if runs is not None else selected.runs

    console.print(
        Panel.fit(
            f"[bold]Reproduce: {selected.name}[/bold]\n"
            f"{selected.description}\n\n"
            f"Scenarios: {', '.join(selected.scenarios)}\n"
            f"{'Pairs: ' + str(pair_count) if pair_count else 'Runs per scenario: ' + str(run_count)}\n"
            f"Static agent nodes: {selected.k8s_agents}  |  Prediction server: {selected.prediction_server}\n"
            f"Controller: {controller}  |  Workload: {workload}  |  Seed: {seed}",
            border_style="cyan",
        )
    )

    suffix = f"{pair_count}p" if pair_count else f"{run_count}r"
    output_dir = output or f"results/experiments/phase-b/{date.today().isoformat()}_{selected.name}-{suffix}"
    bundle_path = Path(output_dir)

    if force and bundle_path.exists():
        shutil.rmtree(bundle_path)
    if bundle_path.exists() and not resume:
        console.print(
            f"[red]Bundle already exists: {output_dir}. Pass --resume to continue it or --force to replace it.[/red]"
        )
        raise typer.Exit(1)

    existing_pairs = _completed_pairs(bundle_path) if pair_count else {}
    existing_runs: frozenset[tuple[str, int]] = _completed_runs(bundle_path) if not pair_count else frozenset()

    if dry_run:
        if pair_count:
            console.print(f"Would run {pair_count - len(existing_pairs)} of {pair_count} pairs into {output_dir}")
        else:
            total = len(selected.scenarios) * run_count
            console.print(f"Would run {total - len(existing_runs)} of {total} runs into {output_dir}")
        for key, value in selected.routing_env.items():
            console.print(f"  daemon environment: {key}={value}")
        return

    from experiment.conditions import RunConditions, apply as apply_conditions
    from infra.readiness import rebuild_testbed

    cluster = os.environ.get("K3D_CLUSTER_NAME", "thesis-hybrid")
    run_conditions = RunConditions(
        agents=selected.k8s_agents,
        needs_prediction_server=selected.prediction_server,
        cluster=cluster,
    )
    stack_rebuild: dict | None = None

    if fresh_stack:
        console.print("[cyan]Rebuilding the testbed...[/cyan]")
        rebuilt = rebuild_testbed(agents=selected.k8s_agents)
        for action in rebuilt["actions"]:
            console.print(f"  [yellow]{action}[/yellow]")
        console.print(f"[cyan]Testbed rebuilt:[/cyan] {rebuilt['summary']}")
        if not rebuilt["ready"]:
            console.print("[red]Rebuilt testbed is not ready; not starting the experiment.[/red]")
            raise typer.Exit(1)
        stack_rebuild = {"actions": rebuilt["actions"], "summary": rebuilt["summary"]}

    try:
        conditions_report = apply_conditions(run_conditions, scenario="bundle start", console=console)
    except Exception as exc:  # noqa: BLE001 — the report is the message
        console.print(f"[red]Conditions unmet before the bundle: {exc}[/red]")
        raise typer.Exit(1) from exc

    testbed = {"nodes": conditions_report["nodes"], "actions": conditions_report["actions"]}
    console.print(f"[cyan]Testbed:[/cyan] {testbed['nodes']} | actions: {testbed['actions'] or 'none needed'}")
    console.print(
        f"[cyan]Host:[/cyan] load {conditions_report['load']['load1']:.1f} on "
        f"{conditions_report['load']['cores']:.0f} cores ({conditions_report['load']['ratio']:.2f}x)"
    )

    server: dict = {"status": "not required"}
    if selected.prediction_server:
        from experiment.services import ensure_prediction_server

        server = ensure_prediction_server()
        console.print(f"[cyan]Prediction server:[/cyan] {server['status']} on port {server.get('port')}")
        if server["status"] == "unavailable":
            console.print(f"[red]Prediction server unavailable: {server.get('reason')}[/red]")
            console.print("[red]S4 runs would be invalid, so the experiment is not started.[/red]")
            raise typer.Exit(1)

    os.environ["CONTROLLER_VERSION"] = controller
    os.environ["WORKLOAD"] = workload
    os.environ.update(selected.routing_env)

    config = ExperimentConfig(phase="experiments", runs=run_count or 1, duration_sec=duration, seed=seed)
    from shared.storage.journal import ExperimentJournal

    exit_code = 0

    if pair_count:
        bundle_journal = ExperimentJournal(
            bundle_path / "events.jsonl",
            experiment_id=bundle_path.name,
            bundle_path=str(bundle_path),
            git_commit=_git_commit_hash(),
        )
        _write_bundle_metadata(output_dir, list(selected.scenarios), pair_count * 2, status="in_progress")
        bundle_journal.record(
            bundle_journal.new_event(
                "profile_applied",
                payload={
                    "profile": selected.as_dict(),
                    "testbed": testbed,
                    "prediction_server": server,
                    "stack_rebuild": stack_rebuild,
                    "conditions": conditions_report,
                },
            )
        )

        missing = pair_count - len(existing_pairs)
        if missing > 0:
            console.print(f"\n[bold cyan]Running {missing} pair(s)[/bold cyan]")
            _run_pairs(
                output_dir,
                pairs=missing,
                start_pair_id=max(existing_pairs, default=0) + 1,
                config=config,
                console=console,
                bundle_journal=bundle_journal,
                conditions=run_conditions,
            )

        s3_results, s4_results, pair_ids = _collect_pairs(bundle_path)
        console.print(f"\n[bold green]{len(pair_ids)} valid pair(s) in the bundle[/bold green]")
        if len(pair_ids) < pair_count:
            _write_insufficient_pairs(output_dir, len(pair_ids), pair_count, 0)
            console.print(f"[red]Insufficient valid pairs: {len(pair_ids)}/{pair_count}[/red]")
            exit_code = 1
        else:
            _write_paired_analysis(output_dir, s3_results, s4_results, pair_ids, console)
    else:
        _write_bundle_metadata(output_dir, list(selected.scenarios), run_count, status="in_progress")
        missing = len(selected.scenarios) * run_count - len(existing_runs)
        if missing > 0:
            console.print(f"\n[bold cyan]Running {missing} of {len(selected.scenarios) * run_count} runs[/bold cyan]")
            _run_replicated(
                config,
                list(selected.scenarios),
                output_dir,
                dry_run=False,
                skip=existing_runs,
                conditions=run_conditions,
            )
        else:
            console.print("\n[green]Every requested run is already present[/green]")

        from experiment.stages.analyze import AnalyzeStage
        from experiment.stages.report import ReportStage

        all_results = _load_run_results(bundle_path)
        analyzer = AnalyzeStage()
        clean, excluded, comparisons = analyzer.analyze_batch(all_results)
        report_stage = ReportStage()
        analysis_set = [r for r in clean if r.stress_validity_passed or r.scenario == "s2-serverless-only"]
        (bundle_path / "report.md").write_text(report_stage.generate_report(clean, analysis_set, excluded, comparisons))
        if excluded:
            exit_code = 1

    from experiment.summary import write_summary

    summary_path = write_summary(bundle_path)
    console.print(f"\n[green]Summary: {summary_path}[/green]")

    status = "completed" if not exit_code else "invalid"
    _write_bundle_metadata(
        output_dir,
        list(selected.scenarios),
        pair_count * 2 if pair_count else run_count,
        status=status,
    )

    if exit_code:
        raise typer.Exit(code=exit_code)


def _load_result(run_dir: Path) -> Optional[ExperimentResult]:
    path = run_dir / "result.json"
    if not path.exists():
        return None
    try:
        return ExperimentResult(**json.loads(path.read_text()))
    except Exception:
        return None


def _load_run_results(bundle_path: Path) -> list[ExperimentResult]:
    results = []
    for run_dir in sorted(p for p in bundle_path.glob("*_run*") if p.is_dir()):
        result = _load_result(run_dir)
        if result is not None:
            results.append(result)
    return results


def _completed_runs(bundle_path: Path) -> frozenset[tuple[str, int]]:
    done = set()
    for result in _load_run_results(bundle_path):
        if result.run_validity_passed:
            done.add((result.scenario, result.run_id))
    return frozenset(done)


def _collect_pairs(bundle_path: Path) -> tuple[list, list, list[str]]:
    """Pairs from disk: both runs valid and the S4 arm fully delivered."""
    by_scenario: dict[str, dict[int, ExperimentResult]] = {}
    for result in _load_run_results(bundle_path):
        by_scenario.setdefault(result.scenario, {})[result.run_id] = result

    s3 = by_scenario.get("s3-hybrid-reactive", {})
    s4 = by_scenario.get("s4-hybrid-predictive", {})
    paired: list[tuple[int, ExperimentResult, ExperimentResult]] = []
    for run_id, s4_result in s4.items():
        s3_result = s3.get(run_id)
        if s3_result is None:
            continue
        delivered = s4_result.treatment_fidelity is not None and s4_result.treatment_fidelity.delivered
        if s3_result.run_validity_passed and s4_result.run_validity_passed and delivered:
            paired.append((run_id, s3_result, s4_result))

    paired.sort(key=lambda item: item[0])
    return (
        [s3_result for _, s3_result, _ in paired],
        [s4_result for _, _, s4_result in paired],
        [f"pair_{run_id:03d}" for run_id, _, _ in paired],
    )


def _completed_pairs(bundle_path: Path) -> set[int]:
    _, _, pair_ids = _collect_pairs(bundle_path)
    return {int(pid.split("_")[1]) for pid in pair_ids}


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
    force: bool = typer.Option(False, "--force", help="Delete an existing bundle dir before running"),
) -> None:
    """Run paired S3/S4 experiment for H2 decision (counterbalanced design).

    Each pair runs S3 and S4 back-to-back under identical conditions.
    Pair order alternates (S3→S4, S4→S3) to control for temporal drift.
    The primary endpoint is paired p99 latency difference (S4 < S3).
    """
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table

    console = Console()

    if calibration:
        os.environ["CALIBRATION_OVERRIDE"] = calibration

    output_dir = output or _bundle_dir("results/experiments/phase-b", "paired-h2", force)
    if output and Path(output).exists() and not force:
        console.print(f"[red]Output bundle already exists: {output}. Pass --force to delete it first.[/red]")
        raise typer.Exit(1)
    if output and force and Path(output).exists():
        shutil.rmtree(output)

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

    _write_bundle_metadata(output_dir, ["s3-hybrid-reactive", "s4-hybrid-predictive"], pairs * 2, status="in_progress")

    config = ExperimentConfig(
        phase="experiments",
        runs=1,
        duration_sec=duration,
        seed=seed,
    )

    # Bundle-level lifecycle journal for governance events (pair exclusion).
    from shared.storage.journal import ExperimentJournal

    bundle_journal = ExperimentJournal(
        Path(output_dir) / "events.jsonl",
        experiment_id=Path(output_dir).name,
        bundle_path=str(output_dir),
        git_commit=_git_commit_hash(),
    )

    s3_results, s4_results, pair_ids, attempt = _run_pairs(
        output_dir,
        pairs=pairs,
        start_pair_id=1,
        config=config,
        console=console,
        bundle_journal=bundle_journal,
    )

    # Paired statistical analysis
    n_valid = len(pair_ids)
    console.print(f"\n[bold green]✅ {n_valid} valid pairs completed[/bold green]")

    if n_valid < pairs:
        _write_insufficient_pairs(output_dir, n_valid, pairs, attempt)
        console.print(
            f"[red]Insufficient valid pairs: {n_valid}/{pairs} after {attempt} attempts. "
            f"S4 treatment delivery gate blocked confounded runs.[/red]"
        )
        raise typer.Exit(code=1)

    _write_paired_analysis(output_dir, s3_results, s4_results, pair_ids, console)


def _run_pairs(
    output_dir: str,
    *,
    pairs: int,
    start_pair_id: int,
    config: ExperimentConfig,
    console: "Console",
    bundle_journal,
    conditions: "RunConditions | None" = None,
) -> tuple[list, list, list[str], int]:
    """Run counterbalanced S3/S4 pairs, excluding pairs whose treatment did not deliver.

    A pair counts only when both runs pass validity and the S4 arm delivered every
    eligible forecast, so a broken treatment surfaces as an excluded pair instead of
    a confounded comparison. Pair numbering starts at ``start_pair_id`` so a resumed
    bundle appends rather than overwrites.
    """
    from shared.progress import countdown

    s3_results: list[ExperimentResult] = []
    s4_results: list[ExperimentResult] = []
    pair_ids: list[str] = []
    max_attempts = pairs * 2
    attempt = 0

    while len(pair_ids) < pairs and attempt < max_attempts:
        attempt += 1
        pair_id = start_pair_id + len(pair_ids)
        # Counterbalanced order: alternate which scenario runs first.
        if pair_id % 2 == 1:
            first_scenario, second_scenario = "s3-hybrid-reactive", "s4-hybrid-predictive"
        else:
            first_scenario, second_scenario = "s4-hybrid-predictive", "s3-hybrid-reactive"
        pid = f"pair_{pair_id:03d}"
        console.print(
            f"\n[bold cyan]Attempt {attempt}/{max_attempts} (valid pairs: {len(pair_ids)}/{pairs})[/bold cyan]"
        )

        console.print(f"  [dim]Running {first_scenario}...[/dim]")
        r1 = _run_single(
            first_scenario, pair_id, (pair_id - 1) * 2, config, output_dir, console=console, conditions=conditions
        )
        if r1 is None:
            console.print(f"  [red]First scenario {first_scenario} failed[/red]")
            continue

        with countdown(console, INTER_RUN_PAUSE_SEC, "Inter-run pause"):
            pass

        console.print(f"  [dim]Running {second_scenario}...[/dim]")
        r2 = _run_single(
            second_scenario,
            pair_id,
            (pair_id - 1) * 2 + 1,
            config,
            output_dir,
            console=console,
            conditions=conditions,
        )
        if r2 is None:
            console.print(f"  [red]Second scenario {second_scenario} failed[/red]")
            continue

        if first_scenario == "s3-hybrid-reactive":
            s3r, s4r = r1, r2
        else:
            s3r, s4r = r2, r1

        s4_delivered = s4r.treatment_fidelity is not None and s4r.treatment_fidelity.delivered
        reasons = s4r.treatment_fidelity.reasons if s4r.treatment_fidelity else []
        if not (s3r.run_validity_passed and s4r.run_validity_passed and s4_delivered):
            console.print(
                f"  [yellow]Pair {pair_id} excluded: S4 treatment not fully delivered "
                f"({'; '.join(reasons) or 'invalid run'})[/yellow]"
            )
            bundle_journal.record(
                bundle_journal.new_event(
                    "pair_excluded",
                    pair_id=pid,
                    payload={
                        "s3_valid": s3r.run_validity_passed,
                        "s4_valid": s4r.run_validity_passed,
                        "s4_delivered": s4_delivered,
                        "reasons": reasons,
                    },
                )
            )
            continue

        s3_results.append(s3r)
        s4_results.append(s4r)
        pair_ids.append(pid)
        console.print(
            f"  [green]Pair {pair_id} complete: "
            f"S3 p99={s3r.p99_latency_ms:.0f}ms, "
            f"S4 p99={s4r.p99_latency_ms:.0f}ms[/green]"
        )

        if len(pair_ids) < pairs:
            with countdown(console, INTER_RUN_PAUSE_SEC, "Inter-pair pause"):
                pass

    return s3_results, s4_results, pair_ids, attempt


def _write_insufficient_pairs(output_dir: str, n_valid: int, pairs: int, attempt: int) -> None:
    from datetime import datetime

    analysis_path = Path(output_dir) / "paired_analysis.json"
    analysis = {
        "status": "insufficient_valid_pairs",
        "n_valid_pairs": n_valid,
        "pairs_requested": pairs,
        "attempts": attempt,
        "timestamp": datetime.now().isoformat(),
    }
    analysis_path.write_text(json.dumps(analysis, indent=2))


def _write_paired_analysis(
    output_dir: str,
    s3_results: list,
    s4_results: list,
    pair_ids: list[str],
    console: "Console",
) -> None:
    """Write the paired comparison for the collected pairs and report the verdict."""
    from datetime import datetime

    from analysis.comparison import run_paired_comparison, apply_holm_paired

    s3_p99 = [r.p99_latency_ms for r in s3_results]
    s4_p99 = [r.p99_latency_ms for r in s4_results]
    primary = run_paired_comparison(s3_p99, s4_p99, metric="p99_latency_ms", pair_ids=pair_ids, label="H2-primary")

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

    analysis_path = Path(output_dir) / "paired_analysis.json"
    analysis = {
        "primary": primary.model_dump(),
        "secondaries": [s.model_dump() for s in secondaries],
        "n_pairs": len(pair_ids),
        "pair_ids": pair_ids,
        "s3_p99_values": s3_p99,
        "s4_p99_values": s4_p99,
        "timestamp": datetime.now().isoformat(),
    }
    analysis_path.write_text(json.dumps(analysis, indent=2, default=str))
    console.print(f"\n[dim]Paired analysis: {analysis_path}[/dim]")


@app.command(name="gru-hpo")
def gru_hpo(
    data_sources: str = typer.Option("clarknet", help="Comma-separated arms: clarknet,synthetic"),
    cells: str = typer.Option("gru,lstm", help="Comma-separated recurrent cells: gru,lstm"),
    seeds: str = typer.Option("42,43,44,45,46", help="Comma-separated training/refit seeds"),
    n_trials: int = typer.Option(30, help="Optuna trials per cell (identical budget for all cells)"),
    horizon: int = typer.Option(9, help="Prediction horizon (calibration default 9)"),
    window: int = typer.Option(30, help="Input-window length defining the split derivation (30 = frozen boundaries)"),
    output_dir: str = typer.Option("results/models/gru/study", help="Output bundle directory"),
    promote: bool = typer.Option(
        False, help="Back up data/models/gru_model.pt and promote the winning clarknet artifact"
    ),
) -> None:
    """Leak-free GRU/LSTM study at the calibration horizon (default 9).

    Chronological splits with embargo = sequence_length + horizon - 1 at every
    boundary. Hyperparameters and the epoch budget are selected on the
    validation portion only, the winner is refit on train+validation at the
    frozen budget, and the test portion is evaluated once per seed. Writes a
    bundle with meta.yaml, study.json, metrics.json, report.md, per-horizon
    CSVs, and hashed artifacts. The ClarkNet arm multiplies the series by the
    replay manifest scale_factor so the scaler matches serving amplitude.
    """
    from rich.console import Console

    from experiment.tuning.gru_study import run_study

    def _csv_list(value: str, cast: type) -> list:
        return [cast(v.strip()) for v in value.split(",") if v.strip()]

    console = Console()
    console.print(
        f"[bold cyan]GRU study[/bold cyan]  sources={data_sources}  cells={cells}  "
        f"seeds={seeds}  trials={n_trials}  horizon={horizon}  window={window}  promote={promote}"
    )

    result = run_study(
        data_sources=_csv_list(data_sources, str),
        cells=_csv_list(cells, str),
        seeds=_csv_list(seeds, int),
        n_trials=n_trials,
        horizon=horizon,
        window=window,
        output_dir=output_dir,
        promote=promote,
    )

    console.print("\n[green]✅ Study complete[/green]")
    winner = result["winner"]
    if winner:
        console.print(f"  Winner:        {winner['source']}/{winner['cell']} (mean RMSE {winner['mean_rmse']:.3f})")
        console.print(f"  Artifact:      {winner['artifact']}")
    else:
        console.print("  Winner:        NONE")
    console.print(f"  Bundle:        {result['bundle']}")
    if result["promoted"]:
        console.print(f"  Promoted to:   {result['promoted']['promoted_to']} (backup: {result['promoted']['backup']})")


@app.command(name="gru-probe")
def gru_probe(
    variant: str = typer.Option(
        "baseline", help="Probe variant: baseline,window120,calendar,revin,log_target,pinball,ensemble"
    ),
    seeds: str = typer.Option("42,43,44", help="Comma-separated training seeds"),
    epochs: int = typer.Option(200, help="Training epoch budget per seed"),
    patience: int = typer.Option(25, help="Early-stopping patience"),
    output_dir: Optional[str] = typer.Option(None, help="Output directory (required unless --dry-run)"),
    study_bundle: Optional[str] = typer.Option(None, help="Study bundle dir for ensemble artifact reuse"),
    dry_run: bool = typer.Option(False, help="Score OLS and statistical baselines only; no training, no writes"),
) -> None:
    """One-lever-at-a-time GRU probe against the OLS autoregression.

    Trains one variant under the frozen measurement contract (ClarkNet at the
    replay amplitude, train [0, 26205), test [26243, end)) and writes
    <output-dir>/<variant>.json plus one row in <output-dir>/probes.md. The
    OLS autoregression is fitted on the training region only and scored on
    the same windows as a first-class arm in every variant's JSON.
    """
    from rich.console import Console

    import experiment.tuning.gru_probe as gru_probe_mod

    console = Console()
    console.print(
        f"[bold cyan]GRU probe[/bold cyan]  variant={variant}  seeds={seeds}  "
        f"epochs={epochs}  patience={patience}  dry_run={dry_run}"
    )

    seed_list = tuple(int(s.strip()) for s in seeds.split(",") if s.strip())
    result = gru_probe_mod.run_probe(
        variant=variant,
        seeds=seed_list,
        output_dir=output_dir,
        epochs=epochs,
        patience=patience,
        dry_run=dry_run,
        study_bundle=study_bundle,
    )
    if dry_run:
        console.print("[green]Dry run complete (linear arms only)[/green]")
    else:
        console.print(f"[green]Probe complete:[/green] {result.get('variant')} -> {output_dir}")


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
    skip: frozenset[tuple[str, int]] = frozenset(),
    conditions: "RunConditions | None" = None,
) -> list[ExperimentResult]:
    """Run replicated experiments with randomized order.

    Entries in ``skip`` are runs already present and valid in the bundle, so a
    resumed invocation only executes what is missing while keeping the schedule
    order identical to a fresh run.
    """
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
    schedule = [(s, r) for s in scenarios for r in range(1, config.runs + 1) if (s, r) not in skip]
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
            result = _run_single(
                scenario,
                run_id,
                idx,
                config,
                output_dir,
                console=console,
                conditions=conditions,
            )
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
    conditions: "RunConditions | None" = None,
) -> Optional[ExperimentResult]:
    """Execute a single experiment run with full protocol.

    Before anything else the testbed is converged, its residue cleared, and the
    checks applied — the run either starts from the declared conditions or it does
    not start. This is the only place every path passes through, so no command can
    skip the conditioning.
    """
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

    condition_report: dict = {}
    if conditions is not None:
        from experiment.conditions import ConditionsUnmet, apply as apply_conditions

        try:
            condition_report = apply_conditions(conditions, scenario=scenario, console=console)
        except ConditionsUnmet as exc:
            console.print(f"  [red]Refusing to run {scenario}: {exc}[/red]")
            logger.error("run_refused", scenario=scenario, run_id=run_id, reason=str(exc))
            from shared.storage.journal import ExperimentJournal as _Journal

            refusal_journal = _Journal(run_dir / "events.jsonl", run_dir.name, str(run_dir))
            refusal_journal.record(
                refusal_journal.new_event(
                    "run_refused",
                    scenario=scenario,
                    run_id=run_id,
                    payload={"reason": str(exc)},
                )
            )
            return None

    logger.info("run_start", scenario=scenario, run_id=run_id, order=run_order_idx)
    from shared.models.evidence import TreatmentFidelity
    from shared.storage.journal import ExperimentJournal
    from experiment.stages.validate import evaluate_node_engagement, evaluate_run_validity

    journal = ExperimentJournal(
        run_dir / "events.jsonl",
        experiment_id=Path(output_dir).name,
        bundle_path=str(output_dir),
        git_commit=_git_commit_hash(),
    )
    journal.record(
        journal.new_event(
            "run_started",
            scenario=scenario,
            run_id=run_id,
            payload={"order": run_order_idx, "seed": config.seed},
        )
    )
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
        journal.record(
            journal.new_event(
                "run_failed",
                scenario=scenario,
                run_id=run_id,
                payload={"stage": "reset", "error": reset_result.error},
            )
        )
        return None

    journal.record(journal.new_event("reset_completed", scenario=scenario, run_id=run_id))

    # Start daemon
    daemon_ctx = _make_ctx(config, scenario, run_id, output_dir)
    daemon_result = daemon_stage.execute(daemon_ctx)
    if not daemon_result.success:
        logger.error("daemon_failed", scenario=scenario, error=daemon_result.error)
        journal.record(
            journal.new_event(
                "run_failed",
                scenario=scenario,
                run_id=run_id,
                payload={"stage": "daemon", "error": daemon_result.error},
            )
        )
        return None

    journal.record(journal.new_event("daemon_started", scenario=scenario, run_id=run_id))

    try:
        # S4 hard prediction-delivery gate: verify the GRU service is healthy
        # and model-loaded before warmup so a dead prediction service produces a
        # durable invalid run instead of a silent reactive fallback.
        if "s4" in scenario or "predictive" in scenario:
            ok, preflight_reason, model_status = daemon_stage.require_prediction_service()
            if not ok:
                journal.record(
                    journal.new_event(
                        "prediction_preflight_failed",
                        scenario=scenario,
                        run_id=run_id,
                        payload={"reason": preflight_reason},
                    )
                )
                preflight_fidelity = TreatmentFidelity(
                    required=True,
                    preflight_passed=False,
                    delivered=False,
                    reasons=[preflight_reason],
                )
                preflight_result = ExperimentResult(
                    scenario=scenario,
                    run_id=run_id,
                    timestamp=datetime.now().isoformat(),
                    run_validity_passed=False,
                    validity_gate_passed=False,
                    treatment_fidelity=preflight_fidelity,
                )
                (run_dir / "result.json").write_text(preflight_result.model_dump_json(indent=2))
                journal.record(
                    journal.new_event(
                        "run_failed",
                        scenario=scenario,
                        run_id=run_id,
                        payload={
                            "stage": "prediction_preflight",
                            "reason": preflight_reason,
                            "treatment_fidelity": preflight_fidelity.model_dump(),
                        },
                    )
                )
                console.print(f"[red]S4 prediction preflight failed: {preflight_reason}[/red]")
                return preflight_result
            journal.record(
                journal.new_event(
                    "prediction_preflight_passed",
                    scenario=scenario,
                    run_id=run_id,
                    payload={"model_status": model_status},
                )
            )
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
            conditions=condition_report,
        )
        with open(run_dir / "manifest.json", "w") as f:
            json.dump(manifest.model_dump(), f, indent=2)

        # (C.warm-up) 30s idle warm-up
        logger.info("warmup_start", seconds=WARMUP_SEC)
        with countdown(console, WARMUP_SEC, "Warmup"):
            pass
        journal.record(journal.new_event("warmup_completed", scenario=scenario, run_id=run_id))

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
        journal.record(journal.new_event("workload_completed", scenario=scenario, run_id=run_id))

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
        prov_log: list[tuple[float, str, dict]] = []
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
        journal.record(journal.new_event("collection_completed", scenario=scenario, run_id=run_id))

        # Hard S4 prediction-delivery gate
        result = evaluate_run_validity(
            result,
            scenario=scenario,
            preflight_passed=True,
            daemon_status=daemon_status,
        )

        # Node tier: a scenario that runs the node autoscaler is only measuring the
        # capacity dimension the hybrid design adds when a pod actually goes pending.
        result = evaluate_node_engagement(
            result,
            scenario=scenario,
            events=[event_type for _, event_type, _ in prov_log],
            nodes_provisioned=result.nodes_provisioned,
        )
        journal.record(
            journal.new_event(
                "validity_evaluated",
                scenario=scenario,
                run_id=run_id,
                payload={
                    "run_validity_passed": result.run_validity_passed,
                    "treatment_fidelity": (
                        result.treatment_fidelity.model_dump() if result.treatment_fidelity else None
                    ),
                    "node_engagement": (result.node_engagement.model_dump() if result.node_engagement else None),
                },
            )
        )

        # Save result
        with open(run_dir / "result.json", "w") as f:
            json.dump(result.model_dump(), f, indent=2)

        logger.info("run_complete", scenario=scenario, run_id=run_id, p99=result.p99_latency_ms)
        journal.record(journal.new_event("run_completed", scenario=scenario, run_id=run_id))
        return result

    except Exception as exc:
        logger.error("run_exception", scenario=scenario, run_id=run_id, error=str(exc))
        try:
            journal.record(
                journal.new_event(
                    "run_failed",
                    scenario=scenario,
                    run_id=run_id,
                    payload={"stage": "runtime", "error": str(exc)},
                )
            )
        except Exception:
            logger.error("journal_record_failed", scenario=scenario, run_id=run_id)
        raise

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


# Evidence sub-app — registry, catalog, and lifecycle governance.
# Thin handlers delegate to experiment.evidence.* modules; no business logic here.
from experiment.evidence.cli_adapter import evidence_app

app.add_typer(evidence_app, name="evidence", help="Evidence registry, catalog, and lifecycle governance")


if __name__ == "__main__":
    app()
