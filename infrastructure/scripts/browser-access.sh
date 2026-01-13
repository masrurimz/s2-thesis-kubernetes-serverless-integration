#!/bin/bash

echo "=== Sprint 1 Browser Access Helper ==="
echo ""

# Option 1: Domain mapping (requires setup)
echo "🌐 Option 1: Browser-friendly domain mapping"
echo "Setup:"
echo "  kubectl apply -f infrastructure/serverless/domain-mapping.yaml"
echo "  echo '127.0.0.1 serverless.localhost' | sudo tee -a /etc/hosts"
echo "Access:"
echo "  http://serverless.localhost:8081"
echo ""

# Option 2: Direct port forwarding
echo "🔗 Option 2: Direct service port forwarding"
echo "Setup:"
echo "  kubectl port-forward svc/serverless-sim 8083:80 &"
echo "Access:"
echo "  http://localhost:8083"
echo ""

# Option 3: Proxy with headers
echo "🚀 Option 3: Simple proxy with headers (RECOMMENDED)"
echo "Setup: Run this script with --proxy"
echo "Access: http://localhost:8085"
echo ""

# Option 4: Through HAProxy (current working method)
echo "⚖️  Option 4: Through HAProxy (works now)"
echo "Access: http://localhost:8082 (80/20 mix of K3s and Knative)"
echo ""

if [[ "$1" == "--proxy" ]]; then
    echo "Starting simple HTTP proxy for Knative..."
    echo "Access Knative at: http://localhost:8085"
    echo "Press Ctrl+C to stop"
    
    # Simple socat proxy that adds the Host header
    while true; do
        echo "Proxy ready on port 8085..."
        socat TCP-LISTEN:8085,reuseaddr,fork EXEC:"bash -c 'echo \"GET / HTTP/1.1\r\nHost: serverless-sim.default.localhost\r\nConnection: close\r\n\r\n\" | nc localhost 8081'"
        sleep 1
    done
elif [[ "$1" == "--setup-domain" ]]; then
    echo "Setting up domain mapping..."
    kubectl apply -f infrastructure/serverless/domain-mapping.yaml
    echo "Add this to /etc/hosts (requires sudo):"
    echo "127.0.0.1 serverless.localhost"
    echo ""
    echo "Then access: http://serverless.localhost:8081"
elif [[ "$1" == "--direct-port" ]]; then
    echo "Setting up direct port forwarding..."
    kubectl port-forward svc/serverless-sim 8083:80 --address=0.0.0.0 &
    echo "Access at: http://localhost:8083"
    echo "PID: $!"
else
    echo "Usage:"
    echo "  $0                  # Show all options"
    echo "  $0 --proxy         # Start simple proxy on port 8085"
    echo "  $0 --setup-domain  # Setup domain mapping"
    echo "  $0 --direct-port   # Setup direct port forwarding"
fi