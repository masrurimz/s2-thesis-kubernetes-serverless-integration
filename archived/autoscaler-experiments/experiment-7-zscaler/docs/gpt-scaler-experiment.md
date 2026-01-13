Certainly! Let's integrate all the steps into a cohesive setup that allows you to create, configure, and test a local k3d autoscaler mimicking the Kubernetes Cluster Autoscaler behavior. This comprehensive guide includes:

1. **Setting Up the k3d Cluster**
2. **Installing the Metrics Server**
3. **Creating the Autoscaler Script**
4. **Configuring Docker Resource Limits**
5. **Deploying Test Workloads**
6. **Running and Testing the Autoscaler**

---

## **1. Set Up the k3d Cluster**

First, ensure you have the necessary tools installed:

- **Docker**: [Install Docker](https://docs.docker.com/get-docker/)
- **kubectl**: [Install kubectl](https://kubernetes.io/docs/tasks/tools/install-kubectl/)
- **k3d**: [Install k3d](https://k3d.io/#installation)

### **Create a k3d Cluster**

We'll create a k3d cluster named `autoscaler-cluster` with an initial single agent node.

```bash
k3d cluster create autoscaler-cluster --agents 1 --port "8080:80@loadbalancer"
```

*This command sets up a local Kubernetes cluster with one worker node and exposes port 80 to your localhost on port 8080.*

### **Verify the Cluster**

Ensure your cluster is up and running:

```bash
kubectl get nodes
```

You should see something like:

```
NAME                           STATUS   ROLES    AGE     VERSION
autoscaler-cluster-agent-0     Ready    agent    2m      v1.25.4+k3s1
```

---

## **2. Install the Metrics Server**

The Metrics Server collects resource usage data, which is essential for the autoscaler to make scaling decisions.

### **Deploy the Metrics Server**

```bash
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
```

### **Verify Metrics Server Installation**

Wait for the Metrics Server pods to be running:

```bash
kubectl get pods -n kube-system
```

Look for `metrics-server` pods with the `Running` status.

### **Test Metrics Collection**

```bash
kubectl top nodes
```

Sample output:

```
NAME                           CPU(cores)   CPU%   MEMORY(bytes)   MEMORY%
autoscaler-cluster-agent-0     100m         5%     200Mi           10%
```

---

## **3. Create the Autoscaler Script**

We'll create a Python script that monitors the cluster's CPU utilization and scales the number of nodes accordingly. This script will:

- **Monitor Metrics**: Check average CPU usage.
- **Scale Up**: Add a node if usage exceeds the upper threshold.
- **Scale Down**: Remove a node if usage falls below the lower threshold.
- **Limit Resources**: Apply Docker resource limits when adding nodes.

### **Prerequisites**

- **Python 3.x**: Ensure Python is installed.
- **Python Packages**: We'll use the `subprocess` and `time` modules, which are part of the standard library.

### **Autoscaler Script**

Create a file named `k3d_autoscaler.py` and add the following content:

```python
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
            '--delete-emptydir-data',  # Updated flag
            '--force'
        ], check=True)
        logging.debug(f"Node '{node_to_remove}' drained successfully.")

        # Delete the node from the k3d cluster without the --cluster flag
        subprocess.run(['k3d', 'node', 'delete', node_to_remove], check=True)
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
```

### **Make the Script Executable**

```bash
chmod +x k3d_autoscaler.py
```

### **Script Explanation**

- **get_average_cpu_utilization**: Fetches CPU usage from all nodes and calculates the average.
- **get_current_node_count**: Retrieves the current number of nodes in the cluster.
- **scale_up**: Adds a new node with specified Docker resource limits.
- **scale_down**: Selects the least loaded node, cordons it, drains workloads, and removes it from the cluster.
- **main**: The main loop that checks metrics and decides whether to scale up or down at regular intervals.

---

## **4. Label Agent Nodes for Resource Limit**

When adding new nodes, we set Docker resource limits directly by calling docker CLI. To label the nodes call script"

```bash
kubectl label nodes k3d-autoscaler-cluster-agent-0 "k3s.io/role=agent"
```

---

## **5. Deploy Test Workloads**

To test the autoscaler's behavior, deploy workloads that consume CPU resources. We'll create a simple deployment that runs CPU-intensive pods.

### **Create a CPU-Intensive Deployment**

Create a file named `cpu-stress.yaml` with the following content:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cpu-stress
spec:
  replicas: 1
  selector:
    matchLabels:
      app: cpu-stress
  template:
    metadata:
      labels:
        app: cpu-stress
    spec:
      containers:
      - name: stress
        image: polinux/stress
        args:
          - --cpu
          - "2"
          - --timeout
          - "600s"
        resources:
          requests:
            cpu: "500m"
            memory: "256Mi"
          limits:
            cpu: "1"
            memory: "512Mi"
```

### **Apply the Deployment**

```bash
kubectl apply -f cpu-stress.yaml
```

### **Scale the Deployment**

To increase CPU load, you can scale the deployment:

```bash
kubectl scale deployment cpu-stress --replicas=5
```

*This command scales the deployment to 5 replicas, increasing CPU usage across the cluster.*

### **Monitor the Deployment**

Check the status of the pods:

```bash
kubectl get pods -l app=cpu-stress
```

You should see multiple `stress` pods running, consuming CPU resources.

---

## **6. Run and Test the Autoscaler**

### **Start the Autoscaler Script**

Run the autoscaler script in the background or in a separate terminal:

```bash
./k3d_autoscaler.py
```

**Sample Output:**

```
Starting k3d Autoscaler...
Average CPU Utilization: 25.00%
Current Node Count: 1
CPU usage below lower threshold. Scaling down...
No scaling action required.
Sleeping for 60 seconds...

Average CPU Utilization: 85.00%
Current Node Count: 1
CPU usage above upper threshold. Scaling up...
Scaling up: Creating node autoscaler-cluster-agent-1700810195
Node autoscaler-cluster-agent-1700810195 created successfully.
Sleeping for 60 seconds...
```

### **Observe Scaling Actions**

1. **Scale Up**: When average CPU utilization exceeds 80%, the autoscaler adds a new node.
2. **Scale Down**: When average CPU utilization falls below 30%, and the cluster has more than the minimum number of nodes, the autoscaler removes a node.

### **Verify Node Changes**

After scaling actions, check the nodes:

```bash
kubectl get nodes
```

You should see nodes being added or removed based on the CPU load.

### **Clean Up Test Resources**

After testing, you can clean up by deleting the deployment and stopping the autoscaler script.

```bash
kubectl delete deployment cpu-stress
```

Terminate the autoscaler script by pressing `Ctrl+C`.

---

## **Additional Considerations**

### **1. Selecting Nodes to Remove**

The provided autoscaler script selects the node with the lowest CPU usage for removal. Depending on your workload and requirements, you might want to implement more sophisticated selection criteria, such as:

- **Avoid Removing Control Plane Nodes**: Ensure you don't remove nodes critical to cluster operations.
- **Consider Pod Affinity/Anti-Affinity**: Maintain workload distribution across nodes.

### **2. Handling Persistent Workloads**

For workloads with persistent storage or stateful sets, ensure proper handling during node removal to prevent data loss.

### **3. Logging and Monitoring**

Enhance the autoscaler script with robust logging and error handling to facilitate troubleshooting and ensure reliability.

### **4. Enhancing the Autoscaler Logic**

Consider implementing features such as:

- **Cooldown Periods**: Prevent rapid scaling actions by introducing delays between scale-up and scale-down operations.
- **Metrics Beyond CPU**: Incorporate memory usage or custom metrics for more informed scaling decisions.
- **Configuration via Environment Variables or Config Files**: Make the autoscaler more flexible and easier to configure.

### **5. Using Containers for the Autoscaler**

For better integration, consider containerizing the autoscaler script and running it as a Kubernetes deployment within the cluster. This approach allows the autoscaler to benefit from Kubernetes' own management and scaling features.

---

## **Conclusion**

By following this integrated setup, you've established a local k3d autoscaler that monitors CPU utilization and dynamically scales the number of nodes in your cluster. This system mimics the behavior of Kubernetes' Cluster Autoscaler, providing a valuable tool for testing and development environments. Adjust configurations as needed to align with your specific requirements and to further enhance the autoscaler's capabilities.

Feel free to reach out if you encounter any issues or need further assistance!
