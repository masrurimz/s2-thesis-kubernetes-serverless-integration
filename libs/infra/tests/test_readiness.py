"""Tests for infra.readiness — monkeypatched subprocess layer, no real cluster."""

import json
import subprocess

from infra import readiness
from infra.cluster.k3d import residue, shaping
from infra.networking.haproxy import manager as haproxy_manager
from infra.observability.prometheus import manager as prometheus_manager

CLUSTER = "thesis-hybrid"


class FakeK3d:
    """Stateful k3d fake: `node list` is read, `node create/delete` mutate the inventory."""

    def __init__(self, nodes, pods=None):
        self.inventory = [dict(node) for node in nodes]
        self.pods = [dict(pod) for pod in (pods or [])]
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
        if cmd[0] == "kubectl" and cmd[-4:] == ["get", "pods", "-o", "json"]:
            stdout = json.dumps(
                {"items": [{"metadata": {"name": pod["name"]}, "spec": {"nodeName": pod["node"]}} for pod in self.pods]}
            )
            return subprocess.CompletedProcess(cmd, 0, stdout=stdout, stderr="")
        if cmd[0] == "kubectl" and "delete" in cmd and "node" in cmd:
            return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")
        if cmd[0] == "kubectl" and "delete" in cmd and "pod" in cmd:
            target = cmd[cmd.index("pod") + 1]
            if not dry_run:
                self.pods = [pod for pod in self.pods if pod["name"] != target]
            return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")
        raise AssertionError(f"unexpected command: {cmd}")

    def mutating_calls(self) -> list[tuple[list[str], bool]]:
        reads = (["k3d", "node", "list"], ["kubectl"])
        return [
            (cmd, dry_run)
            for cmd, dry_run in self.calls
            if not (cmd[:3] == reads[0] or (cmd[0] == "kubectl" and "get" in cmd))
        ]

    def kubectl_deletes(self) -> list[str]:
        return [cmd[cmd.index("pod") + 1] for cmd, _ in self.calls if cmd[0] == "kubectl" and "delete" in cmd]


class FakeCompose:
    """`ps --services` reports status, `up -d` starts the service."""

    def __init__(self, running, service):
        self.running = running
        self.service = service
        self.calls: list[list[str]] = []

    def __call__(self, cmd, dry_run=False, cwd=None, check=False, env=None):
        self.calls.append(list(cmd))
        if "ps" in cmd:
            return subprocess.CompletedProcess(cmd, 0, stdout=self.service if self.running else "", stderr="")
        if "up" in cmd:
            self.running = True
            return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")
        raise AssertionError(f"unexpected command: {cmd}")


class FakeClusterStart:
    """Answers `kubectl get nodes` from the k3d inventory; records lifecycle calls."""

    def __init__(self, k3d=None):
        self.k3d = k3d
        self.calls: list[list[str]] = []

    def __call__(self, cmd, dry_run=False, cwd=None, check=False, env=None):
        self.calls.append(list(cmd))
        if cmd[0] == "kubectl" and "get" in cmd and "nodes" in cmd:
            names = [node["name"] for node in (self.k3d.inventory if self.k3d else [])]
            stdout = json.dumps({"items": [{"metadata": {"name": name}} for name in names]})
            return subprocess.CompletedProcess(cmd, 0, stdout=stdout, stderr="")
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    def cluster_starts(self) -> list[list[str]]:
        return [cmd for cmd in self.calls if cmd[:2] == ["k3d", "cluster"]]


def server(state="running"):
    return {"name": f"k3d-{CLUSTER}-server-0", "role": "server", "state": state}


def agent(number):
    return {"name": f"k3d-{CLUSTER}-agent-{number}-0", "role": "agent", "state": "running"}


def patch_all(monkeypatch, nodes, *, haproxy_running, prometheus_running, pods=None):
    fake_k3d = FakeK3d(nodes, pods)
    fake_haproxy = FakeCompose(haproxy_running, "haproxy")
    fake_prometheus = FakeCompose(prometheus_running, "prometheus")
    fake_start = FakeClusterStart(fake_k3d)
    monkeypatch.setattr(shaping, "run", fake_k3d)
    monkeypatch.setattr(residue, "run", fake_k3d)
    monkeypatch.setattr(readiness, "run", fake_start)
    # The proxy-host refresh reads the live cluster and restarts HAProxy; it has its
    # own test below, and the stateful fakes here do not model it.
    monkeypatch.setattr(readiness, "_refresh_haproxy_host", lambda actions: None)
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
        "nodes": {"servers": 1, "agents": 1, "dynamic_agents": 0},
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
    assert fake_start.cluster_starts() == [["k3d", "cluster", "start", CLUSTER]]
    assert any("up" in cmd for cmd in fake_haproxy.calls)
    assert not any("up" in cmd for cmd in fake_prometheus.calls)
    assert result["nodes"] == {"servers": 0, "agents": 1, "dynamic_agents": 0}


