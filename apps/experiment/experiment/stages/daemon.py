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

# Project paths
SCRIPT_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent / "scripts"
PROJECT_ROOT = SCRIPT_DIR.parent
CONTROLLER_DIR = PROJECT_ROOT / "controller"


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

    @staticmethod
    def _kill_stale_daemon() -> None:
        """Kill any process listening on DAEMON_API_PORT before starting fresh."""
        try:
            sock = _socket.socket(_socket.AF_INET, _socket.SOCK_STREAM)
            sock.settimeout(2)
            sock.connect(("localhost", DAEMON_API_PORT))
            sock.close()
        except (ConnectionRefusedError, OSError):
            return  # Port free — nothing to kill

        logger.warning("stale_daemon_detected", port=DAEMON_API_PORT)
        try:
            r = subprocess.run(
                ["ss", "-tlnp", f"sport = :{DAEMON_API_PORT}"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            for line in r.stdout.strip().split("\n"):
                if f":{DAEMON_API_PORT}" in line and "pid=" in line:
                    pid_str = line.split("pid=")[1].split(",")[0]
                    pid = int(pid_str)
                    logger.warning("killing_stale_daemon", pid=pid)
                    os.kill(pid, signal.SIGKILL)
                    time.sleep(1)
        except Exception as e:
            logger.warning("stale_daemon_kill_failed", error=str(e))

    def _start(self, scenario: str, log_path: Path) -> Optional[subprocess.Popen]:
        self._kill_stale_daemon()

        cmd = [
            sys.executable,
            "-m",
            "daemon.routing_daemon",
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
            cwd=str(CONTROLLER_DIR),
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
