"""The per-pair mechanism table, read back from a bundle a test wrote.

A pair's lead and both arms' ramp shares are computed across three artifacts
(result.json for engagement, provision_events.json for arrivals, the k6 data
file plus the Prometheus export for the windowed weight share), so the test
writes all of them and asserts the numbers that come out.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from analysis import bundle_evidence
from analysis.bundle_evidence import mechanism_pairs, mechanism_rows
from shared.artifacts import write_provision_events, write_result
from shared.models.experiment import ExperimentResult
from shared.models.evidence import TreatmentFidelity

_DURATION_MS = 1_200_000


def _result(scenario: str, run_id: int, *, eligible: int = 0, proactive: int = 0) -> ExperimentResult:
    return ExperimentResult(
        scenario=scenario,
        run_id=run_id,
        p99_latency_ms=150.0,
        time_in_serverless_pct=25.0,
        treatment_fidelity=TreatmentFidelity(
            required=eligible > 0,
            delivered=True,
            eligible_cycles=eligible,
            successful_predictions=eligible,
            proactive_scaleups=proactive,
        ),
    )


def _write_run(
    bundle: Path,
    scenario: str,
    run_id: int,
    *,
    node_at_s: float,
    knative: float,
    k3s: float,
    eligible: int = 0,
    proactive: int = 0,
) -> None:
    run_dir = bundle / f"{scenario}_run{run_id}"
    run_dir.mkdir(parents=True, exist_ok=True)
    write_result(run_dir, _result(scenario, run_id, eligible=eligible, proactive=proactive))

    started = datetime(2026, 7, 13, 18, 0, 0, tzinfo=timezone.utc).timestamp()
    write_provision_events(
        run_dir,
        [(started, "autoscaler_started", {}), (started + node_at_s, "node_created", {"node": "n"})],
    )

    ended = datetime.fromtimestamp(started + _DURATION_MS / 1000.0, tz=timezone.utc)
    stamp = ended.strftime("%Y-%m-%dT%H-%M-%S-") + f"{ended.microsecond // 1000:03d}Z"
    k6_dir = run_dir / "k6"
    k6_dir.mkdir(exist_ok=True)
    (k6_dir / f"clarknet_replay_{scenario}_run{run_id}_{stamp}.json").write_text(
        json.dumps({"state": {"testRunDurationMs": _DURATION_MS}, "metrics": {}})
    )

    window = bundle_evidence._ramp_window()
    assert window is not None
    lo, hi, _, _ = window
    samples = [started + (lo + hi) / 2, started + lo + 1, started + hi - 1]
    export = {
        "daemon_weight_knative": [[ts, knative] for ts in samples],
        "daemon_weight_k3s": [[ts, k3s] for ts in samples],
    }
    prom_dir = run_dir / "prometheus"
    prom_dir.mkdir(exist_ok=True)
    (prom_dir / "prometheus_export.json").write_text(json.dumps(export))


class TestMechanismPairs:
    def test_lead_shares_and_engagement_come_from_the_bundle(self, tmp_path: Path):
        bundle = tmp_path / "bundle"
        _write_run(bundle, "s3-hybrid-reactive", 1, node_at_s=400.0, knative=10.0, k3s=90.0)
        _write_run(
            bundle,
            "s4-hybrid-predictive",
            1,
            node_at_s=380.0,
            knative=30.0,
            k3s=70.0,
            eligible=50,
            proactive=1,
        )

        pairs = mechanism_pairs(bundle)

        assert len(pairs) == 1
        pair = pairs[0]
        assert pair.baseline_node_at_s == 400.0
        assert pair.comparison_node_at_s == 380.0
        assert pair.lead_s == 20.0
        assert pair.baseline_ramp_share_pct == 10.0
        assert pair.comparison_ramp_share_pct == 30.0
        assert pair.baseline_prediction_use is None
        assert pair.comparison_prediction_use == 1 / 50
        assert pair.prediction_use_source == "treatment_fidelity"

    def test_a_missing_run_id_on_one_side_is_not_a_pair(self, tmp_path: Path):
        bundle = tmp_path / "bundle"
        _write_run(bundle, "s3-hybrid-reactive", 1, node_at_s=400.0, knative=10.0, k3s=90.0)
        _write_run(bundle, "s4-hybrid-predictive", 2, node_at_s=380.0, knative=30.0, k3s=70.0)

        assert mechanism_pairs(bundle) == []

    def test_no_weight_series_degrades_to_none_not_a_crash(self, tmp_path: Path):
        bundle = tmp_path / "bundle"
        _write_run(bundle, "s3-hybrid-reactive", 1, node_at_s=400.0, knative=10.0, k3s=90.0)
        _write_run(
            bundle,
            "s4-hybrid-predictive",
            1,
            node_at_s=380.0,
            knative=10.0,
            k3s=90.0,
            eligible=50,
        )
        for run_dir in bundle.iterdir():
            (run_dir / "prometheus" / "prometheus_export.json").unlink()

        rows = mechanism_rows(bundle)
        pairs = mechanism_pairs(bundle)

        assert all(row.ramp_serverless_share_pct is None for row in rows)
        assert all(pair.baseline_ramp_share_pct is None for pair in pairs)
        assert pairs[0].lead_s == 20.0

    def test_missing_fidelity_falls_back_to_prometheus_counters(self, tmp_path: Path):
        bundle = tmp_path / "bundle"
        for scenario, node_at in (("s3-hybrid-reactive", 400.0), ("s4-hybrid-predictive", 380.0)):
            _write_run(bundle, scenario, 1, node_at_s=node_at, knative=10.0, k3s=90.0)
            run_dir = bundle / f"{scenario}_run1"
            result = json.loads((run_dir / "result.json").read_text())
            del result["treatment_fidelity"]
            (run_dir / "result.json").write_text(json.dumps(result))
            export_path = run_dir / "prometheus" / "prometheus_export.json"
            export = json.loads(export_path.read_text())
            export["daemon_decisions"] = [[0.0, 10.0], [1000.0, 60.0]]
            export["daemon_predictions_used"] = [[0.0, 0.0], [1000.0, 25.0]]
            export_path.write_text(json.dumps(export))

        rows = {row.scenario: row for row in mechanism_rows(bundle)}

        assert rows["s4-hybrid-predictive"].prediction_use_ratio == 0.5
        assert rows["s4-hybrid-predictive"].prediction_use_source == "prometheus"
        assert mechanism_pairs(bundle)[0].prediction_use_source == "prometheus"
