#!/usr/bin/env bash
# Prometheus Stack Deployment for VPS
# Deploys Prometheus with 15s scrape interval and 7d retention
# Usage: ./setup-prometheus.sh

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
PROMETHEUS_CONFIG="$PROJECT_ROOT/infrastructure/prometheus/prometheus.yaml"
PROMETHEUS_K8S="$PROJECT_ROOT/infrastructure/prometheus/prometheus-k8s.yaml"

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster. Is K3s running?"
        exit 1
    fi
    
    if [ ! -f "$PROMETHEUS_CONFIG" ]; then
        log_error "Prometheus config not found at $PROMETHEUS_CONFIG"
        exit 1
    fi
    
    if [ ! -f "$PROMETHEUS_K8S" ]; then
        log_error "Prometheus K8s manifest not found at $PROMETHEUS_K8S"
        exit 1
    fi
    
    log_info "Prerequisites satisfied."
}

# Create monitoring namespace
create_namespace() {
    log_info "Creating monitoring namespace..."
    kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -
}

# Create Prometheus ConfigMap
create_configmap() {
    log_info "Creating Prometheus ConfigMap..."
    
    kubectl create configmap prometheus-config \
        --from-file=prometheus.yml="$PROMETHEUS_CONFIG" \
        -n monitoring \
        --dry-run=client -o yaml | kubectl apply -f -
    
    log_info "ConfigMap created."
}

# Deploy Prometheus
deploy_prometheus() {
    log_info "Deploying Prometheus..."
    
    kubectl apply -f "$PROMETHEUS_K8S"
    
    log_info "Waiting for Prometheus to be ready..."
    kubectl wait --for=condition=Available deployment/prometheus -n monitoring --timeout=180s
    
    log_info "Prometheus deployed."
}

# Create RBAC for Prometheus
create_rbac() {
    log_info "Creating RBAC for Prometheus..."
    
    cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ServiceAccount
metadata:
  name: prometheus
  namespace: monitoring
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: prometheus
rules:
  - apiGroups: [""]
    resources:
      - nodes
      - nodes/proxy
      - nodes/metrics
      - services
      - endpoints
      - pods
    verbs: ["get", "list", "watch"]
  - apiGroups: ["extensions", "networking.k8s.io"]
    resources:
      - ingresses
    verbs: ["get", "list", "watch"]
  - nonResourceURLs: ["/metrics", "/metrics/cadvisor"]
    verbs: ["get"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: prometheus
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: prometheus
subjects:
  - kind: ServiceAccount
    name: prometheus
    namespace: monitoring
EOF
    
    log_info "RBAC created."
}

# Verify Prometheus is scraping targets
verify_targets() {
    log_info "Verifying Prometheus targets..."
    
    # Wait for Prometheus to start scraping
    sleep 10
    
    # Port-forward to check targets
    kubectl port-forward -n monitoring svc/prometheus 9090:9090 &
    PF_PID=$!
    sleep 3
    
    if curl -s "http://localhost:9090/api/v1/targets" | grep -q "activeTargets"; then
        log_info "Prometheus is scraping targets."
        
        # Show target status
        echo ""
        echo "=== Active Targets ==="
        curl -s "http://localhost:9090/api/v1/targets" | \
            jq -r '.data.activeTargets[] | "\(.labels.job): \(.health)"' 2>/dev/null || \
            echo "(Install jq for formatted output)"
    else
        log_warn "Prometheus may not be scraping yet. Check manually."
    fi
    
    # Kill port-forward
    kill $PF_PID 2>/dev/null || true
}

# Print access instructions
print_access_info() {
    echo ""
    log_info "=== Prometheus Access ==="
    echo ""
    echo "Port-forward to access Prometheus UI:"
    echo "  kubectl port-forward -n monitoring svc/prometheus 9090:9090"
    echo ""
    echo "Then open: http://localhost:9090"
    echo ""
    echo "Or use NodePort (if configured):"
    NODEPORT=$(kubectl get svc prometheus -n monitoring -o jsonpath='{.spec.ports[0].nodePort}' 2>/dev/null || echo "not configured")
    echo "  http://<VPS-IP>:$NODEPORT"
    echo ""
}

# Verify installation
verify_installation() {
    log_info "Verifying Prometheus installation..."
    
    echo ""
    echo "=== Prometheus Pods ==="
    kubectl get pods -n monitoring
    
    echo ""
    echo "=== Prometheus Service ==="
    kubectl get svc -n monitoring
    
    echo ""
    echo "=== Prometheus ConfigMap ==="
    kubectl get configmap prometheus-config -n monitoring
    
    echo ""
    log_info "Prometheus installation complete!"
}

# Main
main() {
    log_info "Starting Prometheus deployment..."
    
    check_prerequisites
    create_namespace
    create_rbac
    create_configmap
    deploy_prometheus
    verify_installation
    verify_targets
    print_access_info
}

main "$@"
