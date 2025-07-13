# Sprint 1 Operations Manual

## HAProxy Traffic Router Operations

### Quick Reference Commands

```bash
# Start/Stop HAProxy
cd sprint-1/infrastructure/haproxy
docker-compose up -d        # Start HAProxy
docker-compose down         # Stop HAProxy
docker-compose restart      # Restart HAProxy

# Monitor HAProxy
docker logs sprint1-haproxy --tail 20    # View logs
docker ps | grep haproxy                 # Check status
curl http://localhost:8404/stats         # View stats

# Test Traffic Distribution
./sprint-1/scripts/test-traffic.sh       # Run traffic test
curl http://localhost:8082               # Single request

# Adjust Traffic Weights
./sprint-1/scripts/adjust-weights.sh 60 40   # 60% k3s, 40% serverless
./sprint-1/scripts/adjust-weights.sh 90 10   # 90% k3s, 10% serverless
```

### System Health Checks

#### 1. Verify All Components
```bash
# K3s cluster
curl http://localhost:8080
kubectl get pods

# Knative serverless  
./sprint-1/scripts/test-knative.sh

# HAProxy
curl http://localhost:8082
curl http://localhost:8404/stats
```

#### 2. Resource Monitoring
```bash
# Container resources
docker stats --no-stream sprint1-haproxy

# System resources
kubectl top nodes
kubectl top pods

# Total system usage
docker system df
```

### Traffic Weight Management

#### Default Configuration
- **K3s Cluster**: 80% (cost-effective, persistent)
- **Knative Serverless**: 20% (overflow, scaling)

#### Common Weight Scenarios

**High Load (Favor Serverless)**:
```bash
./sprint-1/scripts/adjust-weights.sh 40 60
```

**Cost Optimization (Favor K3s)**:
```bash
./sprint-1/scripts/adjust-weights.sh 90 10
```

**Load Testing (Even Split)**:
```bash
./sprint-1/scripts/adjust-weights.sh 50 50
```

**Emergency K3s Only**:
```bash
./sprint-1/scripts/adjust-weights.sh 100 0
```

#### Weight Adjustment Verification
```bash
# Check current weights
echo "show stat" | docker exec -i sprint1-haproxy socat - /tmp/haproxy.sock | grep servers

# View in web interface
open http://localhost:8404/stats
```

### Troubleshooting Guide

#### HAProxy Container Won't Start

**Symptoms**: Container restarting, logs show config errors
```bash
# Check configuration syntax
docker run --rm -v $(pwd)/haproxy.cfg:/tmp/haproxy.cfg:ro haproxy:2.4-alpine haproxy -c -f /tmp/haproxy.cfg

# Check container logs
docker logs sprint1-haproxy
```

**Common Fixes**:
- Ensure haproxy.cfg has proper line endings
- Verify socket permissions (/tmp/haproxy.sock mode 666)
- Check port availability (8082, 8404)

#### Backend Health Check Failures

**K3s Backend Down**:
```bash
# Check K3s cluster
kubectl cluster-info
kubectl get pods
curl http://localhost:8080

# Restart if needed
kubectl rollout restart deployment/nginx-app
```

**Knative Backend Down**:
```bash
# Check Knative service
kubectl get ksvc serverless-sim
kubectl get pods -l serving.knative.dev/service=serverless-sim

# Test with proper Host header
curl -H "Host: serverless-sim.default.localhost" http://localhost:8081

# Restart port forwarding
pkill -f "kubectl port-forward.*kourier"
kubectl port-forward -n kourier-system service/kourier 8081:80 --address=0.0.0.0 &
```

#### Traffic Distribution Issues

**All Traffic to One Backend**:
1. Check backend health in stats: http://localhost:8404/stats
2. Verify weight configuration
3. Test individual backends directly
4. Check HAProxy logs for routing errors

**No Traffic Response**:
1. Verify HAProxy is running and accessible
2. Check frontend binding (port 8082)
3. Test backend connectivity from HAProxy container
4. Review network configuration

### Performance Monitoring

#### Key Metrics to Track

**HAProxy Stats** (http://localhost:8404/stats):
- Backend status (UP/DOWN)
- Request rates and response times
- Connection counts and queues
- Error rates and timeouts

**Resource Usage**:
- Container memory usage (<256MB)
- CPU utilization (<0.25 cores)
- Network throughput
- Response time percentiles

#### Performance Thresholds

**Normal Operation**:
- Response time: <50ms p95
- Error rate: <1%
- Backend health: All UP
- Memory usage: <200MB

**Warning Levels**:
- Response time: 50-150ms p95
- Error rate: 1-5%
- Memory usage: 200-250MB

**Critical Levels**:
- Response time: >150ms p95
- Error rate: >5%
- Backend DOWN status
- Memory usage: >250MB

### Maintenance Procedures

#### Planned Maintenance
```bash
# 1. Drain traffic gradually
./sprint-1/scripts/adjust-weights.sh 0 100  # Route to healthy backend

# 2. Wait for connections to drain
echo "show stat" | docker exec -i sprint1-haproxy socat - /tmp/haproxy.sock

# 3. Perform maintenance
docker-compose down

# 4. Restore service
docker-compose up -d
./sprint-1/scripts/adjust-weights.sh 80 20  # Restore weights
```

#### Emergency Recovery
```bash
# 1. Stop all components
docker-compose down
kubectl delete ksvc serverless-sim

# 2. Clean restart
k3d cluster delete hybrid-sprint1
k3d cluster create -c ../k3s/cluster-config.yaml

# 3. Redeploy system
kubectl apply -f ../k3s/
kubectl apply -f ../serverless/
docker-compose up -d

# 4. Verify functionality
./sprint-1/scripts/test-traffic.sh
```

### Configuration Management

#### HAProxy Configuration Changes
1. Edit `sprint-1/infrastructure/haproxy/haproxy.cfg`
2. Validate syntax: `haproxy -c -f haproxy.cfg`
3. Restart container: `docker-compose restart`
4. Verify functionality: `./sprint-1/scripts/test-traffic.sh`

#### Weight Persistence
- Manual weight changes are temporary (lost on restart)
- Permanent changes require haproxy.cfg updates
- Document weight changes in operations log

### Security Considerations

#### Network Access
- HAProxy stats interface (8404) contains sensitive information
- Consider authentication for production use
- Restrict network access to management ports

#### Container Security
- HAProxy runs with minimal privileges
- Socket access limited to /tmp directory
- No sensitive data in configuration files

This operations manual provides comprehensive guidance for managing the HAProxy traffic router in Sprint 1's hybrid architecture.