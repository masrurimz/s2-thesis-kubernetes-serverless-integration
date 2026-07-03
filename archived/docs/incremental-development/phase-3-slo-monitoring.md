# Sprint 3: SLO Monitoring & Tail Latency

## Goal

Implement thesis-level SLO monitoring with 99th percentile tail latency focus and Algorithm 1 routing controller.

## Duration

**1 Week** (5 working days)

## Prerequisites

- Completed Sprint 2: Automated load prediction working
- Historical data collection and simple prediction functional
- Basic traffic weight automation operational

## Success Criteria

- ✅ 99th percentile tail latency monitoring implemented
- ✅ 5-second SLO violation detection working
- ✅ Algorithm 1 (thesis routing controller) operational
- ✅ Cost tracking and analysis automated
- ✅ System maintains <200ms p99 latency under normal load

## Scope & Approach

### What We're Adding

- **Tail Latency Monitoring**: 99th percentile response time tracking
- **SLO Violation Detection**: 5-second rolling window detection
- **Algorithm 1 Implementation**: Thesis routing controller logic
- **Cost Analysis**: Formal cost calculation and optimization
- **Performance SLO Management**: Target <200ms p99 latency

### Key Transition: From RPS to SLO-Based Routing

- **Sprint 2**: Routing based on predicted RPS thresholds
- **Sprint 3**: Routing based on actual SLO violations and tail latency

## Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Tail Latency  │    │ SLO Violation   │    │ Routing         │
│   Monitor       │───►│ Detector        │───►│ Controller      │
│   (p99 tracking)│    │ (5s window)     │    │ (Algorithm 1)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         ▲                       │                       │
         │                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Prometheus    │    │ Cost Calculator │    │   HAProxy       │
│   (Metrics)     │    │ (Google Cloud)  │    │ (SLO routing)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Components to Build

### 1. Tail Latency Monitor

**Purpose**: Track 99th percentile response times in real-time

```python
class TailLatencyMonitor:
    def __init__(self):
        self.latency_window = deque(maxlen=300)  # 5 minutes of data

    async def get_p99_latency(self) -> float:
        # Query Prometheus for histogram_quantile(0.99, ...)
        # Return current 99th percentile latency in milliseconds
```

### 2. SLO Violation Detector

**Purpose**: Detect sustained SLO violations using 5-second windows

```python
class SLOViolationDetector:
    def __init__(self, slo_threshold_ms: float = 200.0):
        self.slo_threshold = slo_threshold_ms
        self.violation_window = deque(maxlen=5)  # 5 seconds

    def check_slo_violation(self, current_p99: float) -> bool:
        # Track violations over 5-second sliding window
        # Return True if SLO consistently violated
```

### 3. Routing Controller (Algorithm 1 from Thesis)

**Purpose**: Implement formal thesis routing algorithm

```python
class RoutingController:
    def __init__(self):
        self.reroute_traffic = False
        self.violation_timer = 0
        self.compliance_timer = 0

    async def routing_control_loop(self):
        # Implementation of Algorithm 1 from thesis
        # Variables: reroute_traffic, violation_timer, compliance_timer
        # repeat: GetTailLatency(), GetCPUUsage(), routing decisions
```

### 4. Cost Calculator

**Purpose**: Real-time cost analysis with Google Cloud pricing

```python
class CostCalculator:
    def __init__(self):
        # Google Cloud pricing (as specified in thesis)
        self.k3s_node_cost_per_hour = 0.095  # e2-standard-2
        self.serverless_cost_per_invocation = 0.0000004  # Cloud Functions

    def calculate_real_time_cost(self) -> Dict[str, float]:
        # Return current cost breakdown and total
```

## Implementation Plan

### Day 1: Tail Latency Monitoring

**Morning**:

- [ ] Implement 99th percentile latency collection from Prometheus
- [ ] Create real-time latency histogram processing
- [ ] Setup sliding window for tail latency tracking

**Afternoon**:

- [ ] Test latency monitoring under various load conditions
- [ ] Calibrate latency measurement accuracy
- [ ] Implement latency alerting thresholds

### Day 2: SLO Violation Detection

**Morning**:

- [ ] Build 5-second violation detection window
- [ ] Implement SLO threshold configuration (200ms default)
- [ ] Create violation state tracking and logging