def test_restarts_cluster_when_server_not_running(monkeypatch):
    fake_k3d, fake_haproxy, fake_prometheus, fake_start = patch_all(
        monkeypatch,
        [server(state="exit"), agent(0)],
        haproxy_running=True,
        prometheus_running=True,
    )

    result = readiness.ensure_testbed()

    assert result["actions"] == [f"started cluster {CLUSTER}"]
    assert fake_start.cluster_starts() == [["k3d", "cluster", "start", CLUSTER]]
    assert not any("up" in cmd for cmd in fake_haproxy.calls)


def test_prunes_pods_left_on_a_node_that_no_longer_exists(monkeypatch):
    """A pod outliving its node still holds CPU on the nodes that remain."""
    fake_k3d, _, _, _ = patch_all(
        monkeypatch,
        [server(), agent(0)],
        haproxy_running=True,
        prometheus_running=True,
        pods=[
            {"name": "test-app-warm-live", "node": f"k3d-{CLUSTER}-agent-0-0"},
            {"name": "test-app-warm-orphan", "node": f"k3d-{CLUSTER}-dynamic-workload-4-0"},
        ],
    )

    result = readiness.ensure_testbed()

    assert fake_k3d.kubectl_deletes() == ["test-app-warm-orphan"]
    assert result["actions"] == [
        "deleted orphaned pod test-app-warm-orphan (node k3d-thesis-hybrid-dynamic-workload-4-0 is gone)"
    ]
    assert result["nodes"]["dynamic_agents"] == 0


def test_prunes_a_leftover_dynamic_node_but_never_a_static_one(monkeypatch):
    fake_k3d, _, _, _ = patch_all(
        monkeypatch,
        [server(), agent(0), {"name": f"k3d-{CLUSTER}-dynamic-workload-3-0", "role": "agent", "state": "running"}],
        haproxy_running=True,
        prometheus_running=True,
    )

    result = readiness.ensure_testbed(agents=1)

    assert result["actions"] == [f"deleted leftover dynamic node k3d-{CLUSTER}-dynamic-workload-3-0"]
    assert [node["name"] for node in fake_k3d.inventory] == [f"k3d-{CLUSTER}-server-0", f"k3d-{CLUSTER}-agent-0-0"]
    assert result["nodes"] == {"servers": 1, "agents": 1, "dynamic_agents": 0}


def test_dry_run_reports_pruning_without_touching_anything(monkeypatch):
    fake_k3d, _, _, _ = patch_all(
        monkeypatch,
        [server(), agent(0), {"name": f"k3d-{CLUSTER}-dynamic-workload-3-0", "role": "agent", "state": "running"}],
        haproxy_running=True,
        prometheus_running=True,
        pods=[{"name": "test-app-warm-orphan", "node": f"k3d-{CLUSTER}-dynamic-workload-4-0"}],
    )

    result = readiness.ensure_testbed(agents=1, dry_run=True)

    assert len(result["actions"]) == 2
    assert fake_k3d.kubectl_deletes() == []
    assert len(fake_k3d.inventory) == 3
    assert len(fake_k3d.pods) == 1


def test_the_proxy_is_restarted_when_its_config_names_another_cluster(monkeypatch, tmp_path):
    """A rebuilt cluster gets a new Kourier IP, and the config embeds it."""
    from infra.networking.haproxy import render

    monkeypatch.setattr(render, "RUNTIME_DIR", tmp_path)
    (tmp_path / "haproxy.cfg").write_text(
        "backend servers\n    http-request set-header Host test-app.default.192.168.0.2.sslip.io\n"
    )
    monkeypatch.setattr(render, "knative_host", lambda **kwargs: "test-app.default.172.22.0.2.sslip.io")

    calls = []
    monkeypatch.setattr(
        "infra.networking.haproxy.manager.HAProxyManager",
        lambda: type(
            "M", (), {"stop": lambda self: calls.append("stop"), "start": lambda self: calls.append("start") or True}
        )(),
    )

    actions: list[str] = []
    readiness._refresh_haproxy_host(actions)

    assert calls == ["stop", "start"]
    assert actions == ["restarted haproxy for knative host test-app.default.172.22.0.2.sslip.io"]
    assert render.current_host_in(tmp_path / "haproxy.cfg") == "test-app.default.172.22.0.2.sslip.io"


def test_the_proxy_is_left_alone_when_its_config_already_matches(monkeypatch, tmp_path):
    from infra.networking.haproxy import render

    monkeypatch.setattr(render, "RUNTIME_DIR", tmp_path)
    monkeypatch.setattr(render, "knative_host", lambda **kwargs: "test-app.default.172.22.0.2.sslip.io")
    (tmp_path / "haproxy.cfg").write_text(
        "backend servers\n    http-request set-header Host test-app.default.172.22.0.2.sslip.io\n"
    )

    calls: list[str] = []
    monkeypatch.setattr(
        "infra.networking.haproxy.manager.HAProxyManager",
        lambda: type(
            "M", (), {"stop": lambda self: calls.append("stop"), "start": lambda self: calls.append("start")}
        )(),
    )

    actions: list[str] = []
    readiness._refresh_haproxy_host(actions)

    assert calls == []
    assert actions == []
