"""Node utilization polling: a node without a metrics reading must not cost the others.

`kubectl top nodes` prints `<unknown>` for a node metrics-server has no sample for
yet — which is the normal state of a node the autoscaler just created, exactly when
the node tier is being watched. The poll used to parse the whole scrape inside one
try, so that single row discarded every other node's sample for that interval.
"""

import subprocess
from unittest.mock import patch

from experiment.stages.collect import ResourcePoller

READY_ROW = "k3d-thesis-hybrid-agent-0   250m   6%   1024Mi   12%"
UNKNOWN_ROW = "k3d-dynamic-workload-0-0   <unknown>   <unknown>   <unknown>   <unknown>"
SERVER_ROW = "k3d-thesis-hybrid-server-0   180m   4%   2048Mi   20%"


def _poll_with(stdout: str) -> list[dict]:
    completed = subprocess.CompletedProcess(args=["kubectl"], returncode=0, stdout=stdout, stderr="")
    poller = ResourcePoller(poll_interval_sec=1)
    with patch("experiment.stages.collect._run_cmd", return_value=completed):
        poller._poll_nodes()
    return poller._node_samples


def test_unknown_row_does_not_discard_other_nodes():
    samples = _poll_with("\n".join([READY_ROW, UNKNOWN_ROW, SERVER_ROW]))

    assert {s["node"] for s in samples} == {
        "k3d-thesis-hybrid-agent-0",
        "k3d-thesis-hybrid-server-0",
    }


def test_known_rows_are_parsed_into_cores_and_percentages():
    samples = {s["node"]: s for s in _poll_with("\n".join([READY_ROW, SERVER_ROW]))}

    agent = samples["k3d-thesis-hybrid-agent-0"]
    assert agent["cpu_cores"] == 0.25
    assert agent["cpu_pct"] == 6.0
    assert agent["memory_mib"] == 1024.0
    assert agent["memory_pct"] == 12.0


def test_all_unknown_yields_no_samples_and_no_raise():
    assert _poll_with("\n".join([UNKNOWN_ROW, UNKNOWN_ROW])) == []
