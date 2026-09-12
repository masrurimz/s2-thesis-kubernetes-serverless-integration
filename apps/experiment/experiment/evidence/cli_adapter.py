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
) -> None:
    """Read-only SQL query against the DuckDB catalog."""

    from rich.console import Console
    from rich.table import Table

    from experiment.evidence.catalog import EvidenceCatalogAdapter

    console = Console()
    root = _results_root()
    adapter = EvidenceCatalogAdapter(root)

    try:
        rows = adapter.query(sql)
    except Exception as exc:
        console.print(f"[red]Query failed:[/red] {exc}")
        console.print("[dim]Hint: run 'thesis experiment evidence catalog refresh' first.[/dim]")
        raise typer.Exit(1) from exc

    if not rows:
        console.print("[dim](no rows)[/dim]")
        return

    columns = list(rows[0].keys())
    table = Table(title=f"Query: {sql[:60]}")
    for col in columns:
        table.add_column(col)
    for row in rows:
        table.add_row(*[str(row.get(c, "")) for c in columns])
    console.print(table)


# ---------------------------------------------------------------------------
# journal — show recent governance events
# ---------------------------------------------------------------------------


@evidence_app.command()
def journal(
    limit: int = typer.Option(20, "--limit", help="Number of recent events to show"),
) -> None:
    """Show recent governance events from registry-events.jsonl."""
    from rich.console import Console
    from rich.table import Table

    from experiment.evidence.registry import read_governance_events

    console = Console()
    root = _results_root()
    events_path = root / "evidence" / "registry-events.jsonl"
    events = read_governance_events(events_path)

    recent = list(reversed(events))[:limit]

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
