#!/bin/bash
# Sprint 1: Complete System Teardown Script
# Cleanly removes all components of the hybrid k3s-serverless architecture

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
INFRASTRUCTURE_DIR="$PROJECT_ROOT/infrastructure"

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

# Stop port forwarding
stop_port_forwarding() {
    log_info "Stopping port forwarding processes..."
    
    # Stop Knative port forwarding
    if [ -f /tmp/knative-port-forward.pid ]; then
        local pid=$(cat /tmp/knative-port-forward.pid)
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid" || true
            log_success "Stopped Knative port forwarding (PID: $pid)"
        fi
        rm -f /tmp/knative-port-forward.pid
    fi
    
    # Kill any remaining kubectl port-forward processes
    pkill -f "kubectl port-forward" || true
    
    # Kill any port forwarding on our specific ports
    for port in 8081 9090; do
        local pids=$(lsof -ti:$port 2>/dev/null || true)
        if [ -n "$pids" ]; then
            echo "$pids" | xargs kill -9 2>/dev/null || true
            log_info "Killed processes on port $port"
        fi
    done
}

# Remove monitoring stack
remove_monitoring() {
    log_info "Removing monitoring stack..."
    
    cd "$INFRASTRUCTURE_DIR/monitoring" 2>/dev/null || {
        log_warning "Monitoring directory not found"
        return 0
    }
    
    if [ -f docker-compose.yml ]; then
        docker-compose down -v --remove-orphans 2>/dev/null || {
            log_warning "Failed to stop monitoring with docker-compose"
        }
        log_success "Monitoring stack removed"
    else
        log_info "No monitoring docker-compose found"
    fi
}

# Remove HAProxy traffic router
remove_haproxy() {
    log_info "Removing HAProxy traffic router..."
    
    cd "$INFRASTRUCTURE_DIR/haproxy" 2>/dev/null || {
        log_warning "HAProxy directory not found"
        return 0
    }
    
    if [ -f docker-compose.yml ]; then
        docker-compose down -v --remove-orphans 2>/dev/null || {
            log_warning "Failed to stop HAProxy with docker-compose"
        }
        log_success "HAProxy traffic router removed"
    else
        log_info "No HAProxy docker-compose found"
    fi
    
    # Remove any standalone HAProxy containers
    docker rm -f haproxy-router 2>/dev/null || true
    docker rm -f traffic-router 2>/dev/null || true
}

# Remove Knative serverless
remove_knative() {
    log_info "Removing Knative serverless..."
    
    # Remove Knative service
    if kubectl get ksvc serverless-sim 2>/dev/null; then
        kubectl delete ksvc serverless-sim || log_warning "Failed to delete Knative service"
    fi
    
    # Remove Knative Serving components
    kubectl delete -f https://github.com/knative/net-kourier/releases/download/knative-v1.12.0/kourier.yaml --ignore-not-found=true || true
    kubectl delete -f https://github.com/knative/serving/releases/download/knative-v1.12.0/serving-core.yaml --ignore-not-found=true || true
    kubectl delete -f https://github.com/knative/serving/releases/download/knative-v1.12.0/serving-crds.yaml --ignore-not-found=true || true
    
    # Wait for namespaces to be fully removed
    for ns in knative-serving kourier-system; do
        if kubectl get namespace "$ns" 2>/dev/null; then
            log_info "Waiting for namespace $ns to be removed..."
            kubectl wait --for=delete namespace/"$ns" --timeout=60s 2>/dev/null || {
                log_warning "Namespace $ns cleanup timed out"
            }
        fi
    done
    
    log_success "Knative serverless removed"
}

# Remove K3s cluster
remove_k3s() {
    log_info "Removing K3s cluster..."
    
    # Get cluster name from config
    local cluster_name="demo-hybrid"
    if [ -f "$INFRASTRUCTURE_DIR/k3s/cluster-config.yaml" ]; then
        cluster_name=$(grep -E "^name:" "$INFRASTRUCTURE_DIR/k3s/cluster-config.yaml" | cut -d: -f2 | tr -d ' ' 2>/dev/null || echo "demo-hybrid")
    fi
    
    # Delete k3d cluster
    if k3d cluster list | grep -q "$cluster_name"; then
        k3d cluster delete "$cluster_name"
        log_success "K3s cluster '$cluster_name' removed"
    else
        log_info "K3s cluster '$cluster_name' not found"
    fi
    
    # Remove any other k3d clusters that might exist
    local other_clusters=$(k3d cluster list -o json 2>/dev/null | jq -r '.[].name' 2>/dev/null || true)
    if [ -n "$other_clusters" ]; then
        for cluster in $other_clusters; do
            if [ "$cluster" != "$cluster_name" ]; then
                log_warning "Found additional k3d cluster: $cluster"
                read -p "Remove cluster '$cluster'? [y/N]: " -n 1 -r
                echo
                if [[ $REPLY =~ ^[Yy]$ ]]; then
                    k3d cluster delete "$cluster"
                    log_success "Cluster '$cluster' removed"
                fi
            fi
        done
    fi
}

