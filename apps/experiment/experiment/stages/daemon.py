"""Daemon stage: start/stop the routing daemon process lifecycle.

Extracted from scripts/run_phase_b_experiments.py lines 697-822 (DaemonManager).
"""

import os
import signal
import socket as _socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional

import requests
import structlog
from shared.config import settings
from shared.models.pipeline import PipelineContext

from experiment.stages.base import BaseStage

logger = structlog.get_logger(__name__)

# Infrastructure constants
HAPROXY_HOST = settings.HAPROXY_HOST
HAPROXY_SOCKET_PORT = settings.HAPROXY_SOCKET_PORT
HAPROXY_STATS_URL = settings.HAPROXY_STATS_URL
GRU_URL = f"http://localhost:{settings.GRU_PORT}"
DAEMON_API = f"http://localhost:{settings.DAEMON_API_PORT}"
DAEMON_API_PORT = settings.DAEMON_API_PORT
KUBECTL_PATH = os.environ.get(
    "KUBECTL_PATH",
    str(Path.home() / ".local/share/mise/installs/kubectl/1.35.0/kubectl"),
)

# Project paths — apps/experiment/experiment/stages/daemon.py → 5 levels up to root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent


def is_port_listening(port: int) -> bool:
    try:
        with _socket.create_connection(("localhost", port), timeout=1):
            return True
    except OSError:
        return False


