"""The prediction server must be the right artifact, on the right device.

Both failure modes seen in practice produce a run that looks successful and is
not: a server started on the integrated GPU aborts mid-run, and a server left
over from an earlier experiment forecasts a different series. These tests pin
the identity check rather than the process mechanics.
"""

from __future__ import annotations

import hashlib

from experiment import services


def _artifact(tmp_path):
    path = tmp_path / "gru_model.pt"
    path.write_bytes(b"model-bytes")
    return path, hashlib.sha256(b"model-bytes").hexdigest()


def test_missing_artifact_is_reported_not_started(tmp_path, monkeypatch):
    started = []
    monkeypatch.setattr(services.subprocess, "Popen", lambda *a, **k: started.append(a))

    result = services.ensure_prediction_server(model_path=tmp_path / "absent.pt")

    assert result["status"] == "unavailable"
    assert "not found" in result["reason"]
    assert started == []


def test_matching_artifact_is_reused(tmp_path, monkeypatch):
    path, digest = _artifact(tmp_path)
    monkeypatch.setattr(
        services,
        "server_status",
        lambda port=services.DEFAULT_PORT, timeout=3.0: {
            "loaded": True,
            "artifact_sha256": digest,
            "sequence_length": 30,
        },
    )
    monkeypatch.setattr(
        services.subprocess, "Popen", lambda *a, **k: (_ for _ in ()).throw(AssertionError("must not start"))
    )

    result = services.ensure_prediction_server(model_path=path)

    assert result["status"] == "reused"
    assert result["artifact_sha256"] == digest


def test_different_artifact_replaces_the_running_server(tmp_path, monkeypatch):
    path, digest = _artifact(tmp_path)
    statuses = iter([{"loaded": True, "artifact_sha256": "stale"}, {"loaded": True, "artifact_sha256": digest}])
    monkeypatch.setattr(services, "server_status", lambda port=services.DEFAULT_PORT, timeout=3.0: next(statuses))
    killed = []
    monkeypatch.setattr(services, "kill_process_on_port", lambda port, name: killed.append((port, name)))
    monkeypatch.setattr(services.subprocess, "Popen", lambda *a, **k: None)

    result = services.ensure_prediction_server(model_path=path)

    assert killed == [(services.DEFAULT_PORT, "gru_prediction_service")]
    assert result["status"] == "started"


def test_started_server_is_checked_for_the_requested_artifact(tmp_path, monkeypatch):
    path, digest = _artifact(tmp_path)
    monkeypatch.setattr(services, "server_status", lambda port=services.DEFAULT_PORT, timeout=3.0: None)
    monkeypatch.setattr(services.subprocess, "Popen", lambda *a, **k: None)
    calls = {"n": 0}

    def fake_status(port=services.DEFAULT_PORT, timeout=3.0):
        calls["n"] += 1
        return {"loaded": True, "artifact_sha256": digest} if calls["n"] > 1 else None

    monkeypatch.setattr(services, "server_status", fake_status)
    monkeypatch.setattr(services.time, "sleep", lambda _seconds: None)

    result = services.ensure_prediction_server(model_path=path, timeout_s=5)

    assert result["status"] == "started"
    assert result["artifact_sha256"] == digest
