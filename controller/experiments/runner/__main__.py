#!/usr/bin/env python3
"""
Experiment Runner CLI.

Single-command experiment orchestration for S1-S4 scenarios.

Usage:
    uv run python -m experiments.runner run --scenario s1
    uv run python -m experiments.runner run --matrix all
    uv run python -m experiments.runner report --run-dir results/...
"""

import argparse
import json
import subprocess
import sys
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional

import httpx
import structlog

from .process import ProcessManager
from config import settings

logger = structlog.get_logger(__name__)

# Project paths
CONTROLLER_DIR = Path(__file__).parent.parent.parent
PROJECT_ROOT = CONTROLLER_DIR.parent
INFRASTRUCTURE_DIR = PROJECT_ROOT / "infrastructure"
RESULTS_DIR = PROJECT_ROOT / "infrastructure" / "results" / "knative-real" / "automated"


class Scenario(str, Enum):
    S1_K8S_ONLY = "s1-k8s-only"
    S2_SERVERLESS_ONLY = "s2-serverless-only"
    S3_HYBRID_REACTIVE = "s3-hybrid-reactive"
    S4_HYBRID_PREDICTIVE = "s4-hybrid-predictive"


class Workload(str, Enum):
    STEADY = "steady"
    SPIKE = "spike"
    STRESS = "stress"


@dataclass
class ScenarioConfig:
    """Configuration for each scenario."""
    name: str
    initial_k3s_weight: int
    initial_knative_weight: int
    use_daemon: bool
    use_gru: bool
    use_hpa: bool
    knative_enabled: bool


SCENARIO_CONFIGS: Dict[Scenario, ScenarioConfig] = {
    Scenario.S1_K8S_ONLY: ScenarioConfig(
        name="S1: K8s Only",
        initial_k3s_weight=100,
        initial_knative_weight=0,
        use_daemon=False,
        use_gru=False,
        use_hpa=True,
        knative_enabled=False,
    ),
    Scenario.S2_SERVERLESS_ONLY: ScenarioConfig(
        name="S2: Serverless Only",
        initial_k3s_weight=0,
        initial_knative_weight=100,
        use_daemon=False,
        use_gru=False,
        use_hpa=False,
        knative_enabled=True,
    ),
    Scenario.S3_HYBRID_REACTIVE: ScenarioConfig(
        name="S3: Hybrid Reactive",
        initial_k3s_weight=100,
        initial_knative_weight=0,
        use_daemon=True,
        use_gru=False,
        use_hpa=True,
        knative_enabled=True,
    ),
    Scenario.S4_HYBRID_PREDICTIVE: ScenarioConfig(
        name="S4: Hybrid Predictive",
        initial_k3s_weight=100,
        initial_knative_weight=0,
        use_daemon=True,
        use_gru=True,
        use_hpa=True,
        knative_enabled=True,
    ),
}


@dataclass
class RunMetadata:
    """Metadata for experiment run."""
    run_id: str
    scenario: str
    workload: str
    start_time: str
    end_time: Optional[str] = None
    git_sha: Optional[str] = None
    duration_sec: Optional[float] = None
    success: bool = False
    error: Optional[str] = None


