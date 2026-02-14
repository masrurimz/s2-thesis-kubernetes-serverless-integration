# Deploying Services

This guide will show you how to deploy services like PostgreSQL, MinIO, and the Rust app across the Kubernetes clusters.

## Deploying PostgreSQL and MinIO (Cluster B)

### Step 1: Deploy PostgreSQL

Apply the PostgreSQL deployment in **Cluster B**:

```bash
kubectl apply -f cluster-configs/cluster-b/postgres.yaml --context k3d-cluster-b
```

### Step 2: Deploy MinIO

Apply the MinIO deployment in **Cluster B**:

```bash
kubectl apply -f cluster-configs/cluster-b/minio.yaml --context k3d-cluster-b
```

Verify the deployments in Cluster B:

```bash
kubectl get pods --context k3d-cluster-b
```

## Deploying Rust App (Cluster A)

Deploy the Rust app to **Cluster A**:

### Rust App Deployment Configuration (in `cluster-configs/cluster-a/deployment.yaml`)

```yml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: rust-app
spec:
  replicas: 1
  selector:
    matchLabels:
      app: rust-app
  template:
    metadata:
      labels:
        app: rust-app
    spec:
      containers:
        - name: rust-app
          image: rust-app:latest
          ports:
            - containerPort: 8080
          resources:
            limits:
              cpu: "0.512"
              memory: "256Mi"
            requests:
              cpu: "0.125"
              memory: "125Mi"
```

### Deploy Rust App on Cluster A

```bash
kubectl apply -f cluster-configs/cluster-a/deployment.yaml --context k3d-cluster-a
```

Verify the deployment:

```bash
kubectl get pods --context k3d-cluster-a
```

## Deploying Knative App (Cluster C)

Install Knative and deploy the serverless Rust app in **Cluster C**:

```bash
kubectl apply -f cluster-configs/clusterC/knative-app.yaml --context k3d-clusterC
```
