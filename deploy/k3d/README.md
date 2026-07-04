# k3d Cluster Configuration

Reproducible k3d cluster setup for thesis hybrid experiments.

## Quick Start

```bash
# Create cluster with all components
./create-cluster.sh

# Install Knative + Kourier
./knative-install.sh

# Verify setup
./test_cluster.sh

# Delete cluster
./delete-cluster.sh
```

## Cluster Configuration

- **Name:** `thesis-hybrid`
- **Nodes:** 1 server + 1 agent (autoscaler adds more dynamically)
- **Traefik:** Disabled (using HAProxy)
- **Registry:** Local registry at `k3d-registry.localhost:5000`

## Port Mappings

| External Port | Internal Port | Service |
|---------------|---------------|---------|
| 8080 | 80 | K8s Service (LoadBalancer) |
| 8081 | 31080 | Kourier (Knative gateway) |
| 8082 | 31082 | HAProxy (external) |
| 8404 | 31404 | HAProxy stats |
| 9090 | 31090 | Prometheus |
| 9102 | 31102 | Autoscaler metrics |

## Resource Limits

Per node (applied via Docker):
- Memory: 512M
- CPU: 1 core
- Memory Swap: 512M

## Components Installed

### By `create-cluster.sh`:
- k3d cluster with k3s v1.28.5
- Metrics Server (patched for k3d)
- thesis-system namespace

### By `knative-install.sh`:
- Knative Serving v1.12.0
- Kourier v1.12.0 (networking layer)
- DNS configured for sslip.io

## Manual Cluster Creation

```bash
k3d cluster create -c k3d-cluster.yaml
```

## Verification

```bash
# Check nodes
kubectl get nodes

# Check metrics
kubectl top nodes

# Check Knative
kubectl get pods -n knative-serving
kubectl get pods -n kourier-system
```

## Test Service

```bash
# Deploy test Knative service
./knative-install.sh --test

# Access test service
curl http://hello.default.127.0.0.1.sslip.io:8081
```