def kill_process_on_port(port: int, label: str = "stale_process") -> None:
    if not is_port_listening(port):
        return
    logger.warning("stale_process_detected", port=port, label=label)
    try:
        result = subprocess.run(
            ["ss", "-tlnp", f"sport = :{port}"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        for line in result.stdout.splitlines():
            if f":{port}" not in line or "pid=" not in line:
                continue
            pid = int(line.split("pid=")[1].split(",")[0])
            logger.warning("killing_stale_process", pid=pid, port=port, label=label)
            os.kill(pid, signal.SIGKILL)
            time.sleep(1)
    except Exception as e:
        logger.warning("stale_process_kill_failed", port=port, label=label, error=str(e))


class DaemonStage(BaseStage):
    """Manages the routing daemon process lifecycle.

    Start the daemon, wait for it to become healthy, and stop it after the run.
    Also provides get_status() for post-run daemon metrics collection.
    """

    name = "daemon"

    def __init__(self):
        self._proc: Optional[subprocess.Popen] = None
        self._log_files: dict[int, Any] = {}

    def _run(self, ctx: PipelineContext) -> None:
        """Start the daemon. Stop is handled separately via stop_daemon()."""
        scenario = ctx.scenario
        run_dir = Path(ctx.output_dir) if ctx.output_dir else Path(".")
        daemon_log = run_dir / "daemon.log"

        if scenario == "s4-hybrid-predictive":
            ok, error, _ = self.require_prediction_service()
            if not ok:
                raise RuntimeError(error)
        self._proc = self._start(scenario, daemon_log)
        if self._proc is None:
            raise RuntimeError(f"Failed to start daemon for scenario {scenario}")

    def stop_daemon(self) -> None:
        """Stop the daemon process. Called after the run completes."""
        self._stop(self._proc)
        self._proc = None

    def get_status(self) -> Optional[Dict[str, Any]]:
        """Get daemon status from the API."""
        try:
            r = requests.get(f"{DAEMON_API}/status", timeout=5)
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass
        return None

    def require_prediction_service(self) -> tuple[bool, str, dict[str, Any]]:
        """For S4: verify the GRU prediction service is healthy, model loaded, and schema valid.

        Performs up to three attempts against ``GET {GRU_URL}/health`` and
        ``GET {GRU_URL}/model/status`` with a 3-second timeout and 1-second gap.
        Succeeds only on HTTP 200 with ``model_loaded`` truthy and a valid
        schema-v2 model status (sequence_length, prediction_horizon, sample_interval_sec).

        Returns:
            (True, "", status_dict) on success; (False, reason, {}) on failure.
        """
        last_error = ""
        for attempt in range(3):
            try:
                r = requests.get(f"{GRU_URL}/health", timeout=3)
                if r.status_code == 200:
                    health = r.json()
                    if not health.get("model_loaded"):
                        last_error = f"model_loaded={health.get('model_loaded')}"
                    else:
                        # Validate model status schema.
                        sr = requests.get(f"{GRU_URL}/model/status", timeout=3)
                        if sr.status_code == 200:
                            status = sr.json()
                            seq = status.get("sequence_length")
                            horizon = status.get("prediction_horizon")
                            interval = status.get("sample_interval_sec")
                            if seq and horizon and interval:
                                return True, "", status
                            last_error = f"model status incomplete: seq={seq}, horizon={horizon}, interval={interval}"
                        else:
                            last_error = f"model/status HTTP {sr.status_code}"
                else:
                    last_error = f"/health HTTP {r.status_code}"
            except Exception as e:
                last_error = str(e)
            if attempt < 2:
                time.sleep(1)
        if is_port_listening(settings.GRU_PORT):
            kill_process_on_port(settings.GRU_PORT, "gru_prediction_service")
            return (
                False,
                (
                    f"prediction service on port {settings.GRU_PORT} is unhealthy or model_loaded=false "
                    f"(last error: {last_error}); start it with the correct model artifact before running S4"
                ),
                {},
            )
        return (
            False,
            (
                f"prediction service is not running on port {settings.GRU_PORT} (last error: {last_error}); "
                "start the operator-managed GRU server with the correct model artifact before running S4"
            ),
            {},
        )

    @staticmethod
    def _kill_stale_daemon() -> None:
        """Kill any process listening on DAEMON_API_PORT before starting fresh."""
        kill_process_on_port(DAEMON_API_PORT, "routing_daemon")

    def _start(self, scenario: str, log_path: Path) -> Optional[subprocess.Popen]:
        self._kill_stale_daemon()

        cmd = [
            sys.executable,
            "-m",
            "routing.daemon.cli",
            "--scenario",
            scenario,
            "--haproxy-host",
            HAPROXY_HOST,
            "--haproxy-port",
            str(HAPROXY_SOCKET_PORT),
            "--haproxy-stats",
            HAPROXY_STATS_URL,
            "--gru-url",
            GRU_URL,
            "--interval",
            "15",
            "--api-port",
            str(DAEMON_API_PORT),
        ]
        env = {**os.environ, "HSA_OVERRIDE_GFX_VERSION": "11.0.0", "KUBECTL_PATH": KUBECTL_PATH}

        log_file = open(log_path, "w")
        proc = subprocess.Popen(
            cmd,
            cwd=str(PROJECT_ROOT),
            env=env,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        self._log_files[proc.pid] = log_file

        # Wait for daemon API + validate scenario and freshness
        for _ in range(20):
            time.sleep(1)
            try:
                r = requests.get(f"{DAEMON_API}/health", timeout=3)
                if r.status_code == 200:
                    health = r.json()
                    if health.get("scenario") != scenario:
                        logger.error("daemon_scenario_mismatch", expected=scenario, got=health.get("scenario"))
                        self._stop(proc)
                        return None
                    # Verify freshness via /status uptime
                    sr = requests.get(f"{DAEMON_API}/status", timeout=3)
                    if sr.status_code == 200:
                        status = sr.json()
                        if status.get("uptime_seconds", 999) > 30:
                            logger.error("daemon_not_fresh", uptime=status.get("uptime_seconds"))
                            self._stop(proc)
                            return None
                    logger.info("daemon_started", scenario=scenario, pid=proc.pid)
                    return proc
            except Exception:
                pass

        logger.error("daemon_failed_to_start", scenario=scenario)
        self._stop(proc)
        return None

    def _stop(self, proc: Optional[subprocess.Popen]) -> None:
        if proc is None:
            return
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        except (ProcessLookupError, OSError):
            proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            except (ProcessLookupError, OSError):
                proc.kill()
            proc.wait()
        if proc.pid in self._log_files:
            self._log_files.pop(proc.pid).close()
        logger.info("daemon_stopped")
