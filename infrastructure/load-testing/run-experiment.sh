#!/bin/bash
# Run complete H1/H2 experiment suite
# Usage: ./run-experiment.sh <scenario> [--quick]
# Example: ./run-experiment.sh s3-hybrid-reactive

set -e

# Load centralized configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../load-config.sh"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }

# Parse arguments
SCENARIO="${1:-s3-hybrid-reactive}"
QUICK="${2:-}"

# Validate scenario
case "$SCENARIO" in
    s1-k8s-only|s2-serverless-only|s3-hybrid-reactive|s4-hybrid-predictive)
        ;;
    *)
        log_error "Invalid scenario: $SCENARIO"
        echo "Valid scenarios:"
        echo "  s1-k8s-only         - Static K8s routing (100/0)"
        echo "  s2-serverless-only  - Static serverless routing (0/100)"
        echo "  s3-hybrid-reactive  - Algorithm 1 without predictions"
        echo "  s4-hybrid-predictive - Algorithm 1 + GRU predictions"
        exit 1
        ;;
esac

echo ""
echo "🔬 H1/H2 Experiment Runner"
echo "=========================="
echo "Scenario: $SCENARIO"
echo "HAProxy: ${HAPROXY_URL}"
echo "Prometheus: ${PROMETHEUS_URL}"
echo "Daemon API: ${DAEMON_URL}"
echo ""

# Check prerequisites
log_info "Checking prerequisites..."

# Check HAProxy
if ! curl -sf "${HAPROXY_URL}/health" > /dev/null 2>&1; then
    log_error "HAProxy not responding at ${HAPROXY_URL}"
    echo "Start with: cd infrastructure/haproxy && docker-compose up -d"
    exit 1
fi
log_success "HAProxy responding"

# Check K3d cluster
if ! kubectl get nodes > /dev/null 2>&1; then
    log_error "K3d cluster not accessible"
    exit 1
fi
log_success "K3d cluster accessible"

# Check warm backend
if ! curl -sf "${K3S_WARM_URL}/health" > /dev/null 2>&1; then
    log_warning "K3s warm backend not responding - may be normal for S2"
fi

# Check activator
if ! curl -sf "${K3S_ACTIVATOR_URL}/health" > /dev/null 2>&1; then
    log_warning "Serverless activator not responding"
fi

# For S4, check GRU server
if [[ "$SCENARIO" == "s4-hybrid-predictive" ]]; then
    if ! curl -sf "${GRU_URL}/health" > /dev/null 2>&1; then
        log_error "GRU server not responding at ${GRU_URL}"
        echo "Start with: cd controller && uv run python -m prediction.prediction_server"
        exit 1
    fi
    log_success "GRU server responding"
fi

# Check if routing daemon is running for S3/S4
if [[ "$SCENARIO" == "s3-hybrid-reactive" || "$SCENARIO" == "s4-hybrid-predictive" ]]; then
    if ! curl -sf "${DAEMON_URL}/health" > /dev/null 2>&1; then
        log_error "Routing daemon not responding at ${DAEMON_URL}"
        echo "Start with: cd controller && uv run python -m daemon.routing_daemon --scenario $SCENARIO"
        exit 1
    fi
    log_success "Routing daemon responding"
    
    # Set scenario via API
    log_info "Setting scenario to $SCENARIO..."
    curl -sf -X POST "${DAEMON_URL}/set_scenario" \
        -H "Content-Type: application/json" \
        -d "{\"scenario\": \"$SCENARIO\"}" > /dev/null
    log_success "Scenario set"
fi

echo ""
log_info "Starting experiment for $SCENARIO..."
echo ""

# Create results directory
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
RESULTS_DIR="${SCRIPT_DIR}/../results/${SCENARIO}/${TIMESTAMP}"
mkdir -p "$RESULTS_DIR"

# Record pre-test state
log_info "Recording pre-test state..."
curl -sf "${HAPROXY_STATS_CSV_URL}" > "${RESULTS_DIR}/haproxy-pre.csv" 2>/dev/null || true

if [[ "$SCENARIO" == "s3-hybrid-reactive" || "$SCENARIO" == "s4-hybrid-predictive" ]]; then
    curl -sf "${DAEMON_URL}/status" > "${RESULTS_DIR}/daemon-pre.json" 2>/dev/null || true
fi

# Run spike-with-idle workload
log_info "Running spike-with-idle workload..."
cd "${SCRIPT_DIR}"

if [[ "$QUICK" == "--quick" ]]; then
    # Run shorter version for quick testing
    k6 run spike-load.js \
        -e TARGET_URL="${HAPROXY_URL}" \
        -e HAPROXY_STATS_URL="${HAPROXY_STATS_URL}" \
        --out json="${RESULTS_DIR}/k6-results.json" \
        --summary-export="${RESULTS_DIR}/k6-summary.json" \
        2>&1 | tee "${RESULTS_DIR}/k6-output.txt"
else
    k6 run spike-with-idle.js \
        -e TARGET_URL="${HAPROXY_URL}" \
        -e HAPROXY_STATS_URL="${HAPROXY_STATS_URL}" \
        --out json="${RESULTS_DIR}/k6-results.json" \
        --summary-export="${RESULTS_DIR}/k6-summary.json" \
        2>&1 | tee "${RESULTS_DIR}/k6-output.txt"
fi

# Record post-test state
log_info "Recording post-test state..."
curl -sf "${HAPROXY_STATS_CSV_URL}" > "${RESULTS_DIR}/haproxy-post.csv" 2>/dev/null || true

if [[ "$SCENARIO" == "s3-hybrid-reactive" || "$SCENARIO" == "s4-hybrid-predictive" ]]; then
    curl -sf "${DAEMON_URL}/status" > "${RESULTS_DIR}/daemon-post.json" 2>/dev/null || true
    curl -sf "${DAEMON_URL}/metrics" > "${RESULTS_DIR}/daemon-metrics.txt" 2>/dev/null || true
fi

echo ""
log_success "Experiment complete for $SCENARIO"
echo ""
echo "📊 Results saved to: ${RESULTS_DIR}"
echo "   - k6-summary.json: Performance metrics"
echo "   - k6-output.txt: Full test output"
echo "   - haproxy-*.csv: Traffic distribution before/after"
if [[ "$SCENARIO" == "s3-hybrid-reactive" || "$SCENARIO" == "s4-hybrid-predictive" ]]; then
    echo "   - daemon-*.json: Routing daemon state"
fi
echo ""
echo "📈 Key metrics to analyze:"
echo "   - p99 latency during spike phases"
echo "   - slo_violations count"
echo "   - Weight changes (for S3/S4)"
echo ""
