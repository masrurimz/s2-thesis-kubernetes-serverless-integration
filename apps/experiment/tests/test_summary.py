"""Tests for experiment.summary bundle summaries."""

from __future__ import annotations

import json
from pathlib import Path

from experiment.summary import build_summary, write_summary

_FIDELITY = {
    "required": True,
    "preflight_passed": True,
    "eligible_cycles": 10,
    "successful_predictions": 9,
    "failed_predictions": 1,
    "delivery_rate": 0.9,
    "delivered": True,
    "model_history_ready": True,
    "forecast_horizon_sufficient": True,
    "forecast_actionable_cycles": 0,
    "proactive_scaleups": 0,
    "reasons": [],
}


def _make_run(
    bundle: Path,
    scenario: str,
    run_id: int,
    *,
    valid: bool = True,
    notes: list[str] | None = None,
    fidelity: dict | None = None,
    **fields,
) -> None:
    run_dir = bundle / f"{scenario}_run{run_id}"
    run_dir.mkdir()
    result: dict = {
        "scenario": scenario,
        "run_id": run_id,
        "nodes_provisioned": fields.pop("nodes_provisioned", 0),
        "first_provision_delay_sec": fields.pop("first_provision_delay_sec", 0.0),
        "validity_gate_passed": valid,
        "validity_gate_notes": notes or [],
        "run_validity_passed": valid,
        "run_validity_notes": [],
        "stress_validity_passed": True,
        "stress_validity_notes": [],
    }
    result.update(fields)
    if fidelity is not None:
        result["treatment_fidelity"] = fidelity
    (run_dir / "result.json").write_text(json.dumps(result))
    (run_dir / "manifest.json").write_text(json.dumps({"git_commit": "abc1234"}))


def _make_beta_events(bundle: Path, run_id: int) -> None:
    event = {
        "event": "prediction_preflight_passed",
        "payload": {
            "model_status": {
                "model_path": "data/models/gru_model.pt",
                "model_type": "pytorch",
            }
        },
    }
    (bundle / f"beta_run{run_id}" / "events.jsonl").write_text(json.dumps(event) + "\n")


def _synthetic_bundle(tmp_path: Path) -> Path:
    bundle = tmp_path / "2026-09-11_synthetic-paired-n3"
    bundle.mkdir()
    (bundle / "meta.yaml").write_text(
        "bundle_schema_version: 2\n"
        "name: 2026-09-11_synthetic-paired-n3\n"
        "date: 2026-09-11\n"
        "scenarios: ['alpha', 'beta']\n"
        "runs: 3\n"
        "status: complete\n"
    )

    _make_run(
        bundle,
        "alpha",
        1,
        p50_latency_ms=60.0,
        p95_latency_ms=80.0,
        p99_latency_ms=100.0,
        error_rate=0.0,
        throughput_rps=70.0,
        slo_violations_k6=5,
        k8s_replica_seconds=1000.0,
        time_in_serverless_pct=10.0,
    )
    _make_run(
        bundle,
        "alpha",
        2,
        valid=False,
        notes=["error_rate above threshold (0.12 > 0.05)"],
        p50_latency_ms=65.0,
        p95_latency_ms=82.0,
        p99_latency_ms=110.0,
        error_rate=0.12,
        throughput_rps=71.0,
        slo_violations_k6=50,
        k8s_replica_seconds=1100.0,
        time_in_serverless_pct=15.0,
    )
    _make_run(
        bundle,
        "alpha",
        3,
        p50_latency_ms=70.0,
        p95_latency_ms=85.0,
        p99_latency_ms=120.0,
        error_rate=0.0,
        throughput_rps=72.0,
        slo_violations_k6=7,
        k8s_replica_seconds=1200.0,
        time_in_serverless_pct=20.0,
    )

    for run_id, (p99, slo, rep) in {
        1: (130.0, 9, 1100.0),
        2: (140.0, 10, 1150.0),
        3: (155.0, 20, 1300.0),
    }.items():
        _make_run(
            bundle,
            "beta",
            run_id,
            p50_latency_ms=61.0 + run_id,
            p95_latency_ms=90.0 + run_id,
            p99_latency_ms=p99,
            error_rate=0.0,
            throughput_rps=70.5 + run_id * 0.5,
            slo_violations_k6=slo,
            k8s_replica_seconds=rep,
            fidelity={**_FIDELITY, "delivered": run_id != 3},
        )
        _make_beta_events(bundle, run_id)
    return bundle


