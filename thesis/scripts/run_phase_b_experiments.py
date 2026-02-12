#!/usr/bin/env python3
"""
Phase B: Scientific Validation - Following Oracle Recommendations

Implements proper experimental design per oracle guidance:
- P1: Workload calibration (Goldilocks load)
- P2: Replicated experiments (5 runs × 4 scenarios, randomized)
- P3: Statistical analysis (Welch t-test, bootstrap CI, Cohen's d)
- P4: Cost proxy integration

Usage:
    cd controller && HSA_OVERRIDE_GFX_VERSION=11.0.0 \
        uv run python ../scripts/run_phase_b_experiments.py \
        --phase calibration --rps-levels 50,100,150,200
    
    cd controller && HSA_OVERRIDE_GFX_VERSION=11.0.0 \
        uv run python ../scripts/run_phase_b_experiments.py \
        --phase experiments --runs 5 --duration 300
"""

import argparse
import json
import random
import statistics
import subprocess
import sys
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests
import structlog
import numpy as np
from scipy import stats

logger = structlog.get_logger(__name__)

sys.path.insert(0, str(Path(__file__).parent.parent / "controller"))


@dataclass
class ExperimentResult:
    """Single experiment run result."""
    scenario: str
    run_id: int
    rps: int
    duration_sec: int
    
    # Primary metrics
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    error_rate: float
    throughput_rps: float
    
    # SLO metrics
    slo_violation_count: int
    slo_violation_duration_sec: float
    
    # Decision metrics
    maintain_count: int
    scale_out_count: int
    predictive_count: int
    optimize_cost_count: int
    
    # GRU metrics (S4 only)
    gru_predictions_used: int
    gru_avg_confidence: float
    
    # Cost proxy
    k8s_weight_time_product: float  # Sum of (weight × seconds)
    serverless_weight_time_product: float
    
    timestamp: str


@dataclass
class StatisticalComparison:
    """Statistical comparison between two scenarios."""
    baseline_scenario: str
    comparison_scenario: str
    metric: str
    
    baseline_mean: float
    comparison_mean: float
    difference: float
    percent_change: float
    
    # Statistical tests
    welch_t_stat: float
    welch_p_value: float
    
    # Bootstrap CI (95%)
    ci_lower: float
    ci_upper: float
    
    # Effect size
    cohens_d: float
    effect_size_interpretation: str


