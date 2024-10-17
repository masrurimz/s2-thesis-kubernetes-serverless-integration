# Cluster API Operator with k3d to Simulate Cluster Autoscaling

Certainly! Below is a **comprehensive, step-by-step guide** to **set up Cluster API Operator with k3d**, **configure Docker-based node resource limits**, and **simulate cluster autoscaling** in your local environment. This guide will walk you through the entire process from installation to testing autoscaling.

---

## **Table of Contents**

1. [Prerequisites](#prerequisites)
2. [Step 1: Install Required Tools](#step-1-install-required-tools)
3. [Step 2: Create a Management Cluster with k3d](#step-2-create-a-management-cluster-with-k3d)
4. [Step 3: Install Cluster API Operator](#step-3-install-cluster-api-operator)
5. [Step 4: Configure Cluster API Providers (Docker)](#step-4-configure-cluster-api-providers-docker)
6. [Step 5: Define and Deploy a Workload Cluster](#step-5-define-and-deploy-a-workload-cluster)
7. [Step 6: Configure DockerMachineTemplate with Resource Limits](#step-6-configure-dockermachinetemplate-with-resource-limits)
8. [Step 7: Deploy Kubernetes Cluster Autoscaler](#step-7-deploy-kubernetes-cluster-autoscaler)
9. [Step 8: Set Up Metrics Server](#step-8-set-up-metrics-server)
10. [Step 9: Simulate Cluster Autoscaling](#step-9-simulate-cluster-autoscaling)
11. [Step 10: Verify Resource Limits and Autoscaling](#step-10-verify-resource-limits-and-autoscaling)
12. [Step 11: (Optional) Implement GitOps with Flux](#step-11-optional-implement-gitops-with-flux)
13. [Troubleshooting Tips](#troubleshooting-tips)
14. [Conclusion](#conclusion)
15. [Additional Resources](#additional-resources)

---

## **Prerequisites**

Before starting, ensure you have the following:

- A **Unix-like** operating system (Linux or macOS recommended). Windows users can use WSL2.
- **Docker** installed and running.
- Sufficient system resources (at least 8 GB RAM and multiple CPU cores) to run multiple Docker containers.

---

## **Step 1: Install Required Tools**

### **1.1 Install Docker**

Ensure Docker is installed and running. You can download Docker from [Docker Desktop](https://www.docker.com/products/docker-desktop) for macOS and Windows or follow the [Docker Engine installation guide](https://docs.docker.com/engine/install/) for Linux.

**Verify Installation:**

```bash
docker --version
```

### **1.2 Install k3d**

**k3d** is a lightweight wrapper to run **k3s** (Rancher's Kubernetes distribution) in Docker.

**Installation Command:**

```bash
curl -s https://raw.githubusercontent.com/k3d-io/k3d/main/install.sh | bash
```

**Verify Installation:**

```bash
k3d version
```

### **1.3 Install kubectl**

**kubectl** is the Kubernetes command-line tool.

**Installation:**

Follow the [official Kubernetes documentation](https://kubernetes.io/docs/tasks/tools/install-kubectl/) for your OS.

**Verify Installation:**

```bash
kubectl version --client
```

### **1.4 Install Helm**

**Helm** is a package manager for Kubernetes.

**Installation Command:**

```bash
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
```

**Verify Installation:**

```bash
helm version
```

### **1.5 Install Git (Optional for GitOps)**

If you plan to implement GitOps workflows, install Git.

**Installation:**

Follow the [Git installation guide](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git) for your OS.

**Verify Installation:**

```bash
git --version
```

---

## **Step 2: Create a Management Cluster with k3d**

The **management cluster** will host the **Cluster API Operator** and manage your workload clusters.

### **2.1 Create the Management Cluster**

```bash
k3d cluster create management-cluster \
  --agents 1 \
  --port "6443:6443@loadbalancer:0" \
  --k3s-arg "--disable=traefik@server:0"
```

**Explanation:**

- `management-cluster`: Name of the cluster.
- `--agents 1`: Starts with one agent node.
- `--port "6443:6443@loadbalancer"`: Maps port 6443 for API access.
- `--k3s-arg "--disable=traefik@server:0"`: Disables Traefik ingress to reduce resource usage.

### **2.2 Verify the Cluster**

```bash
kubectl cluster-info --context k3d-management-cluster
```

**Expected Output:**

You should see information about the Kubernetes master and services running.

---

## **Step 3: Install Cluster API Operator**

The **Cluster API Operator** manages Cluster API components declaratively.

### **3.1 Install Cluster Cert Manager from Helm Repository**

```bash
kubectl apply -f https://github.com/jetstack/cert-manager/releases/latest/download/cert-manager.yaml
```

### **3.2 Install the Cluster API Operator**

```bash
helm repo add capi-operator https://kubernetes-sigs.github.io/cluster-api-operator
helm repo update
helm install capi-operator capi-operator/cluster-api-operator --create-namespace -n capi-operator-system

# helm install capi-operator cluster-api/cluster-api \
#   --namespace capi-operator-system \
#   --create-namespace
```

**Explanation:**

- `capi-operator`: Name of the Helm release.
- `cluster-api/cluster-api`: Chart name.
- `--namespace capi-operator-system`: Namespace to install the operator.
- `--create-namespace`: Creates the namespace if it doesn't exist.

### **3.3 Verify the Installation**

```bash
kubectl get pods -n capi-operator-system
```

**Expected Output:**

All pods should be in the `Running` state without issues.

---

## **Step 4: Configure Cluster API Providers (Docker)**

Configure the **Docker** infrastructure provider to manage Kubernetes nodes as Docker containers.

### **4.1 Add the Cluster API Docker Provider Repository**

```bash
helm repo add cluster-api https://cluster-api.github.io/cluster-api
helm repo update
```

### **4.2 Install the Docker Infrastructure Provider**

```bash
helm install capi-operator capi-operator/cluster-api-operator --create-namespace -n capi-operator-system --set infrastructure=docker:v1.4.2  --wait --timeout 90s
# core Cluster API with kubeadm bootstrap and control plane providers will also be installed
```

**Explanation:**

- `capi-docker`: Name of the Helm release.
- `cluster-api/docker`: Chart name.
- `--namespace capi-operator-system`: Namespace where Cluster API Operator is installed.

### **4.3 Verify Provider Installation**

```bash
kubectl get pods -n capi-operator-system
```

**Expected Output:**

Ensure that Docker provider pods are running without issues.

---

## **Step 5: Define and Deploy a Workload Cluster**

Create a **workload cluster** that Cluster API will manage.

### **5.1 Create a Namespace for Cluster API Resources**

```bash
kubectl create namespace cluster-api
```

### **5.2 Define the Infrastructure Template**

Create a file named `docker-machine-template.yaml`:

```yaml
apiVersion: infrastructure.cluster.x-k8s.io/v1alpha4
kind: DockerMachineTemplate
metadata:
  name: my-docker-control-plane
  namespace: cluster-api
spec:
  template:
    spec:
      image: rancher/k3s:v1.26.0-k3s1
      extraMounts:
        - hostPath: /var/run/docker.sock
          containerPath: /var/run/docker.sock
```

### **5.3 Apply the Infrastructure Template**

```bash
kubectl apply -f docker-machine-template.yaml
```

### **5.4 Define the Control Plane Configuration**

Create a file named `control-plane.yaml`:

```yaml
apiVersion: controlplane.cluster.x-k8s.io/v1beta1
kind: KubeadmControlPlane
metadata:
  name: my-cluster-control-plane
  namespace: cluster-api
spec:
  replicas: 1
  version: v1.26.0
  infrastructureTemplate:
    apiVersion: infrastructure.cluster.x-k8s.io/v1alpha4
    kind: DockerMachineTemplate
    name: my-docker-control-plane
  kubeadmConfigSpec:
    clusterConfiguration:
      apiServer:
        extraArgs:
          "enable-admission-plugins": "NodeRestriction"
    initConfiguration:
      nodeRegistration:
        kubeletExtraArgs:
          "node-labels": "node-role.kubernetes.io/control-plane=true"
    joinConfiguration:
      nodeRegistration:
        kubeletExtraArgs:
          "node-labels": "node-role.kubernetes.io/control-plane=true"
```

### **5.5 Apply the Control Plane Configuration**

```bash
kubectl apply -f control-plane.yaml
```

### **5.6 Define the Cluster**

Create a file named `my-cluster.yaml`:

```yaml
apiVersion: cluster.x-k8s.io/v1beta1
kind: Cluster
metadata:
  name: my-cluster
  namespace: cluster-api
spec:
  infrastructureRef:
    apiVersion: infrastructure.cluster.x-k8s.io/v1alpha4
    kind: DockerCluster
    name: my-docker-cluster
  controlPlaneRef:
    apiVersion: controlplane.cluster.x-k8s.io/v1beta1
    kind: KubeadmControlPlane
    name: my-cluster-control-plane
  version: v1.26.0
```

### **5.7 Apply the Cluster Definition**

```bash
kubectl apply -f my-cluster.yaml
```

### **5.8 Monitor the Cluster Creation**

```bash
kubectl get clusters -n cluster-api
kubectl get kubeadmcontrolplanes -n cluster-api
kubectl get machinetemplates -n cluster-api
kubectl get machines -n cluster-api
```

**Expected Outcome:**

Your workload cluster should be up and running with the defined control plane.

---

## **Step 6: Configure DockerMachineTemplate with Resource Limits**

Limit each node's CPU and memory resources to prevent a single node from using excessive system resources.

### **6.1 Update DockerMachineTemplate with Resource Constraints**

Modify `docker-machine-template.yaml` to include resource limits. Here's the updated content:

```yaml
apiVersion: infrastructure.cluster.x-k8s.io/v1alpha4
kind: DockerMachineTemplate
metadata:
  name: my-docker-control-plane
  namespace: cluster-api
spec:
  template:
    spec:
      image: rancher/k3s:v1.26.0-k3s1
      extraMounts:
        - hostPath: /var/run/docker.sock
          containerPath: /var/run/docker.sock
      resources:
        limits:
          cpu: "2"       # Limit to 2 CPU cores
          memory: "4Gi"  # Limit to 4 GB RAM
        requests:
          cpu: "1"       # Request 1 CPU core
          memory: "2Gi"  # Request 2 GB RAM
```

### **6.2 Apply the Updated DockerMachineTemplate**

```bash
kubectl apply -f docker-machine-template.yaml
```

### **6.3 Recreate Existing Nodes to Apply New Resource Limits**

Resource limits are applied during node creation. To enforce the new limits, recreate existing nodes.

1. **Scale Down the MachineDeployment**

   ```bash
   kubectl scale machinedeployment my-cluster-md-0 --replicas=0 -n cluster-api
   ```

2. **Scale Up the MachineDeployment**

   ```bash
   kubectl scale machinedeployment my-cluster-md-0 --replicas=1 -n cluster-api
   ```

   This will delete the existing node and create a new one with the updated resource limits.

### **6.4 Verify the New Node**

```bash
kubectl get nodes
```

You should see the new node listed and in the `Ready` state.

---

## **Step 7: Deploy Kubernetes Cluster Autoscaler**

The **Cluster Autoscaler** automatically adjusts the number of nodes in your cluster based on resource demands.

### **7.1 Add the Cluster Autoscaler Helm Repository**

```bash
helm repo add autoscaler https://kubernetes.github.io/autoscaler
helm repo update
```

### **7.2 Create a Values File for Cluster Autoscaler**

Create a file named `cluster-autoscaler-values.yaml` with the following content:

```yaml
autoDiscovery:
  clusterName: my-cluster
  enabled: false

# Since using Docker, cloud provider specific configs are not needed
cloudProvider: ""

# Enable event-based scaling (optional)
awsRegion: ""

# Set node group options
scaleDown:
  enabled: true
  delayAfterAdd: 10m
  delayAfterDelete: 10s
  delayAfterFailure: 3m

extraArgs:
  balance-similar-node-groups: "true"
  skip-nodes-with-system-pods: "false"
  expander: "least-waste"

# Set RBAC permissions if necessary
rbac:
  create: true
```

**Note:** Adjust parameters as needed. Since you're using Docker, many cloud-specific settings are unnecessary.

### **7.3 Install Cluster Autoscaler via Helm**

```bash
helm install cluster-autoscaler autoscaler/cluster-autoscaler-chart \
  --namespace kube-system \
  --create-namespace \
  -f cluster-autoscaler-values.yaml
```

**Note:** Replace `cluster-autoscaler-chart` with the actual chart name if different. As of writing, the Cluster Autoscaler Helm chart may not be officially available. If unavailable, consider deploying via manifests:

**Alternative Deployment via Manifests:**

1. **Download Cluster Autoscaler Manifest**

   ```bash
   wget https://raw.githubusercontent.com/kubernetes/autoscaler/master/cluster-autoscaler/cloudprovider/docker/cluster-autoscaler-docker.yaml
   ```

   *(Note: Ensure you have the correct manifest for the Docker provider.)*

2. **Apply the Manifest**

   ```bash
   kubectl apply -f cluster-autoscaler-docker.yaml
   ```

**Verify Installation:**

```bash
kubectl get pods -n kube-system | grep cluster-autoscaler
```

Ensure the Cluster Autoscaler pod is running without issues.

---

## **Step 8: Set Up Metrics Server**

The **Cluster Autoscaler** relies on metrics to make scaling decisions.

### **8.1 Deploy Metrics Server**

```bash
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
```

### **8.2 Verify Metrics Server Deployment**

```bash
kubectl get pods -n kube-system | grep metrics-server
```

All Metrics Server pods should be in the `Running` state.

### **8.3 Test Metrics Collection**

```bash
kubectl top nodes
```

You should see resource usage metrics for each node.

---

## **Step 9: Simulate Cluster Autoscaling**

Generate workloads that exceed current cluster capacity to trigger autoscaling.

### **9.1 Create a MachineDeployment with Autoscaling Parameters**

Define a `MachineDeployment` that allows scaling between 1 and 3 replicas.

Create a file named `machine-deployment-autoscale.yaml`:

```yaml
apiVersion: cluster.x-k8s.io/v1beta1
kind: MachineDeployment
metadata:
  name: my-cluster-md-autoscale
  namespace: cluster-api
spec:
  replicas: 1
  minReadySeconds: 0
  selector:
    matchLabels:
      cluster.x-k8s.io/deployment-name: my-cluster-md-autoscale
  template:
    metadata:
      labels:
        cluster.x-k8s.io/deployment-name: my-cluster-md-autoscale
    spec:
      clusterName: my-cluster
      bootstrap:
        configRef:
          apiVersion: bootstrap.cluster.x-k8s.io/v1beta1
          kind: KubeadmConfigTemplate
          name: my-cluster-md-autoscale
      infrastructureRef:
        apiVersion: infrastructure.cluster.x-k8s.io/v1alpha4
        kind: DockerMachineTemplate
        name: my-docker-control-plane
      version: v1.26.0
      replicas: 1
```

**Note:** Adjust labels and references as necessary.

### **9.2 Apply the MachineDeployment**

```bash
kubectl apply -f machine-deployment-autoscale.yaml
```

### **9.3 Configure Autoscaling on the MachineDeployment**

Currently, Cluster API does not natively support autoscaling via `MachineDeployment`. To integrate with Kubernetes Cluster Autoscaler, you need to label node groups and ensure proper annotations.

**Example Annotation for Cluster Autoscaler:**

Add the following annotations to your `MachineDeployment` to inform the Cluster Autoscaler about scaling policies.

```yaml
metadata:
  annotations:
    cluster-autoscaler.kubernetes.io/scale-down-enabled: "true"
    cluster-autoscaler.kubernetes.io/max-nodes-total: "3"
    cluster-autoscaler.kubernetes.io/min-nodes-total: "1"
```

**Updated `machine-deployment-autoscale.yaml`:**

```yaml
apiVersion: cluster.x-k8s.io/v1beta1
kind: MachineDeployment
metadata:
  name: my-cluster-md-autoscale
  namespace: cluster-api
  annotations:
    cluster-autoscaler.kubernetes.io/scale-down-enabled: "true"
    cluster-autoscaler.kubernetes.io/max-nodes-total: "3"
    cluster-autoscaler.kubernetes.io/min-nodes-total: "1"
spec:
  replicas: 1
  minReadySeconds: 0
  selector:
    matchLabels:
      cluster.x-k8s.io/deployment-name: my-cluster-md-autoscale
  template:
    metadata:
      labels:
        cluster.x-k8s.io/deployment-name: my-cluster-md-autoscale
    spec:
      clusterName: my-cluster
      bootstrap:
        configRef:
          apiVersion: bootstrap.cluster.x-k8s.io/v1beta1
          kind: KubeadmConfigTemplate
          name: my-cluster-md-autoscale
      infrastructureRef:
        apiVersion: infrastructure.cluster.x-k8s.io/v1alpha4
        kind: DockerMachineTemplate
        name: my-docker-control-plane
      version: v1.26.0
      replicas: 1
```

**Apply the Updated MachineDeployment:**

```bash
kubectl apply -f machine-deployment-autoscale.yaml
```

### **9.4 Deploy a Load-Generating Application**

Create a deployment that consumes significant CPU and memory to trigger autoscaling.

Create a file named `load-generator.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: load-generator
  namespace: default
spec:
  replicas: 10
  selector:
    matchLabels:
      app: load-generator
  template:
    metadata:
      labels:
        app: load-generator
    spec:
      containers:
      - name: stress
        image: progrium/stress
        args:
          - --cpu
          - "2"
          - --io
          - "1"
          - --vm
          - "1"
          - --vm-bytes
          - "128M"
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

### **9.5 Apply the Load Generator Deployment**

```bash
kubectl apply -f load-generator.yaml
```

### **9.6 Monitor Resource Usage and Autoscaling**

**Monitor Pods:**

```bash
kubectl get pods -n default -l app=load-generator
```

**Monitor Node Metrics:**

```bash
kubectl top nodes
```

**Expected Behavior:**

As the load increases, the Cluster Autoscaler should detect the resource demand and scale out by adding more nodes up to the maximum defined (e.g., 3 nodes).

---

## **Step 10: Verify Resource Limits and Autoscaling**

Ensure that resource limits are enforced and autoscaling behaves as expected.

### **10.1 Check Node Resource Limits**

List Docker containers representing Kubernetes nodes:

```bash
docker ps --filter "name=k3d-my-cluster-md-autoscale"
```

**Inspect a Node Container:**

Replace `<container_id>` with the actual container ID.

```bash
docker inspect <container_id> --format='{{json .HostConfig}}' | jq
```

**Verify CPU and Memory Limits:**

- **CpuQuota**: Should correspond to the CPU limits set (e.g., 2 CPUs).
- **Memory**: Should reflect the memory limits (e.g., 4GiB).

**Example Output:**

```json
{
  "CpuShares": 1024,
  "CpuSet": "",
  "CpuQuota": 200000,
  "CpuPeriod": 100000,
  "Memory": 4294967296,
  ...
}
```

**Interpretation:**

- `CpuQuota`: 200000 microseconds per 100000 microseconds period = 2 CPUs.
- `Memory`: 4294967296 bytes = 4 GiB.

### **10.2 Check Kubernetes Node Capacity**

Describe a node to verify resource allocations:

```bash
kubectl describe node <node-name>
```

**Look for the `Capacity` and `Allocatable` Sections:**

```
Capacity:
  cpu:                2
  memory:             4Gi
  pods:               110
Allocatable:
  cpu:                2
  memory:             4Gi
  pods:               110
```

### **10.3 Monitor Cluster Autoscaler Logs**

Retrieve logs from the Cluster Autoscaler to observe scaling decisions:

```bash
kubectl logs -n kube-system deployment/cluster-autoscaler
```

**Look for Messages Indicating Scaling Actions:**

- Adding nodes when resource demands exceed current capacity.
- Removing nodes when they are underutilized.

### **10.4 Simulate Node Removal**

To test scale-down, reduce the workload and observe if the autoscaler removes unnecessary nodes.

1. **Scale Down the Load Generator:**

   ```bash
   kubectl scale deployment load-generator --replicas=2 -n default
   ```

2. **Monitor Cluster Autoscaler Logs:**

   Check if the autoscaler detects underutilized nodes and removes them.

3. **Verify Node Count:**

   ```bash
   kubectl get nodes
   ```

   The number of nodes should decrease accordingly, respecting the minimum node limit.

---

## **Step 11: (Optional) Implement GitOps with Flux**

For declarative management and automation, integrate **GitOps** using **Flux**.

### **11.1 Install Flux CLI**

```bash
curl -s https://fluxcd.io/install.sh | sudo bash
```

### **11.2 Initialize a Git Repository for Cluster Configurations**

```bash
mkdir cluster-api-config
cd cluster-api-config
git init
```

### **11.3 Add Cluster API Manifests to the Repository**

Copy your YAML manifests (`docker-machine-template.yaml`, `control-plane.yaml`, `my-cluster.yaml`, etc.) into this repository.

### **11.4 Bootstrap Flux to Your Git Repository**

Replace `<your-github-username>`, `<repository-name>`, and `<branch>` with your details.

```bash
flux bootstrap github \
  --owner=<your-github-username> \
  --repository=<repository-name> \
  --branch=main \
  --path=./
```

**Explanation:**

Flux will monitor the specified Git repository and apply any changes automatically to the management cluster.

### **11.5 Commit and Push Changes**

```bash
git add .
git commit -m "Initial Cluster API configuration"
git push origin main
```

**Outcome:**

Flux detects the changes and applies the manifests to ensure your Cluster API providers and workload clusters are in the desired state.

---

## **Troubleshooting Tips**

- **Cluster Autoscaler Not Scaling:**
  - Ensure that the Cluster Autoscaler has the necessary permissions.
  - Verify annotations and labels on `MachineDeployments`.
  - Check if Metrics Server is functioning correctly.

- **Pods Failing to Schedule:**
  - Confirm that nodes have the correct resource allocations.
  - Check for any `ResourceQuotas` or `LimitRanges` that might restrict pod scheduling.

- **Docker Resource Limits Not Applied:**
  - Ensure that the `DockerMachineTemplate` is correctly configured with resource limits.
  - Recreate nodes after applying changes to enforce new limits.

- **Flux Not Applying Changes:**
  - Verify Flux installation and its connection to your Git repository.
  - Check Flux logs for any errors.

---

## **Conclusion**

You've successfully:

1. **Set Up a Management Cluster** using k3d.
2. **Installed the Cluster API Operator** to manage Kubernetes clusters declaratively.
3. **Configured the Docker Infrastructure Provider** with resource limits.
4. **Deployed a Workload Cluster** managed by Cluster API.
5. **Installed and Configured the Cluster Autoscaler** to manage node scaling based on workload demands.
6. **Set Up Metrics Server** to provide necessary metrics for autoscaling decisions.
7. **Simulated Cluster Autoscaling** by deploying resource-intensive applications.
8. **(Optionally) Implemented GitOps** using Flux for automated, declarative cluster management.

This setup allows you to **experiment with cluster lifecycle management**, **autoscaling behaviors**, and **resource constraints** in a local environment, leveraging the power of **Cluster API** and **GitOps** practices.
