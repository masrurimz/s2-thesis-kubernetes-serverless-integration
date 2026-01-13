#!/bin/bash

# Monitor Cluster Autoscaler logs and simulate node scaling

KUBECTL="kubectl"
CLUSTER_NAME="mycluster"

CPU_LIMIT="0.5"          # CPUs per node
MEMORY_LIMIT="500m"      # Memory per node
MEMORY_SWAP_LIMIT="500m" # Memory swap per node

# Function to add a node
add_node() {
  NODE_COUNT=$(k3d node list | grep "${CLUSTER_NAME}-agent" | wc -l)
  NODE_NAME="k3d-${CLUSTER_NAME}-agent-${NODE_COUNT}"
  echo "Adding node $NODE_NAME..."
  k3d node create $NODE_NAME --cluster $CLUSTER_NAME --role agent
  # Apply resource limits
  docker update --cpus=$CPU_LIMIT --memory=$MEMORY_LIMIT --memory-swap=$MEMORY_SWAP_LIMIT $NODE_NAME
}

# Function to remove a node
remove_node() {
  NODE_NAME=$(k3d node list | grep "${CLUSTER_NAME}-agent" | tail -1 | awk '{print $1}')
  if [ -n "$NODE_NAME" ]; then
    echo "Removing node $NODE_NAME..."
    k3d node delete $NODE_NAME
  else
    echo "No agent nodes to remove."
  fi
}

# Monitor Cluster Autoscaler logs
echo "Monitoring Cluster Autoscaler logs..."
$KUBECTL -n kube-system logs -f deployment/cluster-autoscaler | while read -r line; do
  if echo "$line" | grep -q "Scale-up"; then
    echo "Scale-up event detected."
    add_node
  elif echo "$line" | grep -q "Scale-down"; then
    echo "Scale-down event detected."
    remove_node
  fi
done
