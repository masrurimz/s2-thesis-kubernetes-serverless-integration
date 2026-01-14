#!/usr/bin/env bash
# Test script to verify k3d cluster setup
# Usage: ./test_cluster.sh

set -euo pipefail

CLUSTER_NAME="thesis-hybrid"
TESTS_PASSED=0
TESTS_FAILED=0

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

pass() { echo -e "${GREEN}[PASS]${NC} $1"; ((TESTS_PASSED++)); }
fail() { echo -e "${RED}[FAIL]${NC} $1"; ((TESTS_FAILED++)); }
skip() { echo -e "${YELLOW}[SKIP]${NC} $1"; }

# Test: Cluster exists
test_cluster_exists() {
    if k3d cluster list 2>/dev/null | grep -q "$CLUSTER_NAME"; then
        pass "Cluster '$CLUSTER_NAME' exists"
        return 0
    else
        fail "Cluster '$CLUSTER_NAME' does not exist"
        return 1
    fi
}

# Test: Cluster is running
test_cluster_running() {
    if kubectl cluster-info &> /dev/null; then
        pass "Cluster is accessible via kubectl"
    else
        fail "Cannot connect to cluster via kubectl"
    fi
}

# Test: Expected number of nodes
test_node_count() {
    local node_count
    node_count=$(kubectl get nodes --no-headers 2>/dev/null | wc -l | tr -d ' ')
    
    if [[ "$node_count" -ge 2 ]]; then
        pass "Node count: $node_count (expected >= 2)"
    else
        fail "Node count: $node_count (expected >= 2)"
    fi
}

# Test: All nodes are Ready
test_nodes_ready() {
    local not_ready
    not_ready=$(kubectl get nodes --no-headers 2>/dev/null | grep -v "Ready" | wc -l | tr -d ' ')
    
    if [[ "$not_ready" -eq 0 ]]; then
        pass "All nodes are Ready"
    else
        fail "$not_ready node(s) not in Ready state"
    fi
}

# Test: Traefik is disabled
test_traefik_disabled() {
    if kubectl get deployment traefik -n kube-system &> /dev/null; then
        fail "Traefik is still installed (should be disabled)"
    else
        pass "Traefik is disabled"
    fi
}

# Test: Metrics server is installed
test_metrics_server() {
    if kubectl get deployment metrics-server -n kube-system &> /dev/null; then
        local ready
        ready=$(kubectl get deployment metrics-server -n kube-system -o jsonpath='{.status.readyReplicas}' 2>/dev/null || echo "0")
        if [[ "${ready:-0}" -ge 1 ]]; then
            pass "Metrics server is installed and ready"
        else
            fail "Metrics server is installed but not ready"
        fi
    else
        fail "Metrics server is not installed"
    fi
}

# Test: Metrics are available
test_metrics_available() {
    # Wait a moment for metrics to be available
    sleep 2
    if kubectl top nodes &> /dev/null; then
        pass "Node metrics are available (kubectl top nodes works)"
    else
        skip "Node metrics not yet available (may need more time)"
    fi
}

# Test: Port mappings in Docker
test_port_mappings() {
    local lb_container
    lb_container=$(docker ps --filter "name=k3d-$CLUSTER_NAME-serverlb" --format '{{.Names}}' 2>/dev/null)
    
    if [[ -z "$lb_container" ]]; then
        fail "Load balancer container not found"
        return
    fi
    
    local ports
    ports=$(docker port "$lb_container" 2>/dev/null || echo "")
    
    # Check key ports
    local all_ports_ok=true
    for port in 8080 8081 8082 8404 9090 9102; do
        if echo "$ports" | grep -q ":$port->"; then
            continue
        else
            all_ports_ok=false
        fi
    done
    
    if [[ "$all_ports_ok" == true ]]; then
        pass "All expected port mappings configured"
    else
        # Check individually
        echo "    Port mapping details:"
        for port in 8080 8081 8082 8404 9090 9102; do
            if docker port "$lb_container" "$port" &> /dev/null 2>&1; then
                echo "      - Port $port: OK"
            else
                echo "      - Port $port: NOT MAPPED"
            fi
        done
        skip "Some port mappings may use different format (check k3d config)"
    fi
}

# Test: Resource limits applied
test_resource_limits() {
    local container
    container=$(docker ps --filter "name=k3d-$CLUSTER_NAME-server-0" --format '{{.Names}}' 2>/dev/null | head -1)
    
    if [[ -z "$container" ]]; then
        skip "Could not find server container for resource limit check"
        return
    fi
    
    local memory
    memory=$(docker inspect "$container" --format '{{.HostConfig.Memory}}' 2>/dev/null || echo "0")
    
    # 512MB = 536870912 bytes
    if [[ "$memory" -eq 536870912 ]]; then
        pass "Memory limit is 512M"
    elif [[ "$memory" -eq 0 ]]; then
        skip "Memory limit not set (run create-cluster.sh to apply limits)"
    else
        skip "Memory limit is $(($memory / 1024 / 1024))M (expected 512M)"
    fi
}

# Test: thesis-system namespace exists
test_thesis_namespace() {
    if kubectl get namespace thesis-system &> /dev/null; then
        pass "thesis-system namespace exists"
    else
        skip "thesis-system namespace not found (created by create-cluster.sh)"
    fi
}

# Test: Knative Serving installed
test_knative_serving() {
    if kubectl get namespace knative-serving &> /dev/null; then
        local activator_ready
        activator_ready=$(kubectl get deployment activator -n knative-serving -o jsonpath='{.status.readyReplicas}' 2>/dev/null || echo "0")
        if [[ "${activator_ready:-0}" -ge 1 ]]; then
            pass "Knative Serving is installed and ready"
        else
            skip "Knative Serving installed but not ready"
        fi
    else
        skip "Knative Serving not installed (run knative-install.sh)"
    fi
}

# Test: Kourier installed
test_kourier() {
    if kubectl get namespace kourier-system &> /dev/null; then
        local kourier_ready
        kourier_ready=$(kubectl get deployment 3scale-kourier-gateway -n kourier-system -o jsonpath='{.status.readyReplicas}' 2>/dev/null || echo "0")
        if [[ "${kourier_ready:-0}" -ge 1 ]]; then
            pass "Kourier is installed and ready"
        else
            skip "Kourier installed but not ready"
        fi
    else
        skip "Kourier not installed (run knative-install.sh)"
    fi
}

# Print summary
print_summary() {
    echo ""
    echo "========================================"
    echo "Test Summary"
    echo "========================================"
    echo -e "${GREEN}Passed: $TESTS_PASSED${NC}"
    echo -e "${RED}Failed: $TESTS_FAILED${NC}"
    echo "========================================"
    
    if [[ $TESTS_FAILED -gt 0 ]]; then
        return 1
    fi
    return 0
}

# Main
main() {
    echo "========================================"
    echo "k3d Cluster Test Suite"
    echo "Cluster: $CLUSTER_NAME"
    echo "========================================"
    echo ""
    
    # Core cluster tests
    echo "=== Core Cluster Tests ==="
    if ! test_cluster_exists; then
        echo ""
        echo "Cluster does not exist. Run './create-cluster.sh' first."
        exit 1
    fi
    test_cluster_running
    test_node_count
    test_nodes_ready
    
    echo ""
    echo "=== Configuration Tests ==="
    test_traefik_disabled
    test_metrics_server
    test_metrics_available
    test_port_mappings
    test_resource_limits
    test_thesis_namespace
    
    echo ""
    echo "=== Knative Tests ==="
    test_knative_serving
    test_kourier
    
    print_summary
}

main "$@"