def test_build_summary_reports_headline_paired_and_rejections(tmp_path: Path) -> None:
    summary = build_summary(_synthetic_bundle(tmp_path))

    assert "- Git commit: abc1234" in summary
    assert "- Scenarios: alpha, beta" in summary

    # Headline: alpha aggregates cover only gate-passing runs 1 and 3.
    # p50/p95/p99 over valid runs (60,70)/(80,85)/(100,120).
    assert "| alpha | 3 | 65.0 | 82.5 | 110.0 | 0.0000 | 71.0 | 6.0 | 1100.0 | 15.0 | 2/3 |" in summary
    # beta has no time_in_serverless_pct anywhere, so that cell must be n/a.
    assert "| beta | 3 | 63.0 | 92.0 | 141.7 | 0.0000 | 71.5 | 13.0 | 1183.3 | n/a | 3/3 |" in summary

    assert "## Paired comparison — beta vs alpha" in summary
    assert "2 of 3 pairs passed" in summary
    assert "| run 1 | 100.0 | 130.0 | +30.0 | 5.0 | 9.0 | +4.0 |" in summary
    assert "| run 2 | 110.0 | 140.0 | +30.0 | 50.0 | 10.0 | -40.0 |" in summary
    assert "| run 3 | 120.0 | 155.0 | +35.0 | 7.0 | 20.0 | +13.0 |" in summary

    # Pair diffs (30, 35): mean +32.5, d = 32.5/3.5355 = 9.19. The effect runs
    # against H1 (S4 slower), so every sign flip is at or below the observed mean and
    # the exact one-sided p is 1.0 — no evidence for H2, which is the correct reading.
    assert (
        "Mean Δp99 latency: +32.5 ms, paired Cohen's d: 9.19, "
        "exact one-sided permutation p (H1: S4 faster): 1.0000 (does not clear 0.05)." in summary
    )
    # Pair diffs (4, 13): mean +8.5, d = 8.5/6.3640 = 1.34, same adverse direction.
    assert (
        "Mean ΔSLO violations: +8.5, paired Cohen's d: 1.34, "
        "exact one-sided permutation p (H1: S4 faster): 1.0000 (does not clear 0.05)." in summary
    )

    assert "Model artifact: n/a" in summary
    assert "Model artifact: data/models/gru_model.pt (pytorch)" in summary

    assert "| beta | 30 | 27 | 0.900 | no |" in summary

    assert "alpha run 2 rejected by the validity gate: error_rate above threshold (0.12 > 0.05)." in summary
    assert "beta run 3 treatment_fidelity.delivered is false." in summary


def test_write_summary_writes_file_and_returns_path(tmp_path: Path) -> None:
    bundle = _synthetic_bundle(tmp_path)

    path = write_summary(bundle)

    assert path == bundle / "SUMMARY.md"
    assert path.exists()
    assert path.read_text() == build_summary(bundle)


def test_summary_reports_a_hybrid_run_that_never_reached_the_node_tier(tmp_path: Path) -> None:
    bundle = tmp_path / "2026-01-01_node-tier-empty"
    bundle.mkdir()
    (bundle / "meta.yaml").write_text(
        "bundle_schema_version: 2\nname: node-tier-empty\ndate: 2026-01-01\n"
        "scenarios: ['s3-hybrid-reactive', 's4-hybrid-predictive']\nruns: 1\nstatus: complete\n"
    )
    _make_run(
        bundle,
        "s3-hybrid-reactive",
        1,
        node_engagement={
            "required": True,
            "autoscaler_engaged": True,
            "pending_events": 2,
            "nodes_provisioned": 2,
            "first_provision_delay_sec": 95.0,
            "reasons": [],
        },
    )
    _make_run(
        bundle,
        "s4-hybrid-predictive",
        1,
        node_engagement={
            "required": True,
            "autoscaler_engaged": False,
            "pending_events": 0,
            "nodes_provisioned": 0,
            "first_provision_delay_sec": 0.0,
            "reasons": ["node tier not exercised"],
        },
    )

    summary = build_summary(bundle)

    assert "## Node tier" in summary
    assert "| s3-hybrid-reactive | yes | 2 | 2 | 95.0 |" in summary
    assert "| s4-hybrid-predictive | no | 0 | 0 | n/a |" in summary
    assert "s4-hybrid-predictive run 1 never exercised the node tier." in summary


def test_summary_derives_engagement_for_bundles_that_predate_the_field(tmp_path: Path) -> None:
    """Older bundles carry no node_engagement: their provisioner events classify them."""
    bundle = tmp_path / "2026-01-01_legacy-n5"
    bundle.mkdir()
    (bundle / "meta.yaml").write_text(
        "bundle_schema_version: 2\nname: legacy-n5\ndate: 2026-01-01\n"
        "scenarios: ['s3-hybrid-reactive']\nruns: 1\nstatus: complete\n"
    )
    _make_run(bundle, "s3-hybrid-reactive", 1)
    run_dir = bundle / "s3-hybrid-reactive_run1"
    result = json.loads((run_dir / "result.json").read_text())
    result["nodes_provisioned"] = 0
    result["provision_log_path"] = str(run_dir / "provision_events.json")
    (run_dir / "result.json").write_text(json.dumps(result))
    (run_dir / "provision_events.json").write_text(
        json.dumps(
            [
                {"ts": 0.0, "event": "autoscaler_started", "data": {}},
                {"ts": 1.0, "event": "autoscaler_stopped", "data": {}},
            ]
        )
    )

    summary = build_summary(bundle)

    assert "| s3-hybrid-reactive | no | 0 | 0 | n/a |" in summary
