Setting up a multi-node Kubernetes cluster with autoscaling locally using **Cluster API (CAPI)**, the **Docker provider**, and **k3d** involves several steps. This setup leverages CAPI to manage the lifecycle of your Kubernetes clusters declaratively, while k3d provides a lightweight Kubernetes distribution running in Docker containers. Below is a comprehensive guide to achieve this configuration.

## Table of Contents

- [Table of Contents](#table-of-contents)
- [Prerequisites](#prerequisites)
- [Install Required Tools](#install-required-tools)
  - [1. Install Docker](#1-install-docker)
  - [2. Install kubectl](#2-install-kubectl)
  - [3. Install k3d](#3-install-k3d)
  - [4. Install Clusterctl](#4-install-clusterctl)
- [Create a Base k3d Cluster](#create-a-base-k3d-cluster)
- [Bootstrap Cluster API](#bootstrap-cluster-api)
  - [1. Initialize Cluster API](#1-initialize-cluster-api)
  - [2. Verify Cluster API Components](#2-verify-cluster-api-components)
- [Install the Docker Provider](#install-the-docker-provider)
- [Create a Cluster with Multi-Node Setup](#create-a-cluster-with-multi-node-setup)
  - [1. Define a Cluster YAML](#1-define-a-cluster-yaml)
  - [2. Apply the Cluster Definition](#2-apply-the-cluster-definition)
  - [3. Add Worker Nodes](#3-add-worker-nodes)
  - [4. Verify Nodes](#4-verify-nodes)
- [Configure Autoscaling](#configure-autoscaling)
  - [1. Install Cluster Autoscaler](#1-install-cluster-autoscaler)
  - [2. Configure Cluster Autoscaler](#2-configure-cluster-autoscaler)
  - [3. Add RBAC Permissions](#3-add-rbac-permissions)
  - [4. Annotate the Cluster](#4-annotate-the-cluster)
  - [5. Test Autoscaling](#5-test-autoscaling)
- [Verify the Setup](#verify-the-setup)
- [Troubleshooting Tips](#troubleshooting-tips)
- [Additional Resources](#additional-resources)

---

## Prerequisites

Before you begin, ensure that your local machine meets the following requirements:

- **Operating System**: Linux, macOS, or Windows (with WSL2 for Windows users)
- **Docker**: Installed and running
- **kubectl**: Installed and configured
- **k3d**: Installed
- **Clusterctl**: Installed
- **Git**: Installed

## Install Required Tools

### 1. Install Docker

Ensure Docker is installed and running on your machine. You can download Docker from [Docker's official website](https://www.docker.com/get-started).

### 2. Install kubectl

kubectl is the command-line tool for interacting with Kubernetes clusters.

```bash
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/$(uname -s | tr '[:upper:]' '[:lower:]')/amd64/kubectl"
chmod +x kubectl
sudo mv kubectl /usr/local/bin/
```

Verify the installation:

```bash
kubectl version --client
```

### 3. Install k3d

k3d allows you to run k3s (Lightweight Kubernetes) in Docker.

```bash
curl -s https://raw.githubusercontent.com/k3d-io/k3d/main/install.sh | bash
```

Verify the installation:

```bash
k3d version
```

### 4. Install Clusterctl

Clusterctl is the CLI tool for Cluster API.

```bash
curl -L https://github.com/kubernetes-sigs/cluster-api/releases/latest/download/clusterctl-linux-amd64 -o clusterctl
chmod +x clusterctl
sudo mv clusterctl /usr/local/bin/
```

Verify the installation:

```bash
clusterctl version
```

## Create a Base k3d Cluster

Create a base k3d cluster that will host the Cluster API management components.

```bash
k3d cluster create capi-management --agents 1 --port "6443:6443@loadbalancer"
```

This command creates a k3d cluster named `capi-management` with one agent node and maps port 6443 for API access.

Verify the cluster is running:

```bash
kubectl config get-contexts
kubectl get nodes
```

## Bootstrap Cluster API

Initialize Cluster API on your management cluster.

### 1. Initialize Cluster API

```bash
clusterctl init --infrastructure docker
```

This command initializes CAPI with the Docker infrastructure provider.

### 2. Verify Cluster API Components

Check that the necessary CAPI components are running:

```bash
kubectl get pods -n capi-system
kubectl get pods -n docker-provider-system
```

All pods should be in the `Running` state.

## Install the Docker Provider

The Docker provider allows CAPI to manage Docker-based nodes.

If you initialized with `--infrastructure docker`, the Docker provider should already be installed. To confirm:

```bash
kubectl get deployments -n docker-provider-system
```

You should see deployments like `docker-controller-manager`.

If not installed, you can add it using:

```bash
clusterctl init --infrastructure docker
```

## Create a Cluster with Multi-Node Setup

### 1. Define a Cluster YAML

Create a YAML file (`cluster.yaml`) to define your desired Kubernetes cluster with multiple nodes.

```yaml
apiVersion: cluster.x-k8s.io/v1beta1
kind: Cluster
metadata:
  name: my-cluster
  namespace: default
spec:
  infrastructureRef:
    apiVersion: infrastructure.cluster.x-k8s.io/v1beta1
    kind: DockerCluster
    name: my-cluster
  controlPlaneRef:
    apiVersion: controlplane.cluster.x-k8s.io/v1beta1
    kind: KubeadmControlPlane
    name: my-cluster-control-plane
  topology:
    version: "v1.25.0" # Specify desired Kubernetes version
---
apiVersion: controlplane.cluster.x-k8s.io/v1beta1
kind: KubeadmControlPlane
metadata:
  name: my-cluster-control-plane
  namespace: default
spec:
  replicas: 1
  version: "v1.25.0"
  infrastructureTemplate:
    apiVersion: infrastructure.cluster.x-k8s.io/v1beta1
    kind: DockerMachineTemplate
    name: my-cluster-control-plane
  machineConfig:
    # Optional: Define additional kubeadm configurations
---
apiVersion: infrastructure.cluster.x-k8s.io/v1beta1
kind: DockerCluster
metadata:
  name: my-cluster
  namespace: default
spec:
  # Docker-specific cluster configurations
---
apiVersion: infrastructure.cluster.x-k8s.io/v1beta1
kind: DockerMachineTemplate
metadata:
  name: my-cluster-control-plane
  namespace: default
spec:
  template:
    spec:
      image: rancher/k3s:v1.25.0-k3s1 # Specify desired k3s image
```

### 2. Apply the Cluster Definition

```bash
kubectl apply -f cluster.yaml
```

### 3. Add Worker Nodes

Define a `machinedeployment.yaml` for worker nodes with autoscaling enabled.

```yaml
apiVersion: cluster.x-k8s.io/v1beta1
kind: MachineDeployment
metadata:
  name: worker-md
  namespace: default
spec:
  replicas: 2
  selector:
    matchLabels:
      cluster.x-k8s.io/cluster-name: my-cluster
      cluster.x-k8s.io/deployment-name: worker-md
  template:
    metadata:
      labels:
        cluster.x-k8s.io/cluster-name: my-cluster
        cluster.x-k8s.io/deployment-name: worker-md
    spec:
      bootstrap:
        configRef:
          apiVersion: bootstrap.cluster.x-k8s.io/v1beta1
          kind: KubeadmConfigTemplate
          name: worker-md
      infrastructureRef:
        apiVersion: infrastructure.cluster.x-k8s.io/v1beta1
        kind: DockerMachineTemplate
        name: worker-md
      version: "v1.25.0"
---
apiVersion: infrastructure.cluster.x-k8s.io/v1beta1
kind: DockerMachineTemplate
metadata:
  name: worker-md
  namespace: default
spec:
  template:
    spec:
      image: rancher/k3s:v1.25.0-k3s1
```

Apply the machine deployment:

```bash
kubectl apply -f machinedeployment.yaml
```

### 4. Verify Nodes

Check that the worker nodes are created and joined to the cluster:

```bash
kubectl get nodes
```

You should see the control plane node and the worker nodes.

## Configure Autoscaling

To enable autoscaling, you'll set up the Kubernetes Cluster Autoscaler or use MachineDeployment's built-in scaling features. Below is an example using **MachineDeployment** with Horizontal Pod Autoscaler (HPA).

### 1. Install Cluster Autoscaler

While Cluster API provides mechanisms to manage machines, integrating the **Cluster Autoscaler** can help automate scaling based on workloads.

First, download the Cluster Autoscaler manifest suitable for your Kubernetes version:

```bash
VERSION=$(curl -s https://api.github.com/repos/kubernetes/autoscaler/releases/latest | grep tag_name | cut -d '"' -f 4)
kubectl apply -f https://github.com/kubernetes/autoscaler/releases/download/${VERSION}/cluster-autoscaler.yaml
```

### 2. Configure Cluster Autoscaler

Edit the Cluster Autoscaler deployment to include the necessary flags and permissions.

```bash
kubectl -n kube-system edit deployment cluster-autoscaler
```

Add the following arguments to the container spec:

```yaml
containers:
- name: cluster-autoscaler
  args:
    - --v=4
    - --stderrthreshold=info
    - --cloud-provider=clusterapi
    - --nodes=1:5:worker-md
    - --scale-down-enabled=true
    - --scale-down-unneeded-time=10m
    - --scale-down-utilization-threshold=0.5
```

**Note**: The `--cloud-provider` is set to `clusterapi`, and `--nodes` specifies the min and max number of replicas for the `worker-md` MachineDeployment.

### 3. Add RBAC Permissions

Ensure Cluster Autoscaler has the necessary permissions to modify MachineDeployments.

Create a `cluster-autoscaler-rbac.yaml`:

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: cluster-autoscaler
rules:
  - apiGroups: ["cluster.x-k8s.io"]
    resources: ["machinedeployments", "machinesets", "machines"]
    verbs: ["get", "list", "watch", "update", "patch"]
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

Apply the RBAC configuration:

```bash
kubectl apply -f cluster-autoscaler-rbac.yaml
```

### 4. Annotate the Cluster

Add necessary annotations to the `Cluster` resource to allow autoscaling.

```bash
kubectl annotate cluster my-cluster cluster-autoscaler.kubernetes.io/safe-to-evict="true"
```

### 5. Test Autoscaling

Deploy a workload that requires more resources to trigger autoscaling.

```bash
kubectl create deployment nginx --image=nginx
kubectl scale deployment nginx --replicas=10
```

Monitor the Cluster Autoscaler logs to ensure it scales the `MachineDeployment` accordingly:

```bash
kubectl -n kube-system logs deployment/cluster-autoscaler
```

## Verify the Setup

1. **Check Nodes**:

   ```bash
   kubectl get nodes
   ```

   Ensure that the number of worker nodes scales up or down based on the workload.

2. **Check MachineDeployments**:

   ```bash
   kubectl get machinedeployments
   ```

   Verify that the replicas increase or decrease as expected.

3. **Monitor Autoscaler**:

   ```bash
   kubectl -n kube-system logs deployment/cluster-autoscaler
   ```

   Look for logs indicating scaling activities.

## Troubleshooting Tips

- **Cluster API Components Not Running**: Ensure all CAPI pods are in the `Running` state. Check with `kubectl get pods -A`.

- **Autoscaler Not Scaling**: Verify that Cluster Autoscaler has the correct permissions and is properly configured with the right flags.

- **Docker Provider Issues**: Ensure that the Docker provider is correctly initialized and that Docker is running without issues.

- **k3d Limitations**: Remember that k3d runs Kubernetes in Docker containers, which might have resource limitations based on your Docker setup.

## Additional Resources

- **Cluster API Documentation**: [https://cluster-api.sigs.k8s.io/](https://cluster-api.sigs.k8s.io/)
- **Docker Provider for Cluster API**: [https://github.com/kubernetes-sigs/cluster-api-provider-docker](https://github.com/kubernetes-sigs/cluster-api-provider-docker)
- **k3d Documentation**: [https://k3d.io/](https://k3d.io/)
- **Cluster Autoscaler Documentation**: [https://github.com/kubernetes/autoscaler/tree/master/cluster-autoscaler](https://github.com/kubernetes/autoscaler/tree/master/cluster-autoscaler)

---

By following the steps outlined above, you should have a local multi-node Kubernetes cluster managed by Cluster API with autoscaling capabilities using the Docker provider and k3d. This setup is ideal for development and testing environments.

If you encounter any issues or have specific requirements, refer to the official documentation of the respective tools for more detailed guidance.