**Afternoon**:

- [ ] Test SLO detection with artificial latency injection
- [ ] Validate detection accuracy and timing
- [ ] Implement detection confidence scoring

### Day 3: Algorithm 1 Implementation

**Morning**:

- [ ] Implement Algorithm 1 state machine from thesis
- [ ] Build violation_timer and compliance_timer logic
- [ ] Create reroute_traffic state management

**Afternoon**:

- [ ] Test Algorithm 1 under SLO violation scenarios
- [ ] Validate 5-second violation and compliance thresholds
- [ ] Ensure routing decisions match thesis specification

### Day 4: Cost Analysis Integration

**Morning**:

- [ ] Implement Google Cloud cost calculation model
- [ ] Create real-time cost tracking and reporting
- [ ] Build cost optimization recommendations

**Afternoon**:

- [ ] Integrate cost analysis with routing decisions
- [ ] Test cost tracking under various routing scenarios
- [ ] Validate cost calculations against expected values

### Day 5: Integration & Validation

**Morning**:

- [ ] Integrate all components into cohesive SLO-aware system
- [ ] Test complete system under thesis evaluation scenarios
- [ ] Validate SLO compliance and routing behavior

**Afternoon**:

- [ ] Performance tuning and optimization
- [ ] Create comprehensive SLO monitoring dashboard
- [ ] Document system behavior and plan Sprint 4

## Technical Specifications

### Algorithm 1 Implementation (From Thesis)

```python
async def algorithm_1_routing_controller():
    """
    Implementation of Algorithm 1 from thesis
    Variables: reroute_traffic, violation_timer, compliance_timer
    """
    # Initialize variables (lines 1-4)
    reroute_traffic = False
    violation_timer = 0
    compliance_timer = 0

    # Main loop (line 5: repeat)
    while True:
        # Line 6: Get tail latency and CPU usage
        tail_latency = await get_tail_latency()
        cpu_usage = await get_cpu_usage()

        # Lines 8-14: Check SLO violation
        if tail_latency > SLO_THRESHOLD:
            violation_timer += 1
            compliance_timer = 0
        else:
            compliance_timer += 1
            violation_timer = 0

        # Lines 15-21: Make routing decisions
        if violation_timer >= 5 and not reroute_traffic:
            await reroute_to_serverless()
            reroute_traffic = True
        elif compliance_timer >= 5 and reroute_traffic:
            await reroute_to_kubernetes()
            reroute_traffic = False

        # Line 22: Wait 1 second
        await asyncio.sleep(1)
```

### Tail Latency Monitoring

```python
class AdvancedLatencyMonitor:
    def __init__(self):
        self.prometheus_url = "http://localhost:9090"
        self.latency_history = []

    async def get_p99_latency(self) -> float:
        """Get 99th percentile latency from Prometheus"""
        query = 'histogram_quantile(0.99, http_request_duration_seconds_bucket)'

        async with aiohttp.ClientSession() as session:
            params = {'query': query}
            async with session.get(f"{self.prometheus_url}/api/v1/query", params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if data['data']['result']:
                        # Convert from seconds to milliseconds
                        return float(data['data']['result'][0]['value'][1]) * 1000
        return 0.0

    def calculate_slo_compliance(self, window_minutes: int = 5) -> float:
        """Calculate SLO compliance percentage over time window"""
        recent_latencies = self.latency_history[-window_minutes*60:]  # Last N minutes
        if not recent_latencies:
            return 100.0

        compliant_measurements = sum(1 for lat in recent_latencies if lat <= 200)
        return (compliant_measurements / len(recent_latencies)) * 100
```

### Cost Analysis Integration

