"""HAProxy configuration, rendered against the cluster that is running now.

The shipped configs name the Knative host by its sslip.io domain, and that domain
embeds the Kourier service IP: `test-app.default.192.168.0.2.sslip.io` on the
cluster created in July, `test-app.default.172.22.0.2.sslip.io` on the one created
today. A rebuilt cluster therefore serves 404 to every request HAProxy forwards to
it, the serverless arm stops answering, and the run measures a broken arm rather
than a slow one.

The config is read from the package and written to a runtime path with the live
host substituted, so the package stays a template and nothing tracked changes.
"""

from __future__ import annotations

import importlib.resources
import re
from pathlib import Path

import structlog

from infra.commands import run

logger = structlog.get_logger(__name__)

SERVERLESS_CONTEXT = "k3d-thesis-serverless"
K8S_WORKLOAD_NODE = "k3d-thesis-hybrid-agent-0"
RUNTIME_DIR = Path.home() / ".cache" / "thesis" / "haproxy"

_HOST_HEADER = re.compile(r"^(\s*http-request set-header Host )\S+$", re.MULTILINE)


def knative_host(*, context: str = SERVERLESS_CONTEXT) -> str | None:
    """The Knative service's own host, read from the cluster rather than assumed."""
    result = run(
        [
            "kubectl",
            "--context",
            context,
            "get",
            "ksvc",
            "test-app",
            "-n",
            "default",
            "-o",
            "jsonpath={.status.url}",
        ]
    )
    url = (result.stdout or "").strip()
    if result.returncode != 0 or "://" not in url:
        logger.warning("knative_host_unavailable", stderr=result.stderr.strip())
        return None
    return url.split("://", 1)[1].rstrip("/")


def render_config(mode: str = "default", *, host: str | None = None) -> Path:
    """Write the HAProxy config for `mode` with the running cluster's host.

    Returns the path to the rendered file, which callers mount in place of the
    package copy.
    """
    filename = {
        "default": "haproxy.cfg",
        "knative": "haproxy-knative.cfg",
        "coldstart": "haproxy-coldstart.cfg",
    }.get(mode, "haproxy.cfg")
    source = importlib.resources.files("infra").joinpath("networking", "haproxy", filename)
    text = source.read_text()
    # The K8s backend is addressed by node name, which survives a rebuild; only the
    # Knative host carries the cluster's IP.
    text = text.replace("k3d-thesis-hybrid-agent-0", K8S_WORKLOAD_NODE)

    resolved = host or knative_host()
    if resolved is None:
        logger.warning("haproxy_host_unresolved", mode=mode)
    else:
        text, replaced = _HOST_HEADER.subn(rf"\g<1>{resolved}", text)
        if not replaced:
            logger.warning("haproxy_host_header_absent", mode=mode)

    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    target = RUNTIME_DIR / filename
    target.write_text(text)
    logger.info("haproxy_config_rendered", mode=mode, path=str(target), knative_host=resolved)
    return target
