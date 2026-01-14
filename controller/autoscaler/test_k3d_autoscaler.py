"""Tests for K3d autoscaler with mocked subprocess calls."""

import pytest
from unittest.mock import patch, MagicMock, call
import subprocess

from autoscaler.k3d_autoscaler import (
    K3dAutoscaler,
    k3d_nodes,
    k3d_scale_up_events_total,
    k3d_scale_down_events_total,
    k3d_node_provision_latency_seconds,
)


class TestK3dAutoscalerInit:
    """Tests for K3dAutoscaler initialization."""

    def test_default_config(self):
        """Test default configuration values."""
        autoscaler = K3dAutoscaler()
        assert autoscaler.cluster_name == "autoscaler-cluster"
        assert autoscaler.min_nodes == 1
        assert autoscaler.max_nodes == 5
        assert autoscaler.cpu_upper_threshold == 80
        assert autoscaler.cpu_lower_threshold == 30
        assert autoscaler.check_interval == 60
        assert autoscaler.cooldown_period == 120
        assert autoscaler.node_memory_limit == "512M"
        assert autoscaler.node_cpu_limit == "1"
        assert autoscaler.metrics_port == 9102

    def test_custom_config(self):
        """Test custom configuration values."""
        autoscaler = K3dAutoscaler(
            cluster_name="test-cluster",
            min_nodes=2,
            max_nodes=10,
            cpu_upper_threshold=90,
            cpu_lower_threshold=20,
            metrics_port=9999,
        )
        assert autoscaler.cluster_name == "test-cluster"
        assert autoscaler.min_nodes == 2
        assert autoscaler.max_nodes == 10
        assert autoscaler.cpu_upper_threshold == 90
        assert autoscaler.cpu_lower_threshold == 20
        assert autoscaler.metrics_port == 9999


class TestMetricsServerCheck:
    """Tests for Kubernetes metrics server availability."""

    @pytest.fixture
    def autoscaler(self):
        """Create autoscaler instance."""
        return K3dAutoscaler()

    @patch("subprocess.run")
    def test_metrics_server_available(self, mock_run, autoscaler):
        """Test when metrics server is available."""
        mock_run.return_value = MagicMock(returncode=0)
        assert autoscaler.is_metrics_server_available() is True
        mock_run.assert_called_once_with(
            ["kubectl", "top", "nodes"],
            capture_output=True,
            text=True,
            check=True,
        )

    @patch("subprocess.run")
    def test_metrics_server_unavailable(self, mock_run, autoscaler):
        """Test when metrics server is unavailable."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "kubectl")
        assert autoscaler.is_metrics_server_available() is False


class TestCpuUtilization:
    """Tests for CPU utilization calculation."""

    @pytest.fixture
    def autoscaler(self):
        """Create autoscaler instance."""
        return K3dAutoscaler()

    @patch("subprocess.run")
    def test_get_average_cpu_single_node(self, mock_run, autoscaler):
        """Test average CPU with single node."""
        mock_run.return_value = MagicMock(
            stdout="node-1   500m   40%   1Gi   30%\n",
            returncode=0,
        )
        result = autoscaler.get_average_cpu_utilization()
        assert result == 50.0

    @patch("subprocess.run")
    def test_get_average_cpu_multiple_nodes(self, mock_run, autoscaler):
        """Test average CPU with multiple nodes."""
        mock_run.return_value = MagicMock(
            stdout="node-1   400m   40%   1Gi   30%\nnode-2   600m   60%   1Gi   40%\n",
            returncode=0,
        )
        result = autoscaler.get_average_cpu_utilization()
        assert result == 50.0

    @patch("subprocess.run")
    def test_get_average_cpu_empty(self, mock_run, autoscaler):
        """Test average CPU with no nodes."""
        mock_run.return_value = MagicMock(stdout="", returncode=0)
        result = autoscaler.get_average_cpu_utilization()
        assert result == 0.0

    @patch("subprocess.run")
    def test_get_average_cpu_error(self, mock_run, autoscaler):
        """Test average CPU when kubectl fails."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "kubectl")
        result = autoscaler.get_average_cpu_utilization()
        assert result is None