```python
class RealTimeCostAnalyzer:
    def __init__(self):
        self.k3s_node_cost_hour = 0.095  # Google Cloud e2-standard-2
        self.serverless_cost_per_100ms = 0.0000004  # Cloud Functions
        self.cost_history = []

    async def calculate_current_cost(self) -> Dict[str, float]:
        """Calculate real-time cost breakdown"""
        # Get current resource usage
        k3s_nodes = await self.get_k3s_node_count()
        serverless_invocations = await self.get_serverless_request_count()
        avg_serverless_duration = await self.get_avg_serverless_duration()

        # Calculate costs
        k3s_cost_per_hour = k3s_nodes * self.k3s_node_cost_hour
        serverless_cost_per_hour = (serverless_invocations * avg_serverless_duration / 100) * self.serverless_cost_per_100ms

        total_cost_per_hour = k3s_cost_per_hour + serverless_cost_per_hour

        return {
            'k3s_cost_per_hour': k3s_cost_per_hour,
            'serverless_cost_per_hour': serverless_cost_per_hour,
            'total_cost_per_hour': total_cost_per_hour,
            'cost_per_request': total_cost_per_hour / await self.get_total_rps() if await self.get_total_rps() > 0 else 0
        }
```

## Resource Configuration for Sprint 3

### Full Environment (16GB+ RAM)

**Complete Monitoring Stack:**
```yaml
# docker-compose-sprint3.yml
version: '3.8'
services:
  prometheus:
    mem_limit: 2g
    cpus: 0.5
    scrape_interval: 15s
    
  influxdb:
    mem_limit: 2g
    cpus: 0.5
    retention: 7d
    
  grafana:
    mem_limit: 1g
    cpus: 0.25
    
  slo-monitor:
    mem_limit: 1g
    cpus: 0.5
    
  # Total: ~6GB + k3s (2GB) = 8GB
```

### Resource-Constrained Environment (8GB RAM)

**Minimal Monitoring Stack:**
```yaml
# docker-compose-sprint3-constrained.yml
version: '3.8'
services:
  prometheus:
    mem_limit: 1g        # Reduced from 2g
    cpus: 0.25           # Reduced from 0.5
    scrape_interval: 30s # Reduced frequency
    retention: 1h        # Shorter retention
    
  influxdb:
    mem_limit: 1g        # Reduced from 2g
    cpus: 0.25           # Reduced from 0.5
    retention: 12h       # Shorter retention
    
  slo-monitor:
    mem_limit: 512m      # Reduced from 1g
    cpus: 0.25           # Reduced from 0.5
    
  # Skip Grafana in constrained mode, use CLI monitoring
  # Total: ~2.5GB + k3s (2GB) = 4.5GB
```

### SLO Monitoring Configuration

**Full Environment:**
```python
# config.py
SLO_CONFIG = {
    'latency_threshold_ms': 200,
    'violation_window_seconds': 5,
    'compliance_window_seconds': 5,
    'monitoring_interval_seconds': 1,
    'histogram_buckets': 100,
    'data_retention_hours': 24
}
```

**Resource-Constrained Environment:**
```python
# config-constrained.py
SLO_CONFIG = {
    'latency_threshold_ms': 200,
    'violation_window_seconds': 5,
    'compliance_window_seconds': 5,
    'monitoring_interval_seconds': 2,    # Reduced frequency
    'histogram_buckets': 50,             # Fewer buckets
    'data_retention_hours': 6            # Shorter retention
}
```

## Metrics to Track

### SLO Metrics

- **99th Percentile Latency**: Current and historical p99 response times
- **SLO Compliance**: Percentage of time within 200ms threshold
- **Violation Frequency**: How often SLO violations occur
- **Recovery Time**: Time to return to SLO compliance

### Algorithm 1 Metrics

- **State Transitions**: Frequency of routing mode changes
- **Timer Accuracy**: Validation of 5-second thresholds
- **Decision Latency**: Time from violation to routing change
- **False Positives**: Unnecessary routing changes

### Cost Metrics

- **Real-time Cost**: Current spending rate per hour
- **Cost Efficiency**: Cost per request served
- **Routing Cost Impact**: Cost difference between routing modes
- **Optimization Opportunities**: Potential cost savings

## Expected Results

### SLO Performance (Full Resources)

- **Normal Load**: >99% compliance with 200ms p99 latency
- **During Spikes**: <30 seconds to detect and respond to violations
- **Recovery**: <60 seconds to return to compliant state
- **Stability**: No oscillation between routing modes

### SLO Performance (Resource-Constrained 8GB)

- **Normal Load**: >97% compliance with 200ms p99 latency
- **During Spikes**: <45 seconds to detect and respond to violations
- **Recovery**: <90 seconds to return to compliant state
- **Stability**: Minimal oscillation due to reduced monitoring frequency
- **Monitoring Impact**: 2-second intervals vs 1-second, affecting response time

