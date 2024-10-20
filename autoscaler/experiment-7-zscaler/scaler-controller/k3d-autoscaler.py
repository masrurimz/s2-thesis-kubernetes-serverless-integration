#!/usr/bin/env python3

import subprocess
import time
import sys

# ===============================
# Configuration Constants
# ===============================

# Cluster Configuration
CLUSTER_NAME = 'autoscaler-cluster'
MIN_NODES = 1
MAX_NODES = 5

# Autoscaler Thresholds
CPU_UPPER_THRESHOLD = 80  # in percent
CPU_LOWER_THRESHOLD = 30  # in percent

# Resource Limits for Each Node
NODE_MEMORY_LIMIT = '2g'  # Memory limit per node (e.g., '2g' for 2 Gigabytes)
NODE_CPU_LIMIT = '2'       # CPU limit per node (e.g., '2' for 2 CPUs)

# Check Interval
CHECK_INTERVAL = 60  # in seconds

# ===============================
# Autoscaler Functions
# ===============================

def get_average_cpu_utilization():
    """
    Fetches the average CPU utilization across all nodes in the cluster.

    Returns:
        float: Average CPU utilization percentage.
    """
    try:
        result = subprocess.run(
            ['kubectl', 'top', 'nodes', '--no-headers'],
            capture_output=True,
            text=True,
            check=True
        )
        total_cpu = 0
        node_count = 0
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue
            parts = line.split()
            # CPU usage is typically in millicores (e.g., "100m")
            cpu_usage_str = parts[1]
            if cpu_usage_str.endswith('m'):
                cpu_usage = int(cpu_usage_str.rstrip('m'))
                cpu_percent = cpu_usage / 1000 * 100  # Convert to percentage
            else:
                # Assume it's in cores
                cpu_usage = float(cpu_usage_str)
                cpu_percent = cpu_usage * 100
            total_cpu += cpu_percent
            node_count += 1
        average_cpu = total_cpu / node_count if node_count else 0
        return average_cpu
    except subprocess.CalledProcessError as e:
        print(f"Error fetching metrics: {e}", file=sys.stderr)
        return 0

def get_current_node_count():
    """
    Retrieves the current number of nodes in the cluster.

    Returns:
        int: Number of nodes.
    """
    try:
        result = subprocess.run(
            ['kubectl', 'get', 'nodes', '--no-headers'],
            capture_output=True,
            text=True,
            check=True
        )
        node_count = len([line for line in result.stdout.strip().split('\n') if line])
        return node_count
    except subprocess.CalledProcessError as e:
        print(f"Error fetching node count: {e}", file=sys.stderr)
        return MIN_NODES

def scale_up():
    """
    Scales up the cluster by adding a new node with specified resource limits.
    """
    node_name = f"autoscaler-cluster-agent-{int(time.time())}"
    print(f"Scaling up: Creating node {node_name}")
    try:
        subprocess.run([
            'k3d', 'node', 'create', node_name,
            '--cluster', CLUSTER_NAME,
            '--role', 'agent',
            '--k3s-node-arg', f'--docker-opt=--memory={NODE_MEMORY_LIMIT}',
            '--k3s-node-arg', f'--docker-opt=--cpus={NODE_CPU_LIMIT}'
        ], check=True)
        print(f"Node {node_name} created successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error scaling up: {e}", file=sys.stderr)

def get_nodes_sorted_by_load():
    """
    Retrieves and sorts nodes by their CPU usage in descending order.

    Returns:
        list of tuples: List containing tuples of (node_name, cpu_percent).
    """
    try:
        result = subprocess.run(
            ['kubectl', 'top', 'nodes', '--no-headers'],
            capture_output=True,
            text=True,
            check=True
        )
        nodes = []
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue
            parts = line.split()
            name = parts[0]
            cpu_usage_str = parts[1]
            if cpu_usage_str.endswith('m'):
                cpu_usage = int(cpu_usage_str.rstrip('m'))
                cpu_percent = cpu_usage / 1000 * 100  # Convert to percentage
            else:
                cpu_usage = float(cpu_usage_str)
                cpu_percent = cpu_usage * 100
            nodes.append((name, cpu_percent))
        # Sort nodes by CPU usage in descending order
        nodes_sorted = sorted(nodes, key=lambda x: x[1], reverse=True)
        return nodes_sorted
    except subprocess.CalledProcessError as e:
        print(f"Error fetching node load: {e}", file=sys.stderr)
        return []

def scale_down():
    """
    Scales down the cluster by removing the least loaded node.
    """
    nodes_sorted = get_nodes_sorted_by_load()
    if not nodes_sorted:
        print("No nodes available to scale down.")
        return
    # Select the node with the lowest CPU usage
    node_to_remove, cpu_percent = nodes_sorted[-1]
    print(f"Scaling down: Removing node {node_to_remove} with CPU usage {cpu_percent}%")
    try:
        subprocess.run(['kubectl', 'cordon', node_to_remove], check=True)
        subprocess.run([
            'kubectl', 'drain', node_to_remove,
            '--ignore-daemonsets',
            '--delete-local-data',
            '--force'
        ], check=True)
        subprocess.run(['k3d', 'node', 'delete', node_to_remove, '--cluster', CLUSTER_NAME], check=True)
        print(f"Node {node_to_remove} removed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error scaling down: {e}", file=sys.stderr)

def main():
    """
    Main loop that continuously monitors CPU utilization and scales the cluster accordingly.
    """
    print("Starting k3d Autoscaler...")
    while True:
        average_cpu = get_average_cpu_utilization()
        print(f"Average CPU Utilization: {average_cpu:.2f}%")
        node_count = get_current_node_count()
        print(f"Current Node Count: {node_count}")
        
        if average_cpu > CPU_UPPER_THRESHOLD and node_count < MAX_NODES:
            print("CPU usage above upper threshold. Scaling up...")
            scale_up()
        elif average_cpu < CPU_LOWER_THRESHOLD and node_count > MIN_NODES:
            print("CPU usage below lower threshold. Scaling down...")
            scale_down()
        else:
            print("No scaling action required.")
        
        print(f"Sleeping for {CHECK_INTERVAL} seconds...\n")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
