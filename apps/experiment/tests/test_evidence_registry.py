"""Tests for the typed evidence registry scanner, reconciler, and backfill.

These tests create temporary bundle fixtures with both v1 (direct-child) and v2
(raw/ subdirectory) layouts and verify:
- Repeated reconciliation preserves human-owned fields.
- v2 paired bundles with partial S4 delivery have fewer valid runs.
- v1 bundles remain discoverable.
- Disappeared bundles archive rather than disappear.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from experiment.evidence.registry import (
    legacy_backfill,
    load_registry,
    reconcile_registry,
    scan_bundles,
    write_registry,
)
from shared.models.evidence import ExperimentRegistryEntry, TreatmentFidelity

# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------


def _make_result(
    scenario: str = "s4-hybrid-predictive",
    run_id: int = 1,
    *,
    run_validity: bool = True,
    stress_validity: bool = True,
    treatment_fidelity: TreatmentFidelity | None = None,
    gru_used: int = 0,
    gru_failed: int = 0,
) -> dict:
    """Build a minimal result.json payload."""
    payload: dict = {
        "scenario": scenario,
        "run_id": run_id,
        "timestamp": "2026-07-12T00:00:00",
        "run_validity_passed": run_validity,
        "stress_validity_passed": stress_validity,
        "gru_predictions_used": gru_used,
        "gru_predictions_failed": gru_failed,
    }
    if treatment_fidelity is not None:
        payload["treatment_fidelity"] = treatment_fidelity.model_dump(mode="json")
    return payload


def _make_v2_bundle(
    base: Path,
    phase: str,
    slug: str,
    runs: list[dict],
) -> Path:
    """Create a v2 bundle under base/experiments/phase/slug with raw/ layout."""
    bundle = base / "experiments" / phase / slug
    bundle.mkdir(parents=True, exist_ok=True)
    (bundle / "meta.yaml").write_text("bundle_schema_version: 2\n")
    (bundle / "report.md").write_text("# Report\n3 clean\n")
    raw = bundle / "raw"
    raw.mkdir(exist_ok=True)
    for run_payload in runs:
        scenario = run_payload["scenario"]
        rid = run_payload["run_id"]
        run_dir = raw / f"{scenario}_run{rid}"
        run_dir.mkdir(exist_ok=True)
        (run_dir / "result.json").write_text(json.dumps(run_payload))
        (run_dir / "manifest.json").write_text(
            json.dumps(
                {
                    "scenario": scenario,
                    "run_id": rid,
                    "git_commit": "abc1234",
                }
            )
        )
    return bundle


def _make_v1_bundle(
    base: Path,
    phase: str,
    slug: str,
    runs: list[dict],
) -> Path:
    """Create a v1 bundle with direct-child run directories."""
    bundle = base / "experiments" / phase / slug
    bundle.mkdir(parents=True, exist_ok=True)
    (bundle / "meta.yaml").write_text("version: 1\n")
    for run_payload in runs:
        scenario = run_payload["scenario"]
        rid = run_payload["run_id"]
        run_dir = bundle / f"{scenario}_run{rid}"
        run_dir.mkdir(exist_ok=True)
        (run_dir / "result.json").write_text(json.dumps(run_payload))
    return bundle


@pytest.fixture()
def results_root(tmp_path: Path) -> Path:
    """Create a results/ root with fixture bundles."""
    base = tmp_path / "results"
    base.mkdir()
    return base


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestScanBundles:
    """Bundle scanning tests."""

    def test_v1_bundle_discoverable(self, results_root: Path):
        """A v1 (direct-child) bundle is scanned and discoverable."""
        _make_v1_bundle(
            results_root,
            "phase-b",
            "2026-07-11_legacy",
            [
                _make_result("s3-hybrid-reactive", 1),
                _make_result("s4-hybrid-predictive", 1, gru_used=5, gru_failed=0),
            ],
        )
        entries = scan_bundles(results_root)
        assert len(entries) == 1
        entry = list(entries.values())[0]
        assert entry.n_runs_total == 2
        assert entry.has_meta is True
        # Both runs pass validity
        assert entry.n_runs_valid == 2

    def test_v2_bundle_with_partial_s4_delivery(self, results_root: Path):
        """A v2 paired bundle with partial S4 delivery has fewer valid runs."""
        good_fid = TreatmentFidelity(
            required=True,
            eligible_cycles=10,
            successful_predictions=10,
            failed_predictions=0,
            delivery_rate=1.0,
            delivered=True,
        )
        bad_fid = TreatmentFidelity(
            required=True,
            eligible_cycles=10,
            successful_predictions=3,
            failed_predictions=7,
            delivery_rate=0.3,
            delivered=False,
            reasons=["prediction delivery failures"],
        )
        _make_v2_bundle(
            results_root,
            "phase-b",
            "2026-07-12_paired",
            [
                _make_result("s3-hybrid-reactive", 1),
                _make_result("s4-hybrid-predictive", 1, treatment_fidelity=good_fid),
                _make_result("s3-hybrid-reactive", 2),
                _make_result("s4-hybrid-predictive", 2, treatment_fidelity=bad_fid),
            ],
        )
        entries = scan_bundles(results_root)
        entry = list(entries.values())[0]
        assert entry.n_runs_total == 4
        # S4 run 2 is invalid due to treatment delivery failure
        assert entry.n_runs_valid == 3
        assert entry.treatment_fidelity is not None
        assert entry.treatment_fidelity.required is True
        assert entry.treatment_fidelity.delivered is False

    def test_scenario_normalization(self, results_root: Path):
        """Short scenario names (s1-k) normalize to canonical (s1-k8s-only)."""
        _make_v1_bundle(
            results_root,
            "phase-b",
            "2026-02-14_old",
            [
                _make_result("s1-k", 1),
            ],
        )
        entries = scan_bundles(results_root)
        entry = list(entries.values())[0]
        assert "s1-k8s-only" in entry.scenarios
        assert "s1-k" not in entry.scenarios

    def test_events_only_bundle_falls_back_to_journal_validity(self, results_root: Path):
        """Bundles whose result.json was never committed still scan as valid.

        Regression guard: evidence refresh must not silently downgrade
        n_runs_valid/treatment_fidelity to 0 when per-run result.json is
        missing but the run journal (events.jsonl) recorded the validity
        verdict and S4 treatment fidelity.
        """
        bundle = results_root / "experiments" / "phase-b" / "2026-08-07_paired-h2_eventsonly"
        bundle.mkdir(parents=True)
        (bundle / "meta.yaml").write_text("bundle_schema_version: 2\n")

        def _events(scenario: str, run_id: int, *, s4: bool = False) -> None:
            run_dir = bundle / f"{scenario}_run{run_id}"
            run_dir.mkdir()
            payload: dict = {
                "run_validity_passed": True,
            }
            if s4:
                payload["treatment_fidelity"] = TreatmentFidelity(
                    required=True,
                    eligible_cycles=56,
                    successful_predictions=56,
                    failed_predictions=0,
                    delivery_rate=1.0,
                    delivered=True,
                    forecast_horizon_sufficient=True,
                ).model_dump(mode="json")
            (run_dir / "events.jsonl").write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "event": "validity_evaluated",
                        "git_commit": "237ec40",
                        "payload": payload,
                    }
                )
                + "\n"
            )

        for rid in (1, 2, 3):
            _events("s3-hybrid-reactive", rid)
            _events("s4-hybrid-predictive", rid, s4=True)

        entries = scan_bundles(results_root)
        entry = list(entries.values())[0]
        assert entry.n_runs_total == 6
        assert entry.n_runs_valid == 6
        assert entry.treatment_fidelity is not None
        assert entry.treatment_fidelity.delivered is True
        assert entry.treatment_fidelity.eligible_cycles == 168
        assert "237ec40" in entry.git_commits

    def test_events_only_bundle_invalid_run_stays_invalid(self, results_root: Path):
        """A journal verdict of failed validity is respected by the fallback."""
        bundle = results_root / "experiments" / "phase-b" / "2026-08-07_paired-h2_invalid"
        bundle.mkdir(parents=True)
        (bundle / "meta.yaml").write_text("bundle_schema_version: 2\n")
        run_dir = bundle / "s3-hybrid-reactive_run1"
        run_dir.mkdir()
        (run_dir / "events.jsonl").write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "event": "validity_evaluated",
                    "payload": {"run_validity_passed": False},
                }
            )
            + "\n"
        )
        entries = scan_bundles(results_root)
        entry = list(entries.values())[0]
        assert entry.n_runs_total == 1
        assert entry.n_runs_valid == 0


class TestReconcileRegistry:
    """Merge-safe reconciliation tests."""

    def test_repeated_reconciliation_preserves_human_fields(self, results_root: Path):
        """Human-owned fields survive repeated reconciliation."""
        _make_v2_bundle(
            results_root,
            "phase-b",
            "2026-07-12_test",
            [
                _make_result("s3-hybrid-reactive", 1),
            ],
        )

        scanned = scan_bundles(results_root)

        # First reconcile: create entries
        recon1 = reconcile_registry({}, scanned)
        assert len(recon1.created) == 1

        # Simulate human editing fields
        eid = list(recon1.merged.keys())[0]
        human_entry = recon1.merged[eid].model_copy(
            update={
                "role": "final",
                "notes": "Human evidence decision",
                "claims_supported": ["H2"],
            }
        )

        # Second reconcile: should preserve human fields
        recon2 = reconcile_registry({eid: human_entry}, scanned)
        merged_entry = recon2.merged[eid]
        assert merged_entry.role == "final"
        assert merged_entry.notes == "Human evidence decision"
        assert merged_entry.claims_supported == ["H2"]

    def test_disappeared_bundle_archived_not_deleted(self, results_root: Path):
        """A bundle that disappears is archived, not deleted."""
        _make_v2_bundle(
            results_root,
            "phase-b",
            "2026-07-12_gone",
            [
                _make_result("s3-hybrid-reactive", 1),
            ],
        )

        scanned = scan_bundles(results_root)
        recon1 = reconcile_registry({}, scanned)
        eid = list(recon1.merged.keys())[0]

        # Now scan an empty root (bundle disappeared)
        empty_scanned: dict[str, ExperimentRegistryEntry] = {}
        recon2 = reconcile_registry(recon1.merged, empty_scanned)
        assert eid in recon2.merged
        assert eid in recon2.archived
        assert recon2.merged[eid].status == "archived"

    def test_new_bundle_gets_suggested_role(self, results_root: Path):
        """A new bundle gets the scanner-suggested role and status='current'."""
        _make_v2_bundle(
            results_root,
            "phase-b",
            "2026-07-12_new",
            [
                _make_result("s3-hybrid-reactive", 1),
            ],
        )
        scanned = scan_bundles(results_root)
        recon = reconcile_registry({}, scanned)
        entry = list(recon.merged.values())[0]
        assert entry.role in ("intermediate", "diagnostic")
        assert entry.status == "current"

    def test_registry_round_trip(self, results_root: Path, tmp_path: Path):
        """Registry YAML round-trips through load/write."""
        _make_v2_bundle(
            results_root,
            "phase-b",
            "2026-07-12_rt",
            [
                _make_result("s3-hybrid-reactive", 1),
            ],
        )
        scanned = scan_bundles(results_root)
        registry_path = tmp_path / "registry.yaml"
        write_registry(registry_path, scanned)
        loaded = load_registry(registry_path)
        assert set(loaded.keys()) == set(scanned.keys())
        eid = list(scanned.keys())[0]
        assert loaded[eid].n_runs_total == scanned[eid].n_runs_total
        assert loaded[eid].n_runs_valid == scanned[eid].n_runs_valid


class TestLegacyBackfill:
    """Legacy v1 backfill tests."""

    def test_preview_mode_lists_without_writing(self, results_root: Path):
        """Preview mode lists bundles without writing registry or events."""
        _make_v1_bundle(
            results_root,
            "phase-b",
            "2026-02-14_legacy",
            [
                _make_result("s3-hybrid-reactive", 1),
            ],
        )
        summary = legacy_backfill(results_root, apply=False)
        assert len(summary.v1_bundle_ids) == 1
        assert summary.applied is False
        assert summary.events_appended == 0
        # No registry file should have been written
        assert not (results_root / "evidence" / "registry.yaml").exists()

    def test_apply_mode_writes_registry_and_events(self, results_root: Path):
        """Apply mode writes registry and appends legacy_backfilled events."""
        _make_v1_bundle(
            results_root,
            "phase-b",
            "2026-02-14_legacy",
            [
                _make_result("s3-hybrid-reactive", 1),
            ],
        )
        summary = legacy_backfill(results_root, apply=True)
        assert summary.applied is True
        assert summary.events_appended == 1

        # Registry should exist and contain the bundle
        registry_path = results_root / "evidence" / "registry.yaml"
        assert registry_path.exists()
        loaded = load_registry(registry_path)
        assert len(loaded) >= 1

        # Events should exist
        events_path = results_root / "evidence" / "registry-events.jsonl"
        assert events_path.exists()
        lines = [line for line in events_path.read_text().splitlines() if line.strip()]
        assert len(lines) == 1
        event = json.loads(lines[0])
        assert event["event"] == "legacy_backfilled"
        assert event["payload"]["source_layout"] == "v1"
        assert event["payload"]["raw_artifacts_preserved"] is True


class TestPairedAnalysisCounts:
    """A bundle with a paired analysis is counted wherever that analysis sits.

    Every bundle on disk writes it at the bundle root, while the flag used to check only
    `derived/`, so the registry reported no paired analysis for any of them.
    """

    @staticmethod
    def _bundle(root: Path, name: str, *, layout: str) -> Path:
        bundle = root / "experiments" / "phase-b" / name
        bundle.mkdir(parents=True)
        (bundle / "meta.yaml").write_text("bundle_schema_version: 2\n")
        analysis = bundle / "paired_analysis.json" if layout == "root" else bundle / "derived" / "paired_analysis.json"
        analysis.parent.mkdir(parents=True, exist_ok=True)
        analysis.write_text(json.dumps({"n_pairs": 5, "h2_supported": True}))
        return bundle

    def test_root_layout_is_counted(self, tmp_path: Path):
        self._bundle(tmp_path, "2026-09-12_pairs", layout="root")

        entries = scan_bundles(tmp_path)

        assert [entry.has_paired_analysis for entry in entries.values()] == [True]

    def test_derived_layout_is_counted(self, tmp_path: Path):
        self._bundle(tmp_path, "2026-09-12_pairs", layout="derived")

        entries = scan_bundles(tmp_path)

        assert [entry.has_paired_analysis for entry in entries.values()] == [True]

    def test_no_analysis_is_not_counted(self, tmp_path: Path):
        bundle = self._bundle(tmp_path, "2026-09-12_baselines", layout="root")
        (bundle / "paired_analysis.json").unlink()

        entries = scan_bundles(tmp_path)

        assert [entry.has_paired_analysis for entry in entries.values()] == [False]
