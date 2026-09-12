"""Evidence Typer sub-app — thin command handlers delegating to evidence modules.

Registered into the experiment app via ``app.add_typer(evidence_app, name="evidence")``
in ``experiment.cli``.

All business logic lives in ``experiment.evidence.registry``, ``renderer``,
and ``catalog``. These handlers are intentionally thin.
"""

from __future__ import annotations

from pathlib import Path

import typer

evidence_app = typer.Typer(help="Evidence registry, catalog, and lifecycle governance", no_args_is_help=True)

# Module-level results root — resolved at call time so tests can monkeypatch.
RESULTS_ROOT = Path.cwd() / "results"


def _results_root() -> Path:
    """Get the results root (read at call time for test monkeypatching)."""
    return RESULTS_ROOT


# ---------------------------------------------------------------------------
# audit — read-only scan summary
# ---------------------------------------------------------------------------


@evidence_app.command()
def audit() -> None:
    """Read-only scan of experiment bundles. Prints a summary."""
    from rich.console import Console
    from rich.table import Table

    from experiment.evidence.registry import scan_bundles

    console = Console()
    root = _results_root()
    entries = scan_bundles(root)

    console.print(f"\n[bold]Scanned {len(entries)} bundles under {root / 'experiments'}[/bold]")

    table = Table(title="Bundle Audit")
    table.add_column("ID", style="cyan")
    table.add_column("Date")
    table.add_column("Role")
    table.add_column("Valid/Total")
    table.add_column("Treatment")
    table.add_column("Path")

    for entry in sorted(entries.values(), key=lambda e: (e.date, e.id), reverse=True):
        fid = entry.treatment_fidelity
        treatment = (
            "—"
            if fid is None
            else f"{fid.successful_predictions}/{fid.eligible_cycles} ({'✓' if fid.delivered else '✗'})"
        )
        table.add_row(
            entry.id,
            str(entry.date),
            entry.role,
            f"{entry.n_runs_valid}/{entry.n_runs_total}",
            treatment,
            entry.path,
        )

    console.print(table)


# ---------------------------------------------------------------------------
# reconcile --apply — merge-safe registry reconciliation
# ---------------------------------------------------------------------------


@evidence_app.command()
def reconcile(
    apply: bool = typer.Option(False, "--apply", help="Write changes. Without this flag, exits non-zero."),
) -> None:
    """Merge-safe reconciliation of the typed registry. Requires --apply."""
    from rich.console import Console

    from experiment.evidence.registry import (
        append_registry_audited_event,
        load_registry,
        reconcile_registry,
        scan_bundles,
        write_registry,
    )

    console = Console()
    root = _results_root()

    if not apply:
        console.print("[red]reconcile requires --apply to write changes.[/red]")
        raise typer.Exit(1)

    registry_path = root / "evidence" / "registry.yaml"
    events_path = root / "evidence" / "registry-events.jsonl"

    existing = load_registry(registry_path)
    scanned = scan_bundles(root)
    recon = reconcile_registry(existing, scanned)
    write_registry(registry_path, recon.merged)

    append_registry_audited_event(events_path, root, recon)

    # Regenerate the journal
    from experiment.evidence.registry import read_governance_events
    from experiment.evidence.renderer import render_experiment_journal

    entries = list(recon.merged.values())
    events = read_governance_events(events_path)
    render_experiment_journal(entries, events, root / "EXPERIMENT_JOURNAL.md")

    console.print(
        f"[green]Reconciled:[/green] {len(recon.created)} created, "
        f"{len(recon.changed)} changed, {len(recon.archived)} archived "
        f"({len(recon.merged)} total)"
    )


# ---------------------------------------------------------------------------
# catalog — DuckDB catalog sub-group
# ---------------------------------------------------------------------------

catalog_app = typer.Typer(help="Local DuckDB evidence catalog management", no_args_is_help=True)


