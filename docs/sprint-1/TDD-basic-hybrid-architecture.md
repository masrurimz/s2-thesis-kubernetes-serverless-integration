# Technical Design Document: Basic Hybrid Architecture

**Sprint**: 1  
**Version**: 1.0  
**Date**: July 2025  
**Related**: [PRD-basic-hybrid-foundation.md](./PRD-basic-hybrid-foundation.md)

## Architecture Overview

### System Architecture Diagram

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Load Testing  │    │ Traffic Router  │    │   K3s Cluster   │
│   (k6 scripts)  │───►│   (HAProxy)     │───►│   (nginx app)   │
│   Port: N/A     │    │   Port: 8082    │    │   Port: 8080    │
└─────────────────┘    │                 │    └─────────────────┘
                       │                 │           │
                       │                 │    ┌─────────────────┐
                       │                 │───►│ Serverless Sim  │
                       │                 │    │ (Docker nginx)  │
                       └─────────────────┘    │ Port: 8081      │
                              │               └─────────────────┘
                       ┌─────────────────┐           │
                       │   Monitoring    │◄──────────┘
                       │  (Prometheus)   │
                       │   Port: 9090    │
                       └─────────────────┘
```

### Data Flow

**Normal Request Flow:**

1. Load testing tool sends HTTP request to HAProxy (port 8082)
2. HAProxy applies weighted round-robin (80% k3s, 20% serverless)
3. Request routed to either k3s (port 8080) or serverless (port 8081)
4. Backend processes request and returns response
5. HAProxy forwards response back to client
6. Prometheus scrapes metrics from HAProxy and backends

**Manual Weight Adjustment Flow:**

1. Administrator connects to HAProxy stats socket
2. Issues weight change command via socat
3. HAProxy immediately applies new weights
4. Subsequent requests use new distribution
5. Change logged in HAProxy stats and Prometheus metrics

### Component Interaction

**HAProxy ↔ K3s Cluster:**

- Health checks every 5 seconds via HTTP GET /
- Load balancing via weighted round-robin
- Connection pooling and keep-alive

**HAProxy ↔ Serverless Simulation:**

- Health checks every 5 seconds via HTTP GET /
- Load balancing via weighted round-robin
- Isolated Docker container networking

**Prometheus ↔ All Components:**

- Metrics scraping every 15 seconds (30 seconds for constrained)
- HAProxy stats endpoint: /stats
- System metrics via node_exporter
- Custom application metrics

## Component Design

### 1. K3s Cluster Backend

**Purpose**: Cost-effective primary compute backend
**Technology**: k3d with nginx deployment

**Configuration**:

```yaml
# Resource Limits (Constrained Environment)
CPU: 1 core
Memory: 2GB
Storage: 5GB

# Resource Limits (Full Environment)
CPU: 2 cores
Memory: 4GB
Storage: 10GB
```

**Services**:

- **nginx deployment**: Basic HTTP server responding on all paths
- **LoadBalancer service**: Exposes nginx on port 8080
- **Health endpoint**: Responds to GET / with HTTP 200

**Files to Create**:

- `sprint-1/infrastructure/k3s/cluster-config.yaml`: k3d cluster configuration
- `sprint-1/infrastructure/k3s/nginx-deployment.yaml`: Kubernetes manifests
- `sprint-1/infrastructure/k3s/nginx-service.yaml`: Service configuration

### 2. Serverless Simulation Backend

**Purpose**: Infinite scaling simulation for overflow traffic
**Technology**: Docker container with nginx

**Configuration**:

```yaml
# Resource Limits (Constrained Environment)
CPU: 0.25 cores
Memory: 512MB
Storage: 1GB

# Resource Limits (Full Environment)
CPU: 0.5 cores
Memory: 1GB
Storage: 2GB
```

**Services**:

- **nginx container**: Isolated HTTP server on port 8081
- **Health endpoint**: Responds to GET / with HTTP 200
- **Container networking**: Bridge mode with port mapping

**Files to Create**:

- `sprint-1/infrastructure/serverless/docker-compose.yml`: Container configuration
- `sprint-1/infrastructure/serverless/nginx.conf`: Custom nginx configuration

### 3. Traffic Router (HAProxy)

**Purpose**: Intelligent traffic distribution and routing control
**Technology**: HAProxy 2.4+ with stats and socket interface

**Configuration**:

```yaml
# Resource Limits (Constrained Environment)
CPU: 0.25 cores
Memory: 256MB
Storage: 512MB

# Resource Limits (Full Environment)
CPU: 0.5 cores
Memory: 512MB
Storage: 1GB
```

**Services**:

- **Frontend**: Accepts traffic on port 8082
- **Backend**: Routes to k3s (8080) and serverless (8081)
- **Stats interface**: Web UI on port 8404
- **Socket interface**: Runtime configuration via Unix socket

**Load Balancing Algorithm**:

```
Default Weights:
- k3s-cluster: 80 (80% of traffic)
- serverless-sim: 20 (20% of traffic)

