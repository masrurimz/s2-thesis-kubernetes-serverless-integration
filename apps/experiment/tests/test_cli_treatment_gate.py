"""Tests for the S4 treatment-fidelity gate wired into _run_single.

Mocks the heavy infra stages (reset/daemon/workload/collect/provisioner) around
``_run_single`` to prove a failed S4 prediction preflight yields a durable
invalid run (no workload, ordered lifecycle events) and a healthy S4 completes
with full delivery.
"""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from rich.console import Console

from experiment.cli import _run_single
from shared.models.experiment import ExperimentConfig
from shared.storage.journal import ExperimentJournal


class _StageResult:
    def __init__(self, success: bool = True, error: str = "") -> None:
        self.success = success
        self.error = error


@contextmanager
def _fake_countdown(*_args, **_kw):  # noqa: ANN202
    yield


@contextmanager
def _fake_run_phase(*_args, **_kw):  # noqa: ANN202
    phase = MagicMock()
    phase.tasks = []
    yield phase


def _install_stages(
    monkeypatch: pytest.MonkeyPatch,
    *,
    preflight_ok: bool,
    daemon_status: dict | None = None,
    provision_events: list[tuple[float, str, dict]] | None = None,
) -> dict:
    """Replace the heavy stages used by _run_single with controllable fakes.

    Returns a mutable ``workload_ran`` flag so a test can assert the workload
    was (or was not) executed.
    """
    workload_ran = {"value": False}

    class _FakeReset:
        def __init__(self, *_a, **_kw) -> None: ...

        def execute(self, _ctx):
            return _StageResult(success=True)

    class _FakeDaemon:
        def __init__(self, *_a, **_kw) -> None: ...

        def execute(self, _ctx):
            return _StageResult(success=True)

        def require_prediction_service(self):
            if preflight_ok:
                return (
                    True,
                    "",
                    {
                        "loaded": True,
                        "sequence_length": 30,
                        "prediction_horizon": 5,
                        "sample_interval_sec": 15,
                    },
                )
            return False, "prediction health preflight failed: Connection refused", {}

        def get_status(self):
            return daemon_status or {}

        def stop_daemon(self) -> None: ...

    class _FakeWorkload:
        def __init__(self, *_a, **_kw) -> None: ...

        def _run(self, _ctx, *, on_progress=None) -> None:
            workload_ran["value"] = True

    class _FakeCollect:
        def __init__(self, *_a, **_kw) -> None: ...

        def start_resource_polling(self) -> None: ...

        def stop_resource_polling(self) -> None: ...

        def execute(self, _ctx):
            return _StageResult(success=True)

    class _FakeProvisioner:
        def __init__(self, *_a, **_kw) -> None: ...
        def clear_log(self) -> None: ...

        def start_background(self) -> None: ...

        def stop(self) -> None: ...

        def get_log(self):
            return provision_events if provision_events is not None else []

    monkeypatch.setattr("experiment.stages.reset.ResetStage", _FakeReset)
    monkeypatch.setattr("experiment.stages.daemon.DaemonStage", _FakeDaemon)
    monkeypatch.setattr("experiment.stages.workload.WorkloadStage", _FakeWorkload)
    monkeypatch.setattr("infra.cluster.k3d.autoscaler.K3dAutoscalerAdapter", _FakeProvisioner)
    monkeypatch.setattr("shared.progress.countdown", _fake_countdown)
    monkeypatch.setattr("shared.progress.run_phase", _fake_run_phase)
    return workload_ran


def _config() -> ExperimentConfig:
    return ExperimentConfig(phase="experiments", runs=1, duration_sec=30, seed=42)


def _read_events(run_dir: Path, out_dir: Path) -> list:
    return ExperimentJournal(run_dir / "events.jsonl", out_dir.name, str(out_dir)).read_all()


class TestS4PreflightFailure:
    """Failed GRU health preflight invalidates the run before any workload."""

    def test_invalid_result_no_workload_ordered_events(self, tmp_path, monkeypatch):
        workload_ran = _install_stages(monkeypatch, preflight_ok=False)
        out_dir = tmp_path / "bundle"
        out_dir.mkdir()

        result = _run_single(
            "s4-hybrid-predictive",
            1,
            0,
            _config(),
            str(out_dir),
            console=Console(quiet=True),
        )

        # Durable invalid result
        assert result is not None
        assert result.run_validity_passed is False
        assert result.validity_gate_passed is False
        assert result.treatment_fidelity is not None
        assert result.treatment_fidelity.required is True
        assert result.treatment_fidelity.preflight_passed is False
        assert result.treatment_fidelity.delivered is False

        # Workload never ran
        assert workload_ran["value"] is False

        # Persisted invalid result; no Parquet artifact produced
        run_dir = out_dir / "s4-hybrid-predictive_run1"
        assert (run_dir / "result.json").exists()
        assert not list(run_dir.glob("*.parquet"))

        # Ordered lifecycle events
        events = _read_events(run_dir, out_dir)
        kinds = [e.event for e in events]
        assert "prediction_preflight_failed" in kinds
        assert "run_failed" in kinds
        assert kinds.index("prediction_preflight_failed") < kinds.index("run_failed")
        assert "workload_completed" not in kinds
        assert "run_completed" not in kinds


class TestS4HealthyCompletes:
    """Healthy S4 completes with full delivery and the full event sequence."""

    def test_full_delivery_and_run_completed(self, tmp_path, monkeypatch):
        _install_stages(
            monkeypatch,
            preflight_ok=True,
            daemon_status={
                "maintain_count": 1,
                "predictive_count": 2,
                "prediction_eligible_cycles": 5,
                "prediction_delivery_failures": 0,
                "model_history_ready": True,
                "forecast_horizon_sufficient": True,
                "forecast_actionable_cycles": 2,
                "proactive_scaleups": 1,
            },
            provision_events=[
                (0.0, "autoscaler_started", {}),
                (10.0, "pending_detected", {}),
                (110.0, "node_created", {}),
                (110.0, "autoscaler_stopped", {}),
            ],
        )
        out_dir = tmp_path / "bundle"
        out_dir.mkdir()

        result = _run_single(
            "s4-hybrid-predictive",
            1,
            0,
            _config(),
            str(out_dir),
            console=Console(quiet=True),
        )

        assert result is not None
        assert result.run_validity_passed is True
        assert result.treatment_fidelity is not None
        assert result.treatment_fidelity.delivered is True
        assert result.treatment_fidelity.delivery_rate == 1.0
        assert result.treatment_fidelity.eligible_cycles == 5
        assert result.node_engagement is not None
        assert result.node_engagement.autoscaler_engaged is True
        assert result.node_engagement.nodes_provisioned == 1
        assert result.first_provision_delay_sec == 100.0

        run_dir = out_dir / "s4-hybrid-predictive_run1"
        events = _read_events(run_dir, out_dir)
        kinds = [e.event for e in events]
        assert kinds[0] == "run_started"
        assert "prediction_preflight_passed" in kinds
        assert "validity_evaluated" in kinds
        assert kinds[-1] == "run_completed"
