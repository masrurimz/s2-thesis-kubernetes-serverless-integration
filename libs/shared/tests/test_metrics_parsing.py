"""Quantity parsing and the node sample model.

These are the unit rules every resource reading passes through. metrics-server
prints `<unknown>` while it has no scrape for a node, and that token must stay a
missing reading — never a zero, which would silently drag an average down.
"""

import pytest

from shared.models.metrics import (
    NodeSample,
    parse_cpu_to_cores,
    parse_memory_to_mib,
)


class TestCpuQuantities:
    @pytest.mark.parametrize(
        ("value", "expected"),
        [("250m", 0.25), ("2", 2.0), ("1", 1.0), ("1500m", 1.5), ("500u", 0.0005), ("100n", 1e-7)],
    )
    def test_quantity_forms(self, value, expected):
        assert parse_cpu_to_cores(value) == pytest.approx(expected)

    @pytest.mark.parametrize("value", ["<unknown>", "unknown", "", "N/A", "nan", "12x"])
    def test_unreadable_is_none_not_zero(self, value):
        assert parse_cpu_to_cores(value) is None


class TestMemoryQuantities:
    @pytest.mark.parametrize(
        ("value", "expected"),
        [("1024Ki", 1.0), ("512Mi", 512.0), ("2Gi", 2048.0), ("1048576", 1.0)],
    )
    def test_quantity_forms(self, value, expected):
        assert parse_memory_to_mib(value) == pytest.approx(expected)

    @pytest.mark.parametrize("value", ["<unknown>", "", "3Pi", "abc"])
    def test_unreadable_or_unsupported_is_none(self, value):
        assert parse_memory_to_mib(value) is None


class TestNodeSampleRow:
    ROW = "k3d-thesis-hybrid-agent-0   250m   6%   1024Mi   12%"

    def test_row_becomes_a_typed_sample(self):
        sample = NodeSample.from_kubectl_top_row(self.ROW, timestamp=123.0)

        assert sample is not None
        assert (sample.node, sample.cpu_cores, sample.cpu_pct) == ("k3d-thesis-hybrid-agent-0", 0.25, 6.0)
        assert (sample.memory_mib, sample.memory_pct) == (1024.0, 12.0)

    def test_row_without_any_reading_is_not_a_sample(self):
        assert (
            NodeSample.from_kubectl_top_row(
                "k3d-dynamic-workload-0-0   <unknown>   <unknown>   <unknown>   <unknown>", 1.0
            )
            is None
        )

    def test_partial_row_keeps_what_exists(self):
        sample = NodeSample.from_kubectl_top_row(
            "k3d-thesis-hybrid-agent-0   250m   <unknown>   1024Mi   <unknown>", 1.0
        )

        assert sample is not None
        assert sample.cpu_cores == 0.25
        assert sample.cpu_pct is None

    def test_short_row_is_rejected(self):
        assert NodeSample.from_kubectl_top_row("k3d-thesis-hybrid-agent-0   250m", 1.0) is None

    def test_artifact_round_trip_preserves_the_sample(self):
        sample = NodeSample.from_kubectl_top_row(self.ROW, timestamp=123.0)
        assert sample is not None

        assert NodeSample.model_validate(sample.model_dump()) == sample
