"""E2E tests for CPU allocation fairness — requires a live cluster.

Skip automatically if no thesis-hybrid cluster is running.
Validates the core assumption: Docker --cpus actually constrains the kubelet.
"""

import subprocess

import pytest


def _cluster_running() -> bool:
    """Check if thesis-hybrid k3d cluster is running."""
    try:
        r = subprocess.run(
            ["k3d", "cluster", "list"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return "thesis-hybrid" in (r.stdout or "")
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


pytestmark = pytest.mark.skipif(
    not _cluster_running(),
    reason="E2E requires thesis-hybrid cluster (run: uv run thesis infra setup)",
)


class TestDockerCpusConstrainsKubelet:
    """The critical E2E test — does docker update --cpus constrain kubelet allocatable?"""

    def test_workload_node_allocatable_is_bounded(self):
        from infra.diagnostics.verifier import ClusterVerifier

        v = ClusterVerifier()
        results = v.verify_all()
        assert results["workload_node_allocatable_bounded"], (
            "Workload node allocatable too high — Docker --cpus not constraining kubelet. "
            "Apply the system-reserved fallback from Step 3."
        )

    def test_infra_node_allocatable_is_bounded(self):
        from infra.diagnostics.verifier import ClusterVerifier

        v = ClusterVerifier()
        assert v.verify_all()["infra_node_allocatable_bounded"]


class TestNodeLabels:
    def test_all_nodes_labeled(self):
        from infra.diagnostics.verifier import ClusterVerifier

        v = ClusterVerifier()
        assert v.verify_all()["node_labels_correct"]


class TestCapacityRatio:
    def test_infra_workload_ratio_under_4x(self):
        """Infra (2 CPU) should be ~2x workload (1 CPU), NOT 40x (old asymmetry)."""
        from infra.diagnostics.verifier import ClusterVerifier

        v = ClusterVerifier()
        assert v.verify_all()["capacity_ratio_acceptable"]


class TestDynamicNodeCpuLimit:
    """E2E: create_node() applies Docker --cpus to dynamic nodes.
    Creates a real k3d node, verifies it, then cleans up. ~30-60s."""

    @pytest.fixture(autouse=True, scope="class")
    def cleanup_orphaned_e2e_nodes(self):
        """Remove leftover 'e2e-verify-dynamic' nodes before and after tests."""
        subprocess.run(
            ["k3d", "node", "delete", "e2e-verify-dynamic", "--cluster", "thesis-hybrid"],
            capture_output=True,
            timeout=30,
        )
        yield
        subprocess.run(
            ["k3d", "node", "delete", "e2e-verify-dynamic", "--cluster", "thesis-hybrid"],
            capture_output=True,
            timeout=30,
        )

    def test_dynamic_node_gets_1_cpu(self):
        from infra.cluster.k3d.autoscaler import K3dAutoscaler
        from infra.diagnostics.verifier import ClusterVerifier

        autoscaler = K3dAutoscaler(
            cluster_name="thesis-hybrid",
            k3d_path="k3d",
            kubectl_path="kubectl",
            k3s_image="rancher/k3s:v1.28.5-k3s1",
        )
        test_node = "e2e-verify-dynamic"
        try:
            assert autoscaler.create_node(test_node)
            v = ClusterVerifier()
            assert v.check_docker_cpus(f"k3d-thesis-hybrid-{test_node}-0", expected=1.0)
        finally:
            autoscaler.delete_node(test_node)
