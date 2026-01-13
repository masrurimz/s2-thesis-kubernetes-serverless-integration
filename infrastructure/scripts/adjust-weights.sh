#!/bin/bash

# HAProxy Weight Adjustment Script
# Usage: ./adjust-weights.sh <k3s_weight> <serverless_weight>
# Example: ./adjust-weights.sh 60 40

set -e

if [ $# -ne 2 ]; then
    echo "Usage: $0 <k3s_weight> <serverless_weight>"
    echo "Example: $0 60 40  # 60% k3s, 40% serverless"
    exit 1
fi

K3S_WEIGHT=$1
SERVERLESS_WEIGHT=$2
CONTAINER_NAME="sprint1-haproxy"

echo "Adjusting traffic weights..."
echo "K3s cluster: ${K3S_WEIGHT}%"
echo "Serverless: ${SERVERLESS_WEIGHT}%"

# Check if HAProxy container is running
if ! docker ps | grep -q $CONTAINER_NAME; then
    echo "Error: HAProxy container '$CONTAINER_NAME' is not running"
    exit 1
fi

# Adjust weights via HAProxy socket
echo "set weight servers/k3s-cluster $K3S_WEIGHT" | docker exec -i $CONTAINER_NAME socat - /tmp/haproxy.sock
echo "set weight servers/serverless-sim $SERVERLESS_WEIGHT" | docker exec -i $CONTAINER_NAME socat - /tmp/haproxy.sock

# Verify changes
echo ""
echo "Current weight distribution:"
echo "show stat" | docker exec -i $CONTAINER_NAME socat - /tmp/haproxy.sock | grep servers | cut -d',' -f1,2,19 | sed 's/,/ | /g'

echo ""
echo "Weight adjustment complete!"
echo "View stats at: http://localhost:8404/stats"