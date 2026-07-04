# cluster/

Kubernetes cluster lifecycle management.

## Why both k3d and k8s?

| Subdirectory | What it does | Tool |
|-------------|-------------|------|
| `k3d/` | Creates and deletes the k3d Kubernetes cluster | k3d (Docker-based K3s) |
| `k8s/` | Scales deployments inside the cluster | kubectl |

**k3d** is the **cluster provisioner** — it creates/deletes the Kubernetes cluster itself.
**k8s** is the **in-cluster operator** — it manages workloads running inside the cluster (scaling replicas, checking pod status).

Both deal with Kubernetes but at different layers:
- `k3d/` = cluster-level (before workloads exist)
- `k8s/` = workload-level (after cluster is running)

If you swapped k3d for kind or minikube, you'd replace `k3d/` — `k8s/` stays unchanged.
