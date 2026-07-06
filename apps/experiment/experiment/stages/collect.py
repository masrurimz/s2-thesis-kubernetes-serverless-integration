"""Collect stage: export Prometheus metrics and poll resources during runs.

Extracted from scripts/run_phase_b_experiments.py lines 940-1317
(MetricExporter + ResourcePoller).
"""

import os
import json
import subprocess
import threading
import time
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import structlog

from shared.config import settings
from shared.models.metrics import MetricsExport
from shared.models.pipeline import PipelineContext

from experiment.stages.base import BaseStage

logger = structlog.get_logger(__name__)

# Tool paths
KUBECTL_PATH = os.environ.get(
    "KUBECTL_PATH",
    str(Path.home() / ".local/share/mise/installs/kubectl/1.35.0/kubectl"),
)

# Infrastructure constants
NAMESPACE = "default"
DEPLOYMENT = "test-app-warm"
K8S_DEPLOYMENT_FILTER = f'deployment="{DEPLOYMENT}",namespace="{NAMESPACE}"'
SERVERLESS_CONTEXT = os.environ.get("K3D_SERVERLESS_CONTEXT", "k3d-thesis-serverless")


def _run_cmd(cmd: List[str], timeout: int = 30, **kwargs: Any) -> subprocess.CompletedProcess:
    """Run a command with timeout."""
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, **kwargs)


# ---------------------------------------------------------------------------
# MetricExporter
# ---------------------------------------------------------------------------


