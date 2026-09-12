"""DCI reads the demand series the run actually recorded.

The old branch looked for ``haproxy_total_requests`` / ``request_rate`` / ``rps``
inside the utilization samples (then ``resource_utilization.json``, now Parquet);
no producer writes those keys, so any run with a utilization file — which is
every run — reported a zero-complexity workload through that path. The demand
series is the exported ``prom_rps`` query.
"""

import json
from pathlib import Path

import pytest

from experiment.tuning.workload_analysis import analyze_workload_from_experiment
from shared.artifacts import write_resource_utilization
from shared.models.metrics import ResourceSample


def _export(dir_path: Path, rps: list[float]) -> None:
    export = dir_path / "prometheus" / "prometheus_export.json"
    export.parent.mkdir(parents=True, exist_ok=True)
    export.write_text(json.dumps({"prom_rps": [[float(i * 15), v] for i, v in enumerate(rps)]}))


def test_dci_comes_from_the_exported_demand_series(tmp_path):
    _export(tmp_path, [10.0, 20.0, 30.0, 40.0])

    dci = analyze_workload_from_experiment(str(tmp_path))

    assert dci["n_samples"] == 4
    assert dci["mean"] == 25.0
    assert dci["cv"] > 0

    write_resource_utilization(
        tmp_path,
        [ResourceSample(timestamp=1.0, pod="p", backend="k8s", cpu_millicores=250.0, memory_mib=64.0)],
    )
    _export(tmp_path, [5.0, 5.0, 15.0])

    dci = analyze_workload_from_experiment(str(tmp_path))

    assert dci["n_samples"] == 3
    assert dci["mean"] == pytest.approx(8.33, abs=0.01)


def test_result_summary_is_the_fallback_when_no_series_exists(tmp_path):
    (tmp_path / "result.json").write_text(
        json.dumps(
            {
                "scenario": "s3-hybrid-reactive",
                "run_id": 1,
                "throughput_rps": 71.5,
            }
        )
    )

    dci = analyze_workload_from_experiment(str(tmp_path))

    assert dci["mean"] == 71.5
    assert dci["n_samples"] == 0
    assert "note" in dci


def test_no_data_is_an_error_not_a_zero(tmp_path):
    assert "error" in analyze_workload_from_experiment(str(tmp_path))