@catalog_app.command()
def refresh() -> None:
    """Rebuild the local DuckDB evidence catalog (ignored, noncanonical)."""
    from rich.console import Console

    from experiment.evidence.catalog import EvidenceCatalogAdapter

    console = Console()
    root = _results_root()
    adapter = EvidenceCatalogAdapter(root)
    adapter.refresh()
    console.print(f"[green]Catalog rebuilt:[/green] {adapter.catalog_path}")


evidence_app.add_typer(catalog_app, name="catalog", help="Local DuckDB evidence catalog management")


# ---------------------------------------------------------------------------
# query — read-only SQL query
# ---------------------------------------------------------------------------


@evidence_app.command()
def query(
    sql: str = typer.Argument(..., help="SQL query to execute against the catalog"),
    limit: int = typer.Option(50, "--limit", help="Rows to show before stopping"),
    full: bool = typer.Option(False, "--full", help="Do not truncate long cell values"),
    as_json: bool = typer.Option(False, "--json", help="Emit the rows as JSON"),
) -> None:
    """Read-only SQL query against the DuckDB catalog."""

    from rich.console import Console
    from rich.table import Table

    from experiment.evidence.catalog import EvidenceCatalogAdapter
    from shared.output import print_json, print_next, truncate

    console = Console()
    root = _results_root()
    adapter = EvidenceCatalogAdapter(root)

    try:
        # One row more than asked for is how we know there were more.
        fetched = adapter.query(sql, max_rows=limit + 1)
    except Exception as exc:
        console.print(f"[red]Query failed:[/red] {exc}")
        console.print("[dim]Hint: run 'thesis experiment evidence catalog refresh' first.[/dim]")
        raise typer.Exit(1) from exc

    hidden = len(fetched) > limit
    rows = fetched[:limit]

    if as_json:
        print_json(rows)
        return

    if not rows:
        console.print("[dim]0 rows[/dim]")
        return

    columns = list(rows[0].keys())
    if full:
        # A table wraps a long cell at the terminal width and pads every line, so --full
        # through a table shows the value in pieces. Blocks show it whole.
        for index, row in enumerate(rows, start=1):
            console.print(f"[bold]row {index}[/bold]", soft_wrap=True)
            for col in columns:
                # soft_wrap: rich would otherwise fold a long value at the console width,
                # which is the same unreadable result the table gave.
                console.print(f"  {col}: {row.get(col, '')}", soft_wrap=True)
    else:
        # A table wider than the terminal makes rich ellipsize every cell, which tells the
        # reader nothing. Show what fits and name the way to the whole row.
        shown, omitted = columns[:8], columns[8:]
        table = Table(title=f"Query: {sql[:60]}")
        for col in shown:
            table.add_column(col)
        for row in rows:
            table.add_row(*[truncate(str(row.get(c, ""))) for c in shown])
        console.print(table)
        if omitted:
            console.print(f"[dim]+{len(omitted)} more column(s) — use --json for the full row[/dim]")
    console.print(f"[dim]{len(rows)} row(s) shown{'; more available — raise --limit' if hidden else ''}[/dim]")
    print_next(["thesis experiment evidence journal --limit 20"])


# ---------------------------------------------------------------------------
# journal — show recent governance events
# ---------------------------------------------------------------------------


@evidence_app.command()
def journal(
    limit: int = typer.Option(20, "--limit", help="Number of recent events to show"),
    as_json: bool = typer.Option(False, "--json", help="Emit the events as JSON"),
) -> None:
    """Show recent governance events from registry-events.jsonl."""
    from rich.console import Console
    from rich.table import Table

    from experiment.evidence.registry import read_governance_events
    from shared.output import print_json

    console = Console()
    root = _results_root()
    events_path = root / "evidence" / "registry-events.jsonl"
    events = read_governance_events(events_path)

    recent = list(reversed(events))[:limit]

    if as_json:
        print_json([event.model_dump() for event in recent])
        return

    if not recent:
        console.print("[dim]No governance events recorded.[/dim]")
        return

    table = Table(title=f"Governance Events (last {len(recent)})")
    table.add_column("Timestamp", style="dim")
    table.add_column("Event", style="cyan")
    table.add_column("Experiment")
    table.add_column("Bundle")

    for ev in recent:
        table.add_row(
            str(ev.timestamp),
            ev.event,
            ev.experiment_id,
            ev.bundle_path or "—",
        )

    console.print(table)


