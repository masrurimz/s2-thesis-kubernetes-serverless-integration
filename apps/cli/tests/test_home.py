"""What the `thesis` command prints with no arguments: the state, then the next commands.

The home view runs before anything else, so its contract is what it does when the world is
not cooperating: a cluster that is down, no `k3d` on the PATH, no predictor answering, no
bundles yet. Each of those has to become a line of text.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest
from cli import home


@pytest.fixture()
def quiet(monkeypatch: pytest.MonkeyPatch) -> None:
    """A testbed that is down and a predictor that is not answering."""
    monkeypatch.setattr(home, "_clusters", lambda: "neither cluster is running")
    monkeypatch.setattr(home, "_predictor", lambda: "not answering on 8090")


def _bundle(root: Path, name: str, runs: int, *, verdict: bool | None = None) -> Path:
    bundle = root / "results" / "experiments" / "phase-b" / name
    raw = bundle / "raw"
    raw.mkdir(parents=True)
    # meta.yaml is what makes a directory a bundle, here and in the registry.
    (bundle / "meta.yaml").write_text("bundle_schema_version: 2\n")
    for index in range(runs):
        run = raw / f"s3-hybrid-reactive_run{index + 1}"
        run.mkdir()
        (run / "result.json").write_text("{}")
    if verdict is not None:
        derived = bundle / "derived"
        derived.mkdir()
        (derived / "paired_analysis.json").write_text(json.dumps({"h2_supported": verdict, "n_pairs": 5}))
    return bundle


class TestClusterLine:
    def test_k3d_missing_is_reported_not_raised(self, monkeypatch: pytest.MonkeyPatch):
        def missing(*args, **kwargs):
            raise FileNotFoundError("k3d")

        monkeypatch.setattr(subprocess, "run", missing)

        assert home._clusters() == "unknown (k3d not available)"

    def test_both_running(self, monkeypatch: pytest.MonkeyPatch):
        payload = json.dumps([{"name": "thesis-hybrid"}, {"name": "thesis-serverless"}])
        monkeypatch.setattr(subprocess, "run", lambda *a, **k: subprocess.CompletedProcess(a[0], 0, payload, ""))

        assert home._clusters() == "both clusters running"

    def test_one_running_names_the_absent_one(self, monkeypatch: pytest.MonkeyPatch):
        payload = json.dumps([{"name": "thesis-hybrid"}])
        monkeypatch.setattr(subprocess, "run", lambda *a, **k: subprocess.CompletedProcess(a[0], 0, payload, ""))

        assert home._clusters() == "thesis-hybrid running, thesis-serverless absent"


class TestLatestBundle:
    def test_a_root_with_no_bundles_says_so(self, tmp_path: Path):
        (tmp_path / "results" / "experiments").mkdir(parents=True)

        bundle, summary = home._latest_bundle(tmp_path)

        assert bundle is None
        assert summary == "no experiment bundles yet"

    def test_the_summary_counts_runs_and_carries_the_verdict(self, tmp_path: Path):
        _bundle(tmp_path, "2026-09-12_pairs", 3, verdict=False)

        bundle, summary = home._latest_bundle(tmp_path)

        assert bundle is not None
        assert "3 run(s)" in summary
        assert "H2 not supported at 5 pairs" in summary

    def test_a_bundle_without_an_analysis_has_no_verdict_claim(self, tmp_path: Path):
        _bundle(tmp_path, "2026-09-12_baselines", 2)

        _, summary = home._latest_bundle(tmp_path)

        assert "H2" not in summary


class TestHomeView:
    def test_prints_bin_state_and_next_steps(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys, quiet: None
    ):
        _bundle(tmp_path, "2026-09-12_pairs", 2, verdict=True)
        monkeypatch.setattr(home, "_repository_root", lambda: tmp_path)

        home.print_home()

        out = capsys.readouterr().out
        assert out.startswith("bin: ")
        assert "testbed: neither cluster is running" in out
        assert "predictor: not answering on 8090" in out
        assert "latest: 2026-09-12_pairs — 2 run(s), H2 supported at 5 pairs" in out
        assert "next: thesis analysis runs results/experiments/phase-b/2026-09-12_pairs" in out

    def test_the_next_steps_stay_useful_with_no_bundles(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys, quiet: None
    ):
        (tmp_path / "results" / "experiments").mkdir(parents=True)
        monkeypatch.setattr(home, "_repository_root", lambda: tmp_path)

        home.print_home()

        out = capsys.readouterr().out
        assert "latest: no experiment bundles yet" in out
        assert "next: thesis experiment preflight --profile h2-pair" in out
        assert "thesis analysis runs" not in out


class TestRepositoryRoot:
    def test_finds_the_checkout_this_file_lives_in(self):
        root = home._repository_root()

        assert (root / "results" / "experiments").is_dir()
