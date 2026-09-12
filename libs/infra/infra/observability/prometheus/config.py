"""Prometheus scrape credentials and the targets that were never reachable.

Prometheus runs on the host, the application runs inside k3d, and pod IPs live on a
docker network the Prometheus container is not on — so the job set that names the
application, the kubelets and kube-state-metrics has never scraped anything. What does
work from the host is the Kubernetes API, which is published by k3d and can proxy to a
pod, a service or a kubelet. The scrape configuration uses that, and this module keeps
the pieces it needs: the API endpoint per cluster and the credentials, rendered from the
kubeconfig into files the container can read.

Rendering rather than committing: the credentials are the cluster admin's, and a
certificate in git is a certificate leaked.
"""

from __future__ import annotations

import base64
import json
import os
from dataclasses import dataclass
from pathlib import Path

from infra.commands import console, run
from shared.output import print_json

SECRETS_DIRNAME = "secrets"
CONTAINER_SECRETS_DIR = "/etc/prometheus/secrets"

# The API ports k3d publishes on the host, per cluster.
CLUSTERS: dict[str, str] = {
    "k3d-thesis-hybrid": "host.docker.internal:6443",
    "k3d-thesis-serverless": "host.docker.internal:6444",
}

SERIES_WATCHED = (
    "prom_rps",
    "prom_p99_ms",
    "cpu_usage_cores",
    "memory_usage_bytes",
)

QUERIES = {
    "prom_rps": "sum(rate(http_requests_total[1m]))",
    "prom_p99_ms": "histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket[1m])) by (le)) * 1000",
    "cpu_usage_cores": 'sum(rate(container_cpu_usage_seconds_total{namespace="default"}[1m]))',
    "memory_usage_bytes": 'sum(container_memory_working_set_bytes{namespace="default"})',
}


@dataclass(frozen=True)
class ClusterCredentials:
    """Where one cluster's API credentials were written."""

    cluster: str
    api_server: str
    certificate: Path
    key: Path


def secrets_dir() -> Path:
    """The directory the container mounts, beside the scrape configuration."""
    import importlib.resources

    return Path(str(importlib.resources.files("infra"))) / "observability" / "prometheus" / SECRETS_DIRNAME


def kubeconfig() -> dict:
    """The current kubeconfig as data, contexts and all."""
    completed = run(["kubectl", "config", "view", "-o", "json", "--raw"])
    if completed.returncode != 0:
        raise RuntimeError(f"kubectl config view failed: {completed.stderr.strip()}")
    return json.loads(completed.stdout)


def _decode(value: str) -> bytes:
    return base64.b64decode(value)


def render_credentials(config: dict, out_dir: Path) -> list[ClusterCredentials]:
    """Write each cluster's client certificate and key where the container can read them.

    Returns one entry per mounted cluster, so the caller can report what it wrote
    without re-deriving the paths.
    """
    users = {entry["name"]: entry.get("user", {}) for entry in config.get("users", [])}
    written: list[ClusterCredentials] = []
    out_dir.mkdir(parents=True, exist_ok=True)

    for context in config.get("contexts", []):
        cluster = context["context"]["cluster"]
        if cluster not in CLUSTERS:
            continue
        user = users.get(context["context"]["user"], {})
        cert_b64 = user.get("client-certificate-data")
        key_b64 = user.get("client-key-data")
        if not cert_b64 or not key_b64:
            continue

        stem = cluster.replace("k3d-", "")
        certificate = out_dir / f"{stem}.crt"
        key = out_dir / f"{stem}.key"
        certificate.write_bytes(_decode(cert_b64))
        key.write_bytes(_decode(key_b64))
        os.chmod(certificate, 0o600)
        os.chmod(key, 0o600)
        written.append(
            ClusterCredentials(
                cluster=cluster,
                api_server=CLUSTERS[cluster],
                certificate=certificate,
                key=key,
            )
        )
    return written


def sync_credentials_into_container(container: str = "sprint1-prometheus") -> tuple[bool, str]:
    """Put the rendered credentials where the running container can read them.

    The container runs as nobody, and the files are rendered 0600 because they are the
    cluster admin's key material — so the readable copy exists inside the container,
    not on the host. A `docker compose up` that recreates the container loses it; the
    rebuild path calls this again after starting Prometheus.
    """
    source = secrets_dir()
    if not any(source.glob("*.crt")):
        return False, f"nothing to sync from {source}"

    # Root inside the container: the copied files belong to the host user, and the
    # process the container runs as cannot chmod what it does not own.
    created = run(["docker", "exec", "-u", "0", container, "mkdir", "-p", CONTAINER_SECRETS_DIR])
    if created.returncode != 0:
        return False, f"container not running: {created.stderr.strip()[:80]}"
    copied = run(["docker", "cp", f"{source}/.", f"{container}:{CONTAINER_SECRETS_DIR}/"])
    if copied.returncode != 0:
        return False, copied.stderr.strip()[:120]
    made_readable = run(["docker", "exec", "-u", "0", container, "sh", "-c", f"chmod 0644 {CONTAINER_SECRETS_DIR}/*"])
    if made_readable.returncode != 0:
        return False, made_readable.stderr.strip()[:120]
    return True, "credentials synced into the container"


