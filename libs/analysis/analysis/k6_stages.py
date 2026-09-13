"""Per-stage k6 percentiles: the ramp window where the hybrid mechanism lives.

The replay script records one Trend/Counter pair per trace stage
(``stage_<NN>_latency_ms`` / ``stage_<NN>_requests``) plus a ``ramp_*`` pair over
the ramp stages, so a windowed p99 comes from the load generator itself — the
Prometheus export carries the daemon's weights but no request percentiles to
window, and a whole-run p99 dilutes exactly the window the mechanism occupies.
"""

from __future__ import annotations

import re
from typing import Sequence

_STAGE_METRIC_RE = re.compile(r"^stage_(\d+)_latency_ms$")


def ramp_stage_indices(targets: Sequence[float]) -> tuple[int, int] | None:
    """The ramp stages of a trace: (first, last) stage index, or None when flat.

    The window runs from the trough that starts the longest strictly rising run
    of stage targets through the stage holding the global maximum target. For
    the canonical ClarkNet replay (40 x 30 s buckets, targets 44..164 RPS) that
    is stages 5-18, elapsed 150-570 s: it contains the 37->131 ascent, the
    node-arrival band the ascents force, and the 73->164 ascent to the trace
    peak. k6 stage i ramps toward ``targets[i]`` over its duration, so a rising
    target is rising offered load — the stretch where the node tier must engage
    and where weight shifting can pay. Ties on the longest run go to the
    earliest; a trace with no rise has no ramp.
    """
    if len(targets) < 2:
        return None
    runs: list[list[int]] = []
    current: list[int] | None = None
    for i in range(1, len(targets)):
        if targets[i] > targets[i - 1]:
            if current is not None and i == current[-1] + 1:
                current.append(i)
            else:
                if current is not None:
                    runs.append(current)
                current = [i]
        else:
            if current is not None:
                runs.append(current)
                current = None
    if current is not None:
        runs.append(current)
    if not runs:
        return None
    longest = max(runs, key=lambda run: (len(run), -run[0]))
    peak = max(range(len(targets)), key=lambda i: (targets[i], -i))
    first = longest[0] - 1
    return (first, peak) if first < peak else (first, first)


def _duration_sec(stage: dict) -> float:
    raw = str(stage.get("duration", "0"))
    return float(raw[:-1] or 0) if raw.endswith("s") else 0.0


def ramp_window_sec(stages: Sequence[dict]) -> tuple[float, float] | None:
    """The ramp window in run-relative seconds, from a k6 stages list."""
    indices = ramp_stage_indices([float(stage.get("target", 0)) for stage in stages])
    if indices is None or indices[1] >= len(stages):
        return None
    first, last = indices
    lo = sum(_duration_sec(stage) for stage in stages[:first])
    hi = sum(_duration_sec(stage) for stage in stages[: last + 1])
    return (lo, hi)


def _percentiles(values: dict) -> dict:
    count = values.get("count")
    return {
        "count": int(count) if isinstance(count, (int, float)) else 0,
        "p50_ms": float(values.get("med") or 0),
        "p95_ms": float(values.get("p(95)") or 0),
        "p99_ms": float(values.get("p(99)") or 0),
    }


def parse_stage_block(payload: dict | None) -> dict | None:
    """The per-stage block of a k6 summary, whichever form carries it.

    Accepts the constructed summary ``handleSummary`` prints (already shaped
    ``{"stages": ..., "ramp": ...}`` — passed through) and the raw end-of-test
    data object ``--summary-export`` writes, where the stage Trends and Counters
    live under ``metrics``. None when neither records stages: bundles that
    predate per-stage recording. A derived ramp block carries the aggregate
    percentiles only; which stages it unions and its window in seconds are
    known to the script that recorded them, not to the raw data object.
    """
    if not isinstance(payload, dict):
        return None
    if isinstance(payload.get("stages"), dict):
        block = {"stages": payload["stages"]}
        if isinstance(payload.get("ramp"), dict):
            block["ramp"] = payload["ramp"]
        return block
    metrics = payload.get("metrics")
    if not isinstance(metrics, dict):
        return None
    stages: dict[str, dict] = {}
    for name, metric in metrics.items():
        match = _STAGE_METRIC_RE.match(name)
        if not match or not isinstance(metric, dict):
            continue
        values = metric.get("values")
        if isinstance(values, dict):
            stage = f"stage_{int(match.group(1)):02d}"
            counts = metrics.get(f"{stage}_requests")
            count = counts.get("values", {}).get("count") if isinstance(counts, dict) else None
            stats = _percentiles(values)
            stats["count"] = int(count) if isinstance(count, (int, float)) else 0
            stages[stage] = stats
    block: dict = {"stages": stages}
    ramp_values = metrics.get("ramp_latency_ms")
    if isinstance(ramp_values, dict) and isinstance(ramp_values.get("values"), dict):
        ramp = _percentiles(ramp_values["values"])
        ramp_counter = metrics.get("ramp_requests")
        ramp_count = ramp_counter.get("values", {}).get("count") if isinstance(ramp_counter, dict) else None
        ramp["count"] = int(ramp_count) if isinstance(ramp_count, (int, float)) else 0
        block["ramp"] = ramp
    return block if stages else None