class MetricExporter:
    """Export time-series metrics from Prometheus for a run window.

    Uses infra.prometheus.PrometheusClient for queries.
    """

    QUERIES = {
        # Performance (corroboration)
        "prom_p99_ms": "histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket[1m])) by (le)) * 1000",
        "prom_rps": "sum(rate(http_requests_total[1m]))",
        # Routing daemon
        "daemon_decisions": "routing_daemon_decision_total",
        "daemon_weight_k3s": 'routing_daemon_current_weight{backend="k3s"}',
        "daemon_weight_knative": 'routing_daemon_current_weight{backend="knative"}',
        "daemon_predictions_used": "routing_daemon_prediction_used_total",
        "daemon_predictions_failed": "routing_daemon_prediction_failed_total",
        # Algorithm 2 replica scaling
        "k8s_desired_replicas": "k8s_deployment_desired_replicas",
        "k8s_available_replicas": "k8s_deployment_available_replicas",
        "k8s_scale_up_success": 'k8s_scaling_events_total{direction="up",result="success"}',
        "k8s_scale_up_fail": 'k8s_scaling_events_total{direction="up",result="fail"}',
        "k8s_scale_down_success": 'k8s_scaling_events_total{direction="down",result="success"}',
        "k8s_scale_down_fail": 'k8s_scaling_events_total{direction="down",result="fail"}',
        # Control-loop metrics (Table 3-5)
        "daemon_decision_latency_ms": "routing_daemon_decision_latency_ms_sum / routing_daemon_decision_latency_ms_count",
        # Resource metrics (Table 3-7)
        "cpu_usage_cores": 'sum(rate(container_cpu_usage_seconds_total{namespace="default",container="test-app-warm"}[1m]))',
        "memory_usage_bytes": 'sum(container_memory_working_set_bytes{namespace="default",container="test-app-warm"})',
        # Node provisioning metrics (v4)
        "node_count_schedulable": "count(kube_node_spec_unschedulable == 0)",
        "pods_pending_count": 'count(kube_pod_status_phase{phase="Pending",namespace="default"})',
    }

    def __init__(self, prometheus_url: Optional[str] = None):
        from infra.observability.prometheus import PrometheusClient

        self._client = PrometheusClient(prometheus_url or settings.PROMETHEUS_URL)

    def export_run(self, t_start: float, t_end: float, output_dir: Path) -> Dict[str, Any]:
        """Export all metrics for [t_start, t_end] window. Returns summary dict."""
        output_dir.mkdir(parents=True, exist_ok=True)
        series: Dict[str, List[Tuple[float, float]]] = {}

        for name, expr in self.QUERIES.items():
            # PrometheusClient.query_range takes int timestamps
            ts = self._client.query_range(expr, int(t_start), int(t_end), step=15)
            series[name] = [(float(t), v) for t, v in ts]

        # Save raw time-series
        export_path = output_dir / "prometheus_export.json"
        with open(export_path, "w") as f:
            json.dump({k: [(t, v) for t, v in vs] for k, vs in series.items()}, f, indent=2)

        # Derive summary values
        summary = self._summarize(series, t_start, t_end)
        summary["export_path"] = str(export_path)
        return summary

    def _summarize(self, series: Dict, t_start: float, t_end: float) -> Dict[str, Any]:
        """Derive scalar summary from time-series."""
        duration_sec = max(1, int(t_end - t_start))

        def _last_val(key: str) -> float:
            ts = series.get(key, [])
            return ts[-1][1] if ts else 0.0

        def _mean_val(key: str) -> float:
            ts = series.get(key, [])
            vals = [v for _, v in ts if np.isfinite(v)]
            return float(np.mean(vals)) if vals else 0.0

        def _counter_delta(key: str) -> float:
            ts = series.get(key, [])
            if len(ts) < 2:
                return 0.0
            return max(0, ts[-1][1] - ts[0][1])

        # Weight time products (integral via trapezoidal)
        k3s_wt = self._weight_time_integral(series.get("daemon_weight_k3s", []))
        kn_wt = self._weight_time_integral(series.get("daemon_weight_knative", []))

        # Time in serverless = fraction of time knative weight > 0
        kn_series = series.get("daemon_weight_knative", [])
        time_in_serverless = sum(1 for _, v in kn_series if v > 0) / max(1, len(kn_series))

        # Weight change count
        k3s_ts = series.get("daemon_weight_k3s", [])
        weight_changes = sum(1 for i in range(1, len(k3s_ts)) if k3s_ts[i][1] != k3s_ts[i - 1][1])

        # k8s_replica_seconds: trapezoidal integral of desired replicas × time
        k8s_replica_seconds = self._weight_time_integral(series.get("k8s_desired_replicas", []))

        # knative_active_seconds: sum of time intervals where knative weight > 0
        knative_active_seconds = 0.0
        for i in range(1, len(kn_series)):
            if kn_series[i][1] > 0 or kn_series[i - 1][1] > 0:
                knative_active_seconds += kn_series[i][0] - kn_series[i - 1][0]

        # Oscillation index: direction changes in desired_replicas series
        desired_ts = series.get("k8s_desired_replicas", [])
        oscillations = 0
        for i in range(2, len(desired_ts)):
            prev_dir = desired_ts[i - 1][1] - desired_ts[i - 2][1]
            curr_dir = desired_ts[i][1] - desired_ts[i - 1][1]
            if (prev_dir > 0 and curr_dir < 0) or (prev_dir < 0 and curr_dir > 0):
                oscillations += 1

        # Scale-up latency: time from first scale-up event to ready replicas matching desired
        avail_ts = series.get("k8s_available_replicas", [])
        scale_up_latency = 0.0
        if desired_ts and avail_ts:
            initial_desired = desired_ts[0][1] if desired_ts else 0
            first_scale_up_t = next((t for t, v in desired_ts if v > initial_desired), None)
            if first_scale_up_t is not None:
                target_at_scale = next((v for t, v in desired_ts if t >= first_scale_up_t), initial_desired)
                ready_t = next((t for t, v in avail_ts if t >= first_scale_up_t and v >= target_at_scale), None)
                if ready_t is not None:
                    scale_up_latency = ready_t - first_scale_up_t

        return {
            "duration_sec": duration_sec,
            "prom_p99_ms": _mean_val("prom_p99_ms"),
            "scale_up_success": int(_counter_delta("k8s_scale_up_success")),
            "scale_down_success": int(_counter_delta("k8s_scale_down_success")),
            "scale_up_fail": int(_counter_delta("k8s_scale_up_fail")),
            "scale_down_fail": int(_counter_delta("k8s_scale_down_fail")),
            "desired_replicas_final": int(_last_val("k8s_desired_replicas")),
            "available_replicas_final": int(_last_val("k8s_available_replicas")),
            "predictions_used": int(_counter_delta("daemon_predictions_used")),
            "predictions_failed": int(_counter_delta("daemon_predictions_failed")),
            "k8s_weight_time": k3s_wt,
            "kn_weight_time": kn_wt,
            "time_in_serverless_pct": time_in_serverless * 100,
            "weight_change_count": weight_changes,
            "daemon_decision_latency_avg_ms": _mean_val("daemon_decision_latency_ms"),
            "cpu_usage_avg_cores": _mean_val("cpu_usage_cores"),
            "memory_usage_avg_bytes": _mean_val("memory_usage_bytes"),
            "k8s_replica_seconds": k8s_replica_seconds,
            "knative_active_seconds": knative_active_seconds,
            "oscillation_index": oscillations,
            "scale_up_latency_sec": scale_up_latency,
        }

    @staticmethod
    def _weight_time_integral(ts: List[Tuple[float, float]]) -> float:
        """Trapezoidal integration of weight × time."""
        if len(ts) < 2:
            return 0.0
        total = 0.0
        for i in range(1, len(ts)):
            dt = ts[i][0] - ts[i - 1][0]
            avg_w = (ts[i][1] + ts[i - 1][1]) / 2
            total += avg_w * dt
        return total


