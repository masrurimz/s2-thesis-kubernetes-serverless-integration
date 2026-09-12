"""The bundle evidence tables: what they print by default, and how a reader asks for more.

These commands are the ones an agent runs against a finished bundle, so the contract they
have to keep is about budget: four columns unless asked otherwise, one line of JSON for a
program, and a name for the field that does not exist rather than a traceback.
"""

from __future__ import annotations

import json

import pytest
from analysis.bundle_evidence import MechanismRow, RunEvidence, as_payload, variance_summary
from analysis_cli.cli import app
from typer.testing import CliRunner

runner = CliRunner()


def _row(scenario: str, run_id: int, p99: float, **extra) -> RunEvidence:
    return RunEvidence(
        scenario=scenario,
        run_id=run_id,
        valid=True,
        p99_latency_ms=p99,
        slo_violations=extra.get("slo_violations", 0),
        nodes_provisioned=extra.get("nodes_provisioned", 1),
        host_load_ratio=extra.get("host_load_ratio", 0.1),
    )


@pytest.fixture()
def two_runs(monkeypatch: pytest.MonkeyPatch) -> None:
    rows = [_row("s3-hybrid-reactive", 1, 215.0), _row("s4-hybrid-predictive", 1, 130.2)]
    monkeypatch.setattr("analysis.bundle_evidence.run_evidence", lambda bundle: rows)


@pytest.fixture()
def two_mechanism_rows(monkeypatch: pytest.MonkeyPatch) -> None:
    rows = [
        MechanismRow(
            scenario="s3-hybrid-reactive",
            run_id=1,
            p99_latency_ms=215.0,
            provisioning_delay_sec=64.8,
            node_arrival_offset_sec=61.0,
        ),
        MechanismRow(
            scenario="s4-hybrid-predictive",
            run_id=1,
            p99_latency_ms=130.2,
            provisioning_delay_sec=89.7,
            node_arrival_offset_sec=86.0,
        ),
    ]
    monkeypatch.setattr("analysis.bundle_evidence.mechanism_rows", lambda bundle: rows)


class TestDefaultColumns:
    def test_four_columns_by_default(self, two_runs: None):
        result = runner.invoke(app, ["runs", "some-bundle"])

        assert result.exit_code == 0, result.output
        header = result.output.splitlines()[0].split()
        assert header == ["scenario", "run", "valid", "p99", "ms"]

    def test_the_row_still_carries_its_values(self, two_runs: None):
        result = runner.invoke(app, ["runs", "some-bundle"])

        assert "s4-hybrid-predictive" in result.output
        assert "130.2" in result.output

    def test_the_answer_says_what_to_run_next(self, two_runs: None):
        result = runner.invoke(app, ["runs", "some-bundle"])

        assert "next: thesis analysis mechanism some-bundle" in result.output

    def test_a_reader_can_ask_for_the_hidden_columns(self, two_runs: None):
        result = runner.invoke(app, ["runs", "some-bundle", "--fields", "scenario,nodes,slo"])

        assert result.exit_code == 0, result.output
        assert result.output.splitlines()[0].split() == ["scenario", "nodes", "slo"]

    def test_all_names_every_column(self, two_runs: None):
        result = runner.invoke(app, ["runs", "some-bundle", "--fields", "all"])

        header = result.output.splitlines()[0]
        assert "nodes" in header
        assert "delivered" in header

    def test_an_unknown_field_names_the_valid_ones_and_exits_two(self, two_runs: None):
        result = runner.invoke(app, ["runs", "some-bundle", "--fields", "scenario,nope"])

        assert result.exit_code == 2
        assert "nope" in result.output
        assert "valid fields" in result.output


class TestJsonContract:
    def test_one_line_and_the_same_four_fields_as_the_table(self, two_runs: None):
        result = runner.invoke(app, ["runs", "some-bundle", "--json"])

        assert result.exit_code == 0, result.output
        payload = result.stdout
        assert "\n" not in payload.strip()
        rows = json.loads(payload)
        assert [sorted(row) for row in rows] == [["p99_ms", "run", "scenario", "valid"]] * 2

    def test_fields_narrows_the_payload_too(self, two_runs: None):
        result = runner.invoke(app, ["runs", "some-bundle", "--json", "--fields", "scenario,nodes"])

        assert json.loads(result.stdout) == [
            {"scenario": "s3-hybrid-reactive", "nodes": 1},
            {"scenario": "s4-hybrid-predictive", "nodes": 1},
        ]

    def test_json_carries_no_human_trailers(self, two_runs: None):
        result = runner.invoke(app, ["runs", "some-bundle", "--json"])

        assert "next:" not in result.stdout


class TestMechanism:
    def test_default_columns_lead_with_when_the_node_arrived(self, two_mechanism_rows: None):
        result = runner.invoke(app, ["mechanism", "some-bundle"])

        assert result.exit_code == 0, result.output
        assert result.output.splitlines()[0].split() == ["scenario", "run", "p99", "ms", "node", "at", "s"]

    def test_the_next_step_is_the_variance_table(self, two_mechanism_rows: None):
        result = runner.invoke(app, ["mechanism", "some-bundle"])

        assert "next: thesis analysis variance some-bundle" in result.output


class TestVariance:
    def test_json_projects_the_arms_but_keeps_the_pair_statistics(self, tmp_path, monkeypatch: pytest.MonkeyPatch):
        summary = variance_summary(tmp_path)
        summary.arms = []
        monkeypatch.setattr("analysis.bundle_evidence.variance_summary", lambda bundle: summary)

        result = runner.invoke(app, ["variance", "some-bundle", "--json", "--fields", "scenario,n"])

        payload = json.loads(result.stdout)
        assert payload["arms"] == []
        assert "n_pairs" in payload
        assert "note" in payload


class TestPayloadShape:
    """`as_payload` is what `--json` is built on: it must not drop a field."""

    def test_every_field_of_a_row_is_in_the_payload(self):
        payload = as_payload([_row("s3-hybrid-reactive", 1, 215.0)])

        assert set(payload[0]) == set(RunEvidence.model_fields)
