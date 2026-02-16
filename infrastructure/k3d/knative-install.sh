#!/usr/bin/env bash
# Install Knative Serving + Kourier on k3d cluster
# Usage: ./knative-install.sh

set -euo pipefail

# Knative versions
KNATIVE_VERSION="${KNATIVE_VERSION:-1.12.0}"
KOURIER_VERSION="${KOURIER_VERSION:-1.12.0}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Check cluster is running
check_cluster() {
    log_info "Checking cluster connectivity..."
    
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster. Is k3d running?"
        exit 1
    fi
    
    log_info "Cluster is accessible."
}

# Install Knative Serving CRDs and core
install_knative_serving() {
    log_info "Installing Knative Serving v${KNATIVE_VERSION}..."
    
    # Install CRDs
    kubectl apply -f "https://github.com/knative/serving/releases/download/knative-v${KNATIVE_VERSION}/serving-crds.yaml"
    
    # Install core components
    kubectl apply -f "https://github.com/knative/serving/releases/download/knative-v${KNATIVE_VERSION}/serving-core.yaml"
    
    log_info "Waiting for Knative Serving to be ready..."
    kubectl wait --for=condition=Available deployment --all -n knative-serving --timeout=180s
}

# Install Kourier networking layer
install_kourier() {
    log_info "Installing Kourier v${KOURIER_VERSION}..."
    
    kubectl apply -f "https://github.com/knative/net-kourier/releases/download/knative-v${KOURIER_VERSION}/kourier.yaml"
    
    log_info "Waiting for Kourier to be ready..."
    kubectl wait --for=condition=Available deployment --all -n kourier-system --timeout=120s
    
    # Configure Knative to use Kourier
    kubectl patch configmap/config-network \
        --namespace knative-serving \
        --type merge \
        --patch '{"data":{"ingress-class":"kourier.ingress.networking.knative.dev"}}'
}

# Configure Kourier NodePort for k3d access
configure_kourier_nodeport() {
    log_info "Configuring Kourier with NodePort for k3d access..."
    
    # Patch Kourier service to use NodePort on 31080
    kubectl patch svc kourier -n kourier-system --type='json' -p='[
      {"op": "replace", "path": "/spec/type", "value": "NodePort"},
      {"op": "add", "path": "/spec/ports/0/nodePort", "value": 31080}
    ]'
    
    log_info "Kourier configured on NodePort 31080 (accessible at localhost:8081)"
}

# Configure DNS for Knative
configure_dns() {
    log_info "Configuring DNS for local development..."
    
    # Use sslip.io for automatic DNS resolution
    kubectl patch configmap/config-domain \
        --namespace knative-serving \
        --type merge \
        --patch '{"data":{"127.0.0.1.sslip.io":""}}'
    
    log_info "DNS configured to use sslip.io"
}

# Configure autoscaling defaults
configure_autoscaling() {
    log_info "Configuring Knative autoscaling defaults..."
    
    kubectl patch configmap/config-autoscaler \
        --namespace knative-serving \
        --type merge \
        --patch '{
          "data": {
            "enable-scale-to-zero": "true",
            "scale-to-zero-grace-period": "30s",
            "scale-to-zero-pod-retention-period": "0s",
            "stable-window": "60s",
            "panic-window-percentage": "10",
            "panic-threshold-percentage": "200",
            "max-scale-up-rate": "1000",
            "max-scale-down-rate": "2",
            "target-burst-capacity": "200",
            "requests-per-second-target-default": "200"
          }
        }'
    
    log_info "Autoscaling configured."
}

# Configure node isolation for Knative and workload scheduling
configure_node_isolation() {
    log_info "Configuring Knative node isolation..."
    
    # Enable nodeSelector support in Knative features
    kubectl patch configmap/config-features \
        --namespace knative-serving \
        --type merge \
        --patch '{"data":{"kubernetes.podspec-nodeselector":"enabled"}}'
    
    # Patch Kourier gateway to run on infra node
    kubectl -n kourier-system patch deploy kourier-gateway \
        --type='json' \
        -p='[{"op":"add","path":"/spec/template/spec/nodeSelector","value":{"node-type":"infra"}}]'
    
    log_info "Node isolation configured."
}

# Verify installation
verify_installation() {
    log_info "Verifying Knative installation..."
    
    echo ""
    echo "=== Knative Serving Pods ==="
    kubectl get pods -n knative-serving
    
    echo ""
    echo "=== Kourier Pods ==="
    kubectl get pods -n kourier-system
    
    echo ""
    echo "=== Kourier Service ==="
    kubectl get svc -n kourier-system
    
    echo ""
    echo "=== Knative Domain Configuration ==="
    kubectl get configmap config-domain -n knative-serving -o jsonpath='{.data}' | jq .
    
    echo ""
    log_info "Knative + Kourier installation complete!"
    log_info "Kourier is accessible at: http://localhost:8081"
    log_info "Services will be available at: http://<service>.<namespace>.127.0.0.1.sslip.io:8081"
}

# Deploy a test service
deploy_test_service() {
    if [[ "${1:-}" == "--test" ]]; then
        log_info "Deploying test Knative service..."
        
        cat <<EOF | kubectl apply -f -
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: hello
  namespace: default
spec:
  template:
    spec:
      containers:
        - image: gcr.io/knative-samples/helloworld-go
          ports:
            - containerPort: 8080
          env:
            - name: TARGET
              value: "Knative on k3d"
EOF
        
        log_info "Waiting for test service to be ready..."
        kubectl wait --for=condition=Ready ksvc/hello -n default --timeout=120s
        
        echo ""
        echo "=== Test Service ==="
        kubectl get ksvc hello -n default
        
        echo ""
        log_info "Test service deployed! Try: curl http://hello.default.127.0.0.1.sslip.io:8081"
    fi
}

# Main
main() {
    log_info "Starting Knative + Kourier installation..."
    
    check_cluster
    install_knative_serving
    install_kourier
    configure_kourier_nodeport
    configure_dns
    configure_autoscaling
    configure_node_isolation
    verify_installation
    deploy_test_service "${1:-}"
}

main "$@"
