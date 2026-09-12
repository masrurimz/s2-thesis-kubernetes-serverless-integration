"""The evidence tables read a real bundle, not a mock of one.

Each test writes a bundle with the artifact writers and reads it back through the
tables, so a change in what a run writes breaks the table that reports it.
"""

import json
from pathlib import Path

import pytest

from analysis.bundle_evidence import (
    as_payload,
    mechanism_rows,
    run_evidence,
    variance_summary,
)
from shared.artifacts import write_manifest, write_provision_events, write_result
from shared.models.experiment import ExperimentResult, RunManifest
from shared.models.evidence import NodeEngagement, TreatmentFidelity


def _write_run(
    bundle: Path,
    scenario: str,
    run_id: int,
    *,
    p99: float,
    valid: bool = True,
    nodes: int = 1,
    delay: float = 90.0,
    delivered: bool | None = None,
    serverless: float = 30.0,
    load_ratio: float = 0.08,
    provision_events: list[tuple[float, str, dict]] | None = None,
) -> None:
    run_dir = bundle / f"{scenario}_run{run_id}"
    run_dir.mkdir(parents=True, exist_ok=True)
    write_result(
        run_dir,
        ExperimentResult(
            scenario=scenario,
            run_id=run_id,
            run_validity_passed=valid,
            p99_latency_ms=p99,
            p95_latency_ms=p99 * 0.8,
            slo_violations_k6=10,
            error_rate=0.0,
            throughput_rps=70.0,
            first_provision_delay_sec=delay,
            time_in_serverless_pct=serverless,
            node_engagement=NodeEngagement(
                required=True,
                autoscaler_engaged=nodes > 0,
                pending_events=1 if nodes else 0,
                nodes_provisioned=nodes,
                first_provision_delay_sec=delay,
            ),
            treatment_fidelity=(
                TreatmentFidelity(delivered=delivered, eligible_cycles=10, successful_predictions=10)
                if delivered is not None
                else None
            ),
        ),
    )
    write_manifest(
        run_dir,
        RunManifest(
            scenario=scenario,
            run_id=run_id,
            run_order_idx=run_id,
            random_seed=42,
            git_commit="abc1234",
            k6_script="clarknet_replay.js",
            k6_stages_json="stages.json",
            replay_manifest={},
            daemon_config={},
            scaling_config={},
            timestamp="2026-09-12T00:00:00",
            conditions={"load": {"load1": 1.3, "cores": 16.0, "ratio": load_ratio}},
        ),
    )
    if provision_events is not None:
        write_provision_events(run_dir, provision_events)


@pytest.fixture
def bundle(tmp_path: Path) -> Path:
    path = tmp_path / "2026-09-12_probe"
    path.mkdir()
    for run_id, (s3_p99, s4_p99) in enumerate([(200.0, 150.0), (250.0, 260.0), (180.0, 140.0)], start=1):
        _write_run(
            path,
            "s3-hybrid-reactive",
            run_id,
            p99=s3_p99,
            delay=100.0,
            provision_events=[(0.0, "autoscaler_started", {}), (150.0, "node_created", {})],
        )
        _write_run(
            path,
            "s4-hybrid-predictive",
            run_id,
            p99=s4_p99,
            delay=70.0,
            delivered=True,
            provision_events=[(0.0, "autoscaler_started", {}), (130.0, "node_created", {})],
        )
    return path


class TestRunEvidence:
    def test_one_row_per_run_with_conditions(self, bundle):
        rows = run_evidence(bundle)

        assert len(rows) == 6
        s3 = [row for row in rows if row.scenario == "s3-hybrid-reactive"]
        assert [row.p99_latency_ms for row in s3] == [200.0, 250.0, 180.0]
        assert all(row.valid for row in rows)
        assert all(row.nodes_provisioned == 1 for row in rows)
        assert s3[0].host_load_ratio == pytest.approx(0.08)

    def test_prediction_delivery_is_reported_only_for_the_predictive_arm(self, bundle):
        rows = {row.scenario: row for row in run_evidence(bundle) if row.run_id == 1}

        assert rows["s4-hybrid-predictive"].prediction_delivered is True
        assert rows["s3-hybrid-reactive"].prediction_delivered is None

    def test_a_run_without_a_result_is_simply_absent(self, bundle):
        (bundle / "s3-hybrid-reactive_run9").mkdir()

        assert len(run_evidence(bundle)) == 6

    def test_payload_is_json_serialisable(self, bundle):
        payload = as_payload(run_evidence(bundle))

        assert json.loads(json.dumps(payload))[0]["scenario"]


class TestMechanism:
    def test_node_arrival_is_measured_from_the_first_provisioner_event(self, bundle):
        rows = {row.scenario: row for row in mechanism_rows(bundle) if row.run_id == 1}

        assert rows["s3-hybrid-reactive"].node_arrival_offset_sec == pytest.approx(150.0)
        assert rows["s4-hybrid-predictive"].node_arrival_offset_sec == pytest.approx(130.0)
        assert rows["s3-hybrid-reactive"].provisioning_delay_sec == pytest.approx(100.0)

    def test_a_run_with_no_provisioner_timeline_reports_no_offset(self, bundle):
        _write_run(bundle, "s3-hybrid-reactive", 7, p99=190.0)

        row = next(row for row in mechanism_rows(bundle) if row.run_id == 7)

        assert row.node_arrival_offset_sec is None


class TestVariance:
    def test_arm_spread_and_pair_differences(self, bundle):
        summary = variance_summary(bundle)

        arms = {arm.scenario: arm for arm in summary.arms}
        assert arms["s3-hybrid-reactive"].n == 3
        assert arms["s3-hybrid-reactive"].mean_p99_ms == pytest.approx(210.0)
        assert summary.pair_differences_ms == [-50.0, 10.0, -40.0]
        assert summary.mean_difference_ms == pytest.approx(-26.6667, abs=1e-3)

    def test_the_designs_floor_is_reported(self, bundle):
        assert variance_summary(bundle).smallest_attainable_p == pytest.approx(0.125)

    def test_an_invalid_run_is_left_out_of_the_spread(self, bundle):
        _write_run(bundle, "s4-hybrid-predictive", 4, p99=900.0, valid=False)

        summary = variance_summary(bundle)

        assert {arm.scenario: arm.n for arm in summary.arms}["s4-hybrid-predictive"] == 3

    def test_one_arm_alone_has_no_paired_difference(self, tmp_path):
        bundle = tmp_path / "solo"
        bundle.mkdir()
        _write_run(bundle, "s1-k8s-only", 1, p99=120.0)

        summary = variance_summary(bundle)

        assert summary.n_pairs == 0
        assert summary.mean_difference_ms is None
