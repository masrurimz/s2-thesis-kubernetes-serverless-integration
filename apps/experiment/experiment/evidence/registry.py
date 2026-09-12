"""Typed experiment registry scanner, merge-safe reconciler, and legacy backfill.

Replaces the destructive ``scripts/audit_experiment_registry.py`` with a
deterministic scanner that never overwrites human-owned registry fields.

Scanner-owned facts (replaced on reconcile): date, scenarios, has_meta,
has_report, has_paired_analysis, n_runs_total, n_runs_valid, treatment_fidelity,
git_commits.

Human-owned fields (preserved on reconcile): role, status, config, results,
claims_supported, supersedes, superseded_by, notes.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path

import yaml
from shared.artifacts import paired_analysis_path, read_manifest_git_commit, read_result
from shared.models.evidence import (
    ExperimentJournalEvent,
    ExperimentRegistryEntry,
    TreatmentFidelity,
)
from shared.models.experiment import ExperimentResult
from shared.scenarios import Scenario
from shared.storage.journal import ExperimentJournal

# ---------------------------------------------------------------------------
# Scenario normalization
# ---------------------------------------------------------------------------

_SCENARIO_PREFIX_MAP: dict[str, str] = {
    "s1": Scenario.S1_K8S_ONLY.value,
    "s2": Scenario.S2_SERVERLESS_ONLY.value,
    "s3": Scenario.S3_HYBRID_REACTIVE.value,
    "s4": Scenario.S4_HYBRID_PREDICTIVE.value,
}

_RUN_DIR_RE = re.compile(r"^(.+)_run(\d+)$")


def normalize_scenario(raw: str) -> str | None:
    """Normalize a scenario directory name to its canonical enum value."""
    lowered = raw.strip().lower()
    for s in Scenario:
        if s.value == lowered:
            return s.value
    for prefix, canonical in _SCENARIO_PREFIX_MAP.items():
        if lowered == prefix or lowered.startswith(prefix + "-") or lowered.startswith(prefix + "_"):
            return canonical
    return None


# ---------------------------------------------------------------------------
# Summary types
# ---------------------------------------------------------------------------


@dataclass
class RegistryReconciliation:
    """Result of merging scanned entries into the existing registry."""

    merged: dict[str, ExperimentRegistryEntry]
    created: list[str] = field(default_factory=list)
    changed: list[str] = field(default_factory=list)
    archived: list[str] = field(default_factory=list)


@dataclass
class LegacyBackfillSummary:
    """Result of a legacy v1 backfill operation."""

    v1_bundle_ids: list[str] = field(default_factory=list)
    artifact_counts: dict[str, int] = field(default_factory=dict)
    events_appended: int = 0
    applied: bool = False


# ---------------------------------------------------------------------------
# Bundle scanning
# ---------------------------------------------------------------------------

_DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")


def _extract_date(dirname: str) -> date:
    """Extract a date from a directory name like ``2026-07-11_paired-h2``."""
    m = _DATE_RE.search(dirname)
    if m:
        try:
            return date.fromisoformat(m.group(1))
        except ValueError:
            pass
    return date(1970, 1, 1)


def _make_bundle_id(root_name: str, dirname: str) -> str:
    """Generate a stable bundle ID matching historical convention."""
    slug = dirname.replace("_", "-")
    return f"{root_name}.{slug}"


def _read_result(path: Path) -> ExperimentResult | None:
    """Read a run's result through the artifact loader."""
    return read_result(path.parent)


def _read_git_commit(manifest_path: Path) -> str:
    """Read the commit a run ran from through the artifact loader."""
    return read_manifest_git_commit(manifest_path.parent)