class ExperimentRunner:
    """
    Orchestrates experiment execution.
    
    Handles:
    - Preflight checks
    - Infrastructure setup per scenario
    - Process lifecycle (daemon, GRU)
    - Load test execution
    - Result collection
    """
    
    def __init__(
        self,
        haproxy_url: str = "http://localhost:18082",
        haproxy_socket: str = "localhost:19999",
        prometheus_url: str = None,
        knative_url: str = None,
        knative_host: str = "test-app.default.localhost",
    ):
        self.haproxy_url = haproxy_url
        self.haproxy_socket_host, self.haproxy_socket_port = haproxy_socket.split(":")
        self.haproxy_socket_port = int(self.haproxy_socket_port)
        self.prometheus_url = prometheus_url or settings.PROMETHEUS_URL
        # Use K3S_NODE_IP from config for Knative URL, defaulting to localhost
        knative_host_ip = settings.K3S_NODE_IP if settings.K3S_NODE_IP != "127.0.0.1" else "localhost"
        self.knative_url = knative_url or f"http://{knative_host_ip}:8081"
        self.knative_host = knative_host
    
    def preflight_check(self) -> bool:
        """Verify all dependencies are available."""
        checks = {
            "kubectl": self._check_kubectl,
            "k6": self._check_k6,
            "haproxy": self._check_haproxy,
            "prometheus": self._check_prometheus,
        }
        
        all_ok = True
        for name, check_fn in checks.items():
            try:
                ok = check_fn()
                status = "✓" if ok else "✗"
                logger.info(f"Preflight {name}: {status}")
                all_ok = all_ok and ok
            except Exception as e:
                logger.error(f"Preflight {name}: ✗ ({e})")
                all_ok = False
        
        return all_ok
    
    def _check_kubectl(self) -> bool:
        result = subprocess.run(["kubectl", "cluster-info"], capture_output=True)
        return result.returncode == 0
    
    def _check_k6(self) -> bool:
        result = subprocess.run(["k6", "version"], capture_output=True)
        return result.returncode == 0
    
    def _check_haproxy(self) -> bool:
        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.get(f"{self.haproxy_url}/health")
                return response.status_code in (200, 404)  # 404 is ok, means HAProxy responds
        except Exception:
            return False
    
    def _check_prometheus(self) -> bool:
        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.get(f"{self.prometheus_url}/-/healthy")
                return response.status_code == 200
        except Exception:
            return False
    
    def _get_git_sha(self) -> Optional[str]:
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"],
                capture_output=True, text=True, cwd=PROJECT_ROOT
            )
            return result.stdout.strip() if result.returncode == 0 else None
        except Exception:
            return None
    
    def _haproxy_cmd(self, cmd: str) -> str:
        """Send command to HAProxy socket."""
        import socket
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((self.haproxy_socket_host, self.haproxy_socket_port))
                s.sendall(f"{cmd}\n".encode())
                time.sleep(0.1)
                return s.recv(4096).decode()
        except Exception as e:
            logger.error("HAProxy command failed", cmd=cmd, error=str(e))
            return ""
    
    def set_haproxy_weights(self, k3s_weight: int, knative_weight: int, knative_enabled: bool) -> None:
        """Set HAProxy backend weights."""
        if knative_enabled and knative_weight > 0:
            self._haproxy_cmd("enable server servers/knative")
            time.sleep(0.3)
        
        self._haproxy_cmd(f"set server servers/k3s-cluster weight {k3s_weight}")
        self._haproxy_cmd(f"set server servers/knative weight {knative_weight}")
        
        if not knative_enabled or knative_weight == 0:
            self._haproxy_cmd("disable server servers/knative")
        
        self._haproxy_cmd("clear counters all")
        
        logger.info("HAProxy weights set", k3s=k3s_weight, knative=knative_weight, enabled=knative_enabled)
    
    def prewarm_knative(self) -> bool:
        """Pre-warm Knative service to avoid cold start during test."""
        logger.info("Pre-warming Knative service...")
        try:
            start = time.time()
            with httpx.Client(timeout=30.0) as client:
                response = client.get(
                    f"{self.knative_url}/health",
                    headers={"Host": self.knative_host}
                )
                elapsed_ms = (time.time() - start) * 1000
                logger.info("Knative pre-warmed", status=response.status_code, elapsed_ms=round(elapsed_ms))
                return response.status_code == 200
        except Exception as e:
            logger.warning("Knative pre-warm failed", error=str(e))
            return False
    
    def run_k6(
        self,
        workload: Workload,
        scenario: Scenario,
        output_dir: Path,
    ) -> bool:
        """Run k6 load test."""
        workload_file = INFRASTRUCTURE_DIR / "load-tests" / f"{workload.value}.js"
        
        if not workload_file.exists():
            # Fall back to stress.js for now
            workload_file = INFRASTRUCTURE_DIR / "load-tests" / "stress.js"
        
        summary_file = output_dir / "k6-summary.json"
        results_file = output_dir / "k6-results.json"
        
        cmd = [
            "k6", "run",
            "-e", f"BASE_URL={self.haproxy_url}",
            "-e", f"SCENARIO={scenario.value}",
            "--summary-export", str(summary_file),
            "--out", f"json={results_file}",
            str(workload_file),
        ]
        
        logger.info("Starting k6 load test", workload=workload.value, scenario=scenario.value)
        
        with open(output_dir / "k6-output.log", "w") as log_file:
            result = subprocess.run(cmd, stdout=log_file, stderr=subprocess.STDOUT)
        
        success = result.returncode == 0
        logger.info("k6 completed", success=success, returncode=result.returncode)
        return success
    
    def collect_daemon_status(self, output_dir: Path, port: int = 9104) -> None:
        """Collect routing daemon status."""
        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.get(f"http://localhost:{port}/status")
                if response.status_code == 200:
                    with open(output_dir / "daemon-status.json", "w") as f:
                        json.dump(response.json(), f, indent=2)
        except Exception as e:
            logger.warning("Failed to collect daemon status", error=str(e))
    
    def run_scenario(
        self,
        scenario: Scenario,
        workload: Workload = Workload.STRESS,
    ) -> RunMetadata:
        """Run a single scenario experiment."""
        config = SCENARIO_CONFIGS[scenario]
        run_id = f"{scenario.value}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        output_dir = RESULTS_DIR / run_id
        output_dir.mkdir(parents=True, exist_ok=True)
        
        metadata = RunMetadata(
            run_id=run_id,
            scenario=scenario.value,
            workload=workload.value,
            start_time=datetime.now().isoformat(),
            git_sha=self._get_git_sha(),
        )
        
        logger.info("=" * 60)
        logger.info(f"Running scenario: {config.name}")
        logger.info("=" * 60)
        
        start_time = time.time()
        
        try:
            # 1. Set initial HAProxy weights
            self.set_haproxy_weights(
                config.initial_k3s_weight,
                config.initial_knative_weight,
                config.knative_enabled,
            )
            
            # 2. Pre-warm Knative if needed
            if config.knative_enabled:
                self.prewarm_knative()
            
            # 3. Start processes
            with ProcessManager(output_dir, CONTROLLER_DIR) as pm:
                if config.use_gru:
                    gru = pm.start_gru(port=8090)
                    gru.wait_healthy()
                
                if config.use_daemon:
                    gru_url = "http://localhost:8090" if config.use_gru else None
                    daemon = pm.start_daemon(
                        scenario=scenario.value,
                        gru_url=gru_url,
                    )
                    daemon.wait_healthy()
                
                # 4. Run load test
                success = self.run_k6(workload, scenario, output_dir)
                
                # 5. Collect final status
                if config.use_daemon:
                    self.collect_daemon_status(output_dir)
                
                metadata.success = success
            
        except Exception as e:
            logger.error("Scenario failed", error=str(e))
            metadata.success = False
            metadata.error = str(e)
        
        finally:
            metadata.end_time = datetime.now().isoformat()
            metadata.duration_sec = round(time.time() - start_time, 2)
            
            # Save metadata
            with open(output_dir / "metadata.json", "w") as f:
                json.dump(asdict(metadata), f, indent=2)
        
        status = "✓" if metadata.success else "✗"
        logger.info(f"Scenario {scenario.value} completed: {status} ({metadata.duration_sec}s)")
        
        return metadata
    
    def run_matrix(
        self,
        scenarios: Optional[List[Scenario]] = None,
        workload: Workload = Workload.STRESS,
    ) -> List[RunMetadata]:
        """Run multiple scenarios sequentially."""
        if scenarios is None:
            scenarios = list(Scenario)
        
        results = []
        for scenario in scenarios:
            metadata = self.run_scenario(scenario, workload)
            results.append(metadata)
            
            # Cool-down between scenarios
            logger.info("Cool-down period (10s)...")
            time.sleep(10)
        
        self.generate_report(results)
        return results
    
    def generate_report(self, results: List[RunMetadata]) -> None:
        """Generate comparison report."""
        report_dir = RESULTS_DIR / "reports"
        report_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        report_file = report_dir / f"comparison-{timestamp}.md"
        
        lines = [
            "# Experiment Results Comparison",
            f"\n**Generated:** {datetime.now().isoformat()}",
            f"**Git SHA:** {results[0].git_sha if results else 'unknown'}",
            "\n## Summary\n",
            "| Scenario | Workload | Duration | Success | Error |",
            "|----------|----------|----------|---------|-------|",
        ]
        
        for r in results:
            status = "✓" if r.success else "✗"
            error = r.error[:30] + "..." if r.error and len(r.error) > 30 else (r.error or "-")
            lines.append(f"| {r.scenario} | {r.workload} | {r.duration_sec}s | {status} | {error} |")
        
        lines.extend([
            "\n## Detailed Results\n",
            "See individual run directories for:",
            "- `k6-summary.json` - Load test metrics",
            "- `daemon-status.json` - Routing daemon final state",
            "- `metadata.json` - Run metadata",
            "- `*.log` - Process logs",
        ])
        
        report_file.write_text("\n".join(lines))
        logger.info(f"Report generated: {report_file}")


