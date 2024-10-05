#!/bin/bash

# Define resource limits
CPU_LIMIT="1"     # CPUs per node
MEMORY_LIMIT="1g" # Memory per node

# Get list of k3d node containers
NODES=$(docker ps --filter "name=k3d-mycluster" --format "{{.Names}}")

# Apply limits to each node container
for NODE in $NODES; do
  echo "Limiting resources for node $NODE"
  docker update --cpus=$CPU_LIMIT --memory=$MEMORY_LIMIT $NODE
done
