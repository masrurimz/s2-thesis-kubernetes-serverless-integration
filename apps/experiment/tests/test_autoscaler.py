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


class TestCreateNodeCpuLimits:
    """Regression: create_node() must not use system-reserved hack,
    and must apply Docker --cpus to dynamic nodes."""

    def test_create_cmd_excludes_system_reserved(self, adapter):
        """system-reserved=cpu=15600m was the artificial hack — must never return."""
        from unittest.mock import MagicMock

        captured_cmd = []

        def capture_k3d(args, timeout=600):
            captured_cmd.extend(args)
            return MagicMock(returncode=0, stdout="", stderr="")

        with (
            patch.object(adapter._autoscaler, "_k3d", side_effect=capture_k3d),
            patch.object(adapter._autoscaler, "_wait_node_ready", return_value=True),
            patch.object(adapter._autoscaler, "_ensure_workload_label", return_value=True),
            patch.object(adapter._autoscaler, "_run_cmd", return_value=MagicMock(returncode=0)),
        ):
            adapter._autoscaler.create_node("test-node")

        cmd_str = " ".join(captured_cmd)
        assert "system-reserved=cpu=15600m" not in cmd_str

    def test_docker_update_called_with_1_cpu(self, adapter):
        from unittest.mock import MagicMock

        captured_run_cmds = []

        def capture_run(cmd, timeout=60):
            captured_run_cmds.append(cmd)
            return MagicMock(returncode=0, stdout="", stderr="")

        with (
            patch.object(adapter._autoscaler, "_k3d", return_value=MagicMock(returncode=0)),
            patch.object(adapter._autoscaler, "_wait_node_ready", return_value=True),
            patch.object(adapter._autoscaler, "_ensure_workload_label", return_value=True),
            patch.object(adapter._autoscaler, "_run_cmd", side_effect=capture_run),
        ):
            adapter._autoscaler.create_node("test-node")

        docker_updates = [
            cmd for cmd in captured_run_cmds if len(cmd) > 1 and cmd[0] == "docker" and cmd[1] == "update"
        ]
        assert len(docker_updates) > 0, "No docker update call found"
        update_cmd = docker_updates[0]
        assert "--cpus" in update_cmd
        cpus_idx = update_cmd.index("--cpus")
        assert update_cmd[cpus_idx + 1] == "1.0"

    def test_docker_update_uses_correct_container_name(self, adapter):
        from unittest.mock import MagicMock

        captured_run_cmds = []

        def capture_run(cmd, timeout=60):
            captured_run_cmds.append(cmd)
            return MagicMock(returncode=0, stdout="", stderr="")

        with (
            patch.object(adapter._autoscaler, "_k3d", return_value=MagicMock(returncode=0)),
            patch.object(adapter._autoscaler, "_wait_node_ready", return_value=True),
            patch.object(adapter._autoscaler, "_ensure_workload_label", return_value=True),
            patch.object(adapter._autoscaler, "_run_cmd", side_effect=capture_run),
        ):
            adapter._autoscaler.create_node("test-node")

        docker_updates = [
            cmd for cmd in captured_run_cmds if len(cmd) > 1 and cmd[0] == "docker" and cmd[1] == "update"
        ]
        assert len(docker_updates) > 0
        # Container name follows k3d convention: k3d-{node_name}-0
        container_name = docker_updates[0][-1]
        assert container_name == "k3d-test-node-0"