# Clean up Docker resources
cleanup_docker() {
    log_info "Cleaning up Docker resources..."
    
    # Remove unused containers
    local unused_containers=$(docker ps -aq --filter "status=exited" 2>/dev/null || true)
    if [ -n "$unused_containers" ]; then
        docker rm $unused_containers 2>/dev/null || true
        log_info "Removed exited containers"
    fi
    
    # Remove unused networks (but keep standard ones)
    local unused_networks=$(docker network ls --filter "driver=bridge" --format "{{.Name}}" | grep -E "(k3d|demo|hybrid)" 2>/dev/null || true)
    if [ -n "$unused_networks" ]; then
        for network in $unused_networks; do
            docker network rm "$network" 2>/dev/null || true
        done
        log_info "Removed project networks"
    fi
    
    # Remove unused volumes
    docker volume prune -f 2>/dev/null || true
    
    log_success "Docker cleanup completed"
}

# Verify cleanup
verify_cleanup() {
    log_info "Verifying cleanup..."
    
    # Check for remaining processes on our ports
    local ports="8080 8081 8082 8404 9090"
    local processes_found=false
    
    for port in $ports; do
        local pids=$(lsof -ti:$port 2>/dev/null || true)
        if [ -n "$pids" ]; then
            log_warning "Port $port still in use by PID(s): $pids"
            processes_found=true
        fi
    done
    
    if [ "$processes_found" = false ]; then
        log_success "All ports are clean"
    fi
    
    # Check for remaining k3d clusters
    local remaining_clusters=$(k3d cluster list -o json 2>/dev/null | jq -r '.[].name' 2>/dev/null || true)
    if [ -n "$remaining_clusters" ]; then
        log_warning "Remaining k3d clusters: $remaining_clusters"
    else
        log_success "No remaining k3d clusters"
    fi
    
    # Check for remaining Docker containers with our labels
    local remaining_containers=$(docker ps -q --filter "label=app=hybrid" 2>/dev/null || true)
    if [ -n "$remaining_containers" ]; then
        log_warning "Remaining project containers found"
        docker ps --filter "label=app=hybrid"
    else
        log_success "No remaining project containers"
    fi
}

# Force cleanup (for emergency situations)
force_cleanup() {
    log_warning "Performing force cleanup..."
    
    # Kill all processes on our ports
    for port in 8080 8081 8082 8404 9090; do
        local pids=$(lsof -ti:$port 2>/dev/null || true)
        if [ -n "$pids" ]; then
            echo "$pids" | xargs kill -9 2>/dev/null || true
            log_info "Force killed processes on port $port"
        fi
    done
    
    # Remove all k3d clusters
    k3d cluster delete --all 2>/dev/null || true
    
    # Force remove Docker containers
    docker rm -f $(docker ps -aq) 2>/dev/null || true
    
    # Clean up networks and volumes
    docker network prune -f 2>/dev/null || true
    docker volume prune -f 2>/dev/null || true
    
    log_warning "Force cleanup completed"
}

# Main teardown function
main() {
    local force_mode=false
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --force|-f)
                force_mode=true
                shift
                ;;
            --help|-h)
                echo "Usage: $0 [--force]"
                echo "  --force    Force cleanup (kills all processes and removes all resources)"
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done
    
    if [ "$force_mode" = true ]; then
        log_warning "Force mode enabled - this will aggressively clean up all resources"
        read -p "Continue with force cleanup? [y/N]: " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "Force cleanup cancelled"
            exit 0
        fi
        force_cleanup
        exit 0
    fi
    
    log_info "Starting Sprint 1 hybrid system teardown..."
    echo
    
    stop_port_forwarding
    echo
    
    remove_monitoring
    echo
    
    remove_haproxy
    echo
    
    remove_knative
    echo
    
    remove_k3s
    echo
    
    cleanup_docker
    echo
    
    verify_cleanup
    echo
    
    log_success "🧹 Sprint 1 hybrid system teardown complete!"
    echo
    echo -e "${BLUE}System Status:${NC}"
    echo "• All components removed"
    echo "• Ports 8080, 8081, 8082, 8404, 9090 should be available"
    echo "• Docker resources cleaned up"
    echo "• K3s clusters removed"
    echo
    echo -e "${GREEN}Environment ready for fresh deployment!${NC}"
    echo
    echo "To redeploy: ./scripts/setup.sh"
}

# Allow script to be sourced for testing
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi