import subprocess
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from workloads.k6_runner import K6Result, K6Runner


class TestK6Result:
    def test_k6_result_creation(self):
        result = K6Result(
            success=True,
            http_reqs=1000,
            http_req_duration_p95=45.5,
            http_req_duration_p99=89.2,
            http_req_failed_rate=0.01,
            vus_max=50,
            raw_output="test output",
        )

        assert result.success is True
        assert result.http_reqs == 1000
        assert result.http_req_duration_p95 == 45.5
        assert result.http_req_duration_p99 == 89.2
        assert result.http_req_failed_rate == 0.01
        assert result.vus_max == 50
        assert result.raw_output == "test output"
        assert result.metrics == {}


class TestK6Runner:
    def test_workload_scripts_mapping(self):
        runner = K6Runner()
        assert runner.WORKLOAD_SCRIPTS["steady"] == "steady-load.js"
        assert runner.WORKLOAD_SCRIPTS["spike"] == "spike-load.js"
        assert runner.WORKLOAD_SCRIPTS["endurance"] == "endurance-test.js"

    def test_list_available_workloads(self):
        runner = K6Runner()
        workloads = runner.list_available_workloads()
        assert "steady" in workloads
        assert "spike" in workloads
        assert "endurance" in workloads

    def test_get_script_path_valid(self):
        runner = K6Runner()
        path = runner.get_script_path("steady")
        assert path is not None
        assert path.name == "steady-load.js"

    def test_get_script_path_invalid(self):
        runner = K6Runner()
        path = runner.get_script_path("nonexistent")
        assert path is None

    def test_invalid_workload_returns_error(self):
        runner = K6Runner()
        result = runner.run_workload("invalid", "s1-k8s-only")

        assert result.success is False
        assert "Unknown workload" in result.raw_output

    def test_missing_script_returns_error(self):
        runner = K6Runner(scripts_dir="/nonexistent/path")
        result = runner.run_workload("steady", "s1-k8s-only")

        assert result.success is False
        assert "not found" in result.raw_output

    @patch("subprocess.run")
    def test_run_workload_success(self, mock_run: MagicMock):
        k6_json_output = """{
            "metrics": {
                "http_reqs": {"count": 5000},
                "http_req_duration": {"p(95)": 45.2, "p(99)": 89.1},
                "http_req_failed": {"rate": 0.005},
                "vus_max": {"max": 100}
            }
        }"""

        mock_run.return_value = subprocess.CompletedProcess(
            args=["k6", "run", "test.js"],
            returncode=0,
            stdout=k6_json_output,
            stderr="",
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            script_path = Path(tmpdir) / "steady-load.js"
            script_path.write_text("export default function() {}")

            runner = K6Runner(scripts_dir=tmpdir)
            result = runner.run_workload("steady", "s1-k8s-only", duration_sec=60)

        assert result.success is True
        assert result.http_reqs == 5000
        assert result.http_req_duration_p95 == 45.2
        assert result.http_req_duration_p99 == 89.1
        assert result.http_req_failed_rate == 0.005
        assert result.vus_max == 100

    @patch("subprocess.run")
    def test_run_workload_k6_not_found(self, mock_run: MagicMock):
        mock_run.side_effect = FileNotFoundError("k6 not found")

        with tempfile.TemporaryDirectory() as tmpdir:
            script_path = Path(tmpdir) / "steady-load.js"
            script_path.write_text("export default function() {}")

            runner = K6Runner(scripts_dir=tmpdir)
            result = runner.run_workload("steady", "s1-k8s-only")

        assert result.success is False
        assert "k6 not found" in result.raw_output

    @patch("subprocess.run")
    def test_run_workload_timeout(self, mock_run: MagicMock):
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="k6", timeout=300)

        with tempfile.TemporaryDirectory() as tmpdir:
            script_path = Path(tmpdir) / "steady-load.js"
            script_path.write_text("export default function() {}")

            runner = K6Runner(scripts_dir=tmpdir)
            result = runner.run_workload("steady", "s1-k8s-only", duration_sec=60)

        assert result.success is False
        assert "timed out" in result.raw_output

    @patch("subprocess.run")
    def test_run_workload_with_target_url(self, mock_run: MagicMock):
        mock_run.return_value = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout="http_reqs: 100",
            stderr="",
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            script_path = Path(tmpdir) / "steady-load.js"
            script_path.write_text("export default function() {}")

            runner = K6Runner(scripts_dir=tmpdir)
            runner.run_workload("steady", "s1-k8s-only", target_url="http://localhost:8080")

        call_args = mock_run.call_args[0][0]
        assert "-e" in call_args
        target_idx = call_args.index("-e")
        assert call_args[target_idx + 1] == "TARGET_URL=http://localhost:8080"


class TestGenerateTraceStages:
    def test_generate_stages_from_request_count(self):
        runner = K6Runner()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("timestamp,request_count\n")
            f.write("0,10\n")
            f.write("60,25\n")
            f.write("120,50\n")
            f.write("180,30\n")
            f.name

        try:
            stages = runner.generate_trace_stages(f.name, interval_sec=60)

            assert len(stages) == 4
            assert stages[0] == {"duration": "60s", "target": 10}
            assert stages[1] == {"duration": "60s", "target": 25}
            assert stages[2] == {"duration": "60s", "target": 50}
            assert stages[3] == {"duration": "60s", "target": 30}
        finally:
            Path(f.name).unlink()

    def test_generate_stages_from_rps(self):
        runner = K6Runner()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("time,rps\n")
            f.write("0,100\n")
            f.write("1,200\n")
            f.write("2,150\n")
            f.name

        try:
            stages = runner.generate_trace_stages(f.name, interval_sec=30)

            assert len(stages) == 3
            assert stages[0]["target"] == 100
            assert stages[1]["target"] == 200
            assert stages[2]["target"] == 150
            assert all(s["duration"] == "30s" for s in stages)
        finally:
            Path(f.name).unlink()

    def test_generate_stages_file_not_found(self):
        runner = K6Runner()

        with pytest.raises(FileNotFoundError):
            runner.generate_trace_stages("/nonexistent/trace.csv")


class TestParseK6Output:
    def test_parse_json_output(self):
        runner = K6Runner()
        json_output = """{
            "metrics": {
                "http_reqs": {"count": 2500},
                "http_req_duration": {"avg": 25.5, "p(95)": 55.0, "p(99)": 120.0},
                "http_req_failed": {"rate": 0.02},
                "vus_max": {"max": 75}
            }
        }"""

        result = runner._parse_k6_output(json_output, exit_success=True)

        assert result.success is True
        assert result.http_reqs == 2500
        assert result.http_req_duration_p95 == 55.0
        assert result.http_req_duration_p99 == 120.0
        assert result.http_req_failed_rate == 0.02
        assert result.vus_max == 75

    def test_parse_text_output(self):
        runner = K6Runner()
        text_output = """
        http_reqs..................: 3000
        http_req_duration..........: avg=30ms p(95)=65ms p(99)=130ms
        http_req_failed............: 1.5%
        vus_max....................: 50
        """

        result = runner._parse_k6_output(text_output, exit_success=True)

        assert result.success is True
        assert result.http_reqs == 3000
        assert result.http_req_duration_p95 == 65.0
        assert result.http_req_duration_p99 == 130.0
        assert result.http_req_failed_rate == 0.015
        assert result.vus_max == 50

    def test_parse_empty_output(self):
        runner = K6Runner()
        result = runner._parse_k6_output("", exit_success=False)

        assert result.success is False
        assert result.http_reqs == 0
        assert result.http_req_duration_p95 == 0.0
