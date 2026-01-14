# VPS Deployment Guide

Production deployment guide for the Kubernetes-Serverless Hybrid Architecture on a 6-core/8GB VPS.

## Prerequisites

- **Hardware**: 6-core CPU, 8GB RAM VPS (Ubuntu 22.04 LTS recommended)
- **Network**: Public IP or domain accessible
- **Software**: 
  - Docker 24.0+ installed
  - curl, wget, git
  - Root or sudo access

### Verify System Requirements

```bash
# Check CPU cores (need 6+)
nproc

# Check RAM (need 8GB+)
free -h

# Check Docker
docker --version
docker run hello-world
```

## Quick Start (< 30 min)

### 1. K3s Installation

```bash
# Run K3s install script
./docs/deployment/scripts/setup-k3s.sh

# Verify installation
kubectl get nodes
kubectl get pods -A
```

**Expected output**: Single node in `Ready` state, all system pods running.

### 2. Knative + Kourier Setup

```bash
# Install Knative Serving + Kourier
./infrastructure/k3d/knative-install.sh

# Verify Knative components
kubectl get pods -n knative-serving
kubectl get pods -n kourier-system
```

**Expected output**: All Knative and Kourier pods in `Running` state.

### 3. Prometheus Deployment

```bash
# Deploy Prometheus stack
./docs/deployment/scripts/setup-prometheus.sh

# Verify Prometheus
kubectl get pods -n monitoring
kubectl get svc -n monitoring
```

**Expected output**: Prometheus pod running, service accessible.

### 4. HAProxy Configuration

```bash
# Install HAProxy
sudo apt-get update && sudo apt-get install -y haproxy

# Copy configuration
sudo cp infrastructure/haproxy/haproxy-vps.cfg /etc/haproxy/haproxy.cfg

# Install haproxy_exporter for Prometheus metrics
wget https://github.com/prometheus/haproxy_exporter/releases/download/v0.15.0/haproxy_exporter-0.15.0.linux-amd64.tar.gz
tar xzf haproxy_exporter-0.15.0.linux-amd64.tar.gz
sudo mv haproxy_exporter-0.15.0.linux-amd64/haproxy_exporter /usr/local/bin/

# Start HAProxy
sudo systemctl enable haproxy
sudo systemctl restart haproxy

# Start exporter (systemd service recommended for production)
haproxy_exporter --haproxy.scrape-uri="http://localhost:8404/stats?stats;csv" &
```

### 5. Test App Deployment

```bash
# Deploy K3s test app
kubectl apply -f infrastructure/test-app/k3s-deployment.yaml

# Deploy Knative test service
kubectl apply -f infrastructure/test-app/knative-service.yaml

# Verify deployments
kubectl get pods -n default
kubectl get ksvc -n default
```

### 6. Verification Steps

```bash
# Run full verification
./docs/deployment/scripts/verify-deployment.sh
```

Or verify manually:

```bash
# K3s health
kubectl get nodes
kubectl get pods -A | grep -v Running | grep -v Completed

# Knative health  
kubectl get ksvc
curl -H "Host: hello.default.example.com" http://localhost:31080

# Prometheus targets
curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | {job: .labels.job, health: .health}'

# HAProxy stats
curl http://localhost:8404/stats
```

## Component Details

### K3s

Single-node K3s installation optimized for VPS deployment.

**Configuration**:
- Traefik disabled (using Kourier for ingress)
- ServiceLB disabled (using HAProxy)
- Metrics-server enabled for HPA
- Memory limits configured for 8GB VPS

**Key Ports**:
| Port | Service |
|------|---------|
| 6443 | Kubernetes API |
| 10250 | Kubelet metrics |
| 31080 | Kourier NodePort |

**Resource Allocation**:
```
K3s server: ~1GB RAM reserved
Kubelet: 512MB system-reserved
Available for workloads: ~5.5GB
```

### Knative + Kourier

Knative Serving v1.12.0 with Kourier ingress controller.

**Configuration**:
- Scale-to-zero enabled (30s grace period)
- Stable window: 60s
- Target concurrency: 200 RPS
- DNS: sslip.io for automatic resolution (or configure custom domain)

**NodePort Access**:
```bash
# Kourier exposed on NodePort 31080
curl -H "Host: <service>.<namespace>.<domain>" http://<VPS-IP>:31080
```

**Custom Domain Setup** (optional):
```bash
# Configure your domain
kubectl patch configmap/config-domain \
  --namespace knative-serving \
  --type merge \
  --patch '{"data":{"yourdomain.com":""}}'
```