# ---------------------------------------------------------------------------
# ResourcePoller
# ---------------------------------------------------------------------------


class ResourcePoller:
    """Poll kubectl metrics-server API for per-pod CPU/memory during experiment runs."""

    def __init__(self, poll_interval_sec: int = 15):
        self._poll_interval = poll_interval_sec
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._node_samples: List[Dict[str, Any]] = []
        self._lock = threading.Lock()

    @staticmethod
    def _parse_cpu(value: str) -> float:
        """Parse Kubernetes CPU string to millicores."""
        try:
            if value.endswith("n"):
                return int(value[:-1]) / 1_000_000
            if value.endswith("u"):
                return int(value[:-1]) / 1000
            if value.endswith("m"):
                return int(value[:-1])
            return float(value) * 1000
        except (ValueError, IndexError):
            return 0.0

    @staticmethod
    def _parse_memory(value: str) -> float:
        """Parse Kubernetes memory string to MiB."""
        if value.endswith("Ki"):
            return int(value[:-2]) / 1024
        if value.endswith("Mi"):
            return int(value[:-2])
        if value.endswith("Gi"):
            return int(value[:-2]) * 1024
        return int(value) / (1024 * 1024)

    def _poll_once(self) -> None:
        """Single poll of metrics-server API via kubectl."""
        self._poll_pods()
        self._poll_serverless_pods()
        self._poll_nodes()

    def _poll_pods(self) -> None:
        """Poll per-pod CPU/memory from metrics-server."""
        try:
            r = _run_cmd(
                [KUBECTL_PATH, "get", "--raw", "/apis/metrics.k8s.io/v1beta1/namespaces/default/pods"],
                timeout=10,
            )
            if r.returncode != 0:
                return
            data = json.loads(r.stdout)
            ts = time.time()
            for item in data.get("items", []):
                labels = item.get("metadata", {}).get("labels", {})
                pod_name = item.get("metadata", {}).get("name", "")
                is_k8s = labels.get("app") == "test-app-warm"
                is_knative = "serving.knative.dev/service" in labels
                if not (is_k8s or is_knative):
                    continue
                for container in item.get("containers", []):
                    cpu_str = container.get("usage", {}).get("cpu", "0n")
                    mem_str = container.get("usage", {}).get("memory", "0Ki")
                    sample = {
                        "timestamp": ts,
                        "pod": pod_name,
                        "backend": "k8s" if is_k8s else "knative",
                        "cpu_millicores": self._parse_cpu(cpu_str),
                        "memory_mib": self._parse_memory(mem_str),
                    }
                    with self._lock:
                        self._samples.append(sample)
        except Exception as e:
            logger.debug("resource_poll_failed", error=str(e))

    def _poll_serverless_pods(self) -> None:
        """Poll Knative pod CPU/memory from thesis-serverless cluster."""
        try:
            r = _run_cmd(
                [
                    KUBECTL_PATH,
                    "--context",
                    SERVERLESS_CONTEXT,
                    "get",
                    "--raw",
                    "/apis/metrics.k8s.io/v1beta1/namespaces/default/pods",
                ],
                timeout=10,
            )
            if r.returncode != 0:
                return
            data = json.loads(r.stdout)
            ts = time.time()
            for item in data.get("items", []):
                labels = item.get("metadata", {}).get("labels", {})
                if "serving.knative.dev/service" not in labels:
                    continue
                pod_name = item.get("metadata", {}).get("name", "")
                for container in item.get("containers", []):
                    cpu_str = container.get("usage", {}).get("cpu", "0n")
                    mem_str = container.get("usage", {}).get("memory", "0Ki")
                    sample = {
                        "timestamp": ts,
                        "pod": pod_name,
                        "backend": "knative",
                        "cpu_millicores": self._parse_cpu(cpu_str),
                        "memory_mib": self._parse_memory(mem_str),
                    }
                    with self._lock:
                        self._samples.append(sample)
        except Exception as e:
            logger.debug("serverless_resource_poll_failed", error=str(e))

    def _poll_nodes(self) -> None:
        """Poll per-node CPU/memory utilization via kubectl top nodes."""
        try:
            r = _run_cmd(
                [KUBECTL_PATH, "top", "nodes", "--no-headers"],
                timeout=10,
            )
            if r.returncode != 0:
                return
            ts = time.time()
            for line in r.stdout.strip().splitlines():
                parts = line.split()
                if len(parts) < 5:
                    continue
                node_name = parts[0]
                cpu_cores = self._parse_cpu(parts[1]) / 1000  # millicores → cores
                cpu_pct = float(parts[2].rstrip("%"))
                mem_mib = self._parse_memory(parts[3])
                mem_pct = float(parts[4].rstrip("%"))
                with self._lock:
                    self._node_samples.append(
                        {
                            "timestamp": ts,
                            "node": node_name,
                            "cpu_cores": cpu_cores,
                            "cpu_pct": cpu_pct,
                            "memory_mib": mem_mib,
                            "memory_pct": mem_pct,
                        }
                    )
        except Exception as e:
            logger.debug("node_poll_failed", error=str(e))

    def _poll_loop(self) -> None:
        """Background polling loop."""
        while not self._stop_event.is_set():
            self._poll_once()
            self._stop_event.wait(self._poll_interval)

    def start(self) -> None:
        with self._lock:
            self._samples = []
            self._node_samples = []
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop background polling thread."""
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=5)
            self._thread = None

    def get_summary(self, output_dir: Path) -> Dict[str, float | str]:
        """Compute avg/peak CPU and memory, save raw samples to JSON."""
        with self._lock:
            samples = list(self._samples)

        output_dir.mkdir(parents=True, exist_ok=True)
        save_path = output_dir / "resource_utilization.json"
        with open(save_path, "w") as f:
            json.dump(samples, f, indent=2)

        if not samples:
            return {
                "avg_cpu_millicores": 0.0,
                "peak_cpu_millicores": 0.0,
                "avg_memory_mib": 0.0,
                "peak_memory_mib": 0.0,
                "resource_utilization_path": str(save_path),
            }

        # Aggregate per-timestamp (sum across pods), then compute avg/peak
        ts_cpu: Dict[float, float] = defaultdict(float)
        ts_mem: Dict[float, float] = defaultdict(float)
        for s in samples:
            ts_cpu[s["timestamp"]] += s["cpu_millicores"]
            ts_mem[s["timestamp"]] += s["memory_mib"]

        cpu_vals = list(ts_cpu.values())
        mem_vals = list(ts_mem.values())

        return {
            "avg_cpu_millicores": float(np.mean(cpu_vals)),
            "peak_cpu_millicores": float(max(cpu_vals)),
            "avg_memory_mib": float(np.mean(mem_vals)),
            "peak_memory_mib": float(max(mem_vals)),
            "resource_utilization_path": str(save_path),
        }

    def get_node_summary(self, output_dir: Path) -> Dict[str, Any]:
        """Compute cluster-level utilization from node polls, save to JSON.

        Excludes control-plane nodes (node role contains 'control-plane' or 'master')
        to report only workload-bearing node utilization.
        """
        with self._lock:
            node_samples = list(self._node_samples)

        if output_dir:
            output_dir.mkdir(parents=True, exist_ok=True)
            save_path = output_dir / "node_utilization.json"
            with open(save_path, "w") as f:
                json.dump(node_samples if node_samples else [], f, indent=2)

        if not node_samples:
            return {
                "avg_cluster_cpu_pct": 0.0,
                "peak_cluster_cpu_pct": 0.0,
                "avg_cluster_mem_pct": 0.0,
                "avg_pod_density": 0.0,
                "node_utilization_path": str(output_dir / "node_utilization.json") if output_dir else "",
            }

        # Exclude control-plane nodes
        workload_nodes = [s for s in node_samples if "server" not in s["node"].lower()]
        if not workload_nodes:
            workload_nodes = node_samples

        cpu_pcts = [s["cpu_pct"] for s in workload_nodes]
        mem_pcts = [s["memory_pct"] for s in workload_nodes]

        # Pod density: count unique workload nodes, then estimate pods per node
        # from total pod samples / total node samples ratio
        unique_nodes = set(s["node"] for s in workload_nodes)
        with self._lock:
            pod_count = len(self._samples)
        node_poll_count = len(workload_nodes) / max(1, len(unique_nodes))
        avg_pod_density = (
            pod_count / max(1, len(unique_nodes) / max(1, node_poll_count)) if node_poll_count > 0 else 0.0
        )

        return {
            "avg_cluster_cpu_pct": float(np.mean(cpu_pcts)),
            "peak_cluster_cpu_pct": float(max(cpu_pcts)),
            "avg_cluster_mem_pct": float(np.mean(mem_pcts)),
            "avg_pod_density": round(avg_pod_density, 1),
            "node_utilization_path": str(output_dir / "node_utilization.json") if output_dir else "",
        }


# ---------------------------------------------------------------------------
# CollectStage
# ---------------------------------------------------------------------------


class CollectStage(BaseStage):
    """Export Prometheus metrics and poll resources for a completed run window.

    Combines MetricExporter (Prometheus time-series) and ResourcePoller
    (kubectl metrics-server) into a single pipeline stage.
    """

    name = "collect"

    def __init__(self, prometheus_url: Optional[str] = None):
        self._exporter = MetricExporter(prometheus_url)
        self._resource_poller = ResourcePoller()

    def start_resource_polling(self) -> None:
        """Start background resource polling (call before workload)."""
        self._resource_poller.start()

    def stop_resource_polling(self) -> None:
        """Stop background resource polling."""
        self._resource_poller.stop()

    def _run(self, ctx: PipelineContext) -> None:
        """Export metrics for the run window [t_start, t_end].

        Expects ctx.result to have t_start and t_end set by the orchestrator.
        """
        run_dir = Path(ctx.output_dir) if ctx.output_dir else Path(".")
        prom_dir = run_dir / "prometheus"

        if ctx.result is None or ctx.result.t_start == 0:
            raise RuntimeError("CollectStage requires ctx.result with t_start/t_end")

        t_start = ctx.result.t_start
        t_end = ctx.result.t_end

        # Export Prometheus metrics
        prom_summary = self._exporter.export_run(t_start, t_end, prom_dir)

        # Collect resource utilization from poller
        resource_summary = self._resource_poller.get_summary(run_dir)

        # Collect node-level utilization
        node_summary = self._resource_poller.get_node_summary(run_dir)

        ctx.metrics = MetricsExport(
            p99_latency_ms=prom_summary.get("prom_p99_ms", 0.0),
        )

        # Store full summaries for downstream stages to read
        ctx.metrics.weight_timeline = []  # reset for downstream
        ctx.metrics.resource_samples = []  # reset for downstream

        # Attach raw summaries to the result for the report stage
        if ctx.result is not None:
            ctx.result.prom_p99_latency_ms = prom_summary.get("prom_p99_ms", 0)
            ctx.result.weight_change_count = prom_summary.get("weight_change_count", 0)
            ctx.result.time_in_serverless_pct = prom_summary.get("time_in_serverless_pct", 0)
            ctx.result.control_loop_latency_avg_ms = prom_summary.get("daemon_decision_latency_avg_ms", 0)
            ctx.result.scale_up_events = prom_summary.get("scale_up_success", 0) + prom_summary.get("scale_up_fail", 0)
            ctx.result.scale_down_events = prom_summary.get("scale_down_success", 0) + prom_summary.get(
                "scale_down_fail", 0
            )
            ctx.result.scale_up_success = prom_summary.get("scale_up_success", 0)
            ctx.result.scale_down_success = prom_summary.get("scale_down_success", 0)
            ctx.result.desired_replicas_final = prom_summary.get("desired_replicas_final", 0)
            ctx.result.available_replicas_final = prom_summary.get("available_replicas_final", 0)
            ctx.result.scale_up_latency_sec = prom_summary.get("scale_up_latency_sec", 0)
            ctx.result.oscillation_index = prom_summary.get("oscillation_index", 0)
            ctx.result.k8s_weight_time_product = prom_summary.get("k8s_weight_time", 0)
            ctx.result.serverless_weight_time_product = prom_summary.get("kn_weight_time", 0)
            ctx.result.k8s_replica_seconds = prom_summary.get("k8s_replica_seconds", 0)
            ctx.result.knative_active_seconds = prom_summary.get("knative_active_seconds", 0)
            ctx.result.gru_predictions_used = prom_summary.get("predictions_used", 0)
            ctx.result.gru_predictions_failed = prom_summary.get("predictions_failed", 0)
            ctx.result.avg_cpu_millicores = float(resource_summary.get("avg_cpu_millicores", 0))
            ctx.result.peak_cpu_millicores = float(resource_summary.get("peak_cpu_millicores", 0))
            ctx.result.avg_memory_mib = float(resource_summary.get("avg_memory_mib", 0))
            ctx.result.peak_memory_mib = float(resource_summary.get("peak_memory_mib", 0))
            ctx.result.avg_cluster_cpu_utilization_pct = float(node_summary.get("avg_cluster_cpu_pct", 0))
            ctx.result.peak_cluster_cpu_utilization_pct = float(node_summary.get("peak_cluster_cpu_pct", 0))
            ctx.result.avg_cluster_mem_utilization_pct = float(node_summary.get("avg_cluster_mem_pct", 0))
            ctx.result.avg_pod_density = float(node_summary.get("avg_pod_density", 0))
            ctx.result.resource_utilization_path = str(resource_summary.get("resource_utilization_path", ""))
            ctx.result.prom_export_path = prom_summary.get("export_path", "")
            ctx.result.replica_timeline_path = str(prom_dir / "prometheus_export.json")
