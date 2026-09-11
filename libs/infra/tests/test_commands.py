"""The subprocess seam every infra action goes through."""

from __future__ import annotations

import subprocess

from infra import commands


def test_a_child_never_inherits_stdin(monkeypatch):
    """A command reading stdin would wait forever otherwise: kubectl apply -f - hung
    a testbed rebuild mid-install."""
    captured = {}

    def fake_run(cmd, **kwargs):
        captured.update(kwargs)
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    monkeypatch.setattr(commands.subprocess, "run", fake_run)

    commands.run(["kubectl", "apply", "-f", "-"])

    assert captured["stdin"] is subprocess.DEVNULL
    assert captured["input"] is None


def test_input_text_is_piped_and_stdin_left_alone(monkeypatch):
    captured = {}

    def fake_run(cmd, **kwargs):
        captured.update(kwargs)
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    monkeypatch.setattr(commands.subprocess, "run", fake_run)

    commands.run(["kubectl", "apply", "-f", "-"], input_text="kind: ConfigMap")

    assert captured["input"] == "kind: ConfigMap"
    assert captured["stdin"] is None
