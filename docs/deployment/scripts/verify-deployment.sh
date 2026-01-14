#!/usr/bin/env bash
# Deployment Verification Script
# Verifies all components of the VPS deployment are running correctly
# Usage: ./verify-deployment.sh

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_section() { echo -e "\n${BLUE}=== $1 ===${NC}"; }

ERRORS=0
WARNINGS=0

check_pass() {
    echo -e "${GREEN}✓${NC} $1"
}

check_fail() {
    echo -e "${RED}✗${NC} $1"
    ERRORS=$((ERRORS + 1))
}

check_warn() {
    echo -e "${YELLOW}!${NC} $1"
    WARNINGS=$((WARNINGS + 1))
}

# Check K3s
check_k3s() {
    log_section "K3s Cluster"
    
    # Check cluster connectivity
    if kubectl cluster-info &> /dev/null; then
        check_pass "Cluster is accessible"
    else
        check_fail "Cannot connect to cluster"
        return 1
    fi
    
    # Check node status
    NODE_STATUS=$(kubectl get nodes -o jsonpath='{.items[0].status.conditions[?(@.type=="Ready")].status}')
    if [ "$NODE_STATUS" == "True" ]; then
        check_pass "Node is Ready"
    else
        check_fail "Node is not Ready"
    fi
    
    # Check system pods
    NOT_RUNNING=$(kubectl get pods -n kube-system --no-headers | grep -v "Running" | grep -v "Completed" | wc -l)
    if [ "$NOT_RUNNING" -eq 0 ]; then
        check_pass "All kube-system pods running"
    else
        check_warn "$NOT_RUNNING pods not in Running state"
        kubectl get pods -n kube-system --no-headers | grep -v "Running" | grep -v "Completed"
    fi
    
    # Check metrics-server
    if kubectl get deployment metrics-server -n kube-system &> /dev/null; then
        READY=$(kubectl get deployment metrics-server -n kube-system -o jsonpath='{.status.readyReplicas}')
        if [ "$READY" == "1" ]; then
            check_pass "Metrics-server is running"
        else
            check_warn "Metrics-server not ready"
        fi
    else
        check_warn "Metrics-server not installed"
    fi
}

# Check Knative
check_knative() {
    log_section "Knative Serving"
    
    # Check knative-serving namespace
    if kubectl get namespace knative-serving &> /dev/null; then
        check_pass "knative-serving namespace exists"
    else
        check_fail "knative-serving namespace not found"
        return 1
    fi
    
    # Check Knative pods
    NOT_RUNNING=$(kubectl get pods -n knative-serving --no-headers 2>/dev/null | grep -v "Running" | wc -l)
    if [ "$NOT_RUNNING" -eq 0 ]; then
        check_pass "All Knative Serving pods running"
    else
        check_fail "$NOT_RUNNING Knative pods not running"
        kubectl get pods -n knative-serving --no-headers | grep -v "Running"
    fi
    
    # Check Kourier
    if kubectl get namespace kourier-system &> /dev/null; then
        KOURIER_RUNNING=$(kubectl get pods -n kourier-system --no-headers 2>/dev/null | grep "Running" | wc -l)
        if [ "$KOURIER_RUNNING" -gt 0 ]; then
            check_pass "Kourier pods running"
        else
            check_fail "Kourier pods not running"
        fi
    else
        check_fail "kourier-system namespace not found"
    fi
    
    # Check Kourier service
    KOURIER_TYPE=$(kubectl get svc kourier -n kourier-system -o jsonpath='{.spec.type}' 2>/dev/null)
    if [ "$KOURIER_TYPE" == "NodePort" ]; then
        NODEPORT=$(kubectl get svc kourier -n kourier-system -o jsonpath='{.spec.ports[0].nodePort}')
        check_pass "Kourier exposed on NodePort $NODEPORT"
    else
        check_warn "Kourier service type is $KOURIER_TYPE (expected NodePort)"
    fi
}

