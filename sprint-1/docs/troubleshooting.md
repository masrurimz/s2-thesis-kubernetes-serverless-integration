# Sprint 1 Troubleshooting Guide

## Common Issues and Solutions

### HAProxy Issues

#### Issue: Container Keeps Restarting
**Symptoms**: 
- `docker ps` shows container restarting
- Logs show configuration errors

**Diagnosis**:
```bash
docker logs sprint1-haproxy --tail 20
```

**Common Causes & Solutions**:

1. **Missing newline in config file**
   ```bash
   # Fix: Add newline to end of haproxy.cfg
   echo "" >> sprint-1/infrastructure/haproxy/haproxy.cfg
   docker-compose restart
   ```

2. **Socket permission issues**
   ```bash
   # Fix: Use /tmp directory with proper permissions
   # Edit haproxy.cfg: stats socket /tmp/haproxy.sock mode 666
   ```

3. **Port conflicts**
   ```bash
   # Check if ports 8082 or 8404 are in use
   lsof -i :8082
   lsof -i :8404
   # Kill conflicting processes or change ports
   ```

#### Issue: Stats Interface Not Accessible
**Symptoms**: 
- `curl http://localhost:8404/stats` fails
- Browser can't access stats page

**Solutions**:
```bash
# 1. Check HAProxy container status
docker ps | grep haproxy

# 2. Check port mapping
docker port sprint1-haproxy

# 3. Test container networking
docker exec sprint1-haproxy netstat -tlnp

# 4. Restart HAProxy
docker-compose restart
```

#### Issue: Weight Adjustment Script Fails
**Symptoms**:
- `./adjust-weights.sh` returns errors
- Socket connection refused

**Solutions**:
```bash
# 1. Check socket path in script matches config
grep "stats socket" sprint-1/infrastructure/haproxy/haproxy.cfg
grep "socat" sprint-1/scripts/adjust-weights.sh

# 2. Verify socat is available in container
docker exec sprint1-haproxy which socat

# 3. Test socket manually
echo "show stat" | docker exec -i sprint1-haproxy socat - /tmp/haproxy.sock
```

### K3s Backend Issues

#### Issue: K3s Cluster Not Responding
**Symptoms**:
- `curl http://localhost:8080` fails
- HAProxy shows k3s-cluster as DOWN

**Diagnosis**:
```bash
kubectl cluster-info
kubectl get pods
kubectl get services
```

**Solutions**:

1. **Cluster not running**
   ```bash
   k3d cluster list
   k3d cluster start hybrid-sprint1
   ```

2. **Pod not ready**
   ```bash
   kubectl get pods -o wide
   kubectl describe pod <pod-name>
   kubectl logs <pod-name>
   ```

3. **Service not accessible**
   ```bash
   kubectl get svc
   kubectl port-forward service/nginx-app 8080:80 --address=0.0.0.0
   ```

4. **Complete restart**
   ```bash
   kubectl rollout restart deployment/nginx-app
   kubectl wait --for=condition=ready pod -l app=nginx-app
   ```

### Knative Backend Issues

#### Issue: Knative Service Down (426 Upgrade Required)
**Symptoms**:
- HAProxy shows serverless-sim as DOWN
- Health check returns 426 status
- L7STS/426 error in stats

**Root Cause**: Knative requires Host header for routing

**Solutions**:

1. **Test Knative directly**
   ```bash
   # Correct way to test Knative
   curl -H "Host: serverless-sim.default.localhost" http://localhost:8081
   ./sprint-1/scripts/test-knative.sh
   ```

2. **Check Knative service status**
   ```bash
   kubectl get ksvc serverless-sim
   kubectl describe ksvc serverless-sim
   kubectl get pods -l serving.knative.dev/service=serverless-sim
   ```

3. **Verify port forwarding**
   ```bash
   # Check if port forwarding is running
   ps aux | grep "kubectl port-forward"
   
   # Restart port forwarding if needed
   pkill -f "kubectl port-forward.*kourier"
   kubectl port-forward -n kourier-system service/kourier 8081:80 --address=0.0.0.0 &
   ```

4. **Fix HAProxy Knative integration** (Advanced)
   ```bash
   # Add to haproxy.cfg backend section:
   # http-request set-header Host serverless-sim.default.localhost if { srv_id 1 }
   ```

#### Issue: Knative Service Not Scaling
**Symptoms**:
- No pods created for Knative service
- Requests timeout or fail

**Solutions**:
```bash
# 1. Check Knative Serving installation
kubectl get pods -n knative-serving

# 2. Check service configuration
kubectl get ksvc serverless-sim -o yaml

# 3. Check autoscaler logs
kubectl logs -n knative-serving -l app=autoscaler

# 4. Force pod creation
kubectl patch ksvc serverless-sim -p '{"spec":{"template":{"metadata":{"annotations":{"autoscaling.knative.dev/minScale":"1"}}}}}'
```

### Network and Connectivity Issues

