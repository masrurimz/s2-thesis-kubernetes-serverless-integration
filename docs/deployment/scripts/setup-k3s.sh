#!/usr/bin/env bash
# K3s Single-Node Installation for VPS
# Target: 6-core/8GB VPS (Ubuntu 22.04)
# Usage: ./setup-k3s.sh

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
K3S_VERSION="${K3S_VERSION:-v1.28.5+k3s1}"
INSTALL_DIR="/usr/local/bin"

# Check system requirements
check_requirements() {
    log_info "Checking system requirements..."
    
    # Check CPU cores
    CORES=$(nproc)
    if [ "$CORES" -lt 4 ]; then
        log_warn "Found $CORES cores. Recommended: 6+ cores for production."
    else
        log_info "CPU cores: $CORES (OK)"
    fi
    
    # Check RAM
    RAM_KB=$(grep MemTotal /proc/meminfo | awk '{print $2}')
    RAM_GB=$((RAM_KB / 1024 / 1024))
    if [ "$RAM_GB" -lt 6 ]; then
        log_warn "Found ${RAM_GB}GB RAM. Recommended: 8GB+ for production."
    else
        log_info "RAM: ${RAM_GB}GB (OK)"
    fi
    
    # Check disk space
    DISK_GB=$(df -BG / | awk 'NR==2 {print $4}' | sed 's/G//')
    if [ "$DISK_GB" -lt 20 ]; then
        log_error "Insufficient disk space: ${DISK_GB}GB. Need at least 20GB."
        exit 1
    else
        log_info "Disk space: ${DISK_GB}GB available (OK)"
    fi
    
    # Check if Docker is installed (optional but recommended)
    if command -v docker &> /dev/null; then
        log_info "Docker found: $(docker --version)"
    else
        log_warn "Docker not found. Install for container builds."
    fi
}

# Disable swap (recommended for Kubernetes)
disable_swap() {
    log_info "Disabling swap..."
    
    if [ "$(swapon --show | wc -l)" -gt 0 ]; then
        sudo swapoff -a
        sudo sed -i '/ swap / s/^\(.*\)$/#\1/g' /etc/fstab
        log_info "Swap disabled."
    else
        log_info "Swap already disabled."
    fi
}

# Configure kernel parameters
configure_kernel() {
    log_info "Configuring kernel parameters..."
    
    cat <<EOF | sudo tee /etc/sysctl.d/k3s.conf
# K3s recommended kernel parameters
net.bridge.bridge-nf-call-iptables = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.ipv4.ip_forward = 1
vm.max_map_count = 262144
fs.inotify.max_user_instances = 8192
fs.inotify.max_user_watches = 524288
EOF

    sudo sysctl --system > /dev/null 2>&1
    log_info "Kernel parameters configured."
}

# Install K3s
install_k3s() {
    log_info "Installing K3s ${K3S_VERSION}..."
    
    # Install K3s with specific options for VPS deployment
    curl -sfL https://get.k3s.io | INSTALL_K3S_VERSION="${K3S_VERSION}" sh -s - \
        --disable traefik \
        --disable servicelb \
        --write-kubeconfig-mode 644 \
        --kubelet-arg="eviction-hard=memory.available<200Mi" \
        --kubelet-arg="eviction-soft=memory.available<500Mi" \
        --kubelet-arg="eviction-soft-grace-period=memory.available=1m" \
        --kubelet-arg="system-reserved=memory=512Mi" \
        --kubelet-arg="kube-reserved=memory=512Mi"
    
    log_info "K3s installed successfully."
}

# Wait for K3s to be ready
wait_for_k3s() {
    log_info "Waiting for K3s to be ready..."
    
    local retries=30
    local count=0
    
    while [ $count -lt $retries ]; do
        if kubectl get nodes &> /dev/null; then
            NODE_STATUS=$(kubectl get nodes -o jsonpath='{.items[0].status.conditions[?(@.type=="Ready")].status}')
            if [ "$NODE_STATUS" == "True" ]; then
                log_info "K3s node is ready!"
                break
            fi
        fi
        
        count=$((count + 1))
        log_info "Waiting for node to be ready... ($count/$retries)"
        sleep 10
    done
    
    if [ $count -eq $retries ]; then
        log_error "K3s node did not become ready in time."
        exit 1
    fi
}

# Configure kubectl for current user
configure_kubectl() {
    log_info "Configuring kubectl..."
    
    # Create .kube directory
    mkdir -p "$HOME/.kube"
    
    # Copy kubeconfig
    sudo cp /etc/rancher/k3s/k3s.yaml "$HOME/.kube/config"
    sudo chown "$(id -u):$(id -g)" "$HOME/.kube/config"
    
    # Add to bashrc if not already present
    if ! grep -q "KUBECONFIG" "$HOME/.bashrc"; then
        echo 'export KUBECONFIG=$HOME/.kube/config' >> "$HOME/.bashrc"
    fi
    
    export KUBECONFIG="$HOME/.kube/config"
    
    log_info "kubectl configured. Run 'source ~/.bashrc' or start a new shell."
}

# Create monitoring namespace
create_namespaces() {
    log_info "Creating namespaces..."
    
    kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -
    kubectl create namespace knative-serving --dry-run=client -o yaml | kubectl apply -f -
    kubectl create namespace kourier-system --dry-run=client -o yaml | kubectl apply -f -
    
    log_info "Namespaces created."
}

# Install metrics-server for HPA
install_metrics_server() {
    log_info "Installing metrics-server..."
    
    kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
    
    # Patch for single-node clusters (skip TLS verification)
    kubectl patch deployment metrics-server -n kube-system --type='json' -p='[
      {"op": "add", "path": "/spec/template/spec/containers/0/args/-", "value": "--kubelet-insecure-tls"},
      {"op": "add", "path": "/spec/template/spec/containers/0/args/-", "value": "--kubelet-preferred-address-types=InternalIP"}
    ]'
    
    log_info "Waiting for metrics-server to be ready..."
    kubectl wait --for=condition=Available deployment/metrics-server -n kube-system --timeout=120s
    
    log_info "metrics-server installed."
}

# Verify installation
verify_installation() {
    log_info "Verifying K3s installation..."
    
    echo ""
    echo "=== Node Status ==="
    kubectl get nodes -o wide
    
    echo ""
    echo "=== System Pods ==="
    kubectl get pods -n kube-system
    
    echo ""
    echo "=== K3s Version ==="
    k3s --version
    
    echo ""
    echo "=== Cluster Info ==="
    kubectl cluster-info
    
    echo ""
    log_info "K3s installation complete!"
    log_info "Next steps:"
    log_info "  1. Run Knative installation: ./infrastructure/k3d/knative-install.sh"
    log_info "  2. Run Prometheus setup: ./docs/deployment/scripts/setup-prometheus.sh"
}

# Main
main() {
    log_info "Starting K3s installation for VPS..."
    
    check_requirements
    disable_swap
    configure_kernel
    install_k3s
    wait_for_k3s
    configure_kubectl
    create_namespaces
    install_metrics_server
    verify_installation
}

main "$@"