def _derive_run_fidelity(result: ExperimentResult) -> TreatmentFidelity | None:
    """Derive per-run TreatmentFidelity from result data.

    For v2 bundles, ``result.treatment_fidelity`` is populated directly.
    For v1 bundles, derive from ``gru_predictions_*`` summary fields.
    """
    if result.scenario != Scenario.S4_HYBRID_PREDICTIVE.value:
        return None

    # v2: treatment_fidelity already set on the result
    if result.treatment_fidelity is not None:
        return result.treatment_fidelity

    # v1: derive from gru prediction summary fields
    successful = result.gru_predictions_used
    failed = result.gru_predictions_failed
    eligible = successful + failed
    delivery_rate = successful / eligible if eligible > 0 else 0.0
    delivered = eligible > 0 and failed == 0
    return TreatmentFidelity(
        required=True,
        eligible_cycles=eligible,
        successful_predictions=successful,
        failed_predictions=failed,
        delivery_rate=delivery_rate,
        delivered=delivered,
        reasons=[] if delivered else ["derived from legacy summary fields: delivery incomplete"],
    )


def _run_is_valid(result: ExperimentResult) -> bool:
    """Check if a run passes validity gates.

    For S4, additionally require treatment delivery if fidelity is known.
    """
    if not (result.run_validity_passed and result.stress_validity_passed):
        return False
    if result.scenario == Scenario.S4_HYBRID_PREDICTIVE.value:
        fid = result.treatment_fidelity
        if fid is not None and not fid.delivered:
            return False
    return True


def _derive_run_events_fallback(run_dir: Path, scenario: str) -> tuple[bool, TreatmentFidelity | None, str]:
    """Derive run validity, S4 treatment fidelity, and git commit from the run
    journal (``validity_evaluated`` event) when ``result.json`` is unavailable.

    Some bundles only ever had ``daemon.log`` + ``events.jsonl`` committed
    (result.json and the k6 summary were deleted pre-commit and are
    gitignored), so the scanner falls back to the journal's own validity gate
    verdict instead of silently downgrading ``n_runs_valid`` to 0.

    Returns ``(valid, fidelity_or_None, git_commit)``.
    """
    events_path = run_dir / "events.jsonl"
    if not events_path.exists():
        return False, None, ""
    try:
        for line in events_path.read_text().splitlines():
            if not line.strip():
                continue
            event = json.loads(line)
            if event.get("event") != "validity_evaluated":
                continue
            payload = event.get("payload") or {}
            valid = bool(payload.get("run_validity_passed"))
            fid = None
            tf_data = payload.get("treatment_fidelity")
            if tf_data and scenario == Scenario.S4_HYBRID_PREDICTIVE.value:
                try:
                    fid = TreatmentFidelity(**tf_data)
                except Exception:
                    fid = None
            return valid, fid, str(event.get("git_commit") or "")
    except Exception:
        return False, None, ""
    return False, None, ""


def _scan_run_dirs(bundle_dir: Path) -> list[tuple[str, int, Path]]:
    """Find all run directories in a bundle (v1 direct-child or v2 raw/ layout).

    Returns list of (scenario, run_id, run_dir) tuples.
    """
    run_dirs: list[tuple[str, int, Path]] = []
    # v2: raw/<scenario>_run<N>
    raw_dir = bundle_dir / "raw"
    search_dirs = [raw_dir, bundle_dir] if raw_dir.is_dir() else [bundle_dir]
    seen: set[Path] = set()
    for parent in search_dirs:
        if not parent.is_dir():
            continue
        for child in sorted(parent.iterdir()):
            if not child.is_dir() or child in seen:
                continue
            m = _RUN_DIR_RE.match(child.name)
            if m:
                scenario = normalize_scenario(m.group(1))
                if scenario is not None:
                    try:
                        run_id = int(m.group(2))
                    except ValueError:
                        continue
                    run_dirs.append((scenario, run_id, child))
                    seen.add(child)
    return run_dirs


def _count_artifacts(bundle_dir: Path) -> int:
    """Count CSV, JSON, JSONL, and Parquet artifacts in a bundle."""
    count = 0
    for pattern in ("**/*.csv", "**/*.json", "**/*.jsonl", "**/*.parquet"):
        count += sum(1 for _ in bundle_dir.glob(pattern))
    return count