Health Check:
- Method: HTTP GET /
- Interval: 5 seconds
- Timeout: 3 seconds
- Retries: 3
```

**Files to Create**:

- `sprint-1/infrastructure/haproxy/haproxy.cfg`: Main configuration
- `sprint-1/infrastructure/haproxy/docker-compose.yml`: Container setup
- `sprint-1/scripts/adjust-weights.sh`: Weight adjustment utility

### 4. Monitoring System (Prometheus)

**Purpose**: Metrics collection and performance monitoring
**Technology**: Prometheus with custom exporters

**Configuration**:

```yaml
# Resource Limits (Constrained Environment)
CPU: 0.25 cores
Memory: 1GB
Storage: 2GB
Retention: 1 hour
Scrape Interval: 30 seconds

# Resource Limits (Full Environment)
CPU: 0.5 cores
Memory: 2GB
Storage: 5GB
Retention: 6 hours
Scrape Interval: 15 seconds
```

**Metrics Collected**:

- **HAProxy**: Request count, response time, backend status, weight distribution
- **System**: CPU usage, memory usage, network I/O
- **Application**: Request count, response codes, latency histograms
- **Custom**: Cost estimation, traffic distribution ratios

**Files to Create**:

- `sprint-1/infrastructure/monitoring/prometheus.yml`: Main configuration
- `sprint-1/infrastructure/monitoring/docker-compose.yml`: Container setup
- `sprint-1/infrastructure/monitoring/rules.yml`: Alert rules

### 5. Load Testing Framework

**Purpose**: Validate system performance and behavior under load
**Technology**: k6 with multiple test scenarios

**Test Scenarios**:

```javascript
// Steady Load Test
Duration: 10 minutes
Virtual Users: 10
RPS Target: 50 (constrained) / 100 (full)
Pattern: Constant load

// Traffic Spike Test
Stages:
- Ramp up: 2 minutes to 50 RPS
- Spike: 1 minute to 200 RPS
- Recovery: 2 minutes back to 50 RPS
- Baseline: 5 minutes at 50 RPS

// Endurance Test
Duration: 30 minutes
Virtual Users: 5
RPS Target: 25 (constrained) / 50 (full)
Pattern: Sustained load for stability
```

**Files to Create**:

- `sprint-1/load-testing/steady-load.js`: Constant load test
- `sprint-1/load-testing/spike-load.js`: Traffic spike simulation
- `sprint-1/load-testing/endurance-test.js`: Long-duration stability test
- `sprint-1/scripts/run-load-tests.sh`: Test execution wrapper

## File and Folder Structure

### Complete Implementation Structure

```
sprint-1/
├── README.md                           # Sprint overview and quick start
├── infrastructure/                     # All infrastructure configurations
│   ├── k3s/
│   │   ├── cluster-config.yaml         # k3d cluster configuration
│   │   ├── nginx-deployment.yaml       # Kubernetes nginx deployment
│   │   └── nginx-service.yaml          # Kubernetes service configuration
│   ├── serverless/
│   │   ├── docker-compose.yml          # Docker container configuration
│   │   └── nginx.conf                  # Custom nginx configuration
│   ├── haproxy/
│   │   ├── haproxy.cfg                 # HAProxy main configuration
│   │   └── docker-compose.yml          # HAProxy container setup
│   └── monitoring/
│       ├── prometheus.yml              # Prometheus configuration
│       ├── docker-compose.yml          # Prometheus container setup
│       └── rules.yml                   # Alert rules and recording rules
├── scripts/                            # Automation and utility scripts
│   ├── setup.sh                        # Complete system setup
│   ├── teardown.sh                     # Complete system teardown
│   ├── adjust-weights.sh               # Manual weight adjustment
│   ├── test-traffic.sh                 # Basic traffic testing
│   ├── run-load-tests.sh               # Load testing wrapper
│   └── check-health.sh                 # System health validation
├── load-testing/                       # k6 load testing scripts
│   ├── steady-load.js                  # Constant load test
│   ├── spike-load.js                   # Traffic spike simulation
│   ├── endurance-test.js               # Long-duration stability test
│   └── utils.js                        # Common testing utilities
├── results/                            # Test results and analysis
│   ├── performance-baseline.md         # Performance test results
│   ├── resource-utilization.md         # Resource usage analysis
│   ├── cost-analysis.md                # Cost calculation baseline
│   └── lessons-learned.md              # Sprint retrospective
└── docs/                               # Local documentation
    ├── setup-guide.md                  # Detailed setup instructions
    ├── troubleshooting.md              # Common issues and solutions
    └── operations-manual.md            # Day-to-day operations guide
