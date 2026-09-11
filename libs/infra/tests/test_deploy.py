"""Deploying the app is only possible once Knative will admit the manifest."""

from __future__ import annotations

import json
import subprocess

from infra.workloads import deploy


def _endpoints(monkeypatch, payload):
    monkeypatch.setattr(
        deploy,
        "run",
        lambda *a, **k: subprocess.CompletedProcess(a[0], 0, stdout=json.dumps(payload), stderr=""),
    )


def test_an_endpoints_object_without_addresses_is_not_ready(monkeypatch):
    """It exists as soon as its Service does, so its presence proves nothing."""
    _endpoints(monkeypatch, {"subsets": None})

    assert deploy._webhook_has_addresses() is False


def test_an_empty_subsets_list_is_not_ready(monkeypatch):
    _endpoints(monkeypatch, {"subsets": []})

    assert deploy._webhook_has_addresses() is False


def test_addresses_mean_ready(monkeypatch):
    _endpoints(monkeypatch, {"subsets": [{"addresses": [{"ip": "10.42.0.7"}]}]})

    assert deploy._webhook_has_addresses() is True


def test_a_failing_kubectl_is_not_ready(monkeypatch):
    monkeypatch.setattr(deploy, "run", lambda *a, **k: subprocess.CompletedProcess(a[0], 1, stdout="", stderr="nope"))

    assert deploy._webhook_has_addresses() is False
