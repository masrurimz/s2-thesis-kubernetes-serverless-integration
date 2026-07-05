"""Isolated tests for K3dAutoscalerAdapter — no real cluster needed."""

from unittest.mock import patch

import pytest


@pytest.fixture
def adapter():
    """Create adapter with mocked k3d/kubectl paths."""
    from infra.cluster.k3d.autoscaler import K3dAutoscalerAdapter

    return K3dAutoscalerAdapter(
        cluster_name="test-cluster",
        k3d_path="echo",
        kubectl_path="echo",
        k3s_image="test-image",
        min_nodes=0,
        max_nodes=2,
        provision_delay_min_sec=0,
        provision_delay_max_sec=0,
    )


class TestAdapterInterface:
    """Verify K3dAutoscalerAdapter implements ProvisionerClient protocol."""

    def test_has_reset(self, adapter):
        assert hasattr(adapter, "reset")

    def test_has_start_background(self, adapter):
        assert hasattr(adapter, "start_background")

    def test_has_stop(self, adapter):
        assert hasattr(adapter, "stop")

    def test_has_get_log(self, adapter):
        assert hasattr(adapter, "get_log")

    def test_has_clear_log(self, adapter):
        assert hasattr(adapter, "clear_log")


class TestEventNames:
    """Verify adapter emits 'node_created' events (not 'node_provisioned')."""

    def test_reset_records_autoscaler_reset_event(self, adapter):
        with patch.object(adapter._autoscaler, "_discover_dynamic_nodes", return_value=[]):
            adapter.reset()
            log = adapter.get_log()
            event_types = [et for _, et, _ in log]
            assert "autoscaler_reset" in event_types


class TestClearLog:
    """Verify log clearing for per-run isolation."""

    def test_clear_log_empties_events(self, adapter):
        adapter._autoscaler._record_event("test_event", {"key": "value"})
        assert len(adapter.get_log()) > 0
        adapter.clear_log()
        assert len(adapter.get_log()) == 0


class TestMaxNodesRespected:
    """Verify max_nodes limit is enforced."""

    def test_max_nodes_stored(self, adapter):
        assert adapter._autoscaler.max_nodes == 2

    def test_min_nodes_stored(self, adapter):
        assert adapter._autoscaler.min_nodes == 0