```

## Configuration Specifications

### 1. K3d Cluster Configuration

**File**: `sprint-1/infrastructure/k3s/cluster-config.yaml`

```yaml
apiVersion: k3d.io/v1alpha1
kind: Simple
metadata:
  name: hybrid-sprint1
servers: 1
agents: 0 # Single node for constrained environments
options:
  k3s:
    extraArgs:
      - --kubelet-arg=eviction-hard=memory.available<100Mi
      - --kubelet-arg=system-reserved=memory=512Mi
  resources:
    limits:
      cpu: 1 # Constrained environment
      memory: 2Gi # Constrained environment
ports:
  - port: 8080:80
    nodeFilters:
      - loadbalancer
```

### 2. HAProxy Configuration

**File**: `sprint-1/infrastructure/haproxy/haproxy.cfg`

```
global
    daemon
    stats socket /var/run/haproxy.sock mode 660 level admin
    log stdout local0

defaults
    mode http
    timeout connect 5000ms
    timeout client 50000ms
    timeout server 50000ms
    option httplog
    log global

frontend hybrid_frontend
    bind *:8082
    default_backend servers

backend servers
    balance roundrobin
    option httpchk GET /
    http-check expect status 200
    server k3s-cluster host.docker.internal:8080 weight 80 check inter 5s
    server serverless-sim host.docker.internal:8081 weight 20 check inter 5s

listen stats
    bind *:8404
    stats enable
    stats uri /stats
    stats refresh 30s
    stats admin if TRUE
```

### 3. Prometheus Configuration

**File**: `sprint-1/infrastructure/monitoring/prometheus.yml`

```yaml
global:
  scrape_interval: 30s # Constrained environment
  evaluation_interval: 30s

scrape_configs:
  - job_name: "haproxy"
    static_configs:
      - targets: ["host.docker.internal:8404"]
    metrics_path: /stats
    params:
      csv: [""]

  - job_name: "k3s-cluster"
    static_configs:
      - targets: ["host.docker.internal:8080"]

  - job_name: "serverless-sim"
    static_configs:
      - targets: ["host.docker.internal:8081"]

  - job_name: "prometheus"
    static_configs:
      - targets: ["localhost:9090"]
```

### 4. Docker Compose Configurations

**HAProxy Container**: `sprint-1/infrastructure/haproxy/docker-compose.yml`

```yaml
version: "3.8"
services:
  haproxy:
    image: haproxy:2.4-alpine
    container_name: sprint1-haproxy
    ports:
      - "8082:8082"
      - "8404:8404"
    volumes:
      - ./haproxy.cfg:/usr/local/etc/haproxy/haproxy.cfg:ro
      - haproxy-socket:/var/run
    deploy:
      resources:
        limits:
          memory: 256M
          cpus: "0.25"
    restart: unless-stopped
    networks:
      - hybrid-network

volumes:
  haproxy-socket:

networks:
  hybrid-network:
    driver: bridge
```

**Serverless Simulation**: `sprint-1/infrastructure/serverless/docker-compose.yml`

```yaml
version: "3.8"
services:
  serverless-sim:
    image: nginx:alpine
    container_name: sprint1-serverless
    ports:
      - "8081:80"
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: "0.25"
    restart: unless-stopped
    networks:
      - hybrid-network

networks:
  hybrid-network:
    external: true
```

## Resource Allocation

### Constrained Environment (6GB Usable RAM)

| Component      | RAM       | CPU      | Storage    | Port |
| -------------- | --------- | -------- | ---------- | ---- |
| K3s Cluster    | 2GB       | 1.0      | 5GB        | 8080 |
| Serverless Sim | 512MB     | 0.25     | 1GB        | 8081 |
| HAProxy        | 256MB     | 0.25     | 512MB      | 8082 |
| Prometheus     | 1GB       | 0.25     | 2GB        | 9090 |
| **Total**      | **3.8GB** | **1.75** | **8.5GB**  | -    |
| **Buffer**     | **2.2GB** | **2.25** | **11.5GB** | -    |

### Full Environment (16GB+ RAM)

| Component      | RAM       | CPU     | Storage  | Port |
| -------------- | --------- | ------- | -------- | ---- |
| K3s Cluster    | 4GB       | 2.0     | 10GB     | 8080 |
| Serverless Sim | 1GB       | 0.5     | 2GB      | 8081 |
| HAProxy        | 512MB     | 0.5     | 1GB      | 8082 |
| Prometheus     | 2GB       | 0.5     | 5GB      | 9090 |
| **Total**      | **7.5GB** | **3.5** | **18GB** | -    |
| **Buffer**     | **8.5GB** | **4.5** | **32GB** | -    |

## Integration Points

### HAProxy Management Interface

**Manual Weight Adjustment**:

```bash
# Connect to HAProxy socket
echo "show stat" | socat - /var/run/haproxy.sock

