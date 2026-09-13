"""Run-config recording: the manifest blocks that name what produced a run.

A run used to leave replay_manifest, daemon_config and scaling_config empty, so
the July result's calibration override (max_k8s_replicas=10, horizon=9) lived
only in a side file and no bundle could say which load generator or predictor
artifact produced it. These tests feed known inputs through the gatherers and
assert the blocks carry those inputs and their sources, or an explicit absence.
"""

import hashlib
import json
from pathlib import Path

from experiment.stages.collect import (
    gather_daemon_block,
    gather_predictor_block,
    record_run_config,
)
from experiment.stages.workload import gather_replay_block
from shared.artifacts import read_manifest, write_manifest
from shared.models.experiment import RunManifest, gather_scaling_block

REPO_ROOT = Path(__file__).resolve().parents[3]
TRACE_MANIFEST = REPO_ROOT / "data" / "trace-replay" / "clarknet_replay_manifest.json"
K6_STAGES = REPO_ROOT / "data" / "trace-replay" / "clarknet_k6_stages.json"
K6_SCRIPT = REPO_ROOT / "apps" / "experiment" / "experiment" / "load_tests" / "canonical" / "clarknet_replay.js"

# Shaped like routing/daemon/service.py get_status(), including fields this
# code never names (provisioning_delay_source) to prove verbatim passthrough.
DAEMON_STATUS = {
    "scenario": "s4-hybrid-predictive",
    "scenario_description": "Hybrid predictive routing",
    "weights": {"k3s": 60, "knative": 40},
    "decision_count": 12,
    "scale_out_count": 3,
    "optimize_cost_count": 2,
    "predictive_count": 4,
    "maintain_count": 3,
    "uptime_seconds": 245.1,
    "gru_available": True,
    "model_sequence_length": 30,
    "forecast_horizon_steps": 9,
    "provisioning_delay_estimate_sec": 87.5,
    "provisioning_delay_samples": 2,
    "provisioning_delay_source": "declared",
}

# Shaped like prediction/model_loader.py get_status().
PREDICTOR_STATUS = {
    "loaded": True,
    "model_type": "pytorch",
    "model_path": "results/models/gru/2026-09-10_clarknet-15s-h9-leakfree/artifacts/clarknet_gru_s43.pt",
    "schema_version": 2,
    "sequence_length": 30,
    "prediction_horizon": 9,
    "sample_interval_sec": 15,
    "artifact_sha256": "ab" * 32,
}

DECLARED_CAPACITY = {"pod_cpu_request": "300m", "max_k8s_replicas": 10, "node_cpus": 1.0, "k8s_agents": 1}


def test_blocks_populate_from_inputs_and_match_them(tmp_path, monkeypatch):
    override = tmp_path / "calibration.json"
    override.write_text(json.dumps({"max_k8s_replicas": 10, "prediction_horizon": 9}))
    monkeypatch.setenv("CALIBRATION_OVERRIDE", str(override))

    replay = gather_replay_block(k6_script=K6_SCRIPT, k6_stages=K6_STAGES, trace_manifest=TRACE_MANIFEST)
    daemon = gather_daemon_block(status=DAEMON_STATUS)
    predictor = gather_predictor_block(status=PREDICTOR_STATUS)
    scaling = gather_scaling_block(declared_capacity=DECLARED_CAPACITY)

    assert replay["trace_manifest"] == json.loads(TRACE_MANIFEST.read_text())
    assert replay["trace_manifest"]["scale_factor"] == 33.0
    assert replay["k6_stages"] == json.loads(K6_STAGES.read_text())
    assert len(replay["k6_stages"]) == 40
    assert replay["k6_script"]["path"] == str(K6_SCRIPT)
    assert replay["k6_script"]["sha256"] == hashlib.sha256(K6_SCRIPT.read_bytes()).hexdigest()
    assert replay["sources"]["trace_manifest"] == str(TRACE_MANIFEST)

    assert daemon["reported"] == DAEMON_STATUS
    assert daemon["reported"]["provisioning_delay_source"] == "declared"
    assert daemon["controller_version"]["value"] == "v3"
    assert "does not report controller_version" in daemon["controller_version"]["source"]

    assert predictor["reported"] == PREDICTOR_STATUS
    assert predictor["reported"]["artifact_sha256"] == "ab" * 32
    assert predictor["reported"]["sequence_length"] == 30
    assert predictor["reported"]["prediction_horizon"] == 9

    assert scaling["calibration"]["resolved"]["max_k8s_replicas"] == 10
    assert scaling["calibration"]["resolved"]["prediction_horizon"] == 9
    assert str(override) in scaling["calibration"]["source"]
    assert scaling["max_k8s_replicas_applied"]["value"] == 10
    assert scaling["declared_capacity"]["values"] == DECLARED_CAPACITY

    manifest = RunManifest(
        scenario="s4-hybrid-predictive",
        run_id=1,
        run_order_idx=0,
        random_seed=42,
        git_commit="abc1234",
        k6_script="",
        k6_stages_json="",
        timestamp="2026-09-12T00:00:00",
        replay_manifest=replay,
        daemon_config=daemon,
        scaling_config=scaling,
        predictor=predictor,
    )
    write_manifest(tmp_path, manifest)
    reread = read_manifest(tmp_path)
    assert reread is not None
    assert reread.daemon_config["reported"]["provisioning_delay_source"] == "declared"
    assert reread.predictor["reported"]["artifact_sha256"] == "ab" * 32
    assert reread.scaling_config["max_k8s_replicas_applied"]["value"] == 10