def _scan_single_bundle(
    root_name: str,
    bundle_dir: Path,
    results_root: Path,
) -> ExperimentRegistryEntry | None:
    """Scan a single experiment bundle directory."""
    if not bundle_dir.is_dir():
        return None

    dirname = bundle_dir.name
    has_meta = (bundle_dir / "meta.yaml").exists()
    has_report = (bundle_dir / "report.md").exists()
    has_paired = paired_analysis_path(bundle_dir) is not None

    run_dirs = _scan_run_dirs(bundle_dir)

    scenarios: set[str] = set()
    git_commits: set[str] = set()
    n_total = 0
    n_valid = 0
    s4_fidelities: list[TreatmentFidelity] = []

    for scenario, _run_id, run_dir in run_dirs:
        result_path = run_dir / "result.json"
        result = _read_result(result_path)
        scenarios.add(scenario)
        n_total += 1

        manifest_path = run_dir / "manifest.json"
        if manifest_path.exists():
            commit = _read_git_commit(manifest_path)
            if commit:
                git_commits.add(commit)

        if result is not None:
            if _run_is_valid(result):
                n_valid += 1
            fid = _derive_run_fidelity(result)
            if fid is not None:
                s4_fidelities.append(fid)
        else:
            # Fallback: derive validity / fidelity / commit from the run
            # journal when result.json was never committed (or was deleted).
            events_valid, events_fid, events_commit = _derive_run_events_fallback(run_dir, scenario)
            if events_valid:
                n_valid += 1
            if events_fid is not None:
                s4_fidelities.append(events_fid)
            if events_commit:
                git_commits.add(events_commit)

    # Bundle-level treatment fidelity
    bundle_fidelity: TreatmentFidelity | None = None
    if s4_fidelities:
        total_eligible = sum(f.eligible_cycles for f in s4_fidelities)
        total_successful = sum(f.successful_predictions for f in s4_fidelities)
        total_failed = sum(f.failed_predictions for f in s4_fidelities)
        all_delivered = all(f.delivered for f in s4_fidelities)
        rate = total_successful / total_eligible if total_eligible > 0 else 0.0
        bundle_fidelity = TreatmentFidelity(
            required=True,
            eligible_cycles=total_eligible,
            successful_predictions=total_successful,
            failed_predictions=total_failed,
            delivery_rate=rate,
            delivered=all_delivered,
            reasons=[] if all_delivered else ["one or more S4 runs had incomplete prediction delivery"],
        )

    # Suggest a role (never 'final')
    if has_report and n_valid > 0:
        suggested_role = "intermediate"
    else:
        suggested_role = "diagnostic"

    exp_id = _make_bundle_id(root_name, dirname)
    rel_path = str(bundle_dir.relative_to(results_root))

    return ExperimentRegistryEntry(
        id=exp_id,
        root=root_name,
        path=rel_path,
        date=_extract_date(dirname),
        role=suggested_role,
        status="current",
        scenarios=sorted(scenarios),
        n_runs_total=n_total,
        n_runs_valid=n_valid,
        treatment_fidelity=bundle_fidelity,
        has_meta=has_meta,
        has_report=has_report,
        has_paired_analysis=has_paired,
        git_commits=sorted(git_commits),
    )


def scan_bundles(results_root: Path) -> dict[str, ExperimentRegistryEntry]:
    """Scan ``results_root / 'experiments'`` for all experiment bundles.

    Returns a dict of bundle ID -> ExperimentRegistryEntry.
    """
    entries: dict[str, ExperimentRegistryEntry] = {}
    exp_root = results_root / "experiments"
    if not exp_root.exists():
        return entries

    for phase_dir in sorted(exp_root.iterdir()):
        if not phase_dir.is_dir():
            continue
        for bundle_dir in sorted(phase_dir.iterdir()):
            if not bundle_dir.is_dir():
                continue
            entry = _scan_single_bundle("experiments", bundle_dir, results_root)
            if entry is not None:
                entries[entry.id] = entry

    return entries


# ---------------------------------------------------------------------------
# Registry I/O
# ---------------------------------------------------------------------------

_SCANNER_OWNED_FIELDS = frozenset(
    {
        "date",
        "scenarios",
        "has_meta",
        "has_report",
        "has_paired_analysis",
        "n_runs_total",
        "n_runs_valid",
        "treatment_fidelity",
        "git_commits",
    }
)