# Check Prometheus
check_prometheus() {
    log_section "Prometheus"
    
    # Check monitoring namespace
    if kubectl get namespace monitoring &> /dev/null; then
        check_pass "monitoring namespace exists"
    else
        check_fail "monitoring namespace not found"
        return 1
    fi
    
    # Check Prometheus deployment
    if kubectl get deployment prometheus -n monitoring &> /dev/null; then
        READY=$(kubectl get deployment prometheus -n monitoring -o jsonpath='{.status.readyReplicas}')
        if [ "$READY" == "1" ]; then
            check_pass "Prometheus is running"
        else
            check_warn "Prometheus not ready"
        fi
    else
        check_fail "Prometheus deployment not found"
    fi
    
    # Check ConfigMap
    if kubectl get configmap prometheus-config -n monitoring &> /dev/null; then
        check_pass "Prometheus ConfigMap exists"
    else
        check_warn "Prometheus ConfigMap not found"
    fi
    
    # Check Prometheus service
    if kubectl get svc prometheus -n monitoring &> /dev/null; then
        check_pass "Prometheus service exists"
    else
        check_fail "Prometheus service not found"
    fi
}

# Check HAProxy
check_haproxy() {
    log_section "HAProxy"
    
    # Check if HAProxy is installed
    if command -v haproxy &> /dev/null; then
        check_pass "HAProxy installed"
    else
        check_warn "HAProxy not installed"
        return 0
    fi
    
    # Check if HAProxy is running
    if systemctl is-active --quiet haproxy 2>/dev/null; then
        check_pass "HAProxy service is running"
    elif pgrep haproxy > /dev/null; then
        check_pass "HAProxy process is running"
    else
        check_warn "HAProxy is not running"
    fi
    
    # Check HAProxy stats endpoint
    if curl -s -o /dev/null -w "%{http_code}" "http://localhost:8404/stats" 2>/dev/null | grep -q "200"; then
        check_pass "HAProxy stats endpoint accessible"
    else
        check_warn "HAProxy stats endpoint not accessible"
    fi
    
    # Check haproxy_exporter
    if curl -s -o /dev/null -w "%{http_code}" "http://localhost:9101/metrics" 2>/dev/null | grep -q "200"; then
        check_pass "haproxy_exporter running"
    else
        check_warn "haproxy_exporter not running"
    fi
}

# Check test applications
check_test_apps() {
    log_section "Test Applications"
    
    # Check for K3s test deployment
    if kubectl get deployment -n default --no-headers 2>/dev/null | grep -q .; then
        check_pass "K3s deployments found"
        kubectl get deployment -n default
    else
        check_warn "No deployments in default namespace"
    fi
    
    # Check for Knative services
    if kubectl get ksvc -n default --no-headers 2>/dev/null | grep -q .; then
        check_pass "Knative services found"
        kubectl get ksvc -n default
    else
        check_warn "No Knative services found"
    fi
}

# Test connectivity
test_connectivity() {
    log_section "Connectivity Tests"
    
    # Test K3s endpoint
    if curl -s -o /dev/null -w "%{http_code}" "http://localhost:8080" 2>/dev/null | grep -qE "200|404"; then
        check_pass "K3s ingress port 8080 reachable"
    else
        check_warn "K3s ingress port 8080 not reachable"
    fi
    
    # Test Kourier endpoint
    KOURIER_PORT=$(kubectl get svc kourier -n kourier-system -o jsonpath='{.spec.ports[0].nodePort}' 2>/dev/null || echo "31080")
    if curl -s -o /dev/null -w "%{http_code}" "http://localhost:$KOURIER_PORT" 2>/dev/null | grep -qE "200|404|503"; then
        check_pass "Kourier port $KOURIER_PORT reachable"
    else
        check_warn "Kourier port $KOURIER_PORT not reachable"
    fi
}

# Print summary
print_summary() {
    log_section "Summary"
    
    echo ""
    if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
        echo -e "${GREEN}All checks passed! Deployment is healthy.${NC}"
    elif [ $ERRORS -eq 0 ]; then
        echo -e "${YELLOW}Deployment OK with $WARNINGS warnings.${NC}"
    else
        echo -e "${RED}$ERRORS errors and $WARNINGS warnings found.${NC}"
    fi
    
    echo ""
    echo "Errors: $ERRORS"
    echo "Warnings: $WARNINGS"
    
    return $ERRORS
}

# Main
main() {
    log_info "Starting deployment verification..."
    
    check_k3s
    check_knative
    check_prometheus
    check_haproxy
    check_test_apps
    test_connectivity
    print_summary
}

main "$@"
