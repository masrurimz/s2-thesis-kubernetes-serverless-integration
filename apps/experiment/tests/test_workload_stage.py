"""WorkloadStage: construction-time configuration and one stub-k6 run.

The k6 binary, script, stages file and target URL used to be module constants read at
import; they are constructor parameters now, which is what lets a test (or a
different trace) drive the stage without editing it.
"""

import json
import stat
from pathlib import Path

import pytest

from experiment.stages.workload import (
    DEFAULT_K6_SCRIPT,
    WORKLOAD_STAGES,
    K6Summary,
    WorkloadStage,
    default_stages_path,
)
from shared.models.experiment import ExperimentConfig
from shared.models.pipeline import PipelineContext

HANDLE_SUMMARY = {
    "metrics": {
        "http_req_duration": {"values": {"med": 60.0, "avg": 65.0, "max": 210.0, "p(95)": 80.0, "p(99)": 100.0}},
        "http_reqs": {"values": {"count": 1000, "rate": 50.0}},
        "http_req_failed": {"values": {"rate": 0.01, "fails": 10}},
        "slo_violations": {"values": {"count": 7}},
        "app_duration_ms": {"values": {"avg": 12.0, "p(50)": 10.0, "p(95)": 20.0}},
        "app_duration_serverless_ms": {"values": {"avg": 30.0, "p(95)": 40.0}},
        "app_duration_k8s_ms": {"values": {"avg": 11.0}},
    }
}


class TestConstruction:
    def test_defaults_resolve_to_the_canonical_artifacts(self):
        stage = WorkloadStage()

        assert Path(stage.k6_script) == DEFAULT_K6_SCRIPT
        assert stage.k6_stages.name == WORKLOAD_STAGES["clarknet"]
        assert stage.target_url.startswith("http://localhost:")

    def test_explicit_arguments_win(self, tmp_path):
        stage = WorkloadStage(
            k6_path="/tmp/fake-k6",
            k6_script=tmp_path / "script.js",
            k6_stages=tmp_path / "stages.json",
            target_url="http://example.test:1234",
        )

        assert stage.k6_path == "/tmp/fake-k6"
        assert stage.k6_script == tmp_path / "script.js"
        assert stage.k6_stages == tmp_path / "stages.json"
        assert stage.target_url == "http://example.test:1234"

    def test_environment_selects_the_binary_and_the_trace(self, monkeypatch, tmp_path):
        stage = WorkloadStage()
        monkeypatch.setenv("K6_PATH", "/from/env/k6")
        monkeypatch.setenv("WORKLOAD", "spike")

        assert WorkloadStage().k6_path == "/from/env/k6"
        assert WorkloadStage().k6_stages.name == WORKLOAD_STAGES["spike"]
        assert stage.k6_stages.name == WORKLOAD_STAGES["clarknet"]

    def test_unknown_workload_is_rejected(self, monkeypatch):
        monkeypatch.setenv("WORKLOAD", "not-a-trace")

        with pytest.raises(ValueError, match="Unknown workload"):
            default_stages_path()


def _stub_k6(path: Path, summary: dict, name: str = "clarknet_replay_stub_run1_1.json") -> Path:
    """A k6 that writes a handleSummary document into RESULTS_DIR and exits 0."""
    path.write_text(
        "#!/bin/sh\n"
        'for arg in "$@"; do case "$arg" in RESULTS_DIR=*) dir="${arg#RESULTS_DIR=}";; esac; done\n'
        'mkdir -p "$dir"\n'
        f"cat > \"$dir/{name}\" <<'JSON'\n{json.dumps(summary)}\nJSON\n"
        "exit 0\n"
    )
    path.chmod(path.stat().st_mode | stat.S_IXUSR)
    return path


def test_stub_run_populates_the_workload_result(tmp_path):
    binary = _stub_k6(tmp_path / "k6", HANDLE_SUMMARY)
    stage = WorkloadStage(k6_path=binary, k6_script=tmp_path / "script.js", k6_stages=tmp_path / "stages.json")
    ctx = PipelineContext(
        batch_id="b",
        scenario="s3-hybrid-reactive",
        run_id=1,
        config=ExperimentConfig(phase="experiments", runs=1, duration_sec=60),
        output_dir=str(tmp_path / "run"),
    )

    stage._run(ctx)

    workload = ctx.workload
    assert workload is not None and workload.success is True
    assert workload.total_requests == 1000
    assert workload.p99_latency_ms == 100.0
    assert workload.slo_violations == 7
    assert workload.app_duration_k8s_avg_ms == 11.0
    assert workload.throughput_rps == 50.0


def test_an_unrelated_json_file_is_not_read_as_the_summary(tmp_path):
    """Only the script's own naming pattern counts; anything else is not this run's."""
    binary = tmp_path / "k6"
    binary.write_text(
        "#!/bin/sh\n"
        'for arg in "$@"; do case "$arg" in RESULTS_DIR=*) dir="${arg#RESULTS_DIR=}";; esac; done\n'
        'mkdir -p "$dir"\n'
        f"cat > \"$dir/injected.json\" <<'JSON'\n{json.dumps(HANDLE_SUMMARY)}\nJSON\n"
        "exit 0\n"
    )
    binary.chmod(binary.stat().st_mode | stat.S_IXUSR)
    stage = WorkloadStage(k6_path=binary, k6_script=tmp_path / "script.js", k6_stages=tmp_path / "stages.json")

    assert stage._run_k6("s3-hybrid-reactive", 1, tmp_path / "run") is None


def test_a_failing_k6_binary_returns_no_summary(tmp_path):
    binary = tmp_path / "k6"
    binary.write_text("#!/bin/sh\nexit 1\n")
    binary.chmod(binary.stat().st_mode | stat.S_IXUSR)
    stage = WorkloadStage(k6_path=binary, k6_script=tmp_path / "script.js", k6_stages=tmp_path / "stages.json")

    assert stage._run_k6("s3-hybrid-reactive", 1, tmp_path / "run") is None


def test_a_summary_from_an_earlier_run_is_not_accepted(tmp_path):
    """Stale files in the run's k6 directory must not be read as this run's output."""
    k6_dir = tmp_path / "run" / "k6"
    k6_dir.mkdir(parents=True)
    stale = k6_dir / "clarknet_replay_stub_run1_0.json"
    stale.write_text(json.dumps(HANDLE_SUMMARY))
    import os
    import time

    old = time.time() - 3600
    os.utime(stale, (old, old))

    binary = tmp_path / "k6"
    binary.write_text("#!/bin/sh\nexit 0\n")
    binary.chmod(binary.stat().st_mode | stat.S_IXUSR)
    stage = WorkloadStage(k6_path=binary, k6_script=tmp_path / "script.js", k6_stages=tmp_path / "stages.json")

    assert stage._run_k6("s3-hybrid-reactive", 1, tmp_path / "run") is None


def test_summary_model_reads_the_handle_summary_document():
    summary = K6Summary.from_handle_summary(HANDLE_SUMMARY, "s3-hybrid-reactive", 3, "p.json")

    assert summary.run_id == 3
    assert summary.k6_summary_path == "p.json"
    assert summary.metrics.successful_requests == 990
    assert summary.metrics.total_errors == 17