_HUMAN_OWNED_FIELDS = frozenset(
    {
        "role",
        "status",
        "config",
        "results",
        "claims_supported",
        "supersedes",
        "superseded_by",
        "notes",
    }
)


_OLD_ROLE_MAP: dict[str, str] = {
    "smoke": "diagnostic",
    "incomplete": "diagnostic",
    "invalidated": "diagnostic",
    "intermediate": "intermediate",
    "final": "final",
    "superseded": "superseded",
}


def _migrate_old_entry(raw: dict) -> dict:
    """Migrate a legacy v1 registry entry dict to the v2 schema.

    Maps old roles, adds missing required fields, and converts ``n_clean`` to
    ``n_runs_valid``/``n_runs_total``.
    """
    out = dict(raw)
    old_role = str(out.get("role", ""))
    out["role"] = _OLD_ROLE_MAP.get(old_role, "diagnostic")
    if "status" not in out:
        out["status"] = "invalidated" if old_role == "invalidated" else "current"
    if "n_runs_total" not in out:
        n_clean = out.pop("n_clean", 0)
        out["n_runs_total"] = max(n_clean, 0) if isinstance(n_clean, int) else 0
    if "n_runs_valid" not in out:
        out["n_runs_valid"] = out.get("n_runs_total", 0)
    if "has_paired_analysis" not in out:
        out["has_paired_analysis"] = False
    if "scenarios" not in out:
        out["scenarios"] = []
    return out


def load_registry(path: Path) -> dict[str, ExperimentRegistryEntry]:
    """Load a typed registry from a YAML file.

    Handles both v2 (``entries`` key) and legacy v1 (``experiments`` key) formats.
    Old-format roles are migrated to the new ``Literal`` set so human decisions
    survive the transition.

    Returns an empty dict if the file does not exist.
    """
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text())
    if not data:
        return {}
    raw_entries = data.get("entries") or data.get("experiments") or []
    entries: dict[str, ExperimentRegistryEntry] = {}
    for raw in raw_entries:
        try:
            entry = ExperimentRegistryEntry(**_migrate_old_entry(raw))
            entries[entry.id] = entry
        except Exception:
            continue
    return entries


