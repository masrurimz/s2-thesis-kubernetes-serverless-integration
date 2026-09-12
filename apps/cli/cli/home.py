"""What `thesis` prints with no arguments: where things stand, and what to run next.

A command with no arguments is the one an agent (or a person) runs when it does not yet
know what to ask. Help text answers a question nobody has asked yet; state answers the
first one — is the testbed up, what did the last experiment measure, what do I run now.

Everything here is bounded and guarded. The home view runs before anything else, so a
cluster that is down, a missing `k3d`, or a predictor that is not answering must degrade
to a line of text, never to a traceback or a hang.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

DESCRIPTION = "Hybrid k3s + Knative testbed: run experiments, check the conditions they ran under, read their evidence."
PREDICTION_URL = "http://localhost:8090/health"
CLUSTERS = ("thesis-hybrid", "thesis-serverless")


def _short(path: str) -> str:
    """A path with the home directory folded to ~."""
    home = os.path.expanduser("~")
    return path.replace(home, "~", 1) if path.startswith(home) else path


def _repository_root() -> Path:
    """The checkout this command belongs to, if it can be found from the executable."""
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "results" / "experiments").is_dir():
            return parent
    return Path.cwd()


def _clusters() -> str:
    """Which of the two k3d clusters exist. Never raises, never waits long."""
    try:
        done = subprocess.run(
            ["k3d", "cluster", "list", "-o", "json"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        if done.returncode != 0:
            return "unknown (k3d did not answer)"
        names = {cluster.get("name") for cluster in json.loads(done.stdout or "[]")}
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError):
        return "unknown (k3d not available)"
    up = [name for name in CLUSTERS if name in names]
    if not up:
        return "neither cluster is running"
    if len(up) == len(CLUSTERS):
        return "both clusters running"
    return f"{up[0]} running, {CLUSTERS[1 - CLUSTERS.index(up[0])]} absent"


def _predictor() -> str:
    """Whether the GRU service answers on its port."""
    import urllib.error
    import urllib.request

    try:
        with urllib.request.urlopen(PREDICTION_URL, timeout=1) as response:
            return f"answering on 8090 ({response.status})"
    except urllib.error.HTTPError as exc:
        return f"answering on 8090 ({exc.code})"
    except (urllib.error.URLError, OSError, TimeoutError):
        return "not answering on 8090"


def _latest_bundle(root: Path) -> tuple[Path | None, str]:
    """The most recently written bundle and what it concluded, if anything."""
    newest: tuple[float, Path] | None = None
    for meta in (root / "results" / "experiments").glob("*/*/meta.yaml"):
        try:
            mtime = meta.stat().st_mtime
        except OSError:
            continue
        if newest is None or mtime > newest[0]:
            newest = (mtime, meta.parent)
    if newest is None:
        return None, "no experiment bundles yet"

    bundle = newest[1]
    runs = len(list(bundle.glob("raw/*/result.json"))) + len(list(bundle.glob("*_run*/result.json")))
    from analysis.bundle_evidence import paired_verdict

    verdict = ""
    payload = paired_verdict(bundle)
    if payload is not None:
        verdict = (
            f", H2 {'supported' if payload.get('h2_supported') else 'not supported'} at {payload.get('n_pairs')} pairs"
        )
    return bundle, f"{bundle.name} — {runs} run(s){verdict}"


def print_home() -> None:
    """Print the state view."""
    root = _repository_root()
    print(f"bin: {_short(os.path.abspath(sys.argv[0]))}")
    print(f"repo: {_short(str(root))}")
    print(DESCRIPTION)
    print(f"testbed: {_clusters()}")
    print(f"predictor: {_predictor()}")

    bundle, summary = _latest_bundle(root)
    print(f"latest: {summary}")
    print()
    print("next: thesis infra status")
    print("next: thesis experiment preflight --profile h2-pair")
    if bundle is not None:
        rel = bundle.relative_to(root) if bundle.is_relative_to(root) else bundle
        print(f"next: thesis analysis runs {rel}")
    print("next: thesis experiment evidence journal --limit 20")
