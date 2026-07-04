#!/usr/bin/env python3
"""
Identify outlier runs in Phase B experiments for potential exclusion.

Suspected stale/reset Prometheus metrics:
- S1-run2: p99=9.9ms, throughput=190 RPS
- S2-run5: p99=9.9ms, throughput=201 RPS
- S3-run5: p99=10.0ms, throughput=84 RPS

These runs have:
1. p99 < 15ms (impossibly low for HTTP through HAProxy)
2. Throughput significantly different from other runs in same scenario

Criteria for exclusion:
- p99 < 15ms AND (throughput > 150 RPS OR throughput anomalously different)
- Likely cause: Prometheus metrics reset/stale during run
"""

import json
import statistics
from pathlib import Path
from typing import List, Dict


def load_phase_b_data() -> List[Dict]:
    """Load Phase B experiments data."""
    phase_b_path = (
        Path(__file__).parent.parent
        / "results/experiments/phase-b/2026-02-12_replicated-20runs/raw/experiments_final.json"
    )
    with open(phase_b_path) as f:
        return json.load(f)


def analyze_outliers():
    """Identify and analyze outlier runs."""
    experiments = load_phase_b_data()

    print("=" * 80)
    print("PHASE B OUTLIER ANALYSIS")
    print("=" * 80)

    # Group by scenario
    scenarios = {}
    for exp in experiments:
        scenario = exp["scenario"]
        if scenario not in scenarios:
            scenarios[scenario] = []
        scenarios[scenario].append(exp)

    print(f"\nTotal experiments: {len(experiments)}")
    print(f"Scenarios: {list(scenarios.keys())}")

    # Define outlier criteria
    P99_THRESHOLD = 15.0  # ms - impossibly low for HAProxy routing
    THROUGHPUT_HIGH = 150.0  # RPS - suspiciously high

    outliers = []

    print("\n" + "=" * 80)
    print("PER-SCENARIO ANALYSIS")
    print("=" * 80)

    for scenario_name, runs in scenarios.items():
        print(f"\n📊 {scenario_name}")
        print(f"   Runs: {len(runs)}")

        p99_values = [r["p99_latency_ms"] for r in runs]
        throughput_values = [r["throughput_rps"] for r in runs]

        p99_mean = statistics.mean(p99_values)
        p99_median = statistics.median(p99_values)
        p99_stdev = statistics.stdev(p99_values) if len(p99_values) > 1 else 0

        throughput_mean = statistics.mean(throughput_values)
        throughput_median = statistics.median(throughput_values)
        throughput_stdev = statistics.stdev(throughput_values) if len(throughput_values) > 1 else 0

        print(f"   p99: mean={p99_mean:.1f}ms, median={p99_median:.1f}ms, stdev={p99_stdev:.1f}ms")
        print(
            f"   throughput: mean={throughput_mean:.1f}RPS, median={throughput_median:.1f}RPS, stdev={throughput_stdev:.1f}RPS"
        )

        # Check each run
        for run in runs:
            run_id = run["run_id"]
            p99 = run["p99_latency_ms"]
            throughput = run["throughput_rps"]

            # Outlier detection
            is_outlier = False
            reasons = []

            # Criterion 1: Impossibly low p99
            if p99 < P99_THRESHOLD:
                is_outlier = True
                reasons.append(f"p99={p99:.1f}ms < {P99_THRESHOLD}ms (impossibly low)")

            # Criterion 2: Anomalously high throughput
            if throughput > THROUGHPUT_HIGH:
                is_outlier = True
                reasons.append(f"throughput={throughput:.1f} > {THROUGHPUT_HIGH} RPS (anomalously high)")

            # Criterion 3: Statistical outlier (>2 stdev from mean)
            if p99_stdev > 0:
                z_score_p99 = abs((p99 - p99_mean) / p99_stdev)
                if z_score_p99 > 2:
                    is_outlier = True
                    reasons.append(f"p99 z-score={z_score_p99:.2f} (>2 stdev from mean)")

            if throughput_stdev > 0:
                z_score_throughput = abs((throughput - throughput_mean) / throughput_stdev)
                if z_score_throughput > 2:
                    # Only flag if throughput is HIGH (not low)
                    if throughput > throughput_mean:
                        is_outlier = True
                        reasons.append(f"throughput z-score={z_score_throughput:.2f} (>2 stdev, HIGH)")

            if is_outlier:
                print(f"   ⚠️ RUN {run_id}: {', '.join(reasons)}")
                outliers.append(
                    {
                        "scenario": scenario_name,
                        "run_id": run_id,
                        "p99": p99,
                        "throughput": throughput,
                        "reasons": reasons,
                    }
                )
            else:
                print(f"   ✅ Run {run_id}: p99={p99:.1f}ms, throughput={throughput:.1f}RPS (normal)")

    print("\n" + "=" * 80)
    print("OUTLIER SUMMARY")
    print("=" * 80)

    if not outliers:
        print("\n✅ No outliers detected.")
    else:
        print(f"\n⚠️ {len(outliers)} outlier runs detected:\n")
        for outlier in outliers:
            print(f"  • {outlier['scenario']} Run {outlier['run_id']}")
            print(f"    p99={outlier['p99']:.1f}ms, throughput={outlier['throughput']:.1f}RPS")
            print(f"    Reasons: {', '.join(outlier['reasons'])}")
            print()

    print("=" * 80)
    print("EXCLUSION CRITERIA")
    print("=" * 80)
    print("""
Defensible exclusion rule:

**Exclude runs where:**
1. p99 < 15ms (impossibly low for HAProxy HTTP routing), OR
2. Throughput > 150 RPS (anomalously high for 100 RPS target load), OR
3. Statistical outlier: >2 standard deviations from scenario mean

**Rationale:**
- Normal HAProxy p99 latency: 50-800ms range across all other runs
- p99 ~10ms suggests Prometheus metrics were reset/stale during run
- Throughput >150 RPS with 100 RPS target → ~50-100% over expected (data error)

**Transparent reporting:**
- Report both with-outliers and without-outliers statistics
- Document exclusion in methodology
- Provide outlier data in appendix
""")

    print("\n" + "=" * 80)
    print("RECOMMENDED ACTIONS")
    print("=" * 80)
    print("""
1. ✅ Use exclusion criteria above (p99<15ms OR throughput>150RPS OR z>2)
2. 📊 Recompute Phase B statistics with outliers excluded
3. 📝 Add exclusion methodology to thesis protocol
4. 📎 Include outlier table in appendix
5. ⚠️ Report both versions: "with outliers" and "clean data"
6. 🔄 Optional: Re-run excluded scenarios (S1-run2, S2-run5, S3-run5) if time permits
""")

    # Export outliers for reference
    outlier_file = (
        Path(__file__).parent.parent / "results/experiments/phase-b/2026-02-12_replicated-20runs/raw/outliers.json"
    )
    with open(outlier_file, "w") as f:
        json.dump(outliers, f, indent=2)

    print(f"\n💾 Outliers exported to: {outlier_file}")


if __name__ == "__main__":
    analyze_outliers()
