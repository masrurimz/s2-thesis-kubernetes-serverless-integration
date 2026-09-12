"""`thesis experiment analyze` recomputes a bundle's verdict from its own runs.

The runner writes the verdict once, at the end of a stage. This command is what makes
the verdict reproducible afterwards — the scene of the two-p-values bug — so it is
tested against a bundle built by the artifact writers and asserted on both renderings.
"""

import json
from pathlib import Path

import pytest
from experiment.cli import app
from shared.artifacts import write_manifest, write_result
from shared.models.evidence import NodeEngagement, TreatmentFidelity
from shared.models.experiment import ExperimentResult, RunManifest
from typer.testing import CliRunner


def _write_run(bundle: Path, scenario: str, run_id: int, p99: float) -> None:
    run_dir = bundle / f"{scenario}_run{run_id}"
    run_dir.mkdir(parents=True, exist_ok=True)
    write_result(
        run_dir,
        ExperimentResult(
            scenario=scenario,
            run_id=run_id,
            run_validity_passed=True,
            p99_latency_ms=p99,
            node_engagement=NodeEngagement(
                required=True, autoscaler_engaged=True, pending_events=1, nodes_provisioned=1
            ),
            # A pair counts only when the predictive arm delivered every forecast it
            # owed; the same rule the runner applies.
            treatment_fidelity=(
                TreatmentFidelity(delivered=True, eligible_cycles=10, successful_predictions=10)
                if scenario == "s4-hybrid-predictive"
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
            k6_script="s.js",
            k6_stages_json="st.json",
            replay_manifest={},
            daemon_config={},
            scaling_config={},
            timestamp="2026-09-12T00:00:00",
        ),
    )


@pytest.fixture
def bundle(tmp_path: Path) -> Path:
    path = tmp_path / "2026-09-12_probe"
    path.mkdir()
    for run_id, (s3, s4) in enumerate([(200.0, 150.0), (250.0, 260.0), (180.0, 100.0)], start=1):
        _write_run(path, "s3-hybrid-reactive", run_id, s3)
        _write_run(path, "s4-hybrid-predictive", run_id, s4)
    return path


def test_json_payload_reports_the_paired_verdict(bundle):
    result = CliRunner().invoke(app, ["analyze", str(bundle), "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload["n_pairs"] == 3
    assert payload["baseline_mean_ms"] == pytest.approx(210.0)
    assert payload["comparison_mean_ms"] == pytest.approx(170.0)
    assert payload["mean_difference_ms"] == pytest.approx(-40.0)
    assert payload["pair_differences_ms" if "pair_differences_ms" in payload else "baseline_values_ms"]
    assert payload["smallest_attainable_p"] == pytest.approx(0.125)
    assert payload["h2_supported"] is False


def test_human_rendering_names_the_direction_and_the_floor(bundle):
    result = CliRunner().invoke(app, ["analyze", str(bundle)])

    assert result.exit_code == 0
    assert "H2 paired verdict" in result.output
    assert "smallest attainable at n=3" in result.output
    assert "verdict: H2 not supported" in result.output


def test_a_bundle_without_valid_pairs_is_an_error_not_a_zero(tmp_path):
    empty = tmp_path / "empty"
    empty.mkdir()

    result = CliRunner().invoke(app, ["analyze", str(empty)])

    assert result.exit_code == 1
    assert "No valid pairs" in result.output
