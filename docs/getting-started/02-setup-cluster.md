# Setting Up Kubernetes Clusters

This guide walks you through setting up the Kubernetes clusters needed for the experiment.

## Step 1: Create Cluster A

Cluster A will host the Rust app and HAProxy.

### Cluster A Configuration (in `cluster-configs/cluster-a/k3d-cluster-a.yaml`)

```yaml
apiVersion: k3d.io/v1alpha5
kind: Simple
metadata:
  name: cluster-a
servers: 1
agents: 2
```

### Create Cluster A

```bash
k3d cluster create cluster-a --config cluster-configs/cluster-a/k3d-cluster-a.yaml
```

## Step 2: Create Cluster B

Cluster B will host PostgreSQL and MinIO.

### Cluster B Configuration

```yaml
apiVersion: k3d.io/v1alpha1
kind: Simple
metadata:
  name: cluster-b
servers: 1
agents: 2
limits:
  cpu: 2
  memory: 1Gi
```

### Create Cluster B

```bash
k3d cluster create cluster-b --config cluster-configs/cluster-b/k3d-cluster-b.yaml
```

## Step 3: Create Cluster C

Cluster C will host the serverless Rust app using Knative.

### Cluster C Configuration

```yaml
apiVersion: k3d.io/v1alpha1
kind: Simple
metadata:
  name: "cluster-c"
servers: 1
agents: 2
limits:
  cpu: 2
  memory: 1Gi
```

### Create Cluster C

```bash
k3d cluster create cluster-c --config cluster-configs/cluster-c/k3d-cluster-c.yaml
```

After the clusters are created, verify them:

```bash
kubectl get nodes --context k3d-cluster-a
kubectl get nodes --context k3d-cluster-b
kubectl get nodes --context k3d-cluster-c
```