# ---------------------------------------------------------------------------
# backfill-legacy --apply — logical legacy migration
# ---------------------------------------------------------------------------


@evidence_app.command(name="backfill-legacy")
def backfill_legacy(
    apply: bool = typer.Option(False, "--apply", help="Write changes. Without this flag, exits non-zero."),
) -> None:
    """Logically backfill legacy v1 bundles into the typed registry. Requires --apply."""
    from rich.console import Console

    from experiment.evidence.registry import legacy_backfill

    console = Console()
    root = _results_root()

    if not apply:
        # Preview mode: show what would be backfilled
        summary = legacy_backfill(root, apply=False)
        console.print(f"[yellow]Preview: {len(summary.v1_bundle_ids)} v1 bundles would be backfilled.[/yellow]")
        for bid in summary.v1_bundle_ids:
            console.print(f"  {bid} ({summary.artifact_counts.get(bid, 0)} artifacts)")
        console.print("[dim]Use --apply to write.[/dim]")
        raise typer.Exit(1)

    summary = legacy_backfill(root, apply=True)
    console.print(
        f"[green]Backfilled:[/green] {len(summary.v1_bundle_ids)} v1 bundles, {summary.events_appended} events appended"
    )


# ---------------------------------------------------------------------------
# derive-parquet — per-artifact Parquet derivation
# ---------------------------------------------------------------------------


@evidence_app.command(name="derive-parquet")
def derive_parquet(
    source: str = typer.Option(..., "--source", help="Path to legacy CSV or JSONL source"),
    output: str = typer.Option(..., "--output", help="Output Parquet path under results/experiments"),
    artifact_name: str = typer.Option("legacy", "--artifact-name", help="Artifact name for metadata"),
) -> None:
    """Derive a provenance-preserving Parquet from a legacy CSV or JSONL artifact."""
    from rich.console import Console

    from experiment.evidence.catalog import EvidenceCatalogAdapter

    console = Console()
    root = _results_root()
    adapter = EvidenceCatalogAdapter(root)

    try:
        out = adapter.derive_legacy_parquet(
            Path(source),
            Path(output),
            artifact_name=artifact_name,
        )
        console.print(f"[green]Derived Parquet:[/green] {out}")
    except ValueError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(1) from exc


# ---------------------------------------------------------------------------
# normalize — legacy utilization JSON -> Parquet
# ---------------------------------------------------------------------------


@evidence_app.command()
def normalize(
    apply: bool = typer.Option(False, "--apply", help="Convert and delete the JSON. Default reports only."),
    as_json: bool = typer.Option(False, "--json", help="Emit the report as JSON"),
) -> None:
    """Convert legacy utilization JSON series to Parquet (verified, idempotent)."""
    from rich.console import Console
    from rich.table import Table

    from experiment.evidence.normalize import normalize_series_artifacts
    from shared.output import print_json

    console = Console()
    report = normalize_series_artifacts(_results_root(), apply=apply)

    if as_json:
        print_json(report)
        return
    elif report["files"]:
        table = Table(title=f"Utilization series normalization ({'apply' if apply else 'dry run'})")
        table.add_column("Run", style="dim")
        table.add_column("Series")
        table.add_column("Rows", justify="right")
        table.add_column("Before", justify="right")
        table.add_column("After", justify="right")
        table.add_column("Status")
        for entry in report["files"]:
            table.add_row(
                entry["run"],
                entry["series"],
                str(entry["rows"]),
                str(entry["bytes_before"]),
                str(entry["bytes_after"] or "—"),
                entry["error"] or entry["status"],
            )
        console.print(table)
    else:
        console.print("[dim]No legacy utilization JSON found under results/experiments/.[/dim]")

    console.print(
        f"[green]{report['converted']} converted[/green], "
        f"{report['would_convert']} pending, [red]{report['failed']} failed[/red]"
    )
    if apply and report["failed"]:
        raise typer.Exit(1)
