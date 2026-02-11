#!/bin/bash
#
# Stress Test Runner for Hybrid Routing Validation
#
# Creates capacity pressure by throttling K8s pods and running high load.
# Demonstrates that K8s-only fails under stress while hybrid routing succeeds.
#
# Prerequisites:
# - kubectl configured for k3s cluster (192.168.156.3)
# - HAProxy running on localhost:18082 (traffic), 18404 (stats), 19999 (socket)
# - Knative test-app.default.localhost via Kourier at 192.168.156.2:80
#
# Usage:
#   ./run-stress-test.sh [scenario]
#   ./run-stress-test.sh all      # Run all scenarios
#   ./run-stress-test.sh s1       # Run S1 only
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
RESULTS_DIR="$PROJECT_ROOT/infrastructure/results/knative-real/stress-test"
LOAD_TEST="$SCRIPT_DIR/stress.js"

# Infrastructure endpoints
HAPROXY_URL="http://localhost:18082"
HAPROXY_STATS="http://localhost:18404/stats"
HAPROXY_SOCKET="localhost:19999"
KNATIVE_URL="http://localhost:8081"
KNATIVE_HOST="test-app.default.localhost"
PROMETHEUS_URL="http://localhost:9090"

# K8s deployment
K8S_DEPLOYMENT="test-app-warm"
K8S_CONTAINER="test-app-warm"
K8S_NAMESPACE="default"

# Original CPU limits (to restore)
ORIGINAL_CPU_LIMIT="200m"
ORIGINAL_CPU_REQUEST="50m"

# Throttled CPU limits (to create pressure)
THROTTLED_CPU_LIMIT="10m"
THROTTLED_CPU_REQUEST="5m"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[OK]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Ensure results directory exists
mkdir -p "$RESULTS_DIR"

throttle_k8s_pods() {
    log_info "Throttling K8s pods (cpu=${THROTTLED_CPU_LIMIT})..."
    kubectl set resources deployment/$K8S_DEPLOYMENT \
        -c $K8S_CONTAINER \
        --limits=cpu=${THROTTLED_CPU_LIMIT},memory=64Mi \
        --requests=cpu=${THROTTLED_CPU_REQUEST},memory=16Mi \
        -n $K8S_NAMESPACE
    
    log_info "Waiting for rollout..."
    kubectl rollout status deployment/$K8S_DEPLOYMENT -n $K8S_NAMESPACE --timeout=60s
    log_success "K8s pods throttled to cpu=${THROTTLED_CPU_LIMIT}"
}

restore_k8s_pods() {
    log_info "Restoring K8s pods to normal resources..."
    kubectl set resources deployment/$K8S_DEPLOYMENT \
        -c $K8S_CONTAINER \
        --limits=cpu=${ORIGINAL_CPU_LIMIT},memory=64Mi \
        --requests=cpu=${ORIGINAL_CPU_REQUEST},memory=16Mi \
        -n $K8S_NAMESPACE
    
    log_info "Waiting for rollout..."
    kubectl rollout status deployment/$K8S_DEPLOYMENT -n $K8S_NAMESPACE --timeout=60s
    log_success "K8s pods restored to cpu=${ORIGINAL_CPU_LIMIT}"
}

haproxy_cmd() {
    # macOS nc doesn't support -q, use subshell with sleep instead
    (echo "$1"; sleep 0.1) | nc localhost 19999
}

set_haproxy_weights() {
    local k3s_weight=$1
    local knative_weight=$2
    
    log_info "Setting HAProxy weights: k3s=${k3s_weight}, knative=${knative_weight}"
    
    if [ "$knative_weight" -gt 0 ]; then
        haproxy_cmd "enable server servers/knative"
        sleep 0.5
    fi
    
    haproxy_cmd "set server servers/k3s-cluster weight ${k3s_weight}"
    haproxy_cmd "set server servers/knative weight ${knative_weight}"
    
    if [ "$knative_weight" -eq 0 ]; then
        haproxy_cmd "disable server servers/knative"
    fi
    
    log_success "HAProxy weights set"
}

