Certainly! Let's adjust the setup to meet your requirements:

- **Apply resource limits at the node level**: We'll limit the resources of the Docker containers that represent the Kubernetes nodes.
- **Applications can access all available node resources**: We'll avoid setting resource requests and limits in Kubernetes manifests.
- **Organize code into a folder and file structure**: This will help you manage everything as Infrastructure as Code (IaC).

---

## **Folder and File Structure**

We'll create a project directory named `my-k3d-cluster` with the following structure:

```
my-k3d-cluster/
├── cluster/
│   └── k3d-config.yaml
├── deployments/
│   └── app-deployment.yaml
├── autoscaler/
│   ├── cluster-autoscaler.yaml
│   └── cluster-autoscaler-rbac.yaml
├── scripts/
│   ├── limit_node_resources.sh
│   └── autoscale_nodes.sh
```

---

## **Step 1: Set Up a Multinode k3d Cluster**

### **1.1. Create Cluster Configuration**

**File:** `cluster/k3d-config.yaml`

```yaml
apiVersion: k3d.io/v1alpha4
kind: Simple
metadata:
  name: mycluster
servers:
  - replicaCount: 1
agents:
  - replicaCount: 2
options:
  k3d:
    wait: true
    timeout: "60s"
  kubeconfig:
    updateDefaultKubeconfig: true
    switchCurrentContext: true
```

**Explanation:**

- **`servers`**: Specifies one control plane node.
- **`agents`**: Specifies two worker nodes.
- No Kubernetes-level resource limits are applied here.

### **1.2. Create the Cluster**

From the `my-k3d-cluster` directory, run:

```bash
k3d cluster create --config cluster/k3d-config.yaml
```

**Verify the Cluster:**

```bash
kubectl get nodes
```

You should see three nodes listed.

---

## **Step 2: Limit Node Resources at the Node Level**

### **2.1. Create Resource Limitation Script**

**File:** `scripts/limit_node_resources.sh`

```bash
#!/bin/bash

# Define resource limits
CPU_LIMIT="1"        # CPUs per node
MEMORY_LIMIT="1g"    # Memory per node

# Get list of k3d node containers
NODES=$(docker ps --filter "name=k3d-mycluster" --format "{{.Names}}")

# Apply limits to each node container
for NODE in $NODES; do
  echo "Limiting resources for node $NODE"
  docker update --cpus=$CPU_LIMIT --memory=$MEMORY_LIMIT $NODE
done
```

**Make the Script Executable:**

```bash
chmod +x scripts/limit_node_resources.sh
```

**Run the Script:**

```bash
./scripts/limit_node_resources.sh
```

**Explanation:**

- The script limits each node's CPU and memory at the Docker container level.
- Applications running on these nodes can utilize all the node's resources.

---

## **Step 3: Deploy an Application Without Kubernetes Resource Limits**

### **3.1. Create Deployment Manifest**

**File:** `deployments/app-deployment.yaml`

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: demo-app
spec:
  replicas: 1
  selector:
    matchLabels:
      app: demo-app
  template:
    metadata:
      labels:
        app: demo-app
    spec:
      containers:
        - name: demo-app
          image: nginx
```

**Apply the Deployment:**

```bash
kubectl apply -f deployments/app-deployment.yaml
```

**Explanation:**

- No resource requests or limits are set in the manifest.
- The application can access all available resources on the node.

---

## **Step 4: Configure Cluster Autoscaler with Automation Scripts**

Since we want to simulate node autoscaling locally, we'll use scripts to mimic the behavior of the Cluster Autoscaler.

### **4.1. Create RBAC Configuration**

**File:** `autoscaler/cluster-autoscaler-rbac.yaml`

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: cluster-autoscaler
  namespace: kube-system
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: cluster-autoscaler
rules:
  - apiGroups: [""]
    resources: ["events", "endpoints"]
    verbs: ["create", "update", "patch"]
  - apiGroups: [""]
    resources: ["pods/eviction"]
    verbs: ["create"]
  - apiGroups: ["extensions", "apps"]
    resources: ["replicasets", "deployments"]
    verbs: ["list", "watch"]
  - apiGroups: [""]
    resources: ["pods", "nodes"]
    verbs: ["list", "watch", "get", "update"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: cluster-autoscaler
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: cluster-autoscaler
subjects:
  - kind: ServiceAccount
    name: cluster-autoscaler
    namespace: kube-system
```