def validate_config(compose_file: Path) -> tuple[bool, str]:
    """Ask promtool whether the scrape configuration is valid, in a throwaway container."""
    completed = run(
        [
            "docker",
            "run",
            "--rm",
            "--entrypoint",
            "promtool",
            "-v",
            f"{compose_file.parent}:/cfg:ro,z",
            # promtool resolves the certificate paths the running container will see.
            "-v",
            f"{compose_file.parent / SECRETS_DIRNAME}:{CONTAINER_SECRETS_DIR}:ro,z",
            "prom/prometheus:v2.47.0",
            "check",
            "config",
            "/cfg/prometheus.yml",
        ]
    )
    output = (completed.stdout + completed.stderr).strip()
    return completed.returncode == 0, output


def reload_prometheus(url: str = "http://localhost:9090") -> tuple[bool, str]:
    """Ask a running Prometheus to re-read its configuration.

    A reload, not a restart: the running instance keeps its targets, its storage and
    its in-flight queries, which is what makes this safe to do while experiments run.
    """
    import urllib.error
    import urllib.request

    request = urllib.request.Request(f"{url}/-/reload", method="POST")
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return response.status == 200, f"reload returned {response.status}"
    except urllib.error.URLError as exc:
        return False, f"reload failed: {exc}"


def series_state(url: str = "http://localhost:9090") -> dict[str, int]:
    """How many series each queried metric currently has. The point of the exercise."""
    import urllib.parse
    import urllib.request

    state: dict[str, int] = {}
    for name, expr in QUERIES.items():
        query = urllib.parse.urlencode({"query": expr})
        try:
            with urllib.request.urlopen(f"{url}/api/v1/query?{query}", timeout=10) as response:
                payload = json.loads(response.read())
            state[name] = len(payload.get("data", {}).get("result", []))
        except Exception:
            state[name] = -1
    return state


def _console_report(
    written: list[ClusterCredentials], valid: bool, detail: str, state: dict[str, int], detail_sync: str = ""
) -> None:
    for entry in written:
        console.print(f"  [green]credentials[/green] {entry.cluster} → {entry.certificate.name}, {entry.key.name}")
    console.print(f"  container credentials: {detail_sync}")
    console.print(f"  config valid: {valid} ({detail.splitlines()[0] if detail else 'no output'})")
    for name, count in state.items():
        console.print(f"  series {name:22} {count}")


def apply(reload: bool = True, as_json: bool = False) -> dict:
    """Render credentials, validate the configuration, reload, and report the series."""
    import importlib.resources

    compose_file = Path(
        str(importlib.resources.files("infra").joinpath("observability", "prometheus", "docker-compose.yml"))
    )
    written = render_credentials(kubeconfig(), secrets_dir())
    synced, sync_detail = sync_credentials_into_container()
    valid, detail = validate_config(compose_file)

    reloaded = False
    reload_detail = "skipped"
    state: dict[str, int] = {}
    if reload and valid:
        reloaded, reload_detail = reload_prometheus()
        state = series_state()

    payload = {
        "credentials": [
            {"cluster": e.cluster, "api_server": e.api_server, "certificate": str(e.certificate)} for e in written
        ],
        "credentials_synced": synced,
        "sync_detail": sync_detail,
        "config_valid": valid,
        "config_detail": detail.splitlines()[0] if detail else "",
        "reloaded": reloaded,
        "reload_detail": reload_detail,
        "series": state,
        "watched": list(SERIES_WATCHED),
    }
    if as_json:
        print_json(payload)
    else:
        _console_report(written, valid, detail, state, sync_detail)
    return payload


def validate_only() -> tuple[bool, str]:
    """Validate the mounted configuration without touching a running instance."""
    import importlib.resources

    compose_file = Path(
        str(importlib.resources.files("infra").joinpath("observability", "prometheus", "docker-compose.yml"))
    )
    return validate_config(compose_file)


def cli(render_only: bool = False, verify_only: bool = False, as_json: bool = False) -> int:
    if verify_only:
        state = series_state()
        if as_json:
            print_json({"series": state})
        else:
            for name, count in state.items():
                console.print(f"  series {name:22} {count}")
        return 0 if all(count > 0 for count in state.values()) else 1
    payload = apply(reload=not render_only, as_json=as_json)
    return 0 if payload["config_valid"] else 1
