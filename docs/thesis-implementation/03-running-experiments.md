# Running the Hybrid K3s-Serverless Experiment

This guide covers executing the complete hybrid k3s-serverless experiment with intelligent routing and cost optimization.

## Prerequisites

Ensure you have completed:

- [Prerequisites installation](0-prerequisites.md)
- [Cluster setup](1-setup-cluster.md)
- [Service deployment](2-deploying-services.md)

## Step 1: Initialize Hybrid System

### Start Monitoring

```bash
# Ensure Prometheus is running
kubectl port-forward service/prometheus 9090 --context k3d-hybrid-cluster &

# Verify metrics are available
curl http://localhost:9090/api/v1/query?query=up
```

### Launch Intelligent Autoscaler

```bash
cd autoscaler/hybrid-experiment
python3 intelligent-scaler.py &
echo $! > /tmp/scaler.pid
```

### Start Traffic Router

```bash
cd controller
python3 hybrid-router.py &
echo $! > /tmp/router.pid
```

## Step 2: Execute Test Scenarios

### Baseline Performance Test

```bash
cd workload
python3 intelligent-load-generator.py \
  --pattern baseline \
  --url http://localhost:8080 \
  --output results/baseline_results.json
```

**Expected**: k3s handles 100% traffic at steady 100 RPS for 30 minutes

### Gradual Scale-Up Test

```bash
python3 intelligent-load-generator.py \
  --pattern gradual_scale \
  --url http://localhost:8080 \
  --output results/gradual_scale_results.json
```

**Expected**: k3s scales up, then hybrid mode activates as load increases

### Traffic Spike Test

```bash
python3 intelligent-load-generator.py \
  --pattern traffic_spike \
  --url http://localhost:8080 \
  --output results/traffic_spike_results.json
```

**Expected**: Immediate serverless activation during 1000 RPS spike

### Sustained Heavy Load Test

```bash
python3 intelligent-load-generator.py \
  --pattern sustained_heavy \
  --url http://localhost:8080 \
  --output results/sustained_heavy_results.json
```

**Expected**: Initial serverless usage, then scale back to k3s for efficiency

### Mixed Workload Test

```bash
python3 intelligent-load-generator.py \
  --pattern mixed_workload \
  --url http://localhost:8080 \
  --output results/mixed_workload_results.json
```

**Expected**: Intelligent routing decisions based on varying traffic patterns

## Step 3: Monitor Real-time Metrics

### System Metrics Dashboard

```bash
# Open Prometheus UI
open http://localhost:9090

# Key queries to monitor:
# - rate(http_requests_total[1m])
# - histogram_quantile(0.95, http_request_duration_seconds_bucket)
# - k3s_node_count
# - routing_decision_total
```

### Live System Status

```bash
# Monitor autoscaler decisions
tail -f /var/log/hybrid-scaler.log

# Watch routing changes
watch -n 5 'cat /tmp/routing_config.json | jq .'

# Check k3s cluster status
kubectl get nodes --context k3d-hybrid-cluster
kubectl top nodes --context k3d-hybrid-cluster
```

### Serverless Simulation Status

```bash
# Monitor serverless containers
docker ps --filter "name=serverless-*"

# Check resource usage
docker stats --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"
```

## Step 4: Data Collection

### Export Prometheus Metrics

```bash
# Create metrics export directory
mkdir -p results/metrics

# Export key metrics for analysis
curl -G 'http://localhost:9090/api/v1/query_range' \
  --data-urlencode 'query=rate(http_requests_total[1m])' \
  --data-urlencode 'start=2024-01-01T00:00:00Z' \
  --data-urlencode 'end=2024-01-01T01:00:00Z' \
  --data-urlencode 'step=60s' > results/metrics/rps_data.json

curl -G 'http://localhost:9090/api/v1/query_range' \
  --data-urlencode 'query=histogram_quantile(0.95, http_request_duration_seconds_bucket)' \
  --data-urlencode 'start=2024-01-01T00:00:00Z' \
  --data-urlencode 'end=2024-01-01T01:00:00Z' \
  --data-urlencode 'step=60s' > results/metrics/latency_p95.json
```

### Collect Routing Decisions

```bash
# Extract routing decisions and costs
grep "Applied routing" /var/log/hybrid-scaler.log > results/routing_decisions.log
grep "Cost:" /var/log/hybrid-scaler.log > results/cost_analysis.log

# Export routing configuration history
cp /tmp/routing_config.json results/final_routing_config.json
```

### Generate Summary Report

```bash
# Run analysis script
python3 analysis/generate_summary.py \
  --input-dir results \
  --output results/experiment_summary.html
```

## Step 5: Validation and Analysis

### Performance Validation

- **Response Time**: Verify p95 latency <200ms during normal load, <500ms during spikes
- **Availability**: Confirm >99.9% success rate across all scenarios
- **Scaling Speed**: Check serverless activation time <30 seconds

### Cost Analysis

- **Efficiency**: Calculate cost savings vs pure serverless approach
- **Utilization**: Measure k3s resource utilization percentage
- **Switching Points**: Analyze optimal threshold values

### Routing Intelligence

- **Decision Quality**: Review routing decision logs for appropriateness
- **Prediction Accuracy**: Compare predicted vs actual load patterns
- **Threshold Effectiveness**: Evaluate switching point timing

## Step 6: Cleanup

### Stop Experiment Components

```bash
# Stop autoscaler and router
kill $(cat /tmp/scaler.pid)
kill $(cat /tmp/router.pid)

# Remove PID files
rm /tmp/scaler.pid /tmp/router.pid

# Stop port forwarding
pkill -f "kubectl port-forward"
```

### Clean Up Resources

```bash
# Remove serverless containers
docker rm -f $(docker ps -q --filter "name=serverless-*")

# Remove test network
docker network rm serverless-net

# Clean up temporary files
rm -f /tmp/routing_config.json /tmp/haproxy.cfg
```

### Preserve Results

```bash
# Archive experiment results
tar -czf experiment_results_$(date +%Y%m%d_%H%M%S).tar.gz results/

# Move to permanent storage
mv experiment_results_*.tar.gz ~/Documents/thesis_results/
```

## Troubleshooting

### Common Issues

**Metrics Server Not Available**

```bash
# Check metrics server status
kubectl get pods -n kube-system | grep metrics-server

# Restart if needed
kubectl rollout restart deployment/metrics-server -n kube-system
```

**Autoscaler Not Responding**

```bash
# Check autoscaler logs
tail -n 50 /var/log/hybrid-scaler.log

# Verify cluster connectivity
kubectl cluster-info --context k3d-hybrid-cluster
```

**Traffic Router Issues**

```bash
# Check HAProxy configuration
cat /tmp/haproxy.cfg

# Test routing manually
curl -v http://localhost:8080/work?duration_ms=5
```

### Performance Issues

- Reduce load generator RPS if system becomes overwhelmed
- Increase check intervals in autoscaler for slower systems
- Adjust resource limits if containers are being killed

## Next Steps

After completing the experiment:

1. Review [experiment results](experiment-results.md)
2. Compare with baseline k3s and pure serverless approaches
3. Document findings and optimize thresholds for future runs
4. Consider scaling up for production environment testing
