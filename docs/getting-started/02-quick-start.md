# Quick Start: 15-Minute Hybrid Demo

## Goal
Get a basic hybrid k3s-serverless system running in 15 minutes to understand the core concept.

## Prerequisites
- Docker running
- kubectl installed
- k3d installed
- 4GB+ available RAM

## Step 1: Setup Basic Infrastructure (3 minutes)

```bash
# Create simple k3s cluster
k3d cluster create demo-hybrid --agents 1 --port "8080:80@loadbalancer"

# Verify cluster
kubectl get nodes
```

## Step 2: Deploy Test Application (2 minutes)

```bash
# Create simple HTTP server
kubectl create deployment test-app --image=nginx:alpine
kubectl expose deployment test-app --port=80 --target-port=80
kubectl create ingress test-app --class=traefik --rule="localhost/*=test-app:80"

# Test application
curl http://localhost:8080
```

## Step 3: Simulate Serverless Environment (3 minutes)

```bash
# Create "serverless" simulation with Docker
docker run -d --name serverless-sim -p 8081:80 nginx:alpine

# Test serverless simulation
curl http://localhost:8081
```

## Step 4: Basic Traffic Router (5 minutes)

Create a simple HAProxy configuration:

```bash
# Create HAProxy config
cat > /tmp/haproxy.cfg << 'EOF'
global
    daemon

defaults
    mode http
    timeout connect 5000ms
    timeout client 50000ms
    timeout server 50000ms

frontend main
    bind *:8082
    default_backend servers

backend servers
    balance roundrobin
    server k3s-cluster 127.0.0.1:8080 weight 80 check
    server serverless-sim 127.0.0.1:8081 weight 20 check
EOF

# Start HAProxy
docker run -d --name traffic-router \
  -p 8082:8082 \
  -v /tmp/haproxy.cfg:/usr/local/etc/haproxy/haproxy.cfg \
  haproxy:alpine
```

## Step 5: Test Hybrid System (2 minutes)

```bash
# Test hybrid routing
for i in {1..10}; do
  curl -s http://localhost:8082 | grep -o "nginx.*"
  sleep 1
done

# You should see traffic distributed between both backends
```

## What You Just Built

🎉 **Congratulations!** You now have a basic hybrid system with:

- **K3s cluster** serving 80% of traffic (cost-effective baseline)
- **Simulated serverless** handling 20% of traffic (overflow capacity)
- **Traffic router** distributing load between both systems

## Understanding the Demo

### Traffic Flow
```
User Request → HAProxy Router → 80% to K3s / 20% to Serverless
```

### Key Concepts Demonstrated
1. **Traffic Distribution**: Requests split between different compute models
2. **Independent Scaling**: Each backend can scale independently
3. **Cost Optimization**: Majority traffic uses cost-effective k3s
4. **Overflow Capacity**: Serverless provides additional capacity

## Next Steps

### Make It Intelligent (Sprint 1)
- Add load monitoring
- Implement dynamic weight adjustment
- Add basic prediction

### Add Sophistication (Later Sprints)
- Machine learning prediction
- SLO-based routing
- Real dataset integration
- Formal evaluation

## Cleanup

```bash
# Stop everything
docker stop traffic-router serverless-sim
docker rm traffic-router serverless-sim
k3d cluster delete demo-hybrid
rm /tmp/haproxy.cfg
```

## Troubleshooting

**HAProxy won't start**: Check if port 8082 is available
```bash
lsof -i :8082
```

**K3s cluster issues**: Verify Docker has enough resources
```bash
docker system df
```

**Can't access services**: Check cluster status
```bash
kubectl get pods --all-namespaces
```

## What's Next?

- **[Understanding Architecture](03-understanding-architecture.md)** - Deep dive into components
- **[Sprint 1](../incremental-development/phase-1-basic-hybrid.md)** - Build a production-ready version
- **[Thesis Implementation](../thesis-implementation/)** - Full research system