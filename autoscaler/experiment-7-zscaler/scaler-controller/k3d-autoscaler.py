#!/usr/bin/env python3

import subprocess
import time
import sys
import logging
from datetime import datetime

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
NODE_MEMORY_LIMIT = '512M'       # Memory limit per node (e.g., '512M' for 512 Megabytes)
NODE_CPU_LIMIT = '1'             # CPU limit per node (e.g., '1' for 1 CPU)
NODE_MEMORY_SWAP_LIMIT = '512M'  # Memory swap limit per node (set equal to NODE_MEMORY_LIMIT)

# Check Interval and Cooldown Periods
CHECK_INTERVAL = 60      # in seconds
COOLDOWN_PERIOD = 120   # in seconds

# Logging Configuration
LOG_FILE = 'k3d_autoscaler.log'
LOG_LEVEL = logging.INFO  # Can be set to DEBUG for more verbosity

# ===============================
# Logging Setup
# ===============================

logging.basicConfig(
    filename=LOG_FILE,
    level=LOG_LEVEL,
    format='%(asctime)s %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Also log to stdout
console = logging.StreamHandler()
console.setLevel(LOG_LEVEL)
formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)

# ===============================
# Autoscaler Functions
# ===============================

def is_metrics_server_available():
    """
    Checks if the Metrics Server is available by attempting to fetch node metrics.
    
    Returns:
        bool: True if available, False otherwise.
    """
    try:
        subprocess.run(
            ['kubectl', 'top', 'nodes'],
            capture_output=True,
            text=True,
            check=True
        )
        logging.debug("Metrics Server is available.")
        return True
    except subprocess.CalledProcessError:
        logging.error("Metrics Server is not available. Ensure it is installed and running.")
        return False

