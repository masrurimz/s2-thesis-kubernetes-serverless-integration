"""Human-readable Markdown summary of one experiment bundle."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from statistics import fmean, stdev
from typing import TypeGuard

import yaml
from shared.artifacts import read_manifest_git_commit, read_result_dict
from shared.models.evidence import NodeEngagement
from shared.stats import paired_permutation_p_from_diffs

NA = "n/a"
_PERMUTATION_MAX_PAIRS = 20
_VALIDITY_FLAGS = (
    ("validity_gate_passed", "validity_gate_notes"),
    ("run_validity_passed", "run_validity_notes"),
    ("stress_validity_passed", "stress_validity_notes"),
)


@dataclass
class Run:
    scenario: str
    run_id: int
    result: dict
    git_commit: str | None
    model_artifact: str | None

    @property
    def valid(self) -> bool:
        flags = [self.result.get(flag) for flag, _ in _VALIDITY_FLAGS if flag in self.result]
        # No recorded gate flags means no recorded rejection.
        return all(flags) if flags else True

    def rejection_reason(self) -> str | None:
        if self.valid:
            return None
        notes: list[str] = []
        for flag, notes_key in _VALIDITY_FLAGS:
            if self.result.get(flag) is False:
                notes.extend(str(n) for n in self.result.get(notes_key) or [])
        return "; ".join(notes) if notes else "no reason recorded"


def build_summary(bundle_dir: Path) -> str:
    """Return a Markdown summary of one experiment bundle."""
    bundle_dir = Path(bundle_dir)
    meta = _load_meta(bundle_dir)
    runs = _discover_runs(bundle_dir)
    by_scenario: dict[str, list[Run]] = {}
    for run in runs:
        by_scenario.setdefault(run.scenario, []).append(run)

    scenarios = _scenario_order(meta, by_scenario)
    lines = _header(bundle_dir, meta, runs, scenarios)
    lines.extend(_what_ran(scenarios, by_scenario))
    lines.extend(_headline(scenarios, by_scenario))
    if len(scenarios) == 2:
        lines.extend(_paired(scenarios[0], scenarios[1], by_scenario))
    lines.extend(_forecast_fidelity(scenarios, by_scenario))
    lines.extend(_node_engagement(scenarios, by_scenario))
    lines.extend(_caveats(runs))
    return "\n".join(lines).rstrip() + "\n"


def write_summary(bundle_dir: Path) -> Path:
    """Write SUMMARY.md into the bundle and return its path."""
    path = Path(bundle_dir) / "SUMMARY.md"
    path.write_text(build_summary(bundle_dir))
    return path


def _load_meta(bundle_dir: Path) -> dict:
    try:
        data = yaml.safe_load((bundle_dir / "meta.yaml").read_text())
    except OSError:
        return {}
    return data if isinstance(data, dict) else {}


def _read_json(path: Path) -> dict:
    try:
        data = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _read_events(path: Path) -> list[dict]:
    try:
        raw_lines = path.read_text().splitlines()
    except OSError:
        return []
    events = []
    for line in raw_lines:
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(event, dict):
            events.append(event)
    return events


def _git_commit(run_dir: Path) -> str | None:
    commit = read_manifest_git_commit(run_dir)
    if commit:
        return commit
    for event in _read_events(run_dir / "events.jsonl"):
        commit = event.get("git_commit")
        if isinstance(commit, str) and commit:
            return commit
    return None


def _model_artifact(run_dir: Path, result: dict) -> str | None:
    recorded = result.get("model_path")
    if isinstance(recorded, str) and recorded:
        return recorded
    for event in _read_events(run_dir / "events.jsonl"):
        if event.get("event") != "prediction_preflight_passed":
            continue
        status = event.get("payload", {}).get("model_status", {})
        path = status.get("model_path")
        if not (isinstance(path, str) and path):
            continue
        model_type = status.get("model_type")
        return f"{path} ({model_type})" if isinstance(model_type, str) else path
    return None


def _discover_runs(bundle_dir: Path) -> list[Run]:
    runs = []
    for run_dir in sorted(bundle_dir.glob("*_run*")):
        if not run_dir.is_dir():
            continue
        scenario, sep, suffix = run_dir.name.rpartition("_run")
        if not sep or not suffix.isdigit():
            continue
        result = read_result_dict(run_dir)
        if not result:
            continue
        runs.append(
            Run(
                scenario=scenario,
                run_id=int(suffix),
                result=result,
                git_commit=_git_commit(run_dir),
                model_artifact=_model_artifact(run_dir, result),
            )
        )
    runs.sort(key=lambda run: (run.scenario, run.run_id))
    return runs


def _scenario_order(meta: dict, by_scenario: dict[str, list[Run]]) -> list[str]:
    declared = meta.get("scenarios")
    ordered = [s for s in declared if isinstance(s, str) and s in by_scenario] if declared else []
    ordered.extend(s for s in sorted(by_scenario) if s not in ordered)
    return ordered


def _bundle_git_commit(bundle_dir: Path, runs: list[Run]) -> str:
    commits = [run.git_commit for run in runs if run.git_commit]
    if not commits:
        for event in _read_events(bundle_dir / "events.jsonl"):
            commit = event.get("git_commit")
            if isinstance(commit, str) and commit:
                commits.append(commit)
                break
    return ", ".join(dict.fromkeys(commits)) if commits else NA


def _header(bundle_dir: Path, meta: dict, runs: list[Run], scenarios: list[str]) -> list[str]:
    name = meta.get("name") or bundle_dir.name
    date = meta.get("date")
    per_scenario = meta.get("runs")
    status = meta.get("status")
    lines = [
        f"# Summary — {name}",
        "",
        f"- Date: {date if date is not None else NA}",
        f"- Git commit: {_bundle_git_commit(bundle_dir, runs)}",
        f"- Scenarios: {', '.join(scenarios) if scenarios else NA}",
        f"- Runs per scenario: {per_scenario if per_scenario is not None else NA}"
        f" (status: {status if status is not None else NA})",
        "",
    ]
    return lines


def _fmt(value: float | None, spec: str = ".1f") -> str:
    return NA if value is None else format(value, spec)


def _numeric(value: object) -> TypeGuard[float]:
    """True when the value is a real number a table may aggregate."""
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _mean_over(runs: list[Run], field: str) -> float | None:
    """Mean of a numeric field across runs; None when no run recorded one."""
    values: list[float] = []
    for run in runs:
        value = run.result.get(field)
        if _numeric(value):
            values.append(float(value))
    return fmean(values) if values else None


def _values_line(runs: list[Run], field: str) -> str:
    recorded = [(run.run_id, run.result[field]) for run in runs if field in run.result]
    if not recorded:
        return NA
    if all(value == recorded[0][1] for _, value in recorded):
        return str(recorded[0][1])
    return ", ".join(f"run{run_id}={value}" for run_id, value in recorded)


def _what_ran(scenarios: list[str], by_scenario: dict[str, list[Run]]) -> list[str]:
    lines = ["## What ran", ""]
    for scenario in scenarios:
        runs = by_scenario[scenario]
        valid = sum(1 for run in runs if run.valid)
        artifacts = [run.model_artifact for run in runs if run.model_artifact]
        lines.extend(
            [
                f"### {scenario}",
                "",
                f"- Runs: {len(runs)}, passed the validity gate: {valid}",
                f"- Model artifact: {', '.join(dict.fromkeys(artifacts)) if artifacts else NA}",
                f"- nodes_provisioned: {_values_line(runs, 'nodes_provisioned')}",
                f"- first_provision_delay_sec: {_values_line(runs, 'first_provision_delay_sec')}",
                "",
            ]
        )
    return lines


_HEADLINE_FIELDS = (
    ("p50_latency_ms", ".1f"),
    ("p95_latency_ms", ".1f"),
    ("p99_latency_ms", ".1f"),
    ("error_rate", ".4f"),
    ("throughput_rps", ".1f"),
    ("slo_violations_k6", ".1f"),
    ("k8s_replica_seconds", ".1f"),
    ("time_in_serverless_pct", ".1f"),
)


def _headline(scenarios: list[str], by_scenario: dict[str, list[Run]]) -> list[str]:
    lines = [
        "## Headline",
        "",
        "Aggregates are means over gate-passing runs.",
        "",
        "| Scenario | n | p50 (ms) | p95 (ms) | p99 (ms) | error rate | throughput (rps) "
        "| SLO violations | replica-seconds | serverless share (%) | valid |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for scenario in scenarios:
        runs = by_scenario[scenario]
        valid_runs = [run for run in runs if run.valid]
        cells = [_fmt(_mean_over(valid_runs, field), spec) for field, spec in _HEADLINE_FIELDS]
        valid_cell = f"{len(valid_runs)}/{len(runs)}" if runs else NA
        lines.append(f"| {scenario} | {len(runs)} | " + " | ".join(cells) + f" | {valid_cell} |")
    lines.append("")
    return lines


def _cohens_d_paired(diffs: list[float]) -> float | None:
    if len(diffs) < 2:
        return None
    sd = stdev(diffs)
    return fmean(diffs) / sd if sd else None


def _permutation_p_one_sided(diffs: list[float]) -> float | None:
    """The paired permutation p for H1: S4 faster than S3.

    Same definition the paired analysis writes into ``paired_analysis.json`` — one
    implementation, so a bundle cannot report two p-values for the same pairs. An
    effect running the other way scores 1.0, which is what "no evidence for H2"
    looks like.
    """
    if not diffs or len(diffs) > _PERMUTATION_MAX_PAIRS:
        return None
    return paired_permutation_p_from_diffs(diffs)


@dataclass
class _MetricPairs:
    label: str
    field: str
    unit: str
    baseline: dict[int, float]
    comparison: dict[int, float]

    def diffs(self, pair_ids: list[int]) -> list[float]:
        return [
            self.comparison[pair_id] - self.baseline[pair_id]
            for pair_id in pair_ids
            if pair_id in self.baseline and pair_id in self.comparison
        ]


def _paired(baseline: str, comparison: str, by_scenario: dict[str, list[Run]]) -> list[str]:
    base_runs = {run.run_id: run for run in by_scenario[baseline]}
    comp_runs = {run.run_id: run for run in by_scenario[comparison]}
    pair_ids = sorted(set(base_runs) & set(comp_runs))
    usable = [pair_id for pair_id in pair_ids if base_runs[pair_id].valid and comp_runs[pair_id].valid]

    metrics = [
        _MetricPairs(
            label="p99 latency",
            field="p99_latency_ms",
            unit="ms",
            baseline=_numeric_values(base_runs, "p99_latency_ms"),
            comparison=_numeric_values(comp_runs, "p99_latency_ms"),
        ),
        _MetricPairs(
            label="SLO violations",
            field="slo_violations_k6",
            unit="",
            baseline=_numeric_values(base_runs, "slo_violations_k6"),
            comparison=_numeric_values(comp_runs, "slo_violations_k6"),
        ),
    ]

    lines = [
        f"## Paired comparison — {comparison} vs {baseline}",
        "",
        f"Pairs are matched by run id, in run order. "
        f"{len(usable)} of {len(pair_ids)} pairs passed the validity gate on both sides.",
        "",
        f"| Pair | {baseline} p99 (ms) | {comparison} p99 (ms) | Δ p99 (ms) "
        f"| {baseline} SLO | {comparison} SLO | Δ SLO |",
        "|---|---|---|---|---|---|---|",
    ]
    for pair_id in pair_ids:
        p99, slo = metrics
        lines.append(
            f"| run {pair_id} | {_cell(p99.baseline, pair_id)} | {_cell(p99.comparison, pair_id)} "
            f"| {_delta_cell(p99, pair_id)} | {_cell(slo.baseline, pair_id)} "
            f"| {_cell(slo.comparison, pair_id)} | {_delta_cell(slo, pair_id)} |"
        )
    lines.append("")

    for metric in metrics:
        diffs = metric.diffs(usable)
        mean_diff = fmean(diffs) if diffs else None
        unit = f" {metric.unit}" if metric.unit else ""
        lines.append(
            f"- Mean Δ{metric.label}: {_fmt(mean_diff, '+.1f')}{unit}, "
            f"paired Cohen's d: {_fmt(_cohens_d_paired(diffs), '.2f')}, "
            f"exact one-sided permutation p (H1: S4 faster): {_fmt(_permutation_p_one_sided(diffs), '.4f')} "
            f"({_significance(diffs)} 0.05)."
        )
    lines.append("")
    return lines


def _numeric_values(runs: dict[int, Run], field: str) -> dict[int, float]:
    return {run_id: run.result[field] for run_id, run in runs.items() if _numeric(run.result.get(field))}


def _cell(values: dict[int, float], pair_id: int) -> str:
    return _fmt(values.get(pair_id))


def _delta_cell(metric: _MetricPairs, pair_id: int) -> str:
    if pair_id not in metric.baseline or pair_id not in metric.comparison:
        return NA
    return format(metric.comparison[pair_id] - metric.baseline[pair_id], "+.1f")


def _significance(diffs: list[float]) -> str:
    p = _permutation_p_one_sided(diffs)
    return "does not clear" if p is None or p > 0.05 else "clears"


def _forecast_fidelity(scenarios: list[str], by_scenario: dict[str, list[Run]]) -> list[str]:
    rows = []
    for scenario in scenarios:
        carrying = [
            run.result["treatment_fidelity"]
            for run in by_scenario[scenario]
            if isinstance(run.result.get("treatment_fidelity"), dict)
        ]
        if not carrying:
            continue
        eligible = sum(f.get("eligible_cycles", 0) for f in carrying)
        successful = sum(f.get("successful_predictions", 0) for f in carrying)
        rate = successful / eligible if eligible else None
        delivered = all(f.get("delivered") is True for f in carrying)
        rows.append(
            f"| {scenario} | {eligible} | {successful} | {_fmt(rate, '.3f')} | {'yes' if delivered else 'no'} |"
        )
    if not rows:
        return []
    return [
        "## Forecast fidelity",
        "",
        "| Scenario | eligible cycles | successful predictions | delivery rate | delivered |",
        "|---|---|---|---|---|",
        *rows,
        "",
    ]


def _engagement_of(run: Run) -> dict | None:
    """Engagement recorded at run time, or derived from the run's provisioner events.

    Older bundles predate the recorded field; reading their event stream classifies
    them by the same rule as a fresh run, so the whole corpus can be filtered.
    """
    recorded = run.result.get("node_engagement")
    if isinstance(recorded, dict):
        return recorded

    scenario = run.result.get("scenario") or run.scenario
    recorded_path = run.result.get("provision_log_path")
    events: list[str] = []
    if isinstance(recorded_path, str) and Path(recorded_path).exists():
        events = _read_event_names(Path(recorded_path))
    return NodeEngagement.from_provision_events(
        scenario,
        events,
        nodes_provisioned=int(run.result.get("nodes_provisioned") or 0),
        first_provision_delay_sec=float(run.result.get("first_provision_delay_sec") or 0.0),
    ).model_dump()


def _read_event_names(path: Path) -> list[str]:
    try:
        payload = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return []
    if isinstance(payload, dict):
        payload = payload.get("events", [])
    if not isinstance(payload, list):
        return []
    return [str(entry.get("event", "")) for entry in payload if isinstance(entry, dict)]


def _node_engagement(scenarios: list[str], by_scenario: dict[str, list[Run]]) -> list[str]:
    """Report whether the node tier — the capacity the hybrid design adds — was exercised."""
    rows = []
    for scenario in scenarios:
        carrying = [e for run in by_scenario[scenario] if (e := _engagement_of(run)) is not None]
        if not carrying:
            continue
        required = all(f.get("required") for f in carrying)
        engaged = all(f.get("autoscaler_engaged") for f in carrying)
        pending = sum(f.get("pending_events", 0) for f in carrying)
        provisioned = sum(f.get("nodes_provisioned", 0) for f in carrying)
        delays = [f.get("first_provision_delay_sec", 0.0) for f in carrying if f.get("first_provision_delay_sec")]
        delay = format(sum(delays) / len(delays), ".1f") if delays else NA
        verdict = "not required" if not required else ("yes" if engaged else "no")
        rows.append(f"| {scenario} | {verdict} | {pending} | {provisioned} | {delay} |")
    if not rows:
        return []
    return [
        "## Node tier",
        "",
        "| Scenario | node tier exercised | pending events | nodes provisioned | mean provisioning delay (s) |",
        "|---|---|---|---|---|",
        *rows,
        "",
    ]


def _caveats(runs: list[Run]) -> list[str]:
    caveats = []
    for run in sorted(runs, key=lambda r: (r.scenario, r.run_id)):
        reason = run.rejection_reason()
        if reason is not None:
            caveats.append(f"- {run.scenario} run {run.run_id} rejected by the validity gate: {reason}.")
        fidelity = run.result.get("treatment_fidelity")
        if isinstance(fidelity, dict) and fidelity.get("delivered") is False:
            caveats.append(f"- {run.scenario} run {run.run_id} treatment_fidelity.delivered is false.")
        engagement = _engagement_of(run)
        if isinstance(engagement, dict) and engagement.get("required") and not engagement.get("autoscaler_engaged"):
            caveats.append(f"- {run.scenario} run {run.run_id} never exercised the node tier.")
    return ["## Caveats", "", *(caveats or ["None."]), ""]