#### Issue: Traffic Distribution Not Working
**Symptoms**:
- All traffic goes to one backend
- `test-traffic.sh` shows 100%/0% distribution

**Diagnosis Steps**:
```bash
# 1. Check backend health
curl http://localhost:8404/stats | grep -E "k3s-cluster|serverless-sim"

# 2. Test backends individually
curl http://localhost:8080  # K3s
curl -H "Host: serverless-sim.default.localhost" http://localhost:8081  # Knative

# 3. Check HAProxy configuration
docker exec sprint1-haproxy cat /usr/local/etc/haproxy/haproxy.cfg
```

**Solutions**:
1. **Both backends must be UP** - Fix unhealthy backends first
2. **Verify weights** - Check weight settings in stats interface
3. **Network connectivity** - Ensure host.docker.internal resolves

#### Issue: Port Conflicts
**Symptoms**:
- Container fails to start
- "Port already in use" errors

**Solutions**:
```bash
# 1. Find process using port
lsof -i :8082
lsof -i :8404
lsof -i :8080
lsof -i :8081

# 2. Stop conflicting services
sudo kill -9 <PID>
docker stop <container-name>

# 3. Use different ports (edit docker-compose.yml)
ports:
  - "8092:8082"  # Change external port
  - "8494:8404"
```

### Resource and Performance Issues

#### Issue: High Memory Usage
**Symptoms**:
- Container using >256MB RAM
- System becoming slow

**Solutions**:
```bash
# 1. Monitor resource usage
docker stats sprint1-haproxy --no-stream

# 2. Check for memory leaks
docker exec sprint1-haproxy ps aux

# 3. Restart container if needed
docker-compose restart

# 4. Reduce HAProxy logging if high traffic
# Edit haproxy.cfg: comment out log lines
```

#### Issue: Slow Response Times
**Symptoms**:
- High latency in traffic tests
- Timeouts in HAProxy stats

**Diagnosis**:
```bash
# 1. Check backend response times
time curl http://localhost:8080
time curl -H "Host: serverless-sim.default.localhost" http://localhost:8081

# 2. Monitor HAProxy stats
curl http://localhost:8404/stats | grep -E "response time|Total time"

# 3. Check system load
top
kubectl top nodes
```

**Solutions**:
1. **Optimize backend performance**
2. **Increase HAProxy timeouts** if needed
3. **Check network latency** between components
4. **Monitor resource constraints**

### Development Environment Issues

#### Issue: Docker Desktop Resource Limits
**Symptoms**:
- Containers failing to start
- "Not enough memory" errors

**Solutions**:
```bash
# 1. Check Docker Desktop settings
# Increase memory allocation to 6GB+

# 2. Clean up unused resources
docker system prune -a
docker volume prune

# 3. Monitor resource usage
docker system df
docker stats --no-stream
```

#### Issue: kubectl Commands Fail
**Symptoms**:
- "connection refused" errors
- kubectl commands timeout

**Solutions**:
```bash
# 1. Check cluster status
k3d cluster list
k3d cluster start hybrid-sprint1

# 2. Update kubeconfig
k3d kubeconfig merge hybrid-sprint1 --kubeconfig-switch-context

# 3. Verify connectivity
kubectl cluster-info
kubectl get nodes
```

## Emergency Recovery Procedures

### Complete System Reset
```bash
# 1. Stop all components
docker-compose down
docker stop $(docker ps -aq)

# 2. Clean Kubernetes cluster
k3d cluster delete hybrid-sprint1

# 3. Remove volumes and networks
docker volume prune -f
docker network prune -f

# 4. Restart from scratch
cd sprint-1/infrastructure/k3s
k3d cluster create -c cluster-config.yaml
kubectl apply -f nginx-deployment.yaml
kubectl apply -f nginx-service.yaml

cd ../serverless
kubectl apply -f knative-service.yaml
kubectl port-forward -n kourier-system service/kourier 8081:80 --address=0.0.0.0 &

cd ../haproxy
docker-compose up -d

# 5. Verify functionality
cd ../../scripts
./test-traffic.sh
```

### Quick Health Check Script
```bash
#!/bin/bash
echo "=== Sprint 1 Health Check ==="

echo "1. K3s Cluster:"
kubectl get pods 2>/dev/null && echo "✅ OK" || echo "❌ FAIL"

echo "2. Knative Service:"
kubectl get ksvc serverless-sim 2>/dev/null && echo "✅ OK" || echo "❌ FAIL"

echo "3. HAProxy Container:"
docker ps | grep -q sprint1-haproxy && echo "✅ OK" || echo "❌ FAIL"

echo "4. Traffic Routing:"
curl -s http://localhost:8082 >/dev/null && echo "✅ OK" || echo "❌ FAIL"

echo "5. Stats Interface:"
curl -s http://localhost:8404/stats >/dev/null && echo "✅ OK" || echo "❌ FAIL"
```

This troubleshooting guide covers the most common issues encountered in Sprint 1's hybrid architecture setup.