def main():
    parser = argparse.ArgumentParser(description="Experiment Runner")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # Run command
    run_parser = subparsers.add_parser("run", help="Run experiments")
    run_parser.add_argument(
        "--scenario", "-s",
        choices=[s.value for s in Scenario],
        help="Single scenario to run",
    )
    run_parser.add_argument(
        "--matrix", "-m",
        choices=["all", "hybrid"],
        help="Run scenario matrix (all or hybrid only)",
    )
    run_parser.add_argument(
        "--workload", "-w",
        choices=[w.value for w in Workload],
        default="stress",
        help="Workload profile",
    )
    
    # Preflight command
    subparsers.add_parser("preflight", help="Run preflight checks only")
    
    args = parser.parse_args()
    
    # Configure logging
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer(),
        ],
    )
    
    runner = ExperimentRunner()
    
    if args.command == "preflight":
        success = runner.preflight_check()
        sys.exit(0 if success else 1)
    
    elif args.command == "run":
        # Preflight first
        if not runner.preflight_check():
            logger.error("Preflight checks failed")
            sys.exit(1)
        
        workload = Workload(args.workload)
        
        if args.scenario:
            runner.run_scenario(Scenario(args.scenario), workload)
        elif args.matrix == "all":
            runner.run_matrix(workload=workload)
        elif args.matrix == "hybrid":
            runner.run_matrix(
                scenarios=[Scenario.S3_HYBRID_REACTIVE, Scenario.S4_HYBRID_PREDICTIVE],
                workload=workload,
            )
        else:
            parser.error("Specify --scenario or --matrix")


if __name__ == "__main__":
    main()
