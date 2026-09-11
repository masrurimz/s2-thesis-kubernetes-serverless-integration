"""The proxy config names the running cluster, not the one from July.

The Knative host embeds the Kourier service IP, so a rebuilt cluster serves 404 to
everything HAProxy forwards to it: the serverless arm stops answering and the run
measures a broken arm instead of a slow one.
"""

from __future__ import annotations

import pathlib
import subprocess

from infra.networking.haproxy import render


def test_the_host_header_comes_from_the_running_cluster(monkeypatch, tmp_path):
    monkeypatch.setattr(render, "RUNTIME_DIR", tmp_path)

    path = render.render_config("default", host="test-app.default.172.22.0.2.sslip.io")

    text = path.read_text()
    assert "http-request set-header Host test-app.default.172.22.0.2.sslip.io" in text
    assert "192.168.0.2" not in text


def test_the_config_is_written_beside_the_package_without_touching_it(monkeypatch, tmp_path):
    monkeypatch.setattr(render, "RUNTIME_DIR", tmp_path)

    render.render_config("default", host="test-app.default.10.0.0.9.sslip.io")

    shipped = pathlib.Path(
        str(render.importlib.resources.files("infra").joinpath("networking", "haproxy", "haproxy.cfg"))
    )
    assert "192.168.0.2" in shipped.read_text()


def test_an_unresolvable_host_leaves_the_config_usable(monkeypatch, tmp_path):
    monkeypatch.setattr(render, "RUNTIME_DIR", tmp_path)

    path = render.render_config("knative", host="")

    assert "set-header Host" in path.read_text()


def test_knative_host_reads_the_service_url(monkeypatch):
    monkeypatch.setattr(
        render,
        "run",
        lambda *a, **k: subprocess.CompletedProcess(
            a[0], 0, stdout="http://test-app.default.172.22.0.2.sslip.io\n", stderr=""
        ),
    )

    assert render.knative_host() == "test-app.default.172.22.0.2.sslip.io"


def test_knative_host_is_none_when_the_service_is_absent(monkeypatch):
    monkeypatch.setattr(
        render,
        "run",
        lambda *a, **k: subprocess.CompletedProcess(a[0], 1, stdout="", stderr="not found"),
    )

    assert render.knative_host() is None
