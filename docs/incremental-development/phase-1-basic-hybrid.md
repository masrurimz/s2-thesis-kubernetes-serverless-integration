# Sprint 1: Basic Hybrid Foundation

## Goal
Build and validate the fundamental hybrid architecture concept with minimal complexity.

## Duration
**1 Week** (5 working days)

## Scope
Create a working system that demonstrates traffic can be intelligently routed between k3s and simulated serverless environments.

## Success Criteria
- ✅ Traffic successfully routes between k3s cluster and serverless simulation
- ✅ Manual traffic switching works reliably under load
- ✅ Basic monitoring collects essential metrics
- ✅ System remains stable during 30-minute load test
- ✅ Clear demonstration of cost vs performance trade-offs

## Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Load Testing  │    │ Traffic Router  │    │   K3s Cluster   │
│   (k6/curl)     │───►│   (HAProxy)     │───►│   (nginx app)   │
│                 │    │                 │    │                 │
└─────────────────┘    │                 │    └─────────────────┘
                       │                 │           │
                       │                 │    ┌─────────────────┐
                       │                 │───►│ Serverless Sim  │
                       │                 │    │ (Docker nginx)  │
                       └─────────────────┘    └─────────────────┘
                              │
                       ┌─────────────────┐
                       │   Monitoring    │
                       │  (Prometheus)   │
                       └─────────────────┘
```

## Components

### 1. K3s Cluster (Primary Backend)
**Purpose**: Cost-effective baseline compute
**Configuration**:
- Single-node k3s cluster with resource limits
- Simple nginx application deployment
- Basic service exposure via LoadBalancer

### 2. Serverless Simulation (Overflow Backend)  
**Purpose**: Infinite scaling simulation
**Configuration**:
- Docker container running nginx
- Isolated from k3s cluster
- Simulates serverless function behavior

### 3. Traffic Router (HAProxy)
**Purpose**: Intelligent traffic distribution
**Configuration**:
- Weighted round-robin load balancing
- Health checks for both backends
- Real-time weight adjustment capability
- Monitoring endpoint for statistics

### 4. Monitoring System (Prometheus)
**Purpose**: Metrics collection and analysis
**Configuration**:
- Basic resource metrics (CPU, memory)
- Request count and response time
- Backend health and distribution
- Cost estimation tracking

### 5. Load Testing (k6)
**Purpose**: Validate system under various loads
**Configuration**:
- Multiple load patterns (steady, spike, gradual)
- Response time measurement
- Error rate tracking
- Realistic HTTP request patterns

## Implementation Plan

### Day 1: Infrastructure Setup
**Morning**:
- [ ] Create k3s cluster with resource constraints
- [ ] Deploy simple nginx application to k3s
- [ ] Verify k3s cluster responds to HTTP requests

**Afternoon**:
- [ ] Setup Docker-based serverless simulation
- [ ] Test serverless simulation independently
- [ ] Document resource requirements and limits

### Day 2: Traffic Router Implementation
**Morning**:
- [ ] Configure HAProxy with both backends
- [ ] Implement basic weighted routing (80% k3s, 20% serverless)
- [ ] Add health checks and monitoring endpoints

**Afternoon**:
- [ ] Test traffic distribution under load
- [ ] Implement weight adjustment mechanism
- [ ] Verify failover behavior when backends are down

### Day 3: Monitoring Integration
**Morning**:
- [ ] Deploy Prometheus for metrics collection
- [ ] Configure metrics scraping from all components
- [ ] Setup basic dashboards for visualization

**Afternoon**:
- [ ] Implement cost tracking calculations
- [ ] Add request distribution monitoring
- [ ] Create alert rules for system health

### Day 4: Load Testing & Validation
**Morning**:
- [ ] Develop k6 load testing scripts
- [ ] Test system under steady load (100 RPS)
- [ ] Test system under traffic spike (100→500 RPS)

**Afternoon**:
- [ ] Test manual traffic weight adjustments
- [ ] Measure response time differences between backends
- [ ] Document performance characteristics

### Day 5: Documentation & Demo
**Morning**:
- [ ] Create setup and deployment scripts
- [ ] Write comprehensive documentation
- [ ] Prepare demonstration scenarios

**Afternoon**:
- [ ] Conduct 30-minute stability test
- [ ] Document lessons learned and improvements
- [ ] Plan Sprint 2 based on findings

## Technical Specifications

### K3s Cluster Configuration
```yaml
# k3d-cluster-config.yaml
apiVersion: k3d.io/v1alpha1
kind: Simple
metadata:
  name: hybrid-sprint1
servers: 1
agents: 1
options:
  k3s:
    extraArgs:
      - --kubelet-arg=eviction-hard=memory.available<200Mi
  resources:
    limits:
      cpu: 2
      memory: 2Gi
