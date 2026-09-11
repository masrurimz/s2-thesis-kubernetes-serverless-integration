"""Resume bookkeeping: what counts as already done.

A resumed reproduce must run only what is missing, and it must not count a run
that failed its gate as done. These tests pin that distinction against synthetic
bundles, since a wrong answer either repeats expensive work or silently skips it.
"""

from __future__ import annotations

import json

from experiment.cli import _collect_pairs, _completed_pairs, _completed_runs


def _write_run(bundle, scenario, run_id, *, valid=True, delivered=None):
    run_dir = bundle / f"{scenario}_run{run_id}"
    run_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "scenario": scenario,
        "run_id": run_id,
        "run_validity_passed": valid,
        "p99_latency_ms": 100.0 + run_id,
        "slo_violations_k6": run_id,
    }
    if delivered is not None:
        payload["treatment_fidelity"] = {"delivered": delivered, "reasons": [] if delivered else ["no predictions"]}
    (run_dir / "result.json").write_text(json.dumps(payload))


def test_missing_bundle_has_nothing_done(tmp_path):
    assert _completed_pairs(tmp_path / "absent") == set()
    assert _completed_runs(tmp_path / "absent") == frozenset()


def test_pair_counts_only_when_both_runs_are_valid_and_delivered(tmp_path):
    _write_run(tmp_path, "s3-hybrid-reactive", 1)
    _write_run(tmp_path, "s4-hybrid-predictive", 1, delivered=True)
    _write_run(tmp_path, "s3-hybrid-reactive", 2)
    _write_run(tmp_path, "s4-hybrid-predictive", 2, delivered=False)
    _write_run(tmp_path, "s3-hybrid-reactive", 3, valid=False)
    _write_run(tmp_path, "s4-hybrid-predictive", 3, delivered=True)

    assert _completed_pairs(tmp_path) == {1}
    s3_results, s4_results, pair_ids = _collect_pairs(tmp_path)
    assert pair_ids == ["pair_001"]
    assert [r.run_id for r in s3_results] == [1]
    assert [r.run_id for r in s4_results] == [1]


def test_runs_ignore_invalid_results(tmp_path):
    _write_run(tmp_path, "s1-k8s-only", 1)
    _write_run(tmp_path, "s1-k8s-only", 2, valid=False)

    assert _completed_runs(tmp_path) == frozenset({("s1-k8s-only", 1)})