def test_absent_sources_leave_an_explicit_reason_and_still_load(tmp_path):
    replay = gather_replay_block(
        k6_script=tmp_path / "missing.js",
        k6_stages=tmp_path / "missing_stages.json",
        trace_manifest=tmp_path / "missing_manifest.json",
    )
    daemon = gather_daemon_block(status=None, absent_reason="http://localhost:9104/status unreachable: refused")
    predictor = gather_predictor_block(status=None, absent_reason="prediction service not running for this scenario")
    scaling = gather_scaling_block(declared_capacity=None)

    assert "not found" in replay["trace_manifest"]["absent_reason"]
    assert "not found" in replay["k6_stages"]["absent_reason"]
    assert "not found" in replay["k6_script"]["absent_reason"]
    assert daemon["reported"]["absent_reason"].startswith("http://localhost:9104/status unreachable")
    assert predictor["reported"]["absent_reason"] == "prediction service not running for this scenario"
    assert scaling["declared_capacity"]["values"] is None
    assert "no capacity contract" in scaling["declared_capacity"]["source"]
    # A value that is always resolvable must still be there, sourced.
    assert isinstance(scaling["max_k8s_replicas_applied"]["value"], int)

    manifest = RunManifest(
        scenario="s3-hybrid-reactive",
        run_id=2,
        run_order_idx=1,
        random_seed=43,
        git_commit="abc1234",
        k6_script="",
        k6_stages_json="",
        timestamp="2026-09-12T00:00:00",
        replay_manifest=replay,
        daemon_config=daemon,
        scaling_config=scaling,
        predictor=predictor,
    )
    write_manifest(tmp_path, manifest)
    assert read_manifest(tmp_path) == manifest

    # A manifest from before the blocks existed (or before they were populated)
    # must load rather than fail validation.
    legacy = RunManifest(
        scenario="s3-hybrid-reactive",
        run_id=3,
        run_order_idx=2,
        random_seed=44,
        git_commit="abc1234",
        k6_script="",
        k6_stages_json="",
        timestamp="2026-07-01T00:00:00",
    )
    assert legacy.replay_manifest == {}
    assert legacy.predictor == {}


def test_record_run_config_fills_empty_blocks_and_keeps_written_ones(tmp_path, monkeypatch):
    run_dir = tmp_path / "run1"
    run_dir.mkdir()
    write_manifest(
        run_dir,
        RunManifest(
            scenario="s4-hybrid-predictive",
            run_id=1,
            run_order_idx=0,
            random_seed=42,
            git_commit="abc1234",
            k6_script="",
            k6_stages_json="",
            timestamp="2026-09-12T00:00:00",
            conditions={"capacity": DECLARED_CAPACITY},
        ),
    )

    def fake_fetch(url, timeout=3.0):
        if url.endswith("/model/status"):
            return dict(PREDICTOR_STATUS), None
        return dict(DAEMON_STATUS), None

    monkeypatch.setattr("experiment.stages.collect.fetch_status_payload", fake_fetch)

    record_run_config(run_dir)

    recorded = read_manifest(run_dir)
    assert recorded is not None
    assert recorded.replay_manifest["k6_script"]["path"] == str(
        REPO_ROOT / "apps" / "experiment" / "experiment" / "load_tests" / "canonical" / "clarknet_replay.js"
    )
    assert len(recorded.replay_manifest["k6_script"]["sha256"]) == 64
    assert recorded.daemon_config["reported"] == DAEMON_STATUS
    assert recorded.predictor["reported"] == PREDICTOR_STATUS
    assert recorded.scaling_config["declared_capacity"]["values"] == DECLARED_CAPACITY
    assert recorded.scaling_config["declared_capacity"]["source"].startswith("run conditions report")

    # A block the writer already populated is authoritative; recording yields.
    recorded.daemon_config = {"orchestrator": "wrote-this-at-start"}
    write_manifest(run_dir, recorded)
    record_run_config(run_dir)
    final = read_manifest(run_dir)
    assert final is not None
    assert final.daemon_config == {"orchestrator": "wrote-this-at-start"}
    assert final.predictor["reported"]["artifact_sha256"] == "ab" * 32


def test_record_run_config_without_a_manifest_does_not_raise(tmp_path):
    record_run_config(tmp_path)
    assert not (tmp_path / "manifest.json").exists()