### Algorithm 1 Validation (Both Configurations)

- **Violation Detection**: Accurate 5-second violation window
- **Routing Response**: Consistent with thesis specification
- **State Management**: Proper reroute_traffic flag handling
- **Timer Behavior**: Correct violation_timer and compliance_timer logic

### Resource Impact Analysis

**Full Environment:**
- **Monitoring Overhead**: <5% CPU, 6GB RAM for complete observability
- **Response Latency**: Real-time SLO detection and response
- **Data Quality**: High-resolution metrics with 24h retention

**Constrained Environment:**
- **Monitoring Overhead**: <10% CPU, 2.5GB RAM for essential monitoring
- **Response Latency**: Near real-time with acceptable 1-2 second delay
- **Data Quality**: Reduced resolution but sufficient for SLO compliance

## Testing Scenarios

### Scenario 1: SLO Violation Response

```
Setup: Inject 400ms latency into k3s backend
Expected: Detection within 5 seconds, reroute to serverless
Measure: Detection time, routing response, recovery time
```

### Scenario 2: False Positive Handling

```
Setup: Brief 1-second latency spike (not sustained)
Expected: No routing change (must sustain 5 seconds)
Measure: Timer behavior, routing stability
```

### Scenario 3: Cost Optimization Validation

```
Setup: Various traffic patterns and routing modes
Expected: Accurate cost calculation and reporting
Measure: Cost accuracy, optimization recommendations
```

## Risk Mitigation

### SLO Monitoring Issues

- **Prometheus Availability**: Fallback to basic metrics if Prometheus fails
- **Metric Accuracy**: Validate latency measurements against external monitoring
- **Clock Synchronization**: Ensure accurate timing for violation windows

### Algorithm 1 Issues

- **State Corruption**: Implement state validation and recovery
- **Timer Drift**: Use precise timing mechanisms
- **Routing Loops**: Add circuit breakers for routing decisions

## Success Validation

### SLO Compliance Tests

```bash
# Test SLO monitoring accuracy
python test_slo_monitoring.py --duration 60 --inject_latency 300ms

# Validate Algorithm 1 behavior
python test_algorithm1.py --scenario violation_response

# Test cost calculation accuracy
python test_cost_analysis.py --routing_modes all
```

### Integration Tests

```bash
# End-to-end SLO violation response
./test_slo_e2e.sh --violation_duration 10s --expected_response 5s

# Cost optimization validation
./test_cost_optimization.sh --duration 30m --patterns varied
```

## Deliverables

### Code Components

- [ ] 99th percentile tail latency monitoring system
- [ ] 5-second SLO violation detection engine
- [ ] Complete Algorithm 1 routing controller implementation
- [ ] Real-time cost calculation and analysis system
- [ ] SLO-aware traffic routing integration

### Documentation

- [ ] SLO monitoring architecture and configuration
- [ ] Algorithm 1 implementation validation against thesis
- [ ] Cost analysis methodology and accuracy validation
- [ ] SLO compliance reporting and dashboard guide
- [ ] Troubleshooting guide for SLO-related issues

### Demonstration

- [ ] Real-time SLO monitoring dashboard
- [ ] Algorithm 1 routing decision demonstration
- [ ] SLO violation detection and response scenarios
- [ ] Cost analysis and optimization recommendations
- [ ] Performance comparison with Sprint 2 approach

## Sprint Review Questions

1. **Does Algorithm 1 behave exactly as specified in thesis?**
2. **Is SLO violation detection accurate and timely?**
3. **Are cost calculations accurate and useful for optimization?**
4. **How does SLO-based routing compare to RPS-based routing?**
5. **What edge cases need attention in Sprint 4?**
6. **Is the system ready for GRU model integration?**

## Next Sprint Preview

Sprint 4 will focus on replacing simple prediction with sophisticated ML:

- **GRU Model Training**: Implement 30-second prediction horizon
- **Real Dataset Integration**: Use ClarkNet and Calgary HTTP traces
- **Advanced Prediction**: Replace linear regression with GRU
- **Model Evaluation**: Implement RMSE accuracy measurement

The SLO-aware foundation built in Sprint 3 provides the monitoring infrastructure needed for validating GRU predictions in Sprint 4.
