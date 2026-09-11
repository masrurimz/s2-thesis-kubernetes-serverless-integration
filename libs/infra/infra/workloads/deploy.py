"""Deploy the test application to both clusters (K8s + Knative).

One implementation, called by ``thesis infra deploy-app`` and by the testbed
rebuild that precedes a headline experiment. Idempotent: safe to re-run.
"""

from __future__ import annotations

import importlib.resources
import json
import os
import time

import structlog

from infra.commands import run

logger = structlog.get_logger(__name__)

IMAGE = "k3d-registry.localhost:5000/test-app:latest"
# k3d names the cluster `thesis-serverless` and prefixes its contexts and
# containers with `k3d-`. k3d commands take the name; kubectl takes the context.
SERVERLESS_CLUSTER = "thesis-serverless"
SERVERLESS_CONTEXT = f"k3d-{SERVERLESS_CLUSTER}"
K8S_DEPLOYMENT = "test-app-warm"
# The first request to a scaled-to-zero revision pays its cold start, so the probe
# gives it a few chances before calling the arm broken.
KNATIVE_PROBE_ATTEMPTS = 6
KNATIVE_PROBE_PAUSE_SEC = 5.0
FALLBACK_KNATIVE_HOST = "test-app.default.192.168.0.2.sslip.io"


def deploy_test_app(*, skip_build: bool = False, verify: bool = True) -> dict:
    """Build, push, and deploy test-app to the K8s and Knative clusters.

    Returns {"k8s_ok": bool, "knative_ok": bool, "actions": [str, ...], "verified": bool}.
    A False endpoint is a real failure: the runs that follow measure whatever is
    serving. `verify` is skipped when the caller still has to start the proxy the K8s
    probe goes through, and the caller verifies with the same function afterwards.
    """
    app_dir = importlib.resources.files("infra").joinpath("workloads", "test_app")
    actions: list[str] = []

    if not skip_build:
        logger.info("test_app_build_start")
        run(["docker", "build", "-t", IMAGE, str(app_dir)], check=True)
        run(["docker", "push", IMAGE], check=True)
        _import_image(SERVERLESS_CLUSTER)
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
    _wait_for_knative_webhook()
    _apply_knative_service(app_dir.joinpath("knative-service.yaml"))
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

    if not verify:
        return {"k8s_ok": True, "knative_ok": True, "actions": actions, "verified": False}

    k8s_ok, knative_ok = verify_endpoints()
    logger.info("test_app_deployed", k8s_ok=k8s_ok, knative_ok=knative_ok)
    return {"k8s_ok": k8s_ok, "knative_ok": knative_ok, "actions": actions, "verified": True}


def _wait_for_knative_webhook(*, timeout_sec: float = 600.0, interval_sec: float = 5.0) -> None:
    """Block until the Knative admission webhook has endpoints.

    Applying a Service before its webhook is reachable fails with "no endpoints
    available for service webhook", which is a race against the install, not a
    problem with the manifest.
    """
    deadline = time.monotonic() + timeout_sec
    while time.monotonic() < deadline:
        if _webhook_has_addresses():
            logger.info("knative_webhook_ready")
            return
        time.sleep(interval_sec)
    logger.warning("knative_webhook_timeout")


def _apply_knative_service(manifest, *, attempts: int = 3, pause_sec: float = 20.0) -> None:
    """Apply the Knative Service, retrying while the admission webhook spins up.

    A freshly installed Knative pulls its images on first use, so the webhook can
    take minutes to answer. The precondition is re-checked rather than assumed, and
    the failure is only reported when the retries are exhausted.
    """
    for attempt in range(1, attempts + 1):
        result = run(["kubectl", "--context", SERVERLESS_CONTEXT, "apply", "-f", str(manifest)])
        if result.returncode == 0:
            return
        logger.warning("knative_apply_failed", attempt=attempt, stderr=result.stderr.strip()[:200])
        if attempt < attempts:
            _wait_for_knative_webhook(timeout_sec=pause_sec * 3)
    result.check_returncode()


def _webhook_has_addresses() -> bool:
    """True only when the endpoints object carries addresses.

    The object exists from the moment its Service does, with `addresses: null`, so
    its mere presence proves nothing.
    """
    endpoints = run(
        [
            "kubectl",
            "--context",
            SERVERLESS_CONTEXT,
            "get",
            "endpoints",
            "webhook",
            "-n",
            "knative-serving",
            "-o",
            "json",
        ]
    )
    if endpoints.returncode != 0:
        return False
    try:
        subsets = json.loads(endpoints.stdout).get("subsets") or []
    except json.JSONDecodeError:
        return False
    return any(subset.get("addresses") for subset in subsets)


def _import_image(cluster: str, *, attempts: int = 3) -> None:
    """Hand the image to a cluster, retrying while k3d finishes registering it.

    Takes the k3d cluster name, not the kubectl context: passing the context makes
    k3d report "No nodes found for given cluster" while the cluster is running.
    """
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
    for attempt in range(1, KNATIVE_PROBE_ATTEMPTS + 1):
        try:
            from infra.networking.haproxy.render import knative_host

            host = knative_host() or FALLBACK_KNATIVE_HOST
            payload = requests.get(
                "http://localhost:8083/fib?n=33",
                headers={"Host": host},
                timeout=10,
            ).json()
            knative_ok = payload.get("io_wait_ms", 0) > 0
            logger.info(
                "endpoint_verified",
                endpoint="knative",
                duration_ms=payload.get("duration_ms"),
                io_wait_ms=payload.get("io_wait_ms"),
            )
            break
        except Exception as exc:  # noqa: BLE001 — an unreachable endpoint is the signal
            logger.warning("endpoint_probe_retry", endpoint="knative", attempt=attempt, error=str(exc)[:120])
            time.sleep(KNATIVE_PROBE_PAUSE_SEC)

    return k8s_ok, knative_ok
