#!/usr/bin/env bash
# Create k3d cluster for thesis hybrid experiments
# Usage: ./create-cluster.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLUSTER_NAME="thesis-hybrid"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    if ! command -v k3d &> /dev/null; then
        log_error "k3d is not installed. Please install it first."
        exit 1
    fi
    
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed. Please install it first."
        exit 1
    fi
    
    if ! command -v docker &> /dev/null; then
        log_error "docker is not installed. Please install it first."
        exit 1
    fi
    
    # Check Docker is running
    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running. Please start Docker."
        exit 1
    fi
    
    log_info "All prerequisites satisfied."
}

# Delete existing cluster if exists
cleanup_existing() {
    if k3d cluster list | grep -q "$CLUSTER_NAME"; then
        log_warn "Cluster '$CLUSTER_NAME' already exists. Deleting..."
        k3d cluster delete "$CLUSTER_NAME"
        sleep 2
    fi
}

# Create the cluster
create_cluster() {
    log_info "Creating k3d cluster '$CLUSTER_NAME'..."
    k3d cluster create -c "$SCRIPT_DIR/k3d-cluster.yaml"
    
    # Wait for nodes to be ready
    log_info "Waiting for nodes to be ready..."
    kubectl wait --for=condition=Ready nodes --all --timeout=120s
}

# Apply resource limits to nodes via Docker
apply_resource_limits() {
    log_info "Applying resource limits to nodes (512M memory, 1 CPU)..."
    
    # Get all k3d containers for this cluster
    for container in $(docker ps --filter "name=k3d-$CLUSTER_NAME" --format '{{.Names}}'); do
        log_info "Setting limits on container: $container"
        docker update --cpus 1 --memory 512m --memory-swap 512m "$container" || true
    done
}

# Install metrics-server
install_metrics_server() {
    log_info "Installing metrics-server..."
    
    kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
    
    # Patch metrics-server for k3d (insecure TLS)
    kubectl patch deployment metrics-server -n kube-system --type='json' -p='[
      {"op": "add", "path": "/spec/template/spec/containers/0/args/-", "value": "--kubelet-insecure-tls"},
      {"op": "add", "path": "/spec/template/spec/containers/0/args/-", "value": "--kubelet-preferred-address-types=InternalIP"}
    ]'
    
    log_info "Waiting for metrics-server to be ready..."
    kubectl rollout status deployment metrics-server -n kube-system --timeout=120s
}

# Create NodePort services for external access
create_nodeport_services() {
    log_info "Creating NodePort configurations..."
    
    cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Namespace
metadata:
  name: thesis-system
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: port-mappings
  namespace: thesis-system
data:
  # Port mapping reference
  k8s-service: "8080 -> 80 (loadbalancer)"
  kourier: "8081 -> 31080 (Knative gateway)"
  haproxy: "8082 -> 31082 (external)"
  haproxy-stats: "8404 -> 31404"
  prometheus: "9090 -> 31090"
  autoscaler-metrics: "9102 -> 31102"
EOF
}

# Verify cluster setup
verify_cluster() {
    log_info "Verifying cluster setup..."
    
    echo ""
    echo "=== Cluster Nodes ==="
    kubectl get nodes -o wide
    
    echo ""
    echo "=== System Pods ==="
    kubectl get pods -n kube-system
    
    echo ""
    echo "=== Port Mappings ==="
    echo "  8080 -> K8s service (port 80)"
    echo "  8081 -> Kourier (Knative gateway, NodePort 31080)"
    echo "  8082 -> HAProxy (NodePort 31082)"
    echo "  8404 -> HAProxy stats (NodePort 31404)"
    echo "  9090 -> Prometheus (NodePort 31090)"
    echo "  9102 -> Autoscaler metrics (NodePort 31102)"
    
    echo ""
    log_info "Cluster '$CLUSTER_NAME' created successfully!"
    log_info "Run './knative-install.sh' to install Knative + Kourier"
}

# Main
main() {
    log_info "Starting k3d cluster setup for thesis experiments..."
    
    check_prerequisites
    cleanup_existing
    create_cluster
    apply_resource_limits
    install_metrics_server
    create_nodeport_services
    verify_cluster
}

main "$@"