def write_registry(path: Path, entries: dict[str, ExperimentRegistryEntry]) -> None:
    """Write a typed registry to a YAML file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "version": 2,
        "last_reconciled": datetime.now(timezone.utc).isoformat(),
        "total_bundles": len(entries),
        "entries": [e.model_dump(mode="json") for e in sorted(entries.values(), key=lambda x: x.id)],
    }
    with open(path, "w") as f:
        yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)


# ---------------------------------------------------------------------------
# Merge-safe reconciliation
# ---------------------------------------------------------------------------


def reconcile_registry(
    existing: dict[str, ExperimentRegistryEntry],
    scanned: dict[str, ExperimentRegistryEntry],
) -> RegistryReconciliation:
    """Merge scanned entries into the existing registry.

    - Existing IDs: replace scanner-owned fields, preserve human-owned fields.
    - New IDs: adopt scanner suggestion with status='current'.
    - Disappeared IDs: retain entry, set status='archived'.
    """
    merged: dict[str, ExperimentRegistryEntry] = {}
    created: list[str] = []
    changed: list[str] = []
    archived: list[str] = []

    for eid, scan_entry in scanned.items():
        if eid in existing:
            old = existing[eid]
            # Detect if scanner-owned fields changed
            old_dump = {k: old.model_dump(mode="json")[k] for k in _SCANNER_OWNED_FIELDS}
            new_dump = {k: scan_entry.model_dump(mode="json")[k] for k in _SCANNER_OWNED_FIELDS}
            if old_dump != new_dump:
                changed.append(eid)

            # Replace scanner-owned, preserve human-owned
            old_data = old.model_dump(mode="json")
            new_data = scan_entry.model_dump(mode="json")
            for fname in _SCANNER_OWNED_FIELDS:
                old_data[fname] = new_data[fname]
            merged[eid] = ExperimentRegistryEntry(**old_data)
        else:
            merged[eid] = scan_entry.model_copy()
            created.append(eid)

    for eid, old in existing.items():
        if eid not in scanned:
            if old.status != "archived":
                archived.append(eid)
            old_data = old.model_dump(mode="json")
            old_data["status"] = "archived"
            merged[eid] = ExperimentRegistryEntry(**old_data)

    return RegistryReconciliation(
        merged=merged,
        created=created,
        changed=changed,
        archived=archived,
    )


# ---------------------------------------------------------------------------
# Legacy backfill
# ---------------------------------------------------------------------------


def _is_v1_bundle(bundle_dir: Path) -> bool:
    """Check if a bundle uses the v1 direct-child layout (no raw/ directory)."""
    return not (bundle_dir / "raw").is_dir()


def _find_v1_bundles(results_root: Path) -> list[tuple[str, Path]]:
    """Find all v1 bundles under results/experiments."""
    v1: list[tuple[str, Path]] = []
    exp_root = results_root / "experiments"
    if not exp_root.exists():
        return v1
    for phase_dir in sorted(exp_root.iterdir()):
        if not phase_dir.is_dir():
            continue
        for bundle_dir in sorted(phase_dir.iterdir()):
            if not bundle_dir.is_dir():
                continue
            if _is_v1_bundle(bundle_dir):
                v1.append((_make_bundle_id("experiments", bundle_dir.name), bundle_dir))
    return v1


def legacy_backfill(
    results_root: Path,
    *,
    apply: bool,
) -> LegacyBackfillSummary:
    """Logically backfill v1 bundles into the typed registry.

    Preview mode: list v1 bundle IDs and artifact counts.
    Apply mode: reconcile each v1 bundle and append a ``legacy_backfilled`` event.
    Never fabricates lifecycle events or moves raw files.
    """
    v1_bundles = _find_v1_bundles(results_root)
    summary = LegacyBackfillSummary(applied=apply)

    for bundle_id, bundle_dir in v1_bundles:
        summary.v1_bundle_ids.append(bundle_id)
        summary.artifact_counts[bundle_id] = _count_artifacts(bundle_dir)

    if not apply:
        return summary

    # Reconcile all v1 bundles into the registry
    registry_path = results_root / "evidence" / "registry.yaml"
    existing = load_registry(registry_path)
    scanned = scan_bundles(results_root)
    recon = reconcile_registry(existing, scanned)
    write_registry(registry_path, recon.merged)

    # Append one legacy_backfilled event per v1 bundle
    events_path = results_root / "evidence" / "registry-events.jsonl"
    journal = ExperimentJournal(
        path=events_path,
        experiment_id="registry",
        bundle_path=str(results_root / "evidence"),
        git_commit="",
    )
    for bundle_id, bundle_dir in v1_bundles:
        artifact_count = summary.artifact_counts[bundle_id]
        event = journal.new_event(
            "legacy_backfilled",
            payload={
                "source_layout": "v1",
                "bundle_id": bundle_id,
                "raw_artifacts_preserved": True,
                "historical_lifecycle_not_reconstructed": True,
                "source_artifact_count": artifact_count,
            },
        )
        journal.record(event)
        summary.events_appended += 1

    return summary


# ---------------------------------------------------------------------------
# Audit event helper
# ---------------------------------------------------------------------------


def append_registry_audited_event(
    events_path: Path,
    results_root: Path,
    recon: RegistryReconciliation,
) -> ExperimentJournalEvent:
    """Append a ``registry_audited`` governance event."""
    journal = ExperimentJournal(
        path=events_path,
        experiment_id="registry",
        bundle_path=str(results_root / "evidence"),
        git_commit="",
    )
    event = journal.new_event(
        "registry_audited",
        payload={
            "created": recon.created,
            "changed": recon.changed,
            "archived": recon.archived,
            "total_bundles": len(recon.merged),
        },
    )
    journal.record(event)
    return event


def read_governance_events(events_path: Path) -> list[ExperimentJournalEvent]:
    """Read governance events from the registry-events.jsonl."""
    if not events_path.exists():
        return []
    events: list[ExperimentJournalEvent] = []
    for line in events_path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            data = json.loads(line)
            events.append(ExperimentJournalEvent(**data))
        except Exception:
            continue
    return events