def get_average_cpu_utilization():
    """
    Fetches the average CPU utilization across all agent nodes in the cluster.

    Returns:
        float: Average CPU utilization percentage, or None if unavailable.
    """
    try:
        result = subprocess.run(
            ['kubectl', 'top', 'nodes', '-l', 'k3s.io/role=agent', '--no-headers'],
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
                cpu_percent = (cpu_usage / 1000) * 100  # Convert to percentage
            else:
                # Assume it's in cores
                cpu_usage = float(cpu_usage_str)
                cpu_percent = cpu_usage * 100
            total_cpu += cpu_percent
            node_count += 1
        average_cpu = total_cpu / node_count if node_count else 0
        logging.debug(f"Total CPU: {total_cpu}, Node Count: {node_count}, Average CPU: {average_cpu}")
        return average_cpu
    except subprocess.CalledProcessError as e:
        logging.error(f"Error fetching metrics: {e}")
        return None

def get_current_node_count():
    """
    Retrieves the current number of agent nodes in the cluster.

    Returns:
        int: Number of agent nodes.
    """
    try:
        result = subprocess.run(
            ['kubectl', 'get', 'nodes', '-l', 'k3s.io/role=agent', '--no-headers'],
            capture_output=True,
            text=True,
            check=True
        )
        node_count = len([line for line in result.stdout.strip().split('\n') if line])
        logging.debug(f"Current agent node count: {node_count}")
        return node_count
    except subprocess.CalledProcessError as e:
        logging.error(f"Error fetching node count: {e}")
        return MIN_NODES

def get_current_docker_containers():
    """
    Retrieves the set of current Docker container names.

    Returns:
        set: Set containing the names of all running Docker containers.
    """
    try:
        result = subprocess.run(
            ['docker', 'ps', '--format', '{{.Names}}'],
            capture_output=True,
            text=True,
            check=True
        )
        containers = set(result.stdout.strip().split('\n'))
        logging.debug(f"Current Docker containers: {containers}")
        return containers
    except subprocess.CalledProcessError as e:
        logging.error(f"Error fetching Docker containers: {e}")
        return set()

def get_docker_container_by_node(node_name):
    """
    Retrieves the Docker container name associated with a given Kubernetes node.

    Args:
        node_name (str): Name of the Kubernetes node.

    Returns:
        str or None: Docker container name if found, else None.
    """
    try:
        # List Docker containers with name matching the node
        result = subprocess.run(
            ['docker', 'ps', '--filter', f'name={node_name}', '--format', '{{.Names}}'],
            capture_output=True,
            text=True,
            check=True
        )
        container_name = result.stdout.strip()
        if container_name:
            logging.debug(f"Found Docker container '{container_name}' for node '{node_name}'.")
            return container_name
        else:
            logging.warning(f"No Docker container found for node '{node_name}'.")
            return None
    except subprocess.CalledProcessError as e:
        logging.error(f"Error fetching Docker container for node '{node_name}': {e}")
        return None

def ensure_resource_limits_on_existing_nodes():
    """
    Ensures that all existing agent nodes in the cluster have the specified resource limits applied.
    """
    logging.info("Ensuring resource limits on existing agent nodes...")
    try:
        result = subprocess.run(
            ['kubectl', 'get', 'nodes', '-l', 'k3s.io/role=agent', '--no-headers'],
            capture_output=True,
            text=True,
            check=True
        )
        node_names = [line.split()[0] for line in result.stdout.strip().split('\n') if line]
        logging.debug(f"Existing agent nodes: {node_names}")

        for node in node_names:
            docker_container_name = get_docker_container_by_node(node)
            if not docker_container_name:
                logging.warning(f"Skipping node '{node}' as its Docker container could not be identified.")
                continue

            # Retrieve current resource limits
            try:
                inspect_result = subprocess.run(
                    ['docker', 'inspect', docker_container_name],
                    capture_output=True,
                    text=True,
                    check=True
                )
                # Check if Memory, MemorySwap, and CpuQuota are already set as desired
                if (f'"Memory": "{NODE_MEMORY_LIMIT}"' in inspect_result.stdout and
                    f'"MemorySwap": "{NODE_MEMORY_SWAP_LIMIT}"' in inspect_result.stdout and
                    f'"NanoCpus": {int(float(NODE_CPU_LIMIT) * 1e9)}' in inspect_result.stdout):
                    logging.info(f"Node '{node}' already has the desired resource limits.")
                    continue  # Resource limits are already set
            except subprocess.CalledProcessError as e:
                logging.error(f"Error inspecting Docker container '{docker_container_name}': {e}")
                continue

            logging.info(f"Applying resource limits to existing node '{node}' (Container: {docker_container_name})")
            try:
                subprocess.run([
                    'docker', 'update',
                    '--cpus', NODE_CPU_LIMIT,
                    '--memory', NODE_MEMORY_LIMIT,
                    '--memory-swap', NODE_MEMORY_SWAP_LIMIT,
                    docker_container_name
                ], check=True)
                logging.info(f"Resource limits applied to node '{node}' successfully.")
            except subprocess.CalledProcessError as e:
                logging.error(f"Error applying resource limits to node '{node}': {e}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Error fetching existing agent nodes: {e}")

def scale_up():
    """
    Scales up the cluster by adding a new agent node with specified resource limits.
    """
    node_name = f"autoscaler-cluster-agent-{int(time.time())}"
    logging.info(f"Scaling up: Creating node '{node_name}'")
    try:
        # Get existing containers before creating the node
        before_containers = get_current_docker_containers()

        # Create the node with k3d
        subprocess.run([
            'k3d', 'node', 'create', node_name,
            '--cluster', CLUSTER_NAME,
            '--role', 'agent',
            '--k3s-node-label', 'k3s.io/role=agent'
        ], check=True)
        logging.info(f"Node '{node_name}' created successfully.")

        # Allow some time for the Docker container to start
        time.sleep(5)  # Adjust as necessary based on your system's performance

        # Get new containers after creating the node
        after_containers = get_current_docker_containers()
        new_containers = after_containers - before_containers

        if not new_containers:
            logging.error("No new Docker container found for the new node.")
            return

        # Assuming only one new container was created
        docker_container_name = new_containers.pop()
        logging.info(f"Applying resource limits to Docker container '{docker_container_name}'")

        # Update the Docker container with resource limits
        subprocess.run([
            'docker', 'update',
            '--cpus', NODE_CPU_LIMIT,
            '--memory', NODE_MEMORY_LIMIT,
            '--memory-swap', NODE_MEMORY_SWAP_LIMIT,
            docker_container_name
        ], check=True)
        logging.info(f"Resource limits applied to node '{node_name}' successfully.")

        # Optional: Cooldown after scaling up
        logging.info(f"Cooling down for {COOLDOWN_PERIOD} seconds after scaling up.")
        time.sleep(COOLDOWN_PERIOD)

    except subprocess.CalledProcessError as e:
        logging.error(f"Error scaling up: {e}")

def get_nodes_sorted_by_load():
    """
    Retrieves and sorts agent nodes by their CPU usage in descending order.

    Returns:
        list of tuples: List containing tuples of (node_name, cpu_percent).
    """
    try:
        result = subprocess.run(
            ['kubectl', 'top', 'nodes', '-l', 'k3s.io/role=agent', '--no-headers'],
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
                cpu_percent = (cpu_usage / 1000) * 100  # Convert to percentage
            else:
                cpu_usage = float(cpu_usage_str)
                cpu_percent = cpu_usage * 100
            nodes.append((name, cpu_percent))
        # Sort nodes by CPU usage in descending order
        nodes_sorted = sorted(nodes, key=lambda x: x[1], reverse=True)
        logging.debug(f"Nodes sorted by load: {nodes_sorted}")
        return nodes_sorted
    except subprocess.CalledProcessError as e:
        logging.error(f"Error fetching node load: {e}")
        return []

def scale_down():
    """
    Scales down the cluster by removing the least loaded agent node.
    """
    nodes_sorted = get_nodes_sorted_by_load()
    if not nodes_sorted:
        logging.warning("No agent nodes available to scale down.")
        return
    # Select the node with the lowest CPU usage
    node_to_remove, cpu_percent = nodes_sorted[-1]
    logging.info(f"Scaling down: Removing node '{node_to_remove}' with CPU usage {cpu_percent}%")
    try:
        # Cordon the node to prevent new pods from being scheduled
        subprocess.run(['kubectl', 'cordon', node_to_remove], check=True)
        logging.debug(f"Node '{node_to_remove}' cordoned successfully.")

        # Drain the node to remove all pods
        subprocess.run([
            'kubectl', 'drain', node_to_remove,
            '--ignore-daemonsets',
            '--delete-local-data',
            '--force'
        ], check=True)
        logging.debug(f"Node '{node_to_remove}' drained successfully.")

        # Delete the node from the k3d cluster
        subprocess.run(['k3d', 'node', 'delete', node_to_remove, '--cluster', CLUSTER_NAME], check=True)
        logging.info(f"Node '{node_to_remove}' removed successfully.")

        # Optional: Cooldown after scaling down
        logging.info(f"Cooling down for {COOLDOWN_PERIOD} seconds after scaling down.")
        time.sleep(COOLDOWN_PERIOD)

    except subprocess.CalledProcessError as e:
        logging.error(f"Error scaling down: {e}")

def main():
    """
    Main loop that continuously monitors CPU utilization and scales the cluster accordingly.
    """
    logging.info("Starting k3d Autoscaler...")

    # Ensure resource limits on existing agent nodes at startup
    ensure_resource_limits_on_existing_nodes()

    while True:
        if not is_metrics_server_available():
            logging.warning("Metrics Server is unavailable. Skipping this cycle.")
        else:
            average_cpu = get_average_cpu_utilization()
            if average_cpu is None:
                logging.warning("Could not retrieve average CPU utilization. Skipping this cycle.")
            else:
                logging.info(f"Average CPU Utilization: {average_cpu:.2f}%")
                node_count = get_current_node_count()
                logging.info(f"Current Agent Node Count: {node_count}")

                if average_cpu > CPU_UPPER_THRESHOLD and node_count < MAX_NODES:
                    logging.info("CPU usage above upper threshold. Initiating scale up...")
                    scale_up()
                elif average_cpu < CPU_LOWER_THRESHOLD and node_count > MIN_NODES:
                    logging.info("CPU usage below lower threshold. Initiating scale down...")
                    scale_down()
                else:
                    logging.info("No scaling action required.")

        logging.info(f"Sleeping for {CHECK_INTERVAL} seconds...\n")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logging.info("Autoscaler terminated by user.")
        sys.exit(0)
    except Exception as e:
        logging.exception(f"Unexpected error: {e}")
        sys.exit(1)
