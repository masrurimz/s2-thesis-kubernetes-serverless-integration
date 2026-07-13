"""Isolated tests for K3dAutoscalerAdapter — no real cluster needed."""

from unittest.mock import MagicMock, patch

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


class TestScaleDownUtilization:
    """Verify utilization-based scale-down logic (cluster-autoscaler semantics)."""

    def test_get_node_cpu_utilization_parses_cpu_requests(self, adapter):
        """_get_node_cpu_utilization sums CPU requests and divides by allocatable."""
        a = adapter._autoscaler
        mock_pods = [
            {"spec": {"containers": [{"resources": {"requests": {"cpu": "300m"}}}]}},
            {"spec": {"containers": [{"resources": {"requests": {"cpu": "300m"}}}]}},
        ]
        with patch.object(a, "_get_workload_pods_on_node", return_value=mock_pods):
            util = a._get_node_cpu_utilization("test-node")
            assert util == pytest.approx(0.6)  # 600m / 1000m

    def test_get_node_cpu_utilization_empty_node(self, adapter):
        """Empty node should return 0.0 utilization."""
        a = adapter._autoscaler
        with patch.object(a, "_get_workload_pods_on_node", return_value=[]):
            with patch.object(a, "_kubectl") as mock_kubectl:
                mock_kubectl.return_value = MagicMock(returncode=0, stdout='{"items":[]}', stderr="")
                util = a._get_node_cpu_utilization("test-node")
                assert util == 0.0

    def test_scale_down_triggers_below_threshold(self, adapter):
        """Node with utilization < threshold and reschedulable pods should be deleted."""
        a = adapter._autoscaler
        a.scale_down_idle_sec = 0  # immediate
        a._last_scale_down_ts = 0  # cooldown passed

        with (
            patch.object(a, "_get_node_cpu_utilization", return_value=0.3),
            patch.object(a, "_get_workload_pods_on_node", return_value=[]),
            patch.object(a, "_can_pods_be_rescheduled", return_value=True),
            patch.object(a, "_discover_dynamic_nodes", return_value=["dynamic-workload-0"]),
            patch.object(a, "delete_node") as mock_delete,
            patch.object(a, "watch_pending", return_value=[]),
            patch("infra.cluster.k3d.autoscaler.time.sleep", side_effect=lambda _: a._stop_event.set()),
        ):
            a._scaling_loop()
            mock_delete.assert_called_once_with("dynamic-workload-0")

    def test_scale_down_skipped_above_threshold(self, adapter):
        """Node with utilization >= threshold should NOT be deleted."""
        a = adapter._autoscaler
        a._last_scale_down_ts = 0

        with (
            patch.object(a, "_get_node_cpu_utilization", return_value=0.6),
            patch.object(a, "_discover_dynamic_nodes", return_value=["dynamic-workload-0"]),
            patch.object(a, "delete_node") as mock_delete,
            patch.object(a, "watch_pending", return_value=[]),
            patch("infra.cluster.k3d.autoscaler.time.sleep", side_effect=lambda _: a._stop_event.set()),
        ):
            a._scaling_loop()
            mock_delete.assert_not_called()

    def test_scale_down_skipped_unreschedulable(self, adapter):
        """Node below threshold but pods can't move should NOT be deleted."""
        a = adapter._autoscaler
        a.scale_down_idle_sec = 0
        a._last_scale_down_ts = 0

        mock_pods = [{"spec": {"containers": [{"resources": {"requests": {"cpu": "300m"}}}]}}]
        with (
            patch.object(a, "_get_node_cpu_utilization", return_value=0.3),
            patch.object(a, "_get_workload_pods_on_node", return_value=mock_pods),
            patch.object(a, "_can_pods_be_rescheduled", return_value=False),
            patch.object(a, "_discover_dynamic_nodes", return_value=["dynamic-workload-0"]),
            patch.object(a, "delete_node") as mock_delete,
            patch.object(a, "watch_pending", return_value=[]),
            patch("infra.cluster.k3d.autoscaler.time.sleep", side_effect=lambda _: a._stop_event.set()),
        ):
            a._scaling_loop()
            mock_delete.assert_not_called()

    def test_scale_down_respects_cooldown(self, adapter):
        """Scale-down should not fire during cooldown period."""
        import time

        a = adapter._autoscaler
        a._last_scale_down_ts = time.time()  # just scaled down

        with (
            patch.object(a, "_get_node_cpu_utilization", return_value=0.0),
            patch.object(a, "_discover_dynamic_nodes", return_value=["dynamic-workload-0"]),
            patch.object(a, "delete_node") as mock_delete,
            patch.object(a, "watch_pending", return_value=[]),
            patch("infra.cluster.k3d.autoscaler.time.sleep", side_effect=lambda _: a._stop_event.set()),
        ):
            a._scaling_loop()
            mock_delete.assert_not_called()

    def test_parse_cpu_request_formats(self):
        """_parse_cpu_request handles '300m', '1', '0.5' correctly."""
        from infra.cluster.k3d.autoscaler import K3dAutoscaler

        assert K3dAutoscaler._parse_cpu_request("300m") == 0.3
        assert K3dAutoscaler._parse_cpu_request("1") == 1.0
        assert K3dAutoscaler._parse_cpu_request("0.5") == 0.5
        assert K3dAutoscaler._parse_cpu_request("1000m") == 1.0
