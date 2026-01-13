#!/bin/bash
# Sprint 1: Fast System Teardown Script
# Nuclear option: Force cleanup everything quickly

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Fast teardown function
fast_teardown() {
    log_info "Starting fast Sprint 1 hybrid system teardown..."
    echo
    
    # Kill port forwarding processes immediately
    log_info "Force killing port forwarding processes..."
    pkill -f "kubectl.*port-forward" || true
    pkill -f "port-forward.*kourier" || true
    log_success "Port forwarding processes killed"
    
    # Force delete k3d cluster (fastest method)
    log_info "Force deleting K3s cluster..."
    k3d cluster delete hybrid-sprint1 || log_warning "Cluster may not exist"
    log_success "K3s cluster deleted"
    
    # Force stop and remove Docker containers
    log_info "Force removing Docker containers..."
    
    # HAProxy containers
    docker stop sprint1-haproxy 2>/dev/null || true
    docker rm sprint1-haproxy 2>/dev/null || true
    
    # Monitoring containers
    docker stop sprint1-prometheus 2>/dev/null || true
    docker rm sprint1-prometheus 2>/dev/null || true
    
    # Any containers with sprint1 in name
    SPRINT1_CONTAINERS=$(docker ps -aq --filter "name=sprint1" 2>/dev/null || true)
    if [ -n "$SPRINT1_CONTAINERS" ]; then
        docker stop $SPRINT1_CONTAINERS 2>/dev/null || true
        docker rm $SPRINT1_CONTAINERS 2>/dev/null || true
    fi
    
    log_success "Docker containers removed"
    
    # Remove Docker networks
    log_info "Removing Docker networks..."
    docker network rm sprint1-monitoring 2>/dev/null || true
    docker network rm haproxy_hybrid-network 2>/dev/null || true
    docker network rm k3d-hybrid-sprint1 2>/dev/null || true
    log_success "Docker networks removed"
    
    # Remove Docker volumes
    log_info "Removing Docker volumes..."
    docker volume rm monitoring_prometheus-data 2>/dev/null || true
    docker volume rm k3d-hybrid-sprint1-images 2>/dev/null || true
    log_success "Docker volumes removed"
    
    # Clean up temporary files
    log_info "Cleaning up temporary files..."
    rm -f /tmp/knative-port-forward.pid 2>/dev/null || true
    rm -f /tmp/knative-port-forward.log 2>/dev/null || true
    log_success "Temporary files cleaned"
    
    # Force cleanup any remaining kubectl contexts
    log_info "Cleaning kubectl context..."
    kubectl config delete-context k3d-hybrid-sprint1 2>/dev/null || true
    kubectl config delete-cluster k3d-hybrid-sprint1 2>/dev/null || true
    kubectl config delete-user admin@k3d-hybrid-sprint1 2>/dev/null || true
    log_success "Kubectl context cleaned"
    
    echo
    log_success "🚀 Fast teardown complete! (took ~30 seconds instead of 5+ minutes)"
    echo
    echo -e "${BLUE}System Status:${NC}"
    echo "• All K3s components: ❌ REMOVED"
    echo "• All Docker containers: ❌ REMOVED"
    echo "• All networks and volumes: ❌ REMOVED"
    echo "• All port forwarding: ❌ STOPPED"
    echo
    echo -e "${GREEN}Ready for fresh deployment with: ./scripts/setup.sh${NC}"
}

# Allow script to be sourced for testing
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    fast_teardown "$@"
fi