# Change weights
echo "set weight servers/k3s-cluster 60" | socat - /var/run/haproxy.sock
echo "set weight servers/serverless-sim 40" | socat - /var/run/haproxy.sock

# Verify changes
echo "show stat" | socat - /var/run/haproxy.sock | grep servers
```

**Health Monitoring**:

```bash
# Check backend health
curl -s http://localhost:8404/stats

# Check individual backends
curl -s http://localhost:8080/  # K3s cluster
curl -s http://localhost:8081/  # Serverless simulation
```

### Prometheus Metrics Interface

**Key Metrics**:

```promql
# Request rate by backend
rate(haproxy_backend_http_requests_total[5m])

# Response time percentiles
histogram_quantile(0.95, rate(haproxy_backend_http_response_time_seconds_bucket[5m]))

# Backend weight distribution
haproxy_backend_weight

# System resource usage
rate(cpu_usage_seconds_total[5m])
memory_usage_bytes
```

### API Specifications

**HAProxy Stats API**:

- **Endpoint**: `http://localhost:8404/stats`
- **Format**: CSV or HTML
- **Authentication**: None (basic setup)
- **Refresh**: 30 second intervals

**Prometheus API**:

- **Query Endpoint**: `http://localhost:9090/api/v1/query`
- **Range Endpoint**: `http://localhost:9090/api/v1/query_range`
- **Metrics Endpoint**: `http://localhost:9090/metrics`

## Testing Strategy

### Unit Testing

**Component Isolation Tests**:

1. **K3s Cluster**: Verify nginx deployment responds correctly
2. **Serverless Sim**: Verify Docker container responds correctly
3. **HAProxy**: Verify configuration loads and health checks work
4. **Prometheus**: Verify metrics collection and storage

### Integration Testing

**End-to-End Tests**:

1. **Traffic Routing**: Verify requests route to both backends
2. **Weight Distribution**: Verify traffic split matches configured weights
3. **Manual Adjustment**: Verify weight changes affect traffic distribution
4. **Health Monitoring**: Verify failed backends are removed from rotation

### Performance Testing

**Load Test Scenarios**:

1. **Steady Load**: 50 RPS for 10 minutes (constrained) / 100 RPS (full)
2. **Traffic Spike**: 50→200→50 RPS transition
3. **Endurance**: 25 RPS for 30 minutes (constrained) / 50 RPS (full)

**Performance Targets**:

- **Response Time**: p95 < 150ms (normal), p95 < 300ms (spike)
- **Error Rate**: < 2% under all conditions
- **Resource Usage**: Within allocated limits
- **Weight Accuracy**: ±5% of configured distribution

### Validation Criteria

**Functional Validation**:

- [ ] All components start successfully
- [ ] Traffic routes to both backends
- [ ] Manual weight adjustment works
- [ ] Monitoring collects expected metrics
- [ ] Health checks detect backend failures

**Performance Validation**:

- [ ] Response time targets met
- [ ] Error rate targets met
- [ ] Resource usage within limits
- [ ] System stable for 30+ minutes
- [ ] Load testing scenarios pass

## Deployment Strategy

### Setup Sequence

1. **Environment Preparation**

   ```bash
   # Verify prerequisites
   docker --version
   kubectl version --client
   k3d version

   # Create project directory
   mkdir -p sprint-1
   cd sprint-1
   ```

2. **Infrastructure Deployment**

   ```bash
   # Deploy in order
   ./scripts/setup.sh

   # Manual verification
   ./scripts/check-health.sh
   ```

3. **Testing and Validation**

   ```bash
   # Run load tests
   ./scripts/run-load-tests.sh

   # Manual traffic testing
   ./scripts/test-traffic.sh
   ```

### Teardown Sequence

```bash
# Complete cleanup
./scripts/teardown.sh

# Manual verification
docker ps -a | grep sprint1
kubectl get all
```

### Rollback Strategy

**Component Failure Recovery**:

1. **Identify Failed Component**: Check logs and health endpoints
2. **Isolate Component**: Remove from load balancer rotation
3. **Restart Component**: Use individual component restart procedures
4. **Verify Recovery**: Health checks and load testing
5. **Return to Service**: Add back to load balancer rotation

**Complete System Recovery**:

1. **Stop All Components**: `./scripts/teardown.sh`
2. **Clean Environment**: Remove containers, networks, volumes
3. **Redeploy System**: `./scripts/setup.sh`
4. **Validate Functionality**: Run complete test suite

This technical design provides comprehensive implementation guidance while maintaining flexibility for both constrained and full resource environments.
