"""Regression tests for CPU allocation fairness.

Pure file-content assertions — no cluster, no Docker, no network.
Prevents the K8s-vs-serverless capacity asymmetry from silently recurring.
"""

import importlib.resources

import yaml


def _read_infra_text(rel_path: str) -> str:
    """Read a text file from the infra package data."""
    base = importlib.resources.files("infra")
    return base.joinpath(*rel_path.split("/")).read_text()


def _load_infra_yaml(rel_path: str) -> dict:
    """Load the first YAML document from an infra package data file.
    Handles multi-document YAML files (e.g., Deployment + Service)."""
    docs = list(yaml.safe_load_all(_read_infra_text(rel_path)))
    return docs[0] if docs else {}


class TestNoSystemReservedHack:
    """The single most important regression guard."""

    def test_cluster_yaml_excludes_system_reserved_15600m(self):
        """system-reserved=cpu=15600m was the artificial hack that only
        constrained K8s nodes while leaving Knative unconstrained (~40× asymmetry).
        It must never be re-introduced."""
        content = _read_infra_text("cluster/k3d/cluster.yaml")
        assert "system-reserved=cpu=15600m" not in content


class TestPodCpuParity:
    """Both K8s and Knative pods must have identical CPU allocation."""

    def test_k8s_and_knative_have_identical_cpu_request(self):
        k8s = _load_infra_yaml("workloads/test_app/test-app-warm-deployment.yaml")
        knative = _load_infra_yaml("workloads/test_app/knative-service.yaml")
        k8s_cpu = k8s["spec"]["template"]["spec"]["containers"][0]["resources"]["requests"]["cpu"]
        knative_cpu = knative["spec"]["template"]["spec"]["containers"][0]["resources"]["requests"]["cpu"]
        assert k8s_cpu == knative_cpu

    def test_k8s_and_knative_have_identical_cpu_limit(self):
        k8s = _load_infra_yaml("workloads/test_app/test-app-warm-deployment.yaml")
        knative = _load_infra_yaml("workloads/test_app/knative-service.yaml")
        k8s_cpu = k8s["spec"]["template"]["spec"]["containers"][0]["resources"]["limits"]["cpu"]
        knative_cpu = knative["spec"]["template"]["spec"]["containers"][0]["resources"]["limits"]["cpu"]
        assert k8s_cpu == knative_cpu

    def test_both_pods_use_200m_cpu(self):
        k8s = _load_infra_yaml("workloads/test_app/test-app-warm-deployment.yaml")
        knative = _load_infra_yaml("workloads/test_app/knative-service.yaml")
        k8s_cpu = k8s["spec"]["template"]["spec"]["containers"][0]["resources"]["requests"]["cpu"]
        knative_cpu = knative["spec"]["template"]["spec"]["containers"][0]["resources"]["requests"]["cpu"]
        # YAML may parse as int (200) or string ("200m")
        for label, val in [("k8s", k8s_cpu), ("knative", knative_cpu)]:
            assert val in (200, "200m"), f"{label} CPU request is {val}, expected 200 or 200m"


class TestNodeSelectorIsolation:
    """Both deployments must have nodeSelectors for scheduling isolation."""

    def test_k8s_deployment_targets_workload_nodes(self):
        deploy = _load_infra_yaml("workloads/test_app/test-app-warm-deployment.yaml")
        selector = deploy["spec"]["template"]["spec"].get("nodeSelector", {})
        assert selector.get("node-type") == "workload"

    def test_knative_service_targets_infra_nodes(self):
        svc = _load_infra_yaml("workloads/test_app/knative-service.yaml")
        selector = svc["spec"]["template"]["spec"].get("nodeSelector", {})
        assert selector.get("node-type") == "infra"
