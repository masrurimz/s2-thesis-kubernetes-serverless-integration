"""The scrape configuration and the credentials it needs.

Two things are pinned here: the configuration still names every job the exporter's
queries depend on, with an API endpoint to discover through (the reason the app and
kubelet series were empty for two months is that the jobs had no `api_server` and the
container was never given the credentials); and the credential renderer writes what the
container needs without writing readable key material on the host.
"""

import base64
import os
import stat
from pathlib import Path

import yaml
from infra.observability.prometheus.config import (
    CLUSTERS,
    CONTAINER_SECRETS_DIR,
    QUERIES,
    render_credentials,
)

CONFIG = Path(__file__).resolve().parents[3] / "libs/infra/infra/observability/prometheus/prometheus.yml"


def _kubeconfig() -> dict:
    return {
        "contexts": [
            {
                "name": "k3d-thesis-hybrid",
                "context": {"cluster": "k3d-thesis-hybrid", "user": "admin@k3d-thesis-hybrid"},
            },
            {
                "name": "k3d-thesis-serverless",
                "context": {"cluster": "k3d-thesis-serverless", "user": "admin@k3d-thesis-serverless"},
            },
            {"name": "other", "context": {"cluster": "unrelated-cluster", "user": "someone"}},
        ],
        "users": [
            {
                "name": "admin@k3d-thesis-hybrid",
                "user": {
                    "client-certificate-data": base64.b64encode(b"hybrid-cert").decode(),
                    "client-key-data": base64.b64encode(b"hybrid-key").decode(),
                },
            },
            {
                "name": "admin@k3d-thesis-serverless",
                "user": {
                    "client-certificate-data": base64.b64encode(b"serverless-cert").decode(),
                    "client-key-data": base64.b64encode(b"serverless-key").decode(),
                },
            },
            {"name": "someone", "user": {"token": "not-a-cert"}},
        ],
    }


class TestCredentialRendering:
    def test_each_mounted_cluster_gets_its_certificate_and_key(self, tmp_path):
        written = render_credentials(_kubeconfig(), tmp_path)

        assert {entry.cluster for entry in written} == set(CLUSTERS)
        hybrid = next(entry for entry in written if entry.cluster == "k3d-thesis-hybrid")
        assert hybrid.certificate.read_bytes() == b"hybrid-cert"
        assert hybrid.key.read_bytes() == b"hybrid-key"
        assert hybrid.api_server == CLUSTERS["k3d-thesis-hybrid"]

    def test_key_material_is_not_world_readable(self, tmp_path):
        render_credentials(_kubeconfig(), tmp_path)

        for name in ("thesis-hybrid.key", "thesis-hybrid.crt", "thesis-serverless.key"):
            mode = stat.S_IMODE((tmp_path / name).stat().st_mode)
            assert mode == 0o600, f"{name} is {oct(mode)}"

    def test_a_cluster_without_certificates_is_skipped(self, tmp_path):
        config = _kubeconfig()
        config["users"] = [entry for entry in config["users"] if entry["name"] == "someone"]

        assert render_credentials(config, tmp_path) == []

    def test_an_unrelated_cluster_is_ignored(self, tmp_path):
        written = render_credentials(_kubeconfig(), tmp_path)

        assert all("unrelated" not in entry.cluster for entry in written)

    def test_rendering_is_idempotent(self, tmp_path):
        first = render_credentials(_kubeconfig(), tmp_path)
        second = render_credentials(_kubeconfig(), tmp_path)

        assert [entry.certificate for entry in first] == [entry.certificate for entry in second]
        assert os.access(second[0].certificate, os.R_OK)


class TestScrapeConfiguration:
    """The jobs the exporter's queries depend on must exist and be able to discover."""

    def test_the_mounted_config_parses(self):
        config = yaml.safe_load(CONFIG.read_text())

        assert config["scrape_configs"]

    def test_the_application_and_kubelet_jobs_exist(self):
        jobs = {job["job_name"] for job in yaml.safe_load(CONFIG.read_text())["scrape_configs"]}

        assert {
            "kubernetes-pods-hybrid",
            "kubernetes-pods-serverless",
            "kubernetes-nodes-cadvisor-hybrid",
            "kubernetes-nodes-cadvisor-serverless",
        } <= jobs

    def test_every_kubernetes_job_names_an_api_endpoint(self):
        config = yaml.safe_load(CONFIG.read_text())

        for job in config["scrape_configs"]:
            for sd in job.get("kubernetes_sd_configs", []):
                assert sd.get("api_server", "").startswith("https://"), f"{job['job_name']} has no api_server"

    def test_the_credentials_live_under_the_container_path(self):
        body = CONFIG.read_text()

        assert body.count(CONTAINER_SECRETS_DIR) >= 8

    def test_the_pod_jobs_read_the_workload_namespace_only(self):
        config = yaml.safe_load(CONFIG.read_text())
        pod_jobs = [job for job in config["scrape_configs"] if job["job_name"] == "kubernetes-pods-hybrid"]

        relabels = pod_jobs[0]["relabel_configs"]
        namespace_keep = [
            rule
            for rule in relabels
            if rule.get("source_labels") == ["__meta_kubernetes_namespace"] and rule.get("action") == "keep"
        ]
        assert namespace_keep, "the pod job would scrape Knative's own pods"

    def test_the_pod_jobs_keep_only_annotated_pods(self):
        """The annotation is what makes a target exist; without the keep, every pod
        in the namespace would be scraped and most would answer 404."""
        config = yaml.safe_load(CONFIG.read_text())
        pod_jobs = [job for job in config["scrape_configs"] if job["job_name"].startswith("kubernetes-pods-")]

        assert len(pod_jobs) == 2
        for job in pod_jobs:
            keeps = [
                rule
                for rule in job["relabel_configs"]
                if rule.get("action") == "keep"
                and rule.get("source_labels") == ["__meta_kubernetes_pod_annotation_prometheus_io_scrape"]
            ]
            assert keeps, f"{job['job_name']} does not filter on the scrape annotation"

    def test_the_queries_the_exporter_runs_are_the_ones_this_config_feeds(self):
        """A mismatch here is the original bug: queries for series nothing scrapes.

        The metric names come from the scrape targets' own exposition, which the live
        check ('thesis infra monitoring --verify') confirms; this pins the two the
        config is responsible for: the app's HTTP counters and the container metrics.
        """
        assert "http_requests_total" in QUERIES["prom_rps"]
        assert "http_request_duration_seconds_bucket" in QUERIES["prom_p99_ms"]
        assert "container_cpu_usage_seconds_total" in QUERIES["cpu_usage_cores"]
        assert "container_memory_working_set_bytes" in QUERIES["memory_usage_bytes"]
