"""Tests for paired_run() treatment-validity gate and retry semantics.

Mocks ``_run_single`` to feed controlled S3/S4 results so we can prove:
  * a partial S4 pair is excluded but its raw run directories are retained;
  * retries continue until the requested number of fully-valid pairs is reached;
  * hitting ``pairs * 2`` attempts without enough valid pairs yields
    ``status: insufficient_valid_pairs`` and a nonzero exit.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest
import typer

from experiment.cli import paired_run
from shared.models.evidence import TreatmentFidelity
from shared.models.experiment import ExperimentResult
from shared.storage.journal import ExperimentJournal


def _fake_countdown(*_a, **_kw):  # noqa: ANN202
    class _Ctx:
        def __enter__(self):  # noqa: ANN204
            return None

        def __exit__(self, *_exc):  # noqa: ANN204
            return False

    return _Ctx()


def _install_fake_run_single(monkeypatch, *, s4_delivered_seq):
    """Fake _run_single that materializes run dirs + result.json.

    ``s4_delivered_seq`` controls S4 delivery in call order (cycled if exhausted).
    S3 runs are always valid; an undelivered S4 run is also run_validity_passed=False.
    """
    state = {"s4_calls": 0}

    def _fake(scenario, run_id, _order, _config, output_dir, *, console=None):
        run_dir = Path(output_dir) / f"{scenario}_run{run_id}"
        run_dir.mkdir(parents=True, exist_ok=True)
        is_s4 = "s4" in scenario or "predictive" in scenario

        delivered = True
        if is_s4:
            delivered = s4_delivered_seq[state["s4_calls"] % len(s4_delivered_seq)]
            state["s4_calls"] += 1

        result = ExperimentResult(
            scenario=scenario,
            run_id=run_id,
            timestamp="2026-07-12T00:00:00",
            p99_latency_ms=100.0,
            run_validity_passed=delivered,
            treatment_fidelity=TreatmentFidelity(
                required=is_s4,
                delivered=delivered,
                eligible_cycles=5 if is_s4 else 0,
                successful_predictions=5 if (is_s4 and delivered) else 0,
                failed_predictions=0 if delivered else 5,
                delivery_rate=1.0 if delivered else 0.0,
                reasons=[] if delivered else ["prediction delivery failed"],
            ),
        )
        (run_dir / "result.json").write_text(result.model_dump_json(indent=2))
        return result

    monkeypatch.setattr("experiment.cli._run_single", _fake)
    return state


def _install_stats(monkeypatch):
    """Stub the paired statistical comparison so the success path completes."""
    comp = MagicMock()
    comp.baseline_mean = 100.0
    comp.comparison_mean = 90.0
    comp.mean_difference = -10.0
    comp.paired_ci_lower = -20.0
    comp.paired_ci_upper = -5.0
    comp.permutation_p_value = 0.04
    comp.cohens_d_paired = 0.5
    comp.effect_size_interpretation = "medium"
    comp.h2_supported = True
    comp.metric = "p99_latency_ms"
    comp.permutation_p_corrected = 0.04
    comp.model_dump.return_value = {"metric": "p99_latency_ms"}
    monkeypatch.setattr("analysis.comparison.run_paired_comparison", lambda *a, **k: comp)
    monkeypatch.setattr("analysis.comparison.apply_holm_paired", lambda _secondaries: None)


def _read_bundle_events(out_dir):
    return ExperimentJournal(out_dir / "events.jsonl", out_dir.name, str(out_dir)).read_all()


@pytest.fixture(autouse=True)
def _no_sleeps(monkeypatch):
    monkeypatch.setattr("shared.progress.countdown", _fake_countdown)


class TestPartialS4Excluded:
    """A partial S4 pair is excluded; raw dirs retained; insufficient exit."""

    def test_partial_s4_excluded_insufficient(self, tmp_path, monkeypatch):
        _install_fake_run_single(monkeypatch, s4_delivered_seq=[False])
        out_dir = tmp_path / "bundle"
        out_dir.mkdir()

        with pytest.raises((typer.Exit, SystemExit)) as exc_info:
            paired_run(
                pairs=1,
                duration=30,
                seed=42,
                workload="clarknet",
                controller="v3",
                calibration=None,
                output=str(out_dir),
                dry_run=False,
            )

        assert getattr(exc_info.value, "exit_code", 1) == 1

        # Insufficient-valid-pairs analysis written
        analysis = json.loads((out_dir / "paired_analysis.json").read_text())
        assert analysis["status"] == "insufficient_valid_pairs"
        assert analysis["n_valid_pairs"] == 0

        # Raw run directories retained (never deleted)
        assert (out_dir / "s4-hybrid-predictive_run1" / "result.json").exists()
        assert (out_dir / "s3-hybrid-reactive_run1" / "result.json").exists()

        # Bundle journal records pair exclusion
        events = _read_bundle_events(out_dir)
        kinds = [e.event for e in events]
        assert kinds.count("pair_excluded") >= 1


class TestRetriesUntilValid:
    """Retries continue until the requested number of valid pairs is collected."""

    def test_retries_then_completes_valid_pairs(self, tmp_path, monkeypatch):
        _install_stats(monkeypatch)
        # First S4 undelivered (excluded), then two delivered (accepted).
        _install_fake_run_single(monkeypatch, s4_delivered_seq=[False, True, True])
        out_dir = tmp_path / "bundle"
        out_dir.mkdir()

        paired_run(
            pairs=2,
            duration=30,
            seed=42,
            workload="clarknet",
            controller="v3",
            calibration=None,
            output=str(out_dir),
            dry_run=False,
        )

        # Proceeded to a full paired analysis (not insufficient)
        analysis = json.loads((out_dir / "paired_analysis.json").read_text())
        assert "status" not in analysis or analysis.get("status") != "insufficient_valid_pairs"
        assert analysis["n_pairs"] == 2

        # Exactly one pair was excluded before two valid pairs were collected
        events = _read_bundle_events(out_dir)
        kinds = [e.event for e in events]
        assert kinds.count("pair_excluded") == 1


class TestAllAttemptsFail:
    """pairs * 2 failed attempts yield insufficient_valid_pairs."""

    def test_all_fail_insufficient(self, tmp_path, monkeypatch):
        _install_fake_run_single(monkeypatch, s4_delivered_seq=[False])
        out_dir = tmp_path / "bundle"
        out_dir.mkdir()

        with pytest.raises((typer.Exit, SystemExit)):
            paired_run(
                pairs=2,
                duration=30,
                seed=42,
                workload="clarknet",
                controller="v3",
                calibration=None,
                output=str(out_dir),
                dry_run=False,
            )

        analysis = json.loads((out_dir / "paired_analysis.json").read_text())
        assert analysis["status"] == "insufficient_valid_pairs"
        assert analysis["n_valid_pairs"] == 0
        # max_attempts = pairs * 2 = 4
        assert analysis["attempts"] == 4
