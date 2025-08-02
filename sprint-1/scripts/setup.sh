#!/bin/bash
# Sprint 1: Complete System Setup Script
# Deploys the entire hybrid k3s-serverless architecture with monitoring and validation

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

# Error handling
cleanup_on_error() {
    log_error "Setup failed. Running cleanup..."
    "$SCRIPT_DIR/teardown.sh" || true
    exit 1
}

trap cleanup_on_error ERR

# Pre-flight checks
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is required but not installed"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running"
        exit 1
    fi
    
    # Check k3d
    if ! command -v k3d &> /dev/null; then
        log_error "k3d is required but not installed"
        exit 1
    fi
    
    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is required but not installed"
        exit 1
    fi
    
    # Check k6 (optional, warn only)
    if ! command -v k6 &> /dev/null; then
        log_warning "k6 not found - load testing will not be available"
    fi
    
    log_success "Prerequisites check passed"
}

# Deploy K3s cluster
deploy_k3s() {
    log_info "Deploying K3s cluster..."
    
    cd "$INFRASTRUCTURE_DIR/k3s"
    
    # Create cluster
    k3d cluster create -c cluster-config.yaml
    
    # Wait for cluster to be ready
    kubectl wait --for=condition=ready node --all --timeout=300s
    
    # Deploy nginx application
    kubectl apply -f nginx-deployment.yaml
    kubectl apply -f nginx-service.yaml
    
    # Wait for deployment to be ready
    kubectl wait --for=condition=available deployment/nginx-app --timeout=300s
    
    log_success "K3s cluster deployed and ready on port 8080"
}

# Deploy Knative serverless
deploy_knative() {
    log_info "Deploying Knative serverless..."
    
    cd "$INFRASTRUCTURE_DIR/serverless"
    
    # Install Knative Serving
    kubectl apply -f https://github.com/knative/serving/releases/download/knative-v1.12.0/serving-crds.yaml
    kubectl apply -f https://github.com/knative/serving/releases/download/knative-v1.12.0/serving-core.yaml
    
    # Install Kourier networking
    kubectl apply -f https://github.com/knative/net-kourier/releases/download/knative-v1.12.0/kourier.yaml
    
    # Configure Knative to use Kourier
    kubectl patch configmap/config-network \
        --namespace knative-serving \
        --type merge \
        --patch '{"data":{"ingress-class":"kourier.ingress.networking.knative.dev"}}'
    
    # Wait for Knative to be ready
    kubectl wait --for=condition=ready pod --all -n knative-serving --timeout=300s
    kubectl wait --for=condition=ready pod --all -n kourier-system --timeout=300s
    
    # Deploy Knative service
    kubectl apply -f knative-service.yaml
    
    # Wait for Knative service to be ready
    kubectl wait --for=condition=ready ksvc/serverless-sim --timeout=300s
    
    # Start port forwarding in background
    kubectl port-forward -n kourier-system service/kourier 8081:80 --address=0.0.0.0 &
    PORT_FORWARD_PID=$!
    echo $PORT_FORWARD_PID > /tmp/knative-port-forward.pid
    
    # Wait a moment for port forwarding to establish
    sleep 5
    
    log_success "Knative serverless deployed and ready on port 8081"
}

# Deploy HAProxy traffic router
deploy_haproxy() {
    log_info "Deploying HAProxy traffic router..."
    
    cd "$INFRASTRUCTURE_DIR/haproxy"
    
    # Start HAProxy
    docker-compose up -d
    
    # Wait for HAProxy to be ready
    for i in {1..30}; do
        if curl -sf http://localhost:8082 > /dev/null; then
            break
        fi
        if [ $i -eq 30 ]; then
            log_error "HAProxy failed to start"
            exit 1
        fi
        sleep 2
    done
    
    log_success "HAProxy traffic router deployed and ready on port 8082"
}

# Deploy monitoring (optional based on resources)
deploy_monitoring() {
    log_info "Deploying monitoring stack..."
    
    cd "$INFRASTRUCTURE_DIR/monitoring"
    
    # Check if monitoring docker-compose exists
    if [ -f docker-compose.yml ]; then
        docker-compose up -d
        
        # Wait for Prometheus to be ready
        for i in {1..30}; do
            if curl -sf http://localhost:9090/-/ready > /dev/null 2>&1; then
                break
            fi
            if [ $i -eq 30 ]; then
                log_warning "Prometheus monitoring failed to start - continuing without full monitoring"
                return 0
            fi
            sleep 2
        done
        
        log_success "Monitoring stack deployed on port 9090"
    else
        log_info "Using lightweight script-based monitoring"
    fi
}

# Validate deployment
validate_deployment() {
    log_info "Validating complete deployment..."
    
    # Test K3s backend
    if curl -sf http://localhost:8080 > /dev/null; then
        log_success "K3s backend responding on port 8080"
    else
        log_error "K3s backend not responding"
        exit 1
    fi
    
    # Test Knative backend
    if curl -sf -H "Host: serverless-sim.default.localhost" http://localhost:8081 > /dev/null; then
        log_success "Knative backend responding on port 8081"
    else
        log_warning "Knative backend not responding - may need time to warm up"
    fi
    
    # Test HAProxy hybrid endpoint
    if curl -sf http://localhost:8082 > /dev/null; then
        log_success "HAProxy hybrid endpoint responding on port 8082"
    else
        log_error "HAProxy hybrid endpoint not responding"
        exit 1
    fi
    
    # Test HAProxy stats
    if curl -sf http://localhost:8404/stats > /dev/null; then
        log_success "HAProxy stats available on port 8404"
    else
        log_warning "HAProxy stats not available"
    fi
    
    # Run health check
    if [ -f "$SCRIPT_DIR/check-health.sh" ]; then
        log_info "Running comprehensive health check..."
        "$SCRIPT_DIR/check-health.sh"
    fi
}

# Main deployment function
main() {
    log_info "Starting Sprint 1 hybrid system deployment..."
    echo
    
    check_prerequisites
    echo
    
    deploy_k3s
    echo
    
    deploy_knative
    echo
    
    deploy_haproxy
    echo
    
    deploy_monitoring
    echo
    
    validate_deployment
    echo
    
    log_success "🎉 Sprint 1 hybrid system deployment complete!"
    echo
    echo -e "${BLUE}System Access:${NC}"
    echo "• K3s cluster: http://localhost:8080"
    echo "• Knative serverless: http://localhost:8081 (with Host: serverless-sim.default.localhost)"
    echo "• HAProxy hybrid: http://localhost:8082 (80/20 distribution)"
    echo "• HAProxy stats: http://localhost:8404/stats"
    echo "• Monitoring: http://localhost:9090 (if enabled)"
    echo
    echo -e "${BLUE}Management Commands:${NC}"
    echo "• Health check: ./scripts/check-health.sh"
    echo "• System monitor: ./scripts/monitor-system.sh"
    echo "• Adjust weights: ./scripts/adjust-weights.sh <k3s%> <knative%>"
    echo "• Load testing: ./load-testing/run-load-tests.sh"
    echo "• Cleanup: ./scripts/teardown.sh"
    echo
    echo -e "${GREEN}Ready for Sprint 1 evaluation and Sprint 2 development!${NC}"
}

# Allow script to be sourced for testing
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi