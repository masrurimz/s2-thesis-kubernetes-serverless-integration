"""Artifact read/write: one loader, validated shapes, tolerant reads.

The fixtures are real run files, trimmed: a bundle's actual shapes are the contract,
and a hand-written fixture drifts from them silently.
"""

import json
from pathlib import Path

import pytest

from shared.artifacts import (
    MANIFEST_FILE,
    NODE_UTILIZATION_FILE,
    PROVISION_EVENTS_FILE,
    RESOURCE_UTILIZATION_FILE,
    RESULT_FILE,
    provision_event_names,
    read_manifest,
    read_manifest_git_commit,
    read_node_utilization,
    read_prometheus_export,
    read_provision_events,
    read_resource_utilization,
    read_result,
    read_result_dict,
    result_validation_error,
    write_manifest,
    write_node_utilization,
    write_provision_events,
    write_resource_utilization,
    write_result,
)
from shared.models.experiment import ExperimentResult, RunManifest
from shared.models.metrics import NodeSample, ResourceSample
from shared.models.provisioning import ProvisionEvent

FIXTURES = Path(__file__).parent / "fixtures"


def _fixture_bytes(name: str) -> bytes:
    return (FIXTURES / name).read_bytes()


class TestResult:
    def test_real_result_reads_back_typed(self, tmp_path):
        (tmp_path / RESULT_FILE).write_bytes(_fixture_bytes(RESULT_FILE))

        result = read_result(tmp_path)

        assert isinstance(result, ExperimentResult)
        assert result.scenario
        assert result.run_validity_passed is True

    def test_round_trip_preserves_the_result(self, tmp_path):
        (tmp_path / RESULT_FILE).write_bytes(_fixture_bytes(RESULT_FILE))
        original = read_result(tmp_path)
        assert original is not None

        write_result(tmp_path, original)

        assert read_result(tmp_path) == original

    def test_dict_view_matches_the_model(self, tmp_path):
        (tmp_path / RESULT_FILE).write_bytes(_fixture_bytes(RESULT_FILE))

        result = read_result(tmp_path)
        assert result is not None

        assert read_result_dict(tmp_path) == result.model_dump(exclude_unset=True)

    def test_dict_view_does_not_invent_defaults_for_absent_fields(self, tmp_path):
        """A field the file omits stays omitted: the summary reports n/a, not 0."""
        (tmp_path / RESULT_FILE).write_text(json.dumps({"scenario": "s3-hybrid-reactive", "run_id": 1}))

        as_dict = read_result_dict(tmp_path)

        assert as_dict["scenario"] == "s3-hybrid-reactive"
        assert "time_in_serverless_pct" not in as_dict

    def test_missing_and_corrupt_are_not_errors(self, tmp_path):
        assert read_result(tmp_path) is None
        assert read_result_dict(tmp_path) == {}

        (tmp_path / RESULT_FILE).write_text("{ not json")
        assert read_result(tmp_path) is None


class TestManifest:
    def test_real_manifest_reads_back_with_conditions(self, tmp_path):
        (tmp_path / MANIFEST_FILE).write_bytes(_fixture_bytes(MANIFEST_FILE))

        manifest = read_manifest(tmp_path)

        assert isinstance(manifest, RunManifest)
        assert manifest.scenario
        assert "load" in manifest.conditions

    def test_commit_helper_is_empty_without_a_manifest(self, tmp_path):
        assert read_manifest_git_commit(tmp_path) == ""

    def test_commit_survives_a_manifest_too_old_to_validate(self, tmp_path):
        """Every bundle records the commit; a manifest missing newer fields still has it."""
        (tmp_path / MANIFEST_FILE).write_text(json.dumps({"git_commit": "abc1234", "scenario": "alpha"}))

        assert read_manifest(tmp_path) is None
        assert read_manifest_git_commit(tmp_path) == "abc1234"

    def test_round_trip_preserves_the_manifest(self, tmp_path):
        (tmp_path / MANIFEST_FILE).write_bytes(_fixture_bytes(MANIFEST_FILE))
        original = read_manifest(tmp_path)
        assert original is not None

        write_manifest(tmp_path, original)

        assert read_manifest(tmp_path) == original