### Prometheus Stack

Minimal Prometheus deployment optimized for thesis research.

**Configuration** (`infrastructure/prometheus/prometheus.yaml`):
- Scrape interval: 15s
- Retention: 7 days
- Storage: 10GB max

**Scrape Targets**:
| Job | Target | Interval |
|-----|--------|----------|
| prometheus | localhost:9090 | 30s |
| haproxy | localhost:9101 | 15s |
| kubernetes-nodes | localhost:10250 | 30s |
| kubernetes-pods | pod annotations | 15s |
| knative | knative-serving | 15s |

**Access**:
```bash
# Port-forward to access UI
kubectl port-forward -n monitoring svc/prometheus 9090:9090

# Or expose via NodePort (configure in prometheus-k8s.yaml)
```

### HAProxy

Load balancer for hybrid routing between K3s and Knative backends.

**Configuration** (`infrastructure/haproxy/haproxy.cfg`):
- Frontend: Port 8082
- K3s backend: weight 80 (port 8080)
- Knative backend: weight 20 (port 31080)
- Stats: Port 8404

**haproxy_exporter**:
```bash
# Metrics endpoint
curl http://localhost:9101/metrics
```

### Monitoring

**Prometheus Queries for Thesis Metrics**:

```promql
# Request latency (p99)
histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))

# Throughput
rate(http_requests_total[5m])

# Error rate
rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m])

# HAProxy backend health
haproxy_backend_up

# Knative pod count
count(kube_pod_info{namespace="default", pod=~".*knative.*"})
```

## Troubleshooting

### K3s Issues

**Node not ready**:
```bash
# Check kubelet logs
journalctl -u k3s -f

# Check disk space
df -h

# Check memory
free -m
```

**Pods stuck in Pending**:
```bash
# Check events
kubectl describe pod <pod-name>

# Check resource availability
kubectl describe node
```

### Knative Issues

**Service not scaling**:
```bash
# Check autoscaler logs
kubectl logs -n knative-serving -l app=autoscaler

# Check activator
kubectl logs -n knative-serving -l app=activator
```

**Cold start too slow**:
```bash
# Reduce scale-to-zero grace period
kubectl patch configmap/config-autoscaler \
  --namespace knative-serving \
  --type merge \
  --patch '{"data":{"scale-to-zero-grace-period":"10s"}}'
```

### Prometheus Issues

**Target down**:
```bash
# Check target status
curl http://localhost:9090/api/v1/targets

# Check service discovery
kubectl get endpoints -n monitoring
```

**High memory usage**:
```bash
# Reduce retention
kubectl patch configmap prometheus-config -n monitoring \
  --patch '{"data":{"prometheus.yml":"... retention.time: 3d ..."}}'
```

### HAProxy Issues

**Backend unhealthy**:
```bash
# Check HAProxy stats
curl http://localhost:8404/stats

# Check backend connectivity
curl -v http://localhost:8080
curl -v http://localhost:31080
```

**Configuration syntax error**:
```bash
# Validate config
haproxy -c -f /etc/haproxy/haproxy.cfg
```

## Reference

### Port Summary

| Port | Service | Description |
|------|---------|-------------|
| 6443 | K3s API | Kubernetes API server |
| 8080 | K3s Ingress | Default K3s service port |
| 8082 | HAProxy | Hybrid load balancer frontend |
| 8404 | HAProxy Stats | HAProxy statistics |
| 9090 | Prometheus | Metrics UI |
| 9101 | haproxy_exporter | Prometheus metrics for HAProxy |
| 31080 | Kourier | Knative ingress NodePort |

### File Locations

| File | Purpose |
|------|---------|
| `/etc/rancher/k3s/k3s.yaml` | K3s kubeconfig |
| `/etc/haproxy/haproxy.cfg` | HAProxy configuration |
| `/var/lib/rancher/k3s/` | K3s data directory |

### Useful Commands

```bash
# K3s
k3s kubectl get nodes
systemctl status k3s
journalctl -u k3s -f

# Knative
kubectl get ksvc -A
kubectl describe ksvc <name>

# Prometheus
kubectl port-forward -n monitoring svc/prometheus 9090:9090

# HAProxy
haproxy -c -f /etc/haproxy/haproxy.cfg
systemctl reload haproxy
```

### Environment Variables

```bash
# K3s
export KUBECONFIG=/etc/rancher/k3s/k3s.yaml
export K3S_TOKEN=<token>

# Knative
export KNATIVE_VERSION=1.12.0
export KOURIER_VERSION=1.12.0
```