class TestNodeCount:
    """Tests for node count retrieval."""

    @pytest.fixture
    def autoscaler(self):
        """Create autoscaler instance."""
        return K3dAutoscaler()

    @patch("subprocess.run")
    def test_get_node_count(self, mock_run, autoscaler):
        """Test node count retrieval."""
        mock_run.return_value = MagicMock(
            stdout="node-1   Ready    <none>   1d   v1.25.0\nnode-2   Ready    <none>   1d   v1.25.0\n",
            returncode=0,
        )
        result = autoscaler.get_current_node_count()
        assert result == 2

    @patch("subprocess.run")
    def test_get_node_count_updates_gauge(self, mock_run, autoscaler):
        """Test that node count updates Prometheus gauge."""
        mock_run.return_value = MagicMock(
            stdout="node-1   Ready    <none>   1d   v1.25.0\nnode-2   Ready    <none>   1d   v1.25.0\nnode-3   Ready    <none>   1d   v1.25.0\n",
            returncode=0,
        )
        result = autoscaler.get_current_node_count()
        assert result == 3

    @patch("subprocess.run")
    def test_get_node_count_error(self, mock_run, autoscaler):
        """Test node count when kubectl fails."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "kubectl")
        result = autoscaler.get_current_node_count()
        assert result == autoscaler.min_nodes


class TestDockerContainers:
    """Tests for Docker container operations."""

    @pytest.fixture
    def autoscaler(self):
        """Create autoscaler instance."""
        return K3dAutoscaler()

    @patch("subprocess.run")
    def test_get_current_docker_containers(self, mock_run, autoscaler):
        """Test getting Docker containers."""
        mock_run.return_value = MagicMock(
            stdout="container-1\ncontainer-2\ncontainer-3\n",
            returncode=0,
        )
        result = autoscaler.get_current_docker_containers()
        assert result == {"container-1", "container-2", "container-3"}

    @patch("subprocess.run")
    def test_get_docker_container_by_node(self, mock_run, autoscaler):
        """Test getting Docker container for a node."""
        mock_run.return_value = MagicMock(
            stdout="k3d-node-1-agent-0\n",
            returncode=0,
        )
        result = autoscaler.get_docker_container_by_node("node-1")
        assert result == "k3d-node-1-agent-0"

    @patch("subprocess.run")
    def test_get_docker_container_by_node_not_found(self, mock_run, autoscaler):
        """Test when Docker container not found for node."""
        mock_run.return_value = MagicMock(stdout="", returncode=0)
        result = autoscaler.get_docker_container_by_node("node-1")
        assert result is None


class TestWaitForNodeReady:
    """Tests for waiting for node to be ready."""

    @pytest.fixture
    def autoscaler(self):
        """Create autoscaler instance."""
        return K3dAutoscaler()

    @patch("time.sleep")
    @patch("subprocess.run")
    def test_wait_for_node_ready_immediate(self, mock_run, mock_sleep, autoscaler):
        """Test node ready immediately."""
        mock_run.return_value = MagicMock(stdout="True", returncode=0)
        result = autoscaler.wait_for_node_ready("test-node", timeout=60)
        assert result is True

    @patch("time.time")
    @patch("time.sleep")
    @patch("subprocess.run")
    def test_wait_for_node_ready_timeout(self, mock_run, mock_sleep, mock_time, autoscaler):
        """Test node ready timeout."""
        mock_time.side_effect = [0, 0, 100, 200, 400]
        mock_run.side_effect = subprocess.CalledProcessError(1, "kubectl")
        result = autoscaler.wait_for_node_ready("test-node", timeout=300)
        assert result is False


class TestScaleUp:
    """Tests for scale up operation."""

    @pytest.fixture
    def autoscaler(self):
        """Create autoscaler instance."""
        return K3dAutoscaler(cooldown_period=0)

    @patch("time.sleep")
    @patch("time.time")
    @patch("subprocess.run")
    def test_scale_up_success(self, mock_run, mock_time, mock_sleep, autoscaler):
        """Test successful scale up."""
        mock_time.return_value = 1234567890

        mock_run.side_effect = [
            MagicMock(stdout="container-1\n", returncode=0),
            MagicMock(returncode=0),
            MagicMock(stdout="container-1\nnew-container\n", returncode=0),
            MagicMock(returncode=0),
            MagicMock(stdout="True", returncode=0),
            MagicMock(stdout="node-1\n", returncode=0),
        ]

        autoscaler.scale_up()

        calls = mock_run.call_args_list
        assert any("k3d" in str(c) and "node" in str(c) and "create" in str(c) for c in calls)
        assert any("docker" in str(c) and "update" in str(c) for c in calls)


class TestScaleDown:
    """Tests for scale down operation."""

    @pytest.fixture
    def autoscaler(self):
        """Create autoscaler instance."""
        return K3dAutoscaler(cooldown_period=0)

    @patch("time.sleep")
    @patch("subprocess.run")
    def test_scale_down_success(self, mock_run, mock_sleep, autoscaler):
        """Test successful scale down."""
        mock_run.side_effect = [
            MagicMock(stdout="node-1   800m   80%\nnode-2   200m   20%\n", returncode=0),
            MagicMock(returncode=0),
            MagicMock(returncode=0),
            MagicMock(returncode=0),
            MagicMock(stdout="node-1\n", returncode=0),
        ]

        autoscaler.scale_down()

        calls = mock_run.call_args_list
        assert any("cordon" in str(c) for c in calls)
        assert any("drain" in str(c) for c in calls)
        assert any("k3d" in str(c) and "delete" in str(c) for c in calls)

    @patch("subprocess.run")
    def test_scale_down_no_nodes(self, mock_run, autoscaler):
        """Test scale down with no nodes."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "kubectl")
        autoscaler.scale_down()


