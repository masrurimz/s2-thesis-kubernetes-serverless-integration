# Sprint 1 Setup Guide

## Prerequisites

- Docker Desktop running with 6GB+ RAM allocated
- kubectl and k3d installed  
- Available ports: 8080, 8081, 8082, 8404, 9090

## Infrastructure Components

### 1. K3s Cluster Backend (Port 8080)

**Purpose**: Cost-effective primary compute backend

**Setup**:
```bash
# Create cluster
k3d cluster create -c infrastructure/k3s/cluster-config.yaml

# Deploy nginx application
kubectl apply -f infrastructure/k3s/nginx-deployment.yaml
kubectl apply -f infrastructure/k3s/nginx-service.yaml

# Verify deployment
kubectl get pods
kubectl get services
```

**Test**:
```bash
curl http://localhost:8080        # Main endpoint
curl http://localhost:8080/health # Health check
```

**Resource Allocation**:
- RAM: 2GB limit
- CPU: 1 core limit  
- Storage: 5GB

### 2. Knative Serverless Backend (Port 8081)

**Purpose**: Realistic serverless simulation with cold starts and autoscaling

**Setup**:
```bash
# Install Knative Serving (already done)
kubectl apply -f https://github.com/knative/serving/releases/download/knative-v1.12.0/serving-crds.yaml
kubectl apply -f https://github.com/knative/serving/releases/download/knative-v1.12.0/serving-core.yaml
kubectl apply -f https://github.com/knative/net-kourier/releases/download/knative-v1.12.0/kourier.yaml

# Configure networking
kubectl patch configmap/config-network --namespace knative-serving --type merge --patch '{"data":{"ingress-class":"kourier.ingress.networking.knative.dev"}}'
kubectl patch configmap/config-domain --namespace knative-serving --type merge --patch '{"data":{"localhost":""}}'

# Deploy Knative Service
kubectl apply -f infrastructure/serverless/knative-service.yaml

# Setup port forwarding
kubectl port-forward -n kourier-system service/kourier 8081:80 --address=0.0.0.0 &
```

**Test**:
```bash
# Use test script
./scripts/test-knative.sh

# Or manually
curl -H "Host: serverless-sim.default.localhost" http://localhost:8081        # Main endpoint
curl -H "Host: serverless-sim.default.localhost" http://localhost:8081/health # Health check
```

**Resource Allocation**:
- Knative overhead: ~200MB RAM
- Per pod: 128MB RAM limit, 64MB request
- Features: Scale-to-zero, cold starts, autoscaling

## Validation Steps

### 1. Both Backends Respond
```bash
# K3s cluster
curl -s http://localhost:8080 | grep "K3s Cluster"

# Knative serverless
curl -s -H "Host: serverless-sim.default.localhost" http://localhost:8081 | grep "Knative Serverless"
```

### 2. Health Endpoints Work
```bash
curl http://localhost:8080/health  # Should return "k3s-cluster healthy"
curl -H "Host: serverless-sim.default.localhost" http://localhost:8081/health  # Should return "serverless-sim healthy (knative)"
```

### 3. Resource Usage Check
```bash
# Docker containers
docker stats --no-stream

# Kubernetes pods
kubectl top pods

# System resources
docker system df
```

## Current Resource Usage

**Total Allocated**: ~2.8GB RAM
- K3s cluster: 2GB
- Knative Serving: ~200MB overhead
- Knative pods: 128MB per pod (scale-to-zero capable)

**Remaining Buffer**: ~3.2GB available for HAProxy, Prometheus, and system overhead.

## Troubleshooting

### K3s Issues
```bash
# Check cluster status
k3d cluster list
kubectl cluster-info

# Check pod logs
kubectl logs -l app=nginx-app

# Restart deployment
kubectl rollout restart deployment/nginx-app
```

### Knative Issues  
```bash
# Check Knative Service status
kubectl get ksvc

# Check Knative pods
kubectl get pods -l serving.knative.dev/service=serverless-sim

# Check Knative logs
kubectl logs -l serving.knative.dev/service=serverless-sim

# Restart Knative service
kubectl delete ksvc serverless-sim
kubectl apply -f infrastructure/serverless/knative-service.yaml

# Check port forwarding
ps aux | grep "kubectl port-forward"
```

### Port Conflicts
```bash
# Check port usage
lsof -i :8080
lsof -i :8081

# Kill conflicting processes
sudo kill -9 <PID>
```

## Cleanup

### Remove Knative Service
```bash
kubectl delete ksvc serverless-sim
kubectl delete configmap serverless-config

# Stop port forwarding
pkill -f "kubectl port-forward.*kourier"
```

### Remove Knative Serving (if needed)
```bash
kubectl delete -f https://github.com/knative/net-kourier/releases/download/knative-v1.12.0/kourier.yaml
kubectl delete -f https://github.com/knative/serving/releases/download/knative-v1.12.0/serving-core.yaml
kubectl delete -f https://github.com/knative/serving/releases/download/knative-v1.12.0/serving-crds.yaml
```

### Remove K3s Cluster
```bash
k3d cluster delete hybrid-sprint1
```

## Next Steps

Day 2 will add HAProxy traffic router to intelligently distribute traffic between these two backends with 80/20 weight distribution and manual adjustment capabilities.

## Knative Serverless Features

The Knative implementation provides authentic serverless behaviors:

- **Scale-to-Zero**: Pods automatically terminate after 30 seconds of no traffic
- **Cold Starts**: New pods created on first request after scale-to-zero
- **Autoscaling**: Automatic pod scaling based on concurrent requests
- **Request Routing**: Industry-standard Knative request lifecycle
- **Metrics**: Real serverless metrics for research analysis