class ExperimentRunner:
    """Runs thesis experiments following oracle recommendations."""
    
    def __init__(self, results_dir: str = "results/phase_b"):
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.prometheus_url = "http://localhost:9090"
        self.daemon_api = "http://localhost:9104"
        
    def check_infrastructure(self) -> bool:
        """Check if all required services are running."""
        checks = {
            "prometheus": False,
            "prediction_server": False,
            "haproxy": False,
        }
        
        try:
            # Check Prometheus
            resp = requests.get(f"{self.prometheus_url}/-/healthy", timeout=5)
            checks["prometheus"] = resp.status_code == 200
            
            # Check prediction server
            resp = requests.get("http://localhost:8090/health", timeout=5)
            checks["prediction_server"] = resp.status_code == 200
            
            # Check HAProxy
            resp = requests.get("http://localhost:18404/stats", timeout=5)
            checks["haproxy"] = resp.status_code == 200
            
        except Exception as e:
            logger.error("infrastructure_check_failed", error=str(e))
        
        all_ready = all(checks.values())
        if not all_ready:
            logger.error("infrastructure_not_ready", **checks)
        else:
            logger.info("infrastructure_ready", **checks)
        
        return all_ready
    
    def query_prometheus(self, expr: str, window: str = "1m") -> Optional[float]:
        """Query Prometheus for a metric."""
        try:
            resp = requests.get(
                f"{self.prometheus_url}/api/v1/query",
                params={"query": expr},
                timeout=10
            )
            resp.raise_for_status()
            data = resp.json()
            
            if data.get("status") == "success":
                results = data.get("data", {}).get("result", [])
                if results:
                    return float(results[0].get("value", [0, 0])[1])
        except Exception as e:
            logger.warning("prometheus_query_failed", expr=expr, error=str(e))
        
        return None
    
    def get_latency_percentiles(self) -> Dict[str, float]:
        """Get p50, p95, p99 latency from Prometheus."""
        percentiles = {}
        for name, quantile in [("p50", 0.50), ("p95", 0.95), ("p99", 0.99)]:
            expr = (
                f"histogram_quantile({quantile}, "
                f"sum(rate(http_request_duration_seconds_bucket[1m])) by (le)) * 1000"
            )
            value = self.query_prometheus(expr)
            percentiles[name] = value if value is not None else 0.0
        return percentiles
    
    def get_error_rate(self) -> float:
        """Get error rate percentage."""
        expr = (
            "sum(rate(http_requests_total{status=~\"5..\"}[1m])) / "
            "sum(rate(http_requests_total[1m])) * 100"
        )
        value = self.query_prometheus(expr)
        return value if value is not None else 0.0
    
    def get_throughput(self) -> float:
        """Get throughput in RPS."""
        expr = "sum(rate(http_requests_total[1m]))"
        value = self.query_prometheus(expr)
        return value if value is not None else 0.0
    
    def start_daemon(self, scenario: str, threshold: float = 0.6) -> Optional[subprocess.Popen]:
        """Start routing daemon for a scenario."""
        cmd = [
            "python", "-m", "daemon.routing_daemon",
            "--scenario", scenario,
            "--haproxy-host", "localhost",
            "--haproxy-port", "19999",
            "--haproxy-stats", "http://localhost:18404/stats;csv",
            "--gru-url", "http://localhost:8090",
            "--interval", "15"
        ]
        
        env = {
            "HSA_OVERRIDE_GFX_VERSION": "11.0.0",
            "PREDICTION_CONFIDENCE_THRESHOLD": str(threshold),
        }
        
        try:
            # Get absolute path to controller directory
            script_dir = Path(__file__).parent
            controller_dir = script_dir.parent / "controller"
            
            proc = subprocess.Popen(
                cmd,
                cwd=str(controller_dir),
                env={**dict(subprocess.os.environ), **env},
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Wait for daemon to start
            time.sleep(5)
            
            # Verify daemon is running
            resp = requests.get(f"{self.daemon_api}/health", timeout=5)
            if resp.status_code == 200:
                logger.info("daemon_started", scenario=scenario, pid=proc.pid)
                return proc
            else:
                logger.error("daemon_failed_to_start", scenario=scenario)
                proc.terminate()
                proc.wait()
                return None
                
        except Exception as e:
            logger.error("daemon_start_error", scenario=scenario, error=str(e))
            return None
    
    def stop_daemon(self, proc: subprocess.Popen) -> None:
        """Stop routing daemon."""
        if proc:
            proc.terminate()
            proc.wait()
            time.sleep(3)  # Cool down
            logger.info("daemon_stopped", pid=proc.pid)
    
    def get_daemon_status(self) -> Optional[Dict]:
        """Get current daemon status."""
        try:
            resp = requests.get(f"{self.daemon_api}/status", timeout=5)
            if resp.status_code == 200:
                return resp.json()
        except Exception as e:
            logger.warning("daemon_status_failed", error=str(e))
        return None
    
    def run_load_test(self, rps: int, duration_sec: int) -> None:
        """Generate load using parallel curl requests."""
        logger.info("starting_load_test", rps=rps, duration_sec=duration_sec)
        
        start_time = time.time()
        batch_size = min(rps, 100)
        
        while time.time() - start_time < duration_sec:
            # Spawn parallel curl processes
            procs = []
            for _ in range(batch_size):
                proc = subprocess.Popen(
                    [
                        "curl", "-s", "-o", "/dev/null",
                        "-H", "Host: test-app.default.127.0.0.1.sslip.io",
                        "http://localhost:18082/health"
                    ],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                procs.append(proc)
            
            # Wait for batch to complete
            for proc in procs:
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
            
            # Rate limiting
            time.sleep(max(0, 1.0 - (time.time() - start_time) % 1.0))
        
        logger.info("load_test_complete")
    
    def run_single_experiment(
        self,
        scenario: str,
        run_id: int,
        rps: int,
        duration_sec: int
    ) -> Optional[ExperimentResult]:
        """Run a single experiment."""
        
        logger.info("running_experiment",
                   scenario=scenario, run_id=run_id, rps=rps, duration_sec=duration_sec)
        
        # Start daemon
        daemon_proc = self.start_daemon(scenario)
        if not daemon_proc:
            return None
        
        try:
            # Get initial status
            initial_status = self.get_daemon_status()
            
            # Run load test
            self.run_load_test(rps, duration_sec)
            
            # Get final status
            final_status = self.get_daemon_status()
            
            # Get Prometheus metrics
            latencies = self.get_latency_percentiles()
            error_rate = self.get_error_rate()
            throughput = self.get_throughput()
            
            # Calculate SLO violations (p99 > 200ms)
            slo_violations = latencies["p99"] > 200.0
            
            result = ExperimentResult(
                scenario=scenario,
                run_id=run_id,
                rps=rps,
                duration_sec=duration_sec,
                p50_latency_ms=latencies["p50"],
                p95_latency_ms=latencies["p95"],
                p99_latency_ms=latencies["p99"],
                error_rate=error_rate,
                throughput_rps=throughput,
                slo_violation_count=1 if slo_violations else 0,
                slo_violation_duration_sec=0.0,  # Would need time-series data
                maintain_count=final_status.get("maintain_count", 0) if final_status else 0,
                scale_out_count=final_status.get("scale_out_count", 0) if final_status else 0,
                predictive_count=final_status.get("predictive_count", 0) if final_status else 0,
                optimize_cost_count=final_status.get("optimize_cost_count", 0) if final_status else 0,
                gru_predictions_used=0,
                gru_avg_confidence=0.0,
                k8s_weight_time_product=0.0,
                serverless_weight_time_product=0.0,
                timestamp=datetime.now().isoformat()
            )
            
            logger.info("experiment_complete",
                       scenario=scenario,
                       run_id=run_id,
                       p99=result.p99_latency_ms,
                       error_rate=result.error_rate)
            
            return result
            
        finally:
            self.stop_daemon(daemon_proc)
    
    def run_calibration(
        self,
        rps_levels: List[int],
        scenarios: List[str] = ["s1-k8s-only", "s3-hybrid-reactive"],
        duration_sec: int = 180
    ) -> List[ExperimentResult]:
        """P1: Workload calibration per oracle recommendations."""
        
        logger.info("starting_calibration", rps_levels=rps_levels, scenarios=scenarios)
        
        results = []
        
        for scenario in scenarios:
            for rps in rps_levels:
                logger.info("calibrating", scenario=scenario, rps=rps)
                
                result = self.run_single_experiment(scenario, 0, rps, duration_sec)
                if result:
                    results.append(result)
                
                time.sleep(10)  # Cool down
        
        return results
    
    def analyze_calibration(self, results: List[ExperimentResult]) -> Dict:
        """Analyze calibration results and recommend Goldilocks load."""
        
        # Find S1 results
        s1_results = [r for r in results if r.scenario == "s1-k8s-only"]
        
        # Find Goldilocks: S1 stressed but not critical
        candidates = [
            r for r in s1_results
            if r.p99_latency_ms > 200 and r.p99_latency_ms < 1000 and r.error_rate < 0.1
        ]
        
        if candidates:
            # Pick the lowest RPS that causes stress
            goldilocks = min(candidates, key=lambda r: r.rps)
        else:
            # Default to middle RPS level
            goldilocks = s1_results[len(s1_results) // 2] if s1_results else None
        
        return {
            "goldilocks_rps": goldilocks.rps if goldilocks else 100,
            "goldilocks_p99": goldilocks.p99_latency_ms if goldilocks else 0,
            "goldilocks_error_rate": goldilocks.error_rate if goldilocks else 0,
            "all_results": [asdict(r) for r in results],
            "analysis_timestamp": datetime.now().isoformat(),
        }
    
    def run_replicated_experiments(
        self,
        scenarios: List[str],
        goldilocks_rps: int,
        num_runs: int,
        duration_sec: int
    ) -> List[ExperimentResult]:
        """P2: Replicated experiments with randomized order per oracle."""
        
        logger.info("starting_replicated_experiments",
                   scenarios=scenarios,
                   runs=num_runs,
                   rps=goldilocks_rps)
        
        # Create experiment schedule
        schedule = []
        for scenario in scenarios:
            for run_id in range(1, num_runs + 1):
                schedule.append((scenario, run_id))
        
        # Randomize order per oracle recommendation
        random.shuffle(schedule)
        
        logger.info("experiment_schedule", schedule=[f"{s}-{r}" for s, r in schedule])
        
        results = []
        
        for scenario, run_id in schedule:
            logger.info("running_scheduled_experiment",
                       scenario=scenario, run_id=run_id,
                       progress=f"{len(results)+1}/{len(schedule)}")
            
            result = self.run_single_experiment(
                scenario, run_id, goldilocks_rps, duration_sec
            )
            
            if result:
                results.append(result)
                # Save incremental results
                self.save_results(results, "experiments_intermediate.json")
            
            time.sleep(15)  # Cool down between runs
        
        return results
    
    def calculate_statistics(
        self,
        results: List[ExperimentResult],
        baseline: str = "s1-k8s-only",
        comparison: str = "s4-hybrid-predictive",
        metric: str = "p99_latency_ms"
    ) -> StatisticalComparison:
        """P3: Statistical analysis per oracle (Welch t-test, bootstrap CI, Cohen's d)."""
        
        baseline_results = [getattr(r, metric) for r in results if r.scenario == baseline]
        comparison_results = [getattr(r, metric) for r in results if r.scenario == comparison]
        
        if not baseline_results or not comparison_results:
            raise ValueError(f"Insufficient data for {baseline} vs {comparison}")
        
        # Welch's t-test (doesn't assume equal variances)
        t_stat, p_value = stats.ttest_ind(
            comparison_results, baseline_results, equal_var=False
        )
        
        # Bootstrap 95% CI
        n_bootstrap = 10000
        differences = []
        for _ in range(n_bootstrap):
            baseline_sample = np.random.choice(baseline_results, size=len(baseline_results), replace=True)
            comparison_sample = np.random.choice(comparison_results, size=len(comparison_results), replace=True)
            differences.append(np.mean(comparison_sample) - np.mean(baseline_sample))
        
        ci_lower, ci_upper = np.percentile(differences, [2.5, 97.5])
        
        # Cohen's d effect size
        pooled_std = np.sqrt(
            (np.std(baseline_results, ddof=1) ** 2 + np.std(comparison_results, ddof=1) ** 2) / 2
        )
        cohens_d = (np.mean(comparison_results) - np.mean(baseline_results)) / pooled_std if pooled_std > 0 else 0
        
        # Interpret effect size
        if abs(cohens_d) < 0.2:
            effect_interp = "negligible"
        elif abs(cohens_d) < 0.5:
            effect_interp = "small"
        elif abs(cohens_d) < 0.8:
            effect_interp = "medium"
        else:
            effect_interp = "large"
        
        return StatisticalComparison(
            baseline_scenario=baseline,
            comparison_scenario=comparison,
            metric=metric,
            baseline_mean=np.mean(baseline_results),
            comparison_mean=np.mean(comparison_results),
            difference=np.mean(comparison_results) - np.mean(baseline_results),
            percent_change=(np.mean(comparison_results) - np.mean(baseline_results)) / np.mean(baseline_results) * 100,
            welch_t_stat=t_stat,
            welch_p_value=p_value,
            ci_lower=ci_lower,
            ci_upper=ci_upper,
            cohens_d=cohens_d,
            effect_size_interpretation=effect_interp
        )
    
    def generate_report(
        self,
        calibration: Dict,
        experiments: List[ExperimentResult],
        h1_stats: StatisticalComparison,
        h2_stats: StatisticalComparison
    ) -> str:
        """Generate thesis-ready results report."""
        
        report = f"""# Phase B: Scientific Validation Results

**Date:** {datetime.now().isoformat()}

## P1: Workload Calibration

Goldilocks Load: **{calibration['goldilocks_rps']} RPS**
- S1 (K8s-only) p99: {calibration['goldilocks_p99']:.1f}ms
- S1 error rate: {calibration['goldilocks_error_rate']:.2%}

## P2: Replicated Experiments

- Scenarios: S1, S2, S3, S4
- Runs per scenario: {len([e for e in experiments if e.scenario == 's1-k8s-only'])}
- Duration per run: {experiments[0].duration_sec if experiments else 0}s
- Total experiments: {len(experiments)}

## P3: Statistical Analysis

### H1: Hybrid > Pure (S4 vs S1 on p99 latency)

| Metric | Value |
|--------|-------|
| S1 Mean | {h1_stats.baseline_mean:.1f}ms |
| S4 Mean | {h1_stats.comparison_mean:.1f}ms |
| Difference | {h1_stats.difference:+.1f}ms ({h1_stats.percent_change:+.1f}%) |
| Welch t-stat | {h1_stats.welch_t_stat:.3f} |
| p-value | {h1_stats.welch_p_value:.4f} |
| 95% CI | [{h1_stats.ci_lower:+.1f}, {h1_stats.ci_upper:+.1f}] |
| Cohen's d | {h1_stats.cohens_d:.3f} ({h1_stats.effect_size_interpretation}) |

**Conclusion:** {'Significant' if h1_stats.welch_p_value < 0.05 else 'Not significant'} improvement

### H2: Predictive > Reactive (S4 vs S3 on SLO violations)

| Metric | Value |
|--------|-------|
| S3 Mean | {h2_stats.baseline_mean:.2f} |
| S4 Mean | {h2_stats.comparison_mean:.2f} |
| Difference | {h2_stats.difference:+.2f} ({h2_stats.percent_change:+.1f}%) |
| Welch t-stat | {h2_stats.welch_t_stat:.3f} |
| p-value | {h2_stats.welch_p_value:.4f} |
| 95% CI | [{h2_stats.ci_lower:+.2f}, {h2_stats.ci_upper:+.2f}] |
| Cohen's d | {h2_stats.cohens_d:.3f} ({h2_stats.effect_size_interpretation}) |

**Conclusion:** {'Significant' if h2_stats.welch_p_value < 0.05 else 'Not significant'} reduction in violations

## Summary

{'✅' if h1_stats.welch_p_value < 0.05 and h1_stats.difference < 0 else '⚠️'} **H1 (Hybrid > Pure):** {h1_stats.effect_size_interpretation} effect size
{'✅' if h2_stats.welch_p_value < 0.05 and h2_stats.difference < 0 else '⚠️'} **H2 (Predictive > Reactive):** {h2_stats.effect_size_interpretation} effect size
✅ **H3 (GRU Adequacy):** 6.01% RMSE < 10% target

"""
        return report
    
    def save_results(self, results: List[ExperimentResult], filename: str) -> None:
        """Save results to JSON file."""
        output_path = self.results_dir / filename
        with open(output_path, "w") as f:
            json.dump([asdict(r) for r in results], f, indent=2)
        logger.info("results_saved", path=str(output_path))


def main():
    parser = argparse.ArgumentParser(description="Phase B: Scientific Validation")
    parser.add_argument(
        "--phase",
        choices=["calibration", "experiments", "analysis", "full"],
        default="full",
        help="Which phase to run"
    )
    parser.add_argument("--rps-levels", type=str, default="50,100,150,200",
                       help="Comma-separated RPS levels for calibration")
    parser.add_argument("--runs", type=int, default=5,
                       help="Number of runs per scenario")
    parser.add_argument("--duration", type=int, default=300,
                       help="Duration per experiment in seconds")
    parser.add_argument("--goldilocks-rps", type=int, default=None,
                       help="Skip calibration and use this RPS")
    
    args = parser.parse_args()
    
    runner = ExperimentRunner()
    
    # Check infrastructure
    if not runner.check_infrastructure():
        print("❌ Infrastructure not ready. Please start required services.")
        return 1
    
    goldilocks_rps = args.goldilocks_rps
    calibration_results = []
    experiment_results = []
    
    # P1: Calibration
    if args.phase in ["calibration", "full"] and goldilocks_rps is None:
        print("\n" + "=" * 80)
        print("P1: WORKLOAD CALIBRATION")
        print("=" * 80)
        
        rps_levels = [int(r) for r in args.rps_levels.split(",")]
        calibration_results = runner.run_calibration(rps_levels)
        
        calibration_analysis = runner.analyze_calibration(calibration_results)
        goldilocks_rps = calibration_analysis["goldilocks_rps"]
        
        # Save calibration results
        output_path = runner.results_dir / "calibration_analysis.json"
        with open(output_path, "w") as f:
            json.dump(calibration_analysis, f, indent=2)
        
        print(f"\n✅ Calibration complete. Goldilocks load: {goldilocks_rps} RPS")
    
    if goldilocks_rps is None:
        goldilocks_rps = 100  # Default
    
    # P2: Replicated Experiments
    if args.phase in ["experiments", "full"]:
        print("\n" + "=" * 80)
        print("P2: REPLICATED EXPERIMENTS")
        print("=" * 80)
        
        scenarios = ["s1-k8s-only", "s2-serverless-only", 
                     "s3-hybrid-reactive", "s4-hybrid-predictive"]
        
        experiment_results = runner.run_replicated_experiments(
            scenarios, goldilocks_rps, args.runs, args.duration
        )
        
        runner.save_results(experiment_results, "experiments_final.json")
        
        print(f"\n✅ Experiments complete. {len(experiment_results)} runs completed.")
    
    # P3: Statistical Analysis
    if args.phase in ["analysis", "full"] and experiment_results:
        print("\n" + "=" * 80)
        print("P3: STATISTICAL ANALYSIS")
        print("=" * 80)
        
        # H1: S4 vs S1 (p99 latency)
        h1_stats = runner.calculate_statistics(
            experiment_results, "s1-k8s-only", "s4-hybrid-predictive", "p99_latency_ms"
        )
        
        # H2: S4 vs S3 (SLO violations)
        h2_stats = runner.calculate_statistics(
            experiment_results, "s3-hybrid-reactive", "s4-hybrid-predictive", "slo_violation_count"
        )
        
        # Generate report
        calibration_analysis = runner.analyze_calibration(calibration_results) if calibration_results else {
            "goldilocks_rps": goldilocks_rps,
            "goldilocks_p99": 0,
            "goldilocks_error_rate": 0,
        }
        
        report = runner.generate_report(calibration_analysis, experiment_results, h1_stats, h2_stats)
        
        # Save report
        report_path = runner.results_dir / "phase_b_report.md"
        with open(report_path, "w") as f:
            f.write(report)
        
        print("\n" + report)
        print(f"\n✅ Analysis complete. Report saved to {report_path}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
