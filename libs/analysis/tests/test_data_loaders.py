"""Tests for analysis data loaders."""

import json

from analysis.data_loaders import build_results_final


def _write_result(bundle_dir, name, **overrides):
    result = {
        "scenario": overrides.pop("scenario"),
        "run_id": overrides.pop("run_id"),
        "p99_latency_ms": 120.0,
        "p95_latency_ms": 90.0,
        "p50_latency_ms": 50.0,
        "error_rate": 0.01,
        "throughput_rps": 95.0,
        "slo_violations_k6": 2,
        "duration_sec": 60.0,
        "timestamp": "2026-07-14T00:00:00Z",
        "run_validity_passed": True,
        **overrides,
    }
    run_dir = bundle_dir / name
    run_dir.mkdir(parents=True)
    (run_dir / "result.json").write_text(json.dumps(result))


def test_build_results_final_schema_v1(tmp_path):
    _write_result(
        tmp_path,
        "s3-hybrid-reactive_run1",
        scenario="s3-hybrid-reactive",
        run_id=1,
    )
    _write_result(
        tmp_path,
        "s4-hybrid-predictive_run2",
        scenario="s4-hybrid-predictive",
        run_id=2,
    )

    results = build_results_final(tmp_path)

    assert [(result["scenario"], result["run_id"]) for result in results] == [
        ("s3-hybrid-reactive", 1),
        ("s4-hybrid-predictive", 2),
    ]
    assert results[0]["p99_latency_ms"] == 120.0
    assert results[0]["slo_violation_count"] == 2
    assert results[0]["rps"] == 95.0
    assert list(results[0]) == [
        "scenario",
        "run_id",
        "rps",
        "duration_sec",
        "p50_latency_ms",
        "p95_latency_ms",
        "p99_latency_ms",
        "error_rate",
        "throughput_rps",
        "slo_violation_count",
        "slo_violations_k6",
        "slo_violation_duration_sec",
        "timestamp",
        "maintain_count",
        "scale_out_count",
        "predictive_count",
        "optimize_cost_count",
        "gru_predictions_used",
        "gru_avg_confidence",
        "k8s_weight_time_product",
        "serverless_weight_time_product",
        "run_validity_passed",
        "stress_validity_passed",
    ]


def test_build_results_final_excludes_invalid(tmp_path):
    _write_result(
        tmp_path,
        "s3-hybrid-reactive_run1",
        scenario="s3-hybrid-reactive",
        run_id=1,
    )
    _write_result(
        tmp_path,
        "s4-hybrid-predictive_run2",
        scenario="s4-hybrid-predictive",
        run_id=2,
    )
    _write_result(
        tmp_path,
        "s4-hybrid-predictive_run3",
        scenario="s4-hybrid-predictive",
        run_id=3,
        run_validity_passed=False,
    )

    assert [result["run_id"] for result in build_results_final(tmp_path)] == [1, 2]
    assert [result["run_id"] for result in build_results_final(tmp_path, include_invalid=True)] == [
        1,
        2,
        3,
    ]
