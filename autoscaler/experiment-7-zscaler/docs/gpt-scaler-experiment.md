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

# Configuration
CLUSTER_NAME = 'autoscaler-cluster'
MIN_NODES = 1
MAX_NODES = 5
CPU_UPPER_THRESHOLD = 80  # in percent
CPU_LOWER_THRESHOLD = 30  # in percent
CHECK_INTERVAL = 60  # in seconds

def get_average_cpu_utilization():
    try:
        result = subprocess.run(['kubectl', 'top', 'nodes', '--no-headers'], capture_output=True, text=True, check=True)
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
    try:
        result = subprocess.run(['kubectl', 'get', 'nodes', '--no-headers'], capture_output=True, text=True, check=True)
        node_count = len([line for line in result.stdout.strip().split('\n') if line])
        return node_count
    except subprocess.CalledProcessError as e:
        print(f"Error fetching node count: {e}", file=sys.stderr)
        return MIN_NODES

def scale_up():
    node_name = f"autoscaler-cluster-agent-{int(time.time())}"
    print(f"Scaling up: Creating node {node_name}")
    try:
        subprocess.run([
            'k3d', 'node', 'create', node_name,
            '--cluster', CLUSTER_NAME,
            '--role', 'agent',
            '--k3s-node-arg', '--docker-opt=--memory=2g',
            '--k3s-node-arg', '--docker-opt=--cpus=2'
        ], check=True)
        print(f"Node {node_name} created successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error scaling up: {e}", file=sys.stderr)

def get_nodes_sorted_by_load():
    try:
        result = subprocess.run(['kubectl', 'top', 'nodes', '--no-headers'], capture_output=True, text=True, check=True)
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
    nodes_sorted = get_nodes_sorted_by_load()
    if not nodes_sorted:
        print("No nodes available to scale down.")
        return
    # Select the node with the lowest CPU usage
    node_to_remove, cpu_percent = nodes_sorted[-1]
    print(f"Scaling down: Removing node {node_to_remove} with CPU usage {cpu_percent}%")
    try:
        subprocess.run(['kubectl', 'cordon', node_to_remove], check=True)
        subprocess.run(['kubectl', 'drain', node_to_remove, '--ignore-daemonsets', '--delete-local-data', '--force'], check=True)
        subprocess.run(['k3d', 'node', 'delete', node_to_remove, '--cluster', CLUSTER_NAME], check=True)
        print(f"Node {node_to_remove} removed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error scaling down: {e}", file=sys.stderr)

def main():
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

## **4. Configure Docker Resource Limits**

When adding new nodes, we set Docker resource limits directly via k3d's node creation arguments. The autoscaler script includes:

```bash
--k3s-node-arg '--docker-opt=--memory=2g'
--k3s-node-arg '--docker-opt=--cpus=2'
```

This configuration ensures each node has a maximum of 2 CPUs and 2GB of memory. Adjust these values as needed based on your testing requirements and host machine capabilities.

**Note:** The `--docker-opt` flags are passed to the Docker daemon running inside each k3d node container. Ensure that your k3d version supports these flags. Refer to the [k3d documentation](https://k3d.io/) for the most up-to-date information.

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
