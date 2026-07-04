#!/usr/bin/env bash
# Delete k3d cluster for thesis hybrid experiments
# Usage: ./delete-cluster.sh

set -euo pipefail

CLUSTER_NAME="thesis-hybrid"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Delete the cluster
delete_cluster() {
    if k3d cluster list 2>/dev/null | grep -q "$CLUSTER_NAME"; then
        log_info "Deleting cluster '$CLUSTER_NAME'..."
        k3d cluster delete "$CLUSTER_NAME"
        log_info "Cluster deleted successfully."
    else
        log_warn "Cluster '$CLUSTER_NAME' does not exist."
    fi
}

# Clean up Docker resources
cleanup_docker() {
    log_info "Cleaning up Docker resources..."
    
    # Remove any orphaned k3d volumes
    docker volume ls -q --filter "name=k3d-$CLUSTER_NAME" 2>/dev/null | xargs -r docker volume rm 2>/dev/null || true
    
    # Remove any orphaned k3d networks
    docker network ls -q --filter "name=k3d-$CLUSTER_NAME" 2>/dev/null | xargs -r docker network rm 2>/dev/null || true
    
    # Remove registry if exists
    if docker ps -a --filter "name=k3d-registry.localhost" --format '{{.Names}}' | grep -q "k3d-registry.localhost"; then
        log_info "Removing local registry..."
        docker rm -f k3d-registry.localhost 2>/dev/null || true
    fi
    
    log_info "Docker cleanup complete."
}

# Prune unused resources (optional)
prune_resources() {
    if [[ "${1:-}" == "--prune" ]]; then
        log_warn "Pruning unused Docker resources..."
        docker system prune -f --volumes
        log_info "Prune complete."
    fi
}

# Main
main() {
    log_info "Starting cleanup for thesis-hybrid cluster..."
    
    delete_cluster
    cleanup_docker
    prune_resources "${1:-}"
    
    echo ""
    log_info "Cleanup complete!"
    log_info "Run './create-cluster.sh' to recreate the cluster."
}

main "$@"
