"""K6 load testing runner: subprocess interface for k6 workload execution."""

import json
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class K6Result:
    """Result of a k6 load test execution."""

    success: bool
    http_reqs: int
    http_req_duration_p95: float
    http_req_duration_p99: float
    http_req_failed_rate: float
    vus_max: int
    raw_output: str
    metrics: dict[str, Any] = field(default_factory=dict)


class K6Runner:
    """Runs k6 load test scripts and parses results."""

    WORKLOAD_SCRIPTS = {
        "steady": "steady-load.js",
        "spike": "spike-load.js",
        "endurance": "endurance-test.js",
        "clarknet_replay": "clarknet_replay.js",
    }

    def __init__(self, scripts_dir: str = "infrastructure/load-tests"):
        self.scripts_dir = Path(scripts_dir)
        if not self.scripts_dir.is_absolute():
            project_root = Path(__file__).parent.parent.parent
            self.scripts_dir = project_root / scripts_dir

    def run_workload(
        self,
        workload: str,
        scenario: str,
        duration_sec: int = 300,
        target_url: str | None = None,
    ) -> K6Result:
        """Run a k6 workload and return parsed results.

        Args:
            workload: Workload name (key into WORKLOAD_SCRIPTS)
            scenario: k6 scenario configuration
            duration_sec: Test duration in seconds
            target_url: Optional target URL override

        Returns:
            K6Result with parsed metrics
        """
        if workload not in self.WORKLOAD_SCRIPTS:
            return K6Result(
                success=False,
                http_reqs=0,
                http_req_duration_p95=0.0,
                http_req_duration_p99=0.0,
                http_req_failed_rate=1.0,
                vus_max=0,
                raw_output=f"Unknown workload: {workload}. Valid: {list(self.WORKLOAD_SCRIPTS.keys())}",
            )

        script_path = self.scripts_dir / self.WORKLOAD_SCRIPTS[workload]
        if not script_path.exists():
            return K6Result(
                success=False,
                http_reqs=0,
                http_req_duration_p95=0.0,
                http_req_duration_p99=0.0,
                http_req_failed_rate=1.0,
                vus_max=0,
                raw_output=f"Script not found: {script_path}",
            )

        cmd = [
            "k6",
            "run",
            "--summary-export=/dev/stdout",
            f"--duration={duration_sec}s",
        ]

        if target_url:
            cmd.extend(["-e", f"TARGET_URL={target_url}"])

        cmd.extend(["-e", f"SCENARIO={scenario}"])
        cmd.append(str(script_path))

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=duration_sec + 120,
            )
            raw_output = result.stdout + result.stderr
            return self._parse_k6_output(raw_output, result.returncode == 0)
        except subprocess.TimeoutExpired:
            return K6Result(
                success=False,
                http_reqs=0,
                http_req_duration_p95=0.0,
                http_req_duration_p99=0.0,
                http_req_failed_rate=1.0,
                vus_max=0,
                raw_output="k6 test timed out",
            )
        except FileNotFoundError:
            return K6Result(
                success=False,
                http_reqs=0,
                http_req_duration_p95=0.0,
                http_req_duration_p99=0.0,
                http_req_failed_rate=1.0,
                vus_max=0,
                raw_output="k6 not found. Install: https://k6.io/docs/get-started/installation/",
            )

    def _parse_k6_output(self, raw_output: str, exit_success: bool) -> K6Result:
        """Parse k6 stdout/stderr to extract metrics.

        Tries JSON summary export first, falls back to regex parsing.
        """
        metrics: dict[str, Any] = {}
        http_reqs = 0
        http_req_duration_p95 = 0.0
        http_req_duration_p99 = 0.0
        http_req_failed_rate = 0.0
        vus_max = 0

        json_match = re.search(r"^\{.*\}$", raw_output, re.MULTILINE | re.DOTALL)
        if json_match:
            try:
                summary = json.loads(json_match.group())
                metrics = summary.get("metrics", {})

                if "http_reqs" in metrics:
                    http_reqs = int(metrics["http_reqs"].get("count", 0))

                if "http_req_duration" in metrics:
                    duration = metrics["http_req_duration"]
                    http_req_duration_p95 = float(duration.get("p(95)", 0))
                    http_req_duration_p99 = float(duration.get("p(99)", 0))

                if "http_req_failed" in metrics:
                    http_req_failed_rate = float(metrics["http_req_failed"].get("rate", 0))

                if "vus_max" in metrics:
                    vus_max = int(metrics["vus_max"].get("max", 0))

                return K6Result(
                    success=exit_success,
                    http_reqs=http_reqs,
                    http_req_duration_p95=http_req_duration_p95,
                    http_req_duration_p99=http_req_duration_p99,
                    http_req_failed_rate=http_req_failed_rate,
                    vus_max=vus_max,
                    raw_output=raw_output,
                    metrics=metrics,
                )
            except json.JSONDecodeError:
                pass

        http_reqs_match = re.search(r"http_reqs[.\s]+:\s+([\d.]+)", raw_output)
        if http_reqs_match:
            http_reqs = int(float(http_reqs_match.group(1)))

        p95_match = re.search(r"p\(95\)[=:]\s*([\d.]+)", raw_output)
        if p95_match:
            http_req_duration_p95 = float(p95_match.group(1))

        p99_match = re.search(r"p\(99\)[=:]\s*([\d.]+)", raw_output)
        if p99_match:
            http_req_duration_p99 = float(p99_match.group(1))

        failed_match = re.search(r"http_req_failed[.\s]+:\s+([\d.]+)%", raw_output)
        if failed_match:
            http_req_failed_rate = float(failed_match.group(1)) / 100

        vus_match = re.search(r"vus_max[.\s]+:\s+(\d+)", raw_output)
        if vus_match:
            vus_max = int(vus_match.group(1))

        return K6Result(
            success=exit_success,
            http_reqs=http_reqs,
            http_req_duration_p95=http_req_duration_p95,
            http_req_duration_p99=http_req_duration_p99,
            http_req_failed_rate=http_req_failed_rate,
            vus_max=vus_max,
            raw_output=raw_output,
            metrics=metrics,
        )

    def generate_trace_stages(self, trace_file: str, interval_sec: int = 60) -> list[dict[str, str | int]]:
        """Generate k6 stages from a trace CSV file.

        Args:
            trace_file: Path to CSV with request count or rps column
            interval_sec: Duration of each stage in seconds

        Returns:
            List of k6 stage dicts with 'duration' and 'target' keys
        """
        trace_path = Path(trace_file)
        if not trace_path.exists():
            raise FileNotFoundError(f"Trace file not found: {trace_file}")

        try:
            import pandas as pd

            df = pd.read_csv(trace_path)

            if "timestamp" in df.columns and "request_count" in df.columns:
                stages = []
                for _, row in df.iterrows():
                    stages.append(
                        {
                            "duration": f"{interval_sec}s",
                            "target": int(row["request_count"]),
                        }
                    )
                return stages

            if "rps" in df.columns:
                stages = []
                for _, row in df.iterrows():
                    stages.append({"duration": f"{interval_sec}s", "target": int(row["rps"])})
                return stages

            if len(df.columns) >= 2:
                value_col = df.columns[1]
                stages = []
                for _, row in df.iterrows():
                    stages.append(
                        {
                            "duration": f"{interval_sec}s",
                            "target": int(row[value_col]),
                        }
                    )
                return stages

            raise ValueError(f"Cannot determine RPS column in trace file. Columns: {list(df.columns)}")
        except ImportError:
            with open(trace_path) as f:
                lines = f.readlines()

            if not lines:
                return []

            header = lines[0].strip().split(",")
            stages = []

            value_idx = 1
            if "request_count" in header:
                value_idx = header.index("request_count")
            elif "rps" in header:
                value_idx = header.index("rps")

            for line in lines[1:]:
                parts = line.strip().split(",")
                if len(parts) > value_idx:
                    try:
                        target = int(float(parts[value_idx]))
                        stages.append({"duration": f"{interval_sec}s", "target": target})
                    except ValueError:
                        continue

            return stages

    def get_script_path(self, workload: str) -> Path | None:
        """Get the filesystem path for a workload script.

        Args:
            workload: Workload name

        Returns:
            Path to the script file, or None if not found
        """
        if workload not in self.WORKLOAD_SCRIPTS:
            return None
        return self.scripts_dir / self.WORKLOAD_SCRIPTS[workload]

    def list_available_workloads(self) -> list[str]:
        """List all available workload names."""
        return list(self.WORKLOAD_SCRIPTS.keys())
