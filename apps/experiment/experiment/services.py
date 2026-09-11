"""Long-lived services an experiment needs, converged to a known state.

The prediction server is operator-managed by design, which made it the step most
likely to be wrong by hand: started on the integrated GPU it aborts the process
mid-run, and started against a stale artifact it silently forecasts the wrong
series. Both failures produce a run that looks successful and is not. This module
makes the server's identity and device part of the experiment.
"""

from __future__ import annotations

import hashlib
import os
import subprocess
import time
from pathlib import Path

import requests
import structlog

from experiment.stages.daemon import kill_process_on_port

logger = structlog.get_logger(__name__)

DEFAULT_MODEL_PATH = Path("data/models/gru_model.pt")
DEFAULT_PORT = 8090
DEFAULT_LOG = Path("/tmp/thesis-prediction-server.log")


def artifact_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def server_status(port: int = DEFAULT_PORT, timeout: float = 3.0) -> dict | None:
    try:
        response = requests.get(f"http://localhost:{port}/model/status", timeout=timeout)
    except requests.RequestException:
        return None
    if response.status_code != 200:
        return None
    payload = response.json()
    return payload if payload.get("loaded") else None


def ensure_prediction_server(
    model_path: Path = DEFAULT_MODEL_PATH,
    port: int = DEFAULT_PORT,
    log_path: Path = DEFAULT_LOG,
    timeout_s: int = 240,
) -> dict:
    """Serve `model_path` on `port`, on CPU, and report what had to change.

    Idempotent: a healthy server already serving the same artifact is reused, and
    one serving a different artifact is replaced rather than trusted.
    """
    model_path = Path(model_path)
    if not model_path.exists():
        return {"status": "unavailable", "reason": f"model artifact not found: {model_path}", "port": port}

    desired = artifact_sha256(model_path)
    current = server_status(port)
    if current is not None and current.get("artifact_sha256") == desired:
        return {
            "status": "reused",
            "port": port,
            "artifact_sha256": desired,
            "sequence_length": current.get("sequence_length"),
            "prediction_horizon": current.get("prediction_horizon"),
        }

    if current is not None:
        logger.warning(
            "prediction_server_artifact_mismatch",
            serving=current.get("artifact_sha256"),
            wanted=desired,
        )
        kill_process_on_port(port, "gru_prediction_service")
        time.sleep(2)

    log_path.parent.mkdir(parents=True, exist_ok=True)
    env = {
        **os.environ,
        # The integrated GPU aborts the process mid-run on this class of host, which
        # fails every eligible forecast and invalidates the S4 arm.
        "CUDA_VISIBLE_DEVICES": "",
        "HIP_VISIBLE_DEVICES": "",
        "ROCR_VISIBLE_DEVICES": "",
        "OMP_NUM_THREADS": os.environ.get("OMP_NUM_THREADS", "4"),
    }
    with open(log_path, "ab") as log:
        subprocess.Popen(
            ["uv", "run", "thesis", "prediction", "serve", "--port", str(port), "--model-path", str(model_path)],
            stdout=log,
            stderr=subprocess.STDOUT,
            env=env,
            start_new_session=True,
        )

    deadline = time.time() + timeout_s
    while time.time() < deadline:
        status = server_status(port, timeout=2.0)
        if status is not None and status.get("artifact_sha256") == desired:
            return {
                "status": "started",
                "port": port,
                "artifact_sha256": desired,
                "sequence_length": status.get("sequence_length"),
                "prediction_horizon": status.get("prediction_horizon"),
                "log": str(log_path),
            }
        time.sleep(2)

    return {
        "status": "unavailable",
        "reason": f"server did not report the requested artifact within {timeout_s}s; see {log_path}",
        "port": port,
        "artifact_sha256": desired,
    }