class TestProvisionEvents:
    def test_real_events_read_back_typed(self, tmp_path):
        (tmp_path / PROVISION_EVENTS_FILE).write_bytes(_fixture_bytes(PROVISION_EVENTS_FILE))

        events = read_provision_events(tmp_path)

        assert events
        assert all(isinstance(event, ProvisionEvent) for event in events)
        assert "autoscaler_started" in provision_event_names(events)

    def test_legacy_key_spelling_still_reads(self, tmp_path):
        """The older spelling put the event name in ``et`` beside ``ts``, not in it."""
        (tmp_path / PROVISION_EVENTS_FILE).write_text(
            json.dumps([{"ts": 12.5, "et": "node_created", "d": {"k8s_node": "k3d-dynamic-workload-0-0"}}])
        )

        events = read_provision_events(tmp_path)

        assert len(events) == 1
        assert events[0].ts == 12.5
        assert events[0].event == "node_created"
        assert events[0].data["k8s_node"] == "k3d-dynamic-workload-0-0"
        assert provision_event_names(events) == ["node_created"]

    def test_unreadable_entries_are_skipped_not_fatal(self, tmp_path):
        (tmp_path / PROVISION_EVENTS_FILE).write_text(
            json.dumps(["nonsense", {"ts": 1.0, "event": "pending_detected", "data": {}}])
        )

        assert provision_event_names(read_provision_events(tmp_path)) == ["pending_detected"]

    def test_write_emits_the_persisted_wire_keys(self, tmp_path):
        write_provision_events(tmp_path, [(1.5, "node_deleted", {"node": "x"})])

        raw = json.loads((tmp_path / PROVISION_EVENTS_FILE).read_text())

        assert raw == [{"ts": 1.5, "event": "node_deleted", "data": {"node": "x"}}]

    def test_missing_file_is_an_empty_stream(self, tmp_path):
        assert read_provision_events(tmp_path) == []


class TestUtilizationSamples:
    def test_real_resource_samples_read_back_typed(self, tmp_path):
        (tmp_path / RESOURCE_UTILIZATION_FILE).write_bytes(_fixture_bytes(RESOURCE_UTILIZATION_FILE))

        samples = read_resource_utilization(tmp_path)

        assert samples
        assert all(isinstance(sample, ResourceSample) for sample in samples)
        assert samples[0].pod

    def test_resource_round_trip(self, tmp_path):
        samples = [
            ResourceSample(timestamp=1.0, pod="test-app-warm-abc", backend="k8s", cpu_millicores=250.0, memory_mib=64.0)
        ]

        write_resource_utilization(tmp_path, samples)

        assert read_resource_utilization(tmp_path) == samples

    def test_real_node_samples_read_back_typed(self, tmp_path):
        (tmp_path / NODE_UTILIZATION_FILE).write_bytes(_fixture_bytes(NODE_UTILIZATION_FILE))

        samples = read_node_utilization(tmp_path)

        assert samples
        assert all(isinstance(sample, NodeSample) for sample in samples)

    def test_node_round_trip_keeps_a_missing_reading_missing(self, tmp_path):
        samples = [NodeSample(timestamp=1.0, node="k3d-dynamic-workload-0-0")]

        write_node_utilization(tmp_path, samples)
        restored = read_node_utilization(tmp_path)

        assert restored == samples
        assert restored[0].cpu_pct is None


class TestPrometheusExport:
    def test_series_read_back_as_pairs(self, tmp_path):
        export = tmp_path / "prometheus" / "prometheus_export.json"
        export.parent.mkdir(parents=True)
        export.write_text(json.dumps({"prom_rps": [[1.0, 5.0], [16.0, 7.5]], "garbage": "no"}))

        series = read_prometheus_export(tmp_path)

        assert series["prom_rps"] == [(1.0, 5.0), (16.0, 7.5)]
        assert "garbage" not in series

    def test_missing_export_is_empty(self, tmp_path):
        assert read_prometheus_export(tmp_path) == {}


@pytest.mark.parametrize("reader", [read_result, read_manifest])
def test_readers_never_raise_on_a_half_written_bundle(tmp_path, reader):
    (tmp_path / RESULT_FILE).write_bytes(b"\x00\x01binary")
    (tmp_path / MANIFEST_FILE).write_bytes(b"\x00\x01binary")

    assert reader(tmp_path) is None


@pytest.mark.parametrize(
    ("reader", "filename"),
    [
        (read_resource_utilization, RESOURCE_UTILIZATION_FILE),
        (read_node_utilization, NODE_UTILIZATION_FILE),
    ],
)
def test_sample_readers_never_raise_on_a_file_that_does_not_validate(tmp_path, reader, filename):
    """Valid JSON of the wrong shape is the same empty answer as a missing file."""
    (tmp_path / filename).write_text(json.dumps([{"not": "a sample"}]))

    assert reader(tmp_path) == []


def test_result_diagnostics_name_the_reason_a_file_was_rejected(tmp_path):
    """A validate command needs the reason, which the reader deliberately swallows."""
    (tmp_path / RESULT_FILE).write_text(json.dumps({"run_id": "not-an-int"}))

    assert read_result(tmp_path) is None
    reason = result_validation_error(tmp_path)
    assert reason is not None
    assert "run_id" in reason


def test_result_diagnostics_are_quiet_for_a_good_file(tmp_path):
    (tmp_path / RESULT_FILE).write_bytes(_fixture_bytes(RESULT_FILE))

    assert result_validation_error(tmp_path) is None