```

### HAProxy Configuration
```
# haproxy.cfg
global
    daemon
    stats socket /var/run/haproxy.sock mode 660

defaults
    mode http
    timeout connect 5000ms
    timeout client 50000ms
    timeout server 50000ms
    option httplog

frontend main
    bind *:8080
    default_backend servers

backend servers
    balance roundrobin
    option httpchk GET /health
    server k3s-cluster 127.0.0.1:30080 weight 80 check
    server serverless-sim 127.0.0.1:30081 weight 20 check

listen stats
    bind *:8404
    stats enable
    stats uri /stats
    stats refresh 30s
```

### Load Testing Script
```javascript
// k6-load-test.js
import http from 'k6/http';
import { check, sleep } from 'k6';

export let options = {
  stages: [
    { duration: '5m', target: 100 },  // Steady load
    { duration: '2m', target: 500 },  // Traffic spike
    { duration: '5m', target: 100 },  // Return to baseline
  ],
};

export default function() {
  let response = http.get('http://localhost:8080/');
  check(response, {
    'status is 200': (r) => r.status === 200,
    'response time < 500ms': (r) => r.timings.duration < 500,
  });
  sleep(1);
}
```

## Metrics to Collect

### Performance Metrics
- **Response Time**: p50, p95, p99 latency
- **Throughput**: Requests per second
- **Error Rate**: Failed request percentage
- **Backend Distribution**: Percentage of traffic to each backend

### Resource Metrics
- **CPU Usage**: Per backend and overall
- **Memory Usage**: Per backend and overall
- **Network I/O**: Bandwidth utilization
- **Container Metrics**: Docker resource consumption

### Cost Metrics
- **K3s Cost**: Simulated based on node hours
- **Serverless Cost**: Simulated based on request count
- **Total Cost**: Combined cost calculation
- **Cost per Request**: Efficiency metric

## Expected Results

### Performance Baseline
- **Normal Load (100 RPS)**: <100ms p95 response time
- **Traffic Spike (500 RPS)**: <200ms p95 response time
- **Error Rate**: <1% under all load conditions
- **Backend Distribution**: 80/20 split maintained

### Cost Analysis
- **K3s Dominant**: Lower cost per request during steady load
- **Serverless Supplement**: Higher cost but better performance during spikes
- **Hybrid Advantage**: Balance of cost and performance

## Deliverables

### Code
- [ ] Complete k3s cluster configuration
- [ ] HAProxy configuration with weight management
- [ ] Docker serverless simulation setup
- [ ] Prometheus monitoring configuration
- [ ] k6 load testing scripts
- [ ] Deployment automation scripts

### Documentation
- [ ] Setup and installation guide
- [ ] Architecture documentation with diagrams
- [ ] Testing procedures and results
- [ ] Cost analysis methodology
- [ ] Lessons learned and Sprint 2 planning

### Demonstration
- [ ] Working hybrid system demo
- [ ] Load testing demonstration
- [ ] Manual traffic weight adjustment demo
- [ ] Monitoring dashboard walkthrough

## Success Validation

### Functional Tests
```bash
# Test k3s backend
curl http://localhost:30080/

# Test serverless simulation  
curl http://localhost:30081/

# Test hybrid routing
for i in {1..100}; do curl -s http://localhost:8080/ | grep -o "Server: .*"; done

# Test weight adjustment
echo "set weight servers/k3s-cluster 60" | socat - /var/run/haproxy.sock
echo "set weight servers/serverless-sim 40" | socat - /var/run/haproxy.sock
```

### Load Tests
```bash
# Run steady load test
k6 run --duration 10m --vus 10 load-test-steady.js

# Run spike test  
k6 run load-test-spike.js

# Run endurance test
k6 run --duration 30m --vus 5 load-test-endurance.js
```

## Risk Mitigation

### Technical Risks
- **HAProxy Configuration**: Test thoroughly before load testing
- **Resource Limits**: Monitor cluster resources during tests
- **Network Issues**: Verify all endpoints are accessible

### Timeline Risks
- **Scope Creep**: Focus only on basic functionality
- **Integration Issues**: Test each component independently first
- **Documentation Debt**: Document as you build, not at the end

## Sprint Review Questions

1. **Does traffic route correctly between backends?**
2. **Can weights be adjusted manually without downtime?**
3. **Do monitoring metrics provide useful insights?**
4. **Is the system stable under sustained load?**
5. **What did we learn about hybrid architecture challenges?**
6. **What should be prioritized in Sprint 2?**

## Next Sprint Preview

Based on Sprint 1 learnings, Sprint 2 will focus on:
- **Automated Decision Making**: Replace manual weight adjustment
- **Simple Load Prediction**: Add basic forecasting capability
- **Historical Data**: Implement data collection for trend analysis
- **Basic Intelligence**: Threshold-based routing decisions

The foundation built in Sprint 1 provides the platform for adding sophistication in subsequent sprints.