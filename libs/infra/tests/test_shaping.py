"""Tests for infra.cluster.k3d.shaping — monkeypatched k3d commands, no real cluster."""

import json
import subprocess

from infra.cluster.k3d import shaping

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


def server(state="running"):
    return {"name": f"k3d-{CLUSTER}-server-0", "role": "server", "state": state}


def agent(number):
    return {"name": f"k3d-{CLUSTER}-agent-{number}-0", "role": "agent", "state": "running"}


def dynamic(number):
    return {"name": f"k3d-dynamic-workload-{number}-0", "role": "agent", "state": "running"}


def test_at_target_is_no_op(monkeypatch):
    fake = FakeK3d([server(), agent(0), agent(1)])
    monkeypatch.setattr(shaping, "run", fake)

    result = shaping.converge_agent_count(CLUSTER, 2)

    assert result["before"] == 2
    assert result["after"] == 2
    assert result["actions"] == []
    assert result["dynamic_agents"] == 0
    assert fake.mutating_calls() == []


def test_scale_down_deletes_highest_numbered_first(monkeypatch):
    fake = FakeK3d([server(), agent(0), agent(1), agent(2)])
    monkeypatch.setattr(shaping, "run", fake)

    result = shaping.converge_agent_count(CLUSTER, 1)

    assert result["actions"] == [f"delete agent k3d-{CLUSTER}-agent-2-0", f"delete agent k3d-{CLUSTER}-agent-1-0"]
    assert result["after"] == 1
    assert [node["name"] for node in fake.inventory if node["role"] == "agent"] == [f"k3d-{CLUSTER}-agent-0-0"]


def test_scale_up_creates_agents_past_max_index(monkeypatch):
    fake = FakeK3d([server(), agent(0), agent(2)])
    monkeypatch.setattr(shaping, "run", fake)

    result = shaping.converge_agent_count(CLUSTER, 4)

    assert result["actions"] == [f"create agent {CLUSTER}-agent-3", f"create agent {CLUSTER}-agent-4"]
    assert result["after"] == 4
    creates = [cmd for cmd, _ in fake.calls if cmd[:3] == ["k3d", "node", "create"]]
    assert creates[0] == ["k3d", "node", "create", f"{CLUSTER}-agent-3", "--cluster", CLUSTER, "--role", "agent"]
    assert creates[1][3] == f"{CLUSTER}-agent-4"


def test_dynamic_agents_never_deleted(monkeypatch):
    fake = FakeK3d([server(), agent(0), agent(1), dynamic(3), dynamic(4)])
    monkeypatch.setattr(shaping, "run", fake)

    result = shaping.converge_agent_count(CLUSTER, 1)

    assert result["actions"] == [f"delete agent k3d-{CLUSTER}-agent-1-0"]
    assert result["after"] == 1
    assert result["dynamic_agents"] == 2
    assert {node["name"] for node in fake.inventory if "dynamic" in node["name"]} == {
        "k3d-dynamic-workload-3-0",
        "k3d-dynamic-workload-4-0",
    }


def test_dry_run_lists_actions_without_mutating(monkeypatch):
    fake = FakeK3d([server()])
    monkeypatch.setattr(shaping, "run", fake)

    result = shaping.converge_agent_count(CLUSTER, 2, dry_run=True)

    assert result["actions"] == [f"create agent {CLUSTER}-agent-0", f"create agent {CLUSTER}-agent-1"]
    assert result["after"] == 2
    assert result["dry_run"] is True
    mutating = fake.mutating_calls()
    assert len(mutating) == 2
    assert all(dry_run for _, dry_run in mutating)
    assert [node for node in fake.inventory if node["role"] == "agent"] == []
