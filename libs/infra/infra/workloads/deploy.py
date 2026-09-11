"""Deploy the test application to both clusters (K8s + Knative).

One implementation, called by ``thesis infra deploy-app`` and by the testbed
rebuild that precedes a headline experiment. Idempotent: safe to re-run.
"""

from __future__ import annotations

import importlib.resources
import os
import time

import structlog

from infra.commands import run

logger = structlog.get_logger(__name__)

IMAGE = "k3d-registry.localhost:5000/test-app:latest"
SERVERLESS_CONTEXT = "k3d-thesis-serverless"
K8S_DEPLOYMENT = "test-app-warm"


def deploy_test_app(*, skip_build: bool = False) -> dict:
    """Build, push, and deploy test-app to the K8s and Knative clusters.

    Returns {"k8s_ok": bool, "knative_ok": bool, "actions": [str, ...]}. A False
    endpoint is a real failure: the runs that follow measure whatever is serving.
    """
    app_dir = importlib.resources.files("infra").joinpath("workloads", "test_app")
    actions: list[str] = []

    if not skip_build:
        logger.info("test_app_build_start")
        run(["docker", "build", "-t", IMAGE, str(app_dir)], check=True)
        run(["docker", "push", IMAGE], check=True)
        _import_image(SERVERLESS_CONTEXT)
        actions.append("built and pushed test-app image")
        logger.info("test_app_build_done")

    # Knative resolves image tags against a registry it cannot reach; tell it to skip.
    run(
        [
            "kubectl",
            "--context",
            SERVERLESS_CONTEXT,
            "patch",
            "configmap",
            "config-deployment",
            "-n",
            "knative-serving",
            "--type",
            "merge",
            "-p",
            '{"data":{"registries-skipping-tag-resolving":"kind.local,ko.local,dev.local,k3d-registry.localhost:5000"}}',
        ],
        check=False,
    )

    run(["kubectl", "apply", "-f", str(app_dir.joinpath("test-app-warm-deployment.yaml"))], check=True)
    run(["kubectl", "rollout", "restart", f"deployment/{K8S_DEPLOYMENT}"], check=True)
    actions.append("applied the K8s deployment")

    run(
        ["kubectl", "--context", SERVERLESS_CONTEXT, "delete", "ksvc", "test-app", "--ignore-not-found"],
        check=False,
    )
    run(
        ["kubectl", "--context", SERVERLESS_CONTEXT, "apply", "-f", str(app_dir.joinpath("knative-service.yaml"))],
        check=True,
    )
    actions.append("recreated the Knative service")

    run(["kubectl", "rollout", "status", f"deployment/{K8S_DEPLOYMENT}", "--timeout=90s"], check=True)
    run(
        [
            "kubectl",
            "--context",
            SERVERLESS_CONTEXT,
            "wait",
            "--for=condition=Ready",
            "ksvc/test-app",
            "--timeout=120s",
        ],
        check=False,
    )
    time.sleep(5)

    k8s_ok, knative_ok = verify_endpoints()
    logger.info("test_app_deployed", k8s_ok=k8s_ok, knative_ok=knative_ok)
    return {"k8s_ok": k8s_ok, "knative_ok": knative_ok, "actions": actions}


def _import_image(cluster: str, *, attempts: int = 3) -> None:
    """Hand the image to a cluster, retrying while k3d finishes registering it."""
    for attempt in range(1, attempts + 1):
        result = run(["k3d", "image", "import", IMAGE, "-c", cluster])
        if result.returncode == 0:
            return
        logger.warning("image_import_failed", cluster=cluster, attempt=attempt, stderr=result.stderr.strip())
        time.sleep(10)
    result.check_returncode()


def verify_endpoints() -> tuple[bool, bool]:
    """Request one fib from each path, requiring the I/O wait the workload declares."""
    import requests

    haproxy_port = os.environ.get("HAPROXY_HTTP_PORT", "18082")
    k8s_ok = False
    try:
        payload = requests.get(f"http://localhost:{haproxy_port}/fib?n=33", timeout=10).json()
        k8s_ok = payload.get("io_wait_ms", 0) > 0
        logger.info(
            "endpoint_verified",
            endpoint="k8s",
            duration_ms=payload.get("duration_ms"),
            io_wait_ms=payload.get("io_wait_ms"),
        )
    except Exception as exc:  # noqa: BLE001 — an unreachable endpoint is the signal
        logger.error("endpoint_verify_failed", endpoint="k8s", error=str(exc))

    knative_ok = False
    try:
        payload = requests.get(
            "http://localhost:8083/fib?n=33",
            headers={"Host": "test-app.default.192.168.0.2.sslip.io"},
            timeout=10,
        ).json()
        knative_ok = payload.get("io_wait_ms", 0) > 0
        logger.info(
            "endpoint_verified",
            endpoint="knative",
            duration_ms=payload.get("duration_ms"),
            io_wait_ms=payload.get("io_wait_ms"),
        )
    except Exception as exc:  # noqa: BLE001 — an unreachable endpoint is the signal
        logger.error("endpoint_verify_failed", endpoint="knative", error=str(exc))

    return k8s_ok, knative_ok
