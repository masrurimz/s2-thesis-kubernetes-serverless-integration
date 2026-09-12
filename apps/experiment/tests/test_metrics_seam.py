"""The metrics seam: an injected client is what the exporter and the SLO monitor read.

The default client is still the Prometheus one built from the settings URL; these
tests pin the substitution, which is what lets the export path be exercised without a
server and what a different metrics backend would use.
"""

from pathlib import Path

import pytest

from experiment.stages.collect import CollectStage, MetricExporter
from routing.monitoring.slo_monitor import SLOMonitor, SLOConfig


class FakeMetricsClient:
    """Canned series, no HTTP."""

    def __init__(self, instant: float | None = 123.0, points: int = 3):
        self.instant = instant
        self.points = points
        self.instant_queries: list[str] = []
        self.range_queries: list[tuple[str, int, int, int]] = []

    def query_instant(self, expr: str, timestamp: int | None = None):
        self.instant_queries.append(expr)
        return self.instant

    def query_range(self, expr: str, start: int, end: int, step: int = 15):
        self.range_queries.append((expr, start, end, step))
        return [(start + i * step, float(i)) for i in range(self.points)]


def test_exporter_writes_the_export_through_the_injected_client(tmp_path: Path):
    client = FakeMetricsClient(points=4)
    exporter = MetricExporter(metrics_client=client)

    summary = exporter.export_run(1000.0, 1100.0, tmp_path)

    assert client.range_queries, "the exporter must query through the injected client"
    assert summary["export_path"] == str(tmp_path / "prometheus_export.json")
    assert (tmp_path / "prometheus_export.json").exists()


def test_exporter_uses_every_query_in_its_table(tmp_path: Path):
    client = FakeMetricsClient()
    MetricExporter(metrics_client=client).export_run(0.0, 100.0, tmp_path)

    queried = {expr for expr, *_ in client.range_queries}
    assert queried == set(MetricExporter.QUERIES.values())


def test_collect_stage_passes_the_client_through(tmp_path: Path):
    client = FakeMetricsClient()

    stage = CollectStage(metrics_client=client)
    stage._exporter.export_run(0.0, 60.0, tmp_path)

    assert client.range_queries


def test_slo_monitor_reads_p99_through_the_client():
    client = FakeMetricsClient(instant=321.5)
    monitor = SLOMonitor(config=SLOConfig(prometheus_url="http://unused:9090"), metrics_client=client)

    assert monitor._get_p99_from_prometheus() == 321.5
    assert client.instant_queries == [SLOMonitor.P99_QUERY]


@pytest.mark.parametrize("value", [None, 0.0])
def test_slo_monitor_reports_zero_when_there_is_no_reading(value):
    """No data is a zero reading, not a crash and not a guess."""
    monitor = SLOMonitor(
        config=SLOConfig(prometheus_url="http://unused:9090"),
        metrics_client=FakeMetricsClient(instant=value),
    )

    assert monitor._get_p99_from_prometheus() == 0.0


def test_slo_monitor_survives_a_failing_client():
    class Broken:
        def query_instant(self, expr: str, timestamp: int | None = None):
            raise RuntimeError("prometheus down")

        def query_range(self, expr: str, start: int, end: int, step: int = 15):
            raise RuntimeError("prometheus down")

    monitor = SLOMonitor(config=SLOConfig(prometheus_url="http://unused:9090"), metrics_client=Broken())

    assert monitor._get_p99_from_prometheus() == 0.0