### **4.2. Create Cluster Autoscaler Deployment**

**File:** `autoscaler/cluster-autoscaler.yaml`

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cluster-autoscaler
  namespace: kube-system
spec:
  replicas: 1
  selector:
    matchLabels:
      app: cluster-autoscaler
  template:
    metadata:
      labels:
        app: cluster-autoscaler
    spec:
      serviceAccountName: cluster-autoscaler
      containers:
        - name: cluster-autoscaler
          image: k8s.gcr.io/autoscaling/cluster-autoscaler:v1.23.0
          command:
            - ./cluster-autoscaler
            - --v=4
            - --stderrthreshold=info
            - --cloud-provider=clusterapi
            - --namespace=kube-system
            - --nodes=1:5:mycluster-agent
```

**Apply the RBAC and Deployment:**

```bash
kubectl apply -f autoscaler/cluster-autoscaler-rbac.yaml
kubectl apply -f autoscaler/cluster-autoscaler.yaml
```

**Explanation:**

- The Cluster Autoscaler is configured to work with the `clusterapi` provider.
- It watches for scaling events but cannot add/remove nodes automatically in a local setup.

### **4.3. Create Automation Script**

**File:** `scripts/autoscale_nodes.sh`

```bash
#!/bin/bash

# Monitor Cluster Autoscaler logs and simulate node scaling

KUBECTL="kubectl"
CLUSTER_NAME="mycluster"

# Function to add a node
add_node() {
  NODE_COUNT=$(k3d node list | grep "${CLUSTER_NAME}-agent" | wc -l)
  NODE_NAME="k3d-${CLUSTER_NAME}-agent-${NODE_COUNT}"
  echo "Adding node $NODE_NAME..."
  k3d node create $NODE_NAME --cluster $CLUSTER_NAME --role agent
  # Apply resource limits
  docker update --cpus=1 --memory=1g $NODE_NAME
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
  if echo "$line" | grep -q "Scale-up": then
    echo "Scale-up event detected."
    add_node
  elif echo "$line" | grep -q "Scale-down": then
    echo "Scale-down event detected."
    remove_node
  fi
done
```

**Make the Script Executable:**

```bash
chmod +x scripts/autoscale_nodes.sh
```

**Run the Script:**

```bash
./scripts/autoscale_nodes.sh
```

**Explanation:**

- The script listens to the Cluster Autoscaler's logs for scale-up and scale-down events.
- It adds or removes nodes by interacting with k3d.
- Resource limits are applied to new nodes at the Docker level.

---

## **Step 5: Test the Autoscaling Setup**

### **5.1. Increase Application Load**

Update the deployment to increase replicas:

**Edit:** `deployments/app-deployment.yaml`

```yaml
spec:
  replicas: 5
```

**Apply the Changes:**

```bash
kubectl apply -f deployments/app-deployment.yaml
```

### **5.2. Observe Autoscaling**

- **Monitor Nodes:**

  ```bash
  kubectl get nodes -w
  ```

- **Check Pods:**

  ```bash
  kubectl get pods -o wide
  ```

- **Watch the Script Output:**

  The `autoscale_nodes.sh` script should display messages about adding nodes when scale-up events are detected.

### **5.3. Reduce Application Load**

Scale the deployment back down:

```bash
kubectl scale deployment demo-app --replicas=1
```

**Observe Node Removal:**

- The script should detect scale-down events and remove nodes accordingly.

---

## **Conclusion**

By applying resource limits at the node (Docker container) level and organizing all configurations and scripts into a structured directory, you can manage your setup effectively as Infrastructure as Code.

- **Node Resource Limits**: Applied directly to the Docker containers.
- **Applications Access All Node Resources**: No Kubernetes-level resource limits are set.
- **Code Organization**: Files are organized into directories for clusters, deployments, autoscaler configurations, and scripts.

---

**Feel free to ask if you need further assistance or clarification on any of these steps!**
