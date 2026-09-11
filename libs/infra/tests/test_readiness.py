"""Tests for infra.readiness — monkeypatched subprocess layer, no real cluster."""

import json
import subprocess

from infra import readiness
from infra.cluster.k3d import shaping
from infra.networking.haproxy import manager as haproxy_manager
from infra.observability.prometheus import manager as prometheus_manager

CLUSTER = "thesis-hybrid"


class FakeK3d:
    """Stateful k3d fake: `node list` is read, `node create/delete` mutate the inventory."""

    def __init__(self, nodes):
        self.inventory = [dict(node) for node in nodes]
        self.calls: list[tuple[list[str], bool]] = []

    def __call__(self, cmd, dry_run=False, cwd=None, check=False):
        self.calls.append((list(cmd), dry_run))
        if cmd[:3] == ["k3d", "node", "list"]:
            stdout = json.dumps(
                [
                    {
                        "name": node["name"],
                        "role": node["role"],
                        "state": node["state"],
                        "runtimeLabels": {"k3d.cluster": CLUSTER},
                    }
                    for node in self.inventory
                ]
            )
            return subprocess.CompletedProcess(cmd, 0, stdout=stdout, stderr="")
        if cmd[:3] == ["k3d", "node", "delete"]:
            if not dry_run:
                self.inventory = [node for node in self.inventory if node["name"] != cmd[3]]
            return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")
        if cmd[:3] == ["k3d", "node", "create"]:
            if not dry_run:
                self.inventory.append({"name": f"k3d-{cmd[3]}-0", "role": "agent", "state": "running"})
            return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")
        raise AssertionError(f"unexpected command: {cmd}")

    def mutating_calls(self) -> list[tuple[list[str], bool]]:
        return [(cmd, dry_run) for cmd, dry_run in self.calls if cmd[:3] != ["k3d", "node", "list"]]


class FakeCompose:
    """`ps --services` reports status, `up -d` starts the service."""

    def __init__(self, running, service):
        self.running = running
        self.service = service
        self.calls: list[list[str]] = []

    def __call__(self, cmd, dry_run=False, cwd=None, check=False):
        self.calls.append(list(cmd))
        if "ps" in cmd:
            return subprocess.CompletedProcess(cmd, 0, stdout=self.service if self.running else "", stderr="")
        if "up" in cmd:
            self.running = True
            return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")
        raise AssertionError(f"unexpected command: {cmd}")


class FakeClusterStart:
    def __init__(self):
        self.calls: list[list[str]] = []

    def __call__(self, cmd, dry_run=False, cwd=None, check=False):
        self.calls.append(list(cmd))
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")


def server(state="running"):
    return {"name": f"k3d-{CLUSTER}-server-0", "role": "server", "state": state}


def agent(number):
    return {"name": f"k3d-{CLUSTER}-agent-{number}-0", "role": "agent", "state": "running"}


def patch_all(monkeypatch, nodes, *, haproxy_running, prometheus_running):
    fake_k3d = FakeK3d(nodes)
    fake_haproxy = FakeCompose(haproxy_running, "haproxy")
    fake_prometheus = FakeCompose(prometheus_running, "prometheus")
    fake_start = FakeClusterStart()
    monkeypatch.setattr(shaping, "run", fake_k3d)
    monkeypatch.setattr(readiness, "run", fake_start)
    monkeypatch.setattr(haproxy_manager, "run", fake_haproxy)
    monkeypatch.setattr(prometheus_manager, "run", fake_prometheus)
    return fake_k3d, fake_haproxy, fake_prometheus, fake_start


def test_no_actions_when_testbed_already_up(monkeypatch):
    fake_k3d, fake_haproxy, fake_prometheus, fake_start = patch_all(
        monkeypatch,
        [server(), agent(0)],
        haproxy_running=True,
        prometheus_running=True,
    )
    result = readiness.ensure_testbed()
    assert result == {
        "cluster": CLUSTER,
        "changed": False,
        "actions": [],
        "nodes": {"servers": 1, "agents": 1},
        "haproxy": True,
        "prometheus": True,
    }
    assert fake_start.calls == []
    assert fake_k3d.mutating_calls() == []
    assert not any("up" in cmd for cmd in fake_haproxy.calls)
    assert not any("up" in cmd for cmd in fake_prometheus.calls)


def test_converges_stopped_testbed(monkeypatch):
    fake_k3d, fake_haproxy, fake_prometheus, fake_start = patch_all(
        monkeypatch,
        [],
        haproxy_running=False,
        prometheus_running=True,
    )

    result = readiness.ensure_testbed(agents=1)

    assert result["changed"] is True
    assert result["actions"] == [
        f"started cluster {CLUSTER}",
        "started haproxy",
        f"create agent {CLUSTER}-agent-0",
    ]
    assert result["haproxy"] is True
    assert result["prometheus"] is True
    assert fake_start.calls == [["k3d", "cluster", "start", CLUSTER]]
    assert any("up" in cmd for cmd in fake_haproxy.calls)
    assert not any("up" in cmd for cmd in fake_prometheus.calls)
    assert result["nodes"] == {"servers": 0, "agents": 1}


def test_restarts_cluster_when_server_not_running(monkeypatch):
    fake_k3d, fake_haproxy, fake_prometheus, fake_start = patch_all(
        monkeypatch,
        [server(state="exit"), agent(0)],
        haproxy_running=True,
        prometheus_running=True,
    )

    result = readiness.ensure_testbed()

    assert result["actions"] == [f"started cluster {CLUSTER}"]
    assert fake_start.calls == [["k3d", "cluster", "start", CLUSTER]]
    assert not any("up" in cmd for cmd in fake_haproxy.calls)
