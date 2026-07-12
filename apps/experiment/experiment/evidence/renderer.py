"""Deterministic Markdown renderer for the experiment evidence journal.

Writes ``results/EXPERIMENT_JOURNAL.md`` from the typed registry and governance
event log. This file is generated only — never hand-edited.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Sequence

from shared.models.evidence import ExperimentJournalEvent, ExperimentRegistryEntry


def _fmt_date(d: object) -> str:
    """Format a date for display."""
    if d is None:
        return ""
    return str(d)


def _fmt_fidelity(entry: ExperimentRegistryEntry) -> str:
    """Format treatment fidelity for the journal table."""
    fid = entry.treatment_fidelity
    if fid is None:
        return "—"
    if not fid.required:
        return "—"
    return f"{fid.successful_predictions}/{fid.eligible_cycles} ({'✓' if fid.delivered else '✗'})"


def _latest_audit_timestamp(events: Sequence[ExperimentJournalEvent]) -> str:
    """Find the latest registry_audited event timestamp."""
    for ev in reversed(events):
        if ev.event == "registry_audited":
            return ev.timestamp.isoformat() if hasattr(ev.timestamp, "isoformat") else str(ev.timestamp)
    return "never"


def render_experiment_journal(
    entries: Sequence[ExperimentRegistryEntry],
    events: Sequence[ExperimentJournalEvent],
    output: Path,
) -> None:
    """Deterministically write the experiment journal Markdown.

    Args:
        entries: Registry entries (sorted by date descending internally).
        events: Governance events (most recent first internally).
        output: Path to write (typically ``results/EXPERIMENT_JOURNAL.md``).
    """
    lines: list[str] = []

    # Header
    lines.append("# Experiment Journal")
    lines.append("")
    lines.append("> **This file is generated.** Do not hand-edit.")
    lines.append(">")
    lines.append("> Canonical sources:")
    lines.append("> - **Governance:** `results/evidence/registry-events.jsonl`")
    lines.append("> - **Execution:** per-run `events.jsonl` inside each bundle")
    lines.append("> - **Registry:** `results/evidence/registry.yaml`")
    lines.append("> - **Query cache:** `results/evidence/catalog.duckdb` (rebuilt, not canonical)")
    lines.append("")

    # Latest audit
    lines.append(f"**Latest audit:** {_latest_audit_timestamp(events)}")
    lines.append("")

    # Counts by role/status
    by_role: Counter[str] = Counter(e.role for e in entries)
    by_status: Counter[str] = Counter(e.status for e in entries)

    lines.append("## Summary")
    lines.append("")
    lines.append(f"- **Total bundles:** {len(entries)}")
    lines.append(f"- **By role:** {', '.join(f'{r}={c}' for r, c in sorted(by_role.items()))}")
    lines.append(f"- **By status:** {', '.join(f'{s}={c}' for s, c in sorted(by_status.items()))}")
    lines.append("")

    # Reverse-chronological table
    sorted_entries = sorted(entries, key=lambda e: (e.date, e.id), reverse=True)

    lines.append("## Bundles")
    lines.append("")
    lines.append("| Date | ID | Role | Valid/Total | Treatment | Claims | Path |")
    lines.append("|------|----|------|------------|-----------|--------|------|")
    for e in sorted_entries:
        claims = ", ".join(e.claims_supported) if e.claims_supported else "—"
        lines.append(
            f"| {_fmt_date(e.date)} | `{e.id}` | {e.role} | "
            f"{e.n_runs_valid}/{e.n_runs_total} | {_fmt_fidelity(e)} | "
            f"{claims} | `{e.path}` |"
        )
    lines.append("")

    # Last 20 governance events
    recent = list(reversed(events))[:20] if events else []
    lines.append("## Recent Governance Events (last 20)")
    lines.append("")
    if not recent:
        lines.append("_No governance events recorded yet._")
    else:
        lines.append("| Timestamp | Event | Experiment | Bundle | Run |")
        lines.append("|-----------|-------|------------|--------|-----|")
        for ev in recent:
            ts = ev.timestamp.isoformat() if hasattr(ev.timestamp, "isoformat") else str(ev.timestamp)
            run = str(ev.run_id) if ev.run_id is not None else "—"
            lines.append(f"| {ts} | {ev.event} | {ev.experiment_id} | {ev.bundle_path or '—'} | {run} |")
    lines.append("")

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines))