prewarm_knative() {
    log_info "Pre-warming Knative service..."
    local start=$(date +%s%3N)
    
    if curl -s -o /dev/null -w "%{http_code}" \
        -H "Host: ${KNATIVE_HOST}" \
        "${KNATIVE_URL}/" --max-time 30; then
        
        local end=$(date +%s%3N)
        local cold_start=$((end - start))
        log_success "Knative pre-warmed (cold start: ${cold_start}ms)"
    else
        log_warn "Knative pre-warm may have failed"
    fi
}

run_scenario() {
    local scenario=$1
    local scenario_dir="$RESULTS_DIR/$scenario"
    mkdir -p "$scenario_dir"
    
    log_info "=========================================="
    log_info "Running scenario: $scenario"
    log_info "=========================================="
    
    case $scenario in
        s1-k8s-only)
            log_info "S1: K8s Only (throttled) - expect failures"
            set_haproxy_weights 100 0
            ;;
        s2-serverless-only)
            log_info "S2: Serverless Only - should handle load"
            prewarm_knative
            set_haproxy_weights 0 100
            ;;
        s3-hybrid-reactive)
            log_info "S3: Hybrid Reactive - start K8s, algorithm adds serverless"
            set_haproxy_weights 100 0
            log_warn "Start routing daemon manually if not running:"
            log_warn "  cd controller && uv run python -m daemon.routing_daemon --scenario s3-hybrid-reactive --prometheus-url $PROMETHEUS_URL --haproxy-host localhost --haproxy-port 19999 --interval 10"
            sleep 3
            ;;
        s4-hybrid-predictive)
            log_info "S4: Hybrid Predictive - start K8s, algorithm adds serverless"
            set_haproxy_weights 100 0
            log_warn "Start routing daemon + GRU server if not running"
            sleep 3
            ;;
    esac
    
    # Clear HAProxy stats
    log_info "Clearing HAProxy stats..."
    haproxy_cmd "clear counters all" || true
    sleep 2
    
    # Run k6 stress test
    log_info "Starting k6 stress test..."
    k6 run \
        -e BASE_URL=$HAPROXY_URL \
        -e SCENARIO=$scenario \
        --out json="$scenario_dir/results.json" \
        --summary-export="$scenario_dir/summary.json" \
        "$LOAD_TEST" 2>&1 | tee "$scenario_dir/output.log"
    
    log_success "Scenario $scenario completed"
    log_info "Results saved to $scenario_dir/"
    
    # Cool-down between scenarios
    sleep 5
}