class TestGetNodesSortedByLoad:
    """Tests for getting nodes sorted by load."""

    @pytest.fixture
    def autoscaler(self):
        """Create autoscaler instance."""
        return K3dAutoscaler()

    @patch("subprocess.run")
    def test_get_nodes_sorted_by_load(self, mock_run, autoscaler):
        """Test nodes are sorted by CPU load descending."""
        mock_run.return_value = MagicMock(
            stdout="node-1   200m   20%\nnode-2   800m   80%\nnode-3   500m   50%\n",
            returncode=0,
        )
        result = autoscaler.get_nodes_sorted_by_load()
        assert len(result) == 3
        assert result[0][0] == "node-2"
        assert result[0][1] == 80.0
        assert result[-1][0] == "node-1"
        assert result[-1][1] == 20.0

    @patch("subprocess.run")
    def test_get_nodes_sorted_by_load_error(self, mock_run, autoscaler):
        """Test nodes sorted by load when kubectl fails."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "kubectl")
        result = autoscaler.get_nodes_sorted_by_load()
        assert result == []


class TestPrometheusMetrics:
    """Tests for Prometheus metrics exposure."""

    def test_metrics_defined(self):
        """Test that all required metrics are defined."""
        assert k3d_nodes is not None
        assert k3d_scale_up_events_total is not None
        assert k3d_scale_down_events_total is not None
        assert k3d_node_provision_latency_seconds is not None

    def test_metrics_types(self):
        """Test metrics are correct types."""
        from prometheus_client import Gauge, Counter, Histogram

        assert k3d_nodes._type == "gauge"
        assert k3d_scale_up_events_total._type == "counter"
        assert k3d_scale_down_events_total._type == "counter"
        assert k3d_node_provision_latency_seconds._type == "histogram"

    @patch("autoscaler.k3d_autoscaler.start_http_server")
    def test_start_metrics_server(self, mock_start):
        """Test metrics server starts on correct port."""
        autoscaler = K3dAutoscaler(metrics_port=9102)
        autoscaler.start_metrics_server()
        mock_start.assert_called_once_with(9102)

    @patch("autoscaler.k3d_autoscaler.start_http_server")
    def test_start_metrics_server_only_once(self, mock_start):
        """Test metrics server only starts once."""
        autoscaler = K3dAutoscaler(metrics_port=9102)
        autoscaler.start_metrics_server()
        autoscaler.start_metrics_server()
        assert mock_start.call_count == 1