generate_comparison() {
    log_info "Generating comparison report..."
    
    local report="$RESULTS_DIR/STRESS-TEST-SUMMARY.md"
    
    cat > "$report" << 'EOF'
# Stress Test Results

**Date:** $(date +%Y-%m-%d)
**Purpose:** Demonstrate hybrid routing value under capacity pressure

## Test Configuration

- K8s CPU throttled to 10m (from 200m)
- Load: 50 → 500 → 1000 → hold → ramp down (3.5 min total)
- HAProxy: localhost:18082
- Knative: test-app.default.localhost via Kourier

## Results Summary

| Scenario | Error Rate | p95 Latency | p99 Latency | Throughput | Status |
|----------|------------|-------------|-------------|------------|--------|
EOF

    for scenario in s1-k8s-only s2-serverless-only s3-hybrid-reactive s4-hybrid-predictive; do
        local summary="$RESULTS_DIR/$scenario/summary.json"
        if [ -f "$summary" ]; then
            local error_rate=$(jq -r '.metrics.errors.values.rate // 0' "$summary")
            local p95=$(jq -r '.metrics.http_req_duration.values["p(95)"] // 0' "$summary")
            local p99=$(jq -r '.metrics.http_req_duration.values["p(99)"] // 0' "$summary")
            local throughput=$(jq -r '.metrics.http_reqs.values.rate // 0' "$summary")
            
            local error_pct=$(echo "$error_rate * 100" | bc -l | xargs printf "%.2f")
            local p95_ms=$(printf "%.2f" "$p95")
            local p99_ms=$(printf "%.2f" "$p99")
            local tps=$(printf "%.1f" "$throughput")
            
            local status="✅"
            if (( $(echo "$error_rate > 0.05" | bc -l) )); then
                status="❌"
            fi
            
            echo "| $scenario | ${error_pct}% | ${p95_ms}ms | ${p99_ms}ms | ${tps} req/s | $status |" >> "$report"
        else
            echo "| $scenario | N/A | N/A | N/A | N/A | ⏳ |" >> "$report"
        fi
    done
    
    cat >> "$report" << 'EOF'

## Analysis

### Expected Outcomes

1. **S1 (K8s Only)** - Should show high error rates due to CPU throttling
2. **S2 (Serverless Only)** - Should handle load (Knative auto-scales)
3. **S3 (Hybrid Reactive)** - Should recover after SCALE_OUT decision
4. **S4 (Hybrid Predictive)** - Should recover faster with predictions

### Key Metrics to Compare

- **Error Rate**: S1 should have highest, S3/S4 should recover to near-zero
- **Latency**: S1 should have timeouts, hybrid should improve after scaling
- **Throughput**: Hybrid should maintain higher sustained throughput

## Files

| Scenario | Results | Summary | Log |
|----------|---------|---------|-----|
| S1 | s1-k8s-only/results.json | s1-k8s-only/summary.json | s1-k8s-only/output.log |
| S2 | s2-serverless-only/results.json | s2-serverless-only/summary.json | s2-serverless-only/output.log |
| S3 | s3-hybrid-reactive/results.json | s3-hybrid-reactive/summary.json | s3-hybrid-reactive/output.log |
| S4 | s4-hybrid-predictive/results.json | s4-hybrid-predictive/summary.json | s4-hybrid-predictive/output.log |
EOF

    log_success "Comparison report: $report"
}

cleanup() {
    log_info "Cleanup: restoring K8s resources..."
    restore_k8s_pods
}

trap cleanup EXIT

# Main execution
main() {
    local scenario="${1:-all}"
    
    log_info "Stress Test Runner"
    log_info "=================="
    
    # Pre-flight checks
    log_info "Checking prerequisites..."
    
    if ! command -v k6 &> /dev/null; then
        log_error "k6 not found. Install: brew install k6"
        exit 1
    fi
    
    if ! curl -s -o /dev/null "$HAPROXY_URL"; then
        log_error "HAProxy not reachable at $HAPROXY_URL"
        exit 1
    fi
    
    if ! kubectl get deployment/$K8S_DEPLOYMENT -n $K8S_NAMESPACE &> /dev/null; then
        log_error "K8s deployment $K8S_DEPLOYMENT not found"
        exit 1
    fi
    
    log_success "Prerequisites OK"
    
    # Throttle K8s pods
    throttle_k8s_pods
    
    # Run scenarios
    case $scenario in
        all)
            run_scenario "s1-k8s-only"
            run_scenario "s2-serverless-only"
            run_scenario "s3-hybrid-reactive"
            run_scenario "s4-hybrid-predictive"
            generate_comparison
            ;;
        s1|s1-k8s-only)
            run_scenario "s1-k8s-only"
            ;;
        s2|s2-serverless-only)
            run_scenario "s2-serverless-only"
            ;;
        s3|s3-hybrid-reactive)
            run_scenario "s3-hybrid-reactive"
            ;;
        s4|s4-hybrid-predictive)
            run_scenario "s4-hybrid-predictive"
            ;;
        compare)
            generate_comparison
            ;;
        *)
            log_error "Unknown scenario: $scenario"
            echo "Usage: $0 [all|s1|s2|s3|s4|compare]"
            exit 1
            ;;
    esac
    
    log_success "Stress test complete!"
}

main "$@"
