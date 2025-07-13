# Hybrid K3s-Serverless Experiment Methodology

## Overview

This document provides the detailed implementation methodology for conducting the hybrid k3s-serverless integration experiment. It builds upon the existing zscaler foundation to create an intelligent system that combines cost-effective k3s clusters with serverless overflow capacity.

## 1. Environment Setup

### 1.1 Base Infrastructure

**Leverage Existing Components:**

- **Zscaler Foundation**: `autoscaler/experiment-7-zscaler/scaler-controller/k3d-autoscaler.py`
- **Rust Applications**: `apps/rust-app/v2-prometheus/` (with metrics)
- **Infrastructure Scripts**: `infra/setup-clusters.sh`

**New Components Required:**

```
hybrid-experiment/
├── controller/
│   ├── hybrid-router.py           # Traffic routing logic
│   ├── load-predictor.py         # Simple ML prediction
│   └── cost-tracker.py           # Cost calculation
├── serverless-sim/
│   ├── function-container/        # Dockerized serverless sim
│   └── scaling-manager.py         # Instant scaling logic
├── monitoring/
│   ├── custom-metrics.py         # Hybrid-specific metrics
│   └── dashboard/                # Grafana dashboards
└── workload/
    ├── load-generator.py         # k6 alternative
    └── test-scenarios/           # Predefined test cases
```

### 1.2 Cluster Configuration

**k3s Cluster Setup:**

```bash
# Enhanced cluster with resource limits
k3d cluster create hybrid-cluster \
  --agents 2 \
  --registry-create hybrid-registry:0.0.0.0:5000 \
  --port "8080:80@loadbalancer" \
  --port "9090:9090@loadbalancer"

# Apply aggressive resource limits (simulate VPS constraints)
./resource-limitter/limit-node-resources.sh
```

**Serverless Simulation Setup:**

```bash
# Docker-based serverless simulation
docker network create serverless-net
docker run -d --name serverless-pool \
  --network serverless-net \
  --memory="256m" \
  --cpus="0.5" \
  nginx:alpine
```

## 2. Implementation Details

### 2.1 Enhanced Autoscaler (Hybrid Scaler)

**File**: `autoscaler/hybrid-experiment/intelligent-scaler.py`

```python
#!/usr/bin/env python3

import subprocess
import time
import requests
import json
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import List, Dict, Tuple
import logging

@dataclass
class LoadMetrics:
    timestamp: datetime
    cpu_usage: float
    memory_usage: float
    rps: int
    response_time_p95: float
    active_connections: int

@dataclass
class RoutingDecision:
    k3s_percentage: int    # 0-100
    serverless_percentage: int  # 0-100
    reason: str
    estimated_cost: float

class HybridIntelligentScaler:
    def __init__(self):
        # Thresholds for decision making
        self.THRESHOLDS = {
            'k3s_comfortable': 70,     # Normal k3s operation
            'k3s_aggressive': 85,      # Push k3s to limits
            'serverless_trigger': 90,   # Activate serverless
            'scale_back': 60,          # Return to k3s only
            'prediction_weight': 0.3   # How much to trust predictions
        }

        # Cost models (simulated)
        self.COSTS = {
            'k3s_per_node_hour': 0.10,
            'serverless_per_100ms': 0.000001,
            'cold_start_penalty': 0.001
        }

        self.metrics_history: List[LoadMetrics] = []
        self.current_routing = RoutingDecision(100, 0, "startup", 0.0)

    def collect_metrics(self) -> LoadMetrics:
        """Collect comprehensive metrics from k3s cluster and application"""
        # Get kubectl metrics
        cpu_usage = self.get_average_cpu_utilization()
        memory_usage = self.get_average_memory_utilization()

        # Get application metrics from Prometheus
        app_metrics = self.get_application_metrics()

        metrics = LoadMetrics(
            timestamp=datetime.now(),
            cpu_usage=cpu_usage or 0,
            memory_usage=memory_usage or 0,
            rps=app_metrics.get('rps', 0),
            response_time_p95=app_metrics.get('p95_latency', 0),
            active_connections=app_metrics.get('connections', 0)
        )

        self.metrics_history.append(metrics)
        # Keep only last 100 metrics (sliding window)
        if len(self.metrics_history) > 100:
            self.metrics_history.pop(0)

        return metrics

    def predict_load(self, horizon_minutes: int = 5) -> float:
        """Simple load prediction based on recent trends"""
        if len(self.metrics_history) < 10:
            return self.metrics_history[-1].cpu_usage if self.metrics_history else 0

        # Simple linear trend calculation
        recent_metrics = self.metrics_history[-10:]
        x_vals = list(range(len(recent_metrics)))
        y_vals = [m.cpu_usage for m in recent_metrics]

        # Calculate simple linear regression
        n = len(recent_metrics)
        sum_x = sum(x_vals)
        sum_y = sum(y_vals)
        sum_xy = sum(x * y for x, y in zip(x_vals, y_vals))
        sum_x_squared = sum(x * x for x in x_vals)

        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x_squared - sum_x * sum_x)
        intercept = (sum_y - slope * sum_x) / n

        # Predict load at horizon
        future_x = n + (horizon_minutes * 60 / 60)  # Assuming 1-minute intervals
        predicted_load = slope * future_x + intercept

        return max(0, min(100, predicted_load))  # Clamp to 0-100%

    def make_routing_decision(self, current_metrics: LoadMetrics) -> RoutingDecision:
        """Intelligent routing decision based on current load and prediction"""
        current_load = current_metrics.cpu_usage
        predicted_load = self.predict_load()

        # Weighted decision: current load + prediction
        decision_load = (current_load * (1 - self.THRESHOLDS['prediction_weight']) +
                        predicted_load * self.THRESHOLDS['prediction_weight'])

        if decision_load < self.THRESHOLDS['k3s_comfortable']:
            # Comfortable k3s operation
            routing = RoutingDecision(100, 0, "k3s_comfortable", self.calculate_cost(100, 0))

        elif decision_load < self.THRESHOLDS['k3s_aggressive']:
            # Aggressive k3s scaling
            routing = RoutingDecision(100, 0, "k3s_aggressive_scaling", self.calculate_cost(100, 0))
            self.trigger_k3s_scale_up()

        elif decision_load < self.THRESHOLDS['serverless_trigger']:
            # Hybrid mode - start shifting to serverless
            serverless_percent = int((decision_load - self.THRESHOLDS['k3s_aggressive']) * 3)
            k3s_percent = 100 - serverless_percent
            routing = RoutingDecision(k3s_percent, serverless_percent, "hybrid_transition",
                                    self.calculate_cost(k3s_percent, serverless_percent))

        else:
            # Heavy serverless usage
            serverless_percent = min(80, int((decision_load - self.THRESHOLDS['serverless_trigger']) * 8 + 20))
            k3s_percent = 100 - serverless_percent
            routing = RoutingDecision(k3s_percent, serverless_percent, "serverless_dominant",
                                    self.calculate_cost(k3s_percent, serverless_percent))
            self.trigger_serverless_scale_up()

        # Apply routing decision
        self.apply_routing(routing)
        self.current_routing = routing

        return routing

    def calculate_cost(self, k3s_percent: int, serverless_percent: int) -> float:
        """Calculate estimated cost for routing decision"""
        # Simplified cost calculation
        current_nodes = self.get_current_node_count()
        k3s_cost = current_nodes * self.COSTS['k3s_per_node_hour']

        # Estimate serverless requests based on percentage
        estimated_requests_per_hour = 3600  # Assume base rate
        serverless_requests = (estimated_requests_per_hour * serverless_percent) / 100
        serverless_cost = serverless_requests * self.COSTS['serverless_per_100ms'] * 10  # 1 second avg

        return k3s_cost + serverless_cost

    def apply_routing(self, routing: RoutingDecision):
        """Apply the routing decision to traffic router"""
        routing_config = {
            'k3s_weight': routing.k3s_percentage,
            'serverless_weight': routing.serverless_percentage,
            'timestamp': datetime.now().isoformat(),
            'reason': routing.reason
        }

        # Write routing config for HAProxy/traffic router
        with open('/tmp/routing_config.json', 'w') as f:
            json.dump(routing_config, f)

        # Signal traffic router to reload config
        subprocess.run(['pkill', '-HUP', 'haproxy'], check=False)

        logging.info(f"Applied routing: k3s={routing.k3s_percentage}%, "
                    f"serverless={routing.serverless_percentage}% - {routing.reason}")

    def trigger_serverless_scale_up(self):
        """Trigger serverless container scaling"""
        try:
            # Start additional serverless containers
            subprocess.run([
                'docker', 'run', '-d', '--name', f'serverless-{int(time.time())}',
                '--network', 'serverless-net',
                '--memory', '256m', '--cpus', '0.5',
                'rust-app:serverless'
            ], check=True)
            logging.info("Triggered serverless scale-up")
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to scale serverless: {e}")

    def get_application_metrics(self) -> Dict:
        """Get application-specific metrics from Prometheus"""
        try:
            # Query Prometheus for application metrics
            prometheus_url = "http://localhost:9090"
            queries = {
                'rps': 'rate(http_requests_total[1m])',
                'p95_latency': 'histogram_quantile(0.95, http_request_duration_seconds_bucket)',
                'connections': 'http_active_connections'
            }

            metrics = {}
            for name, query in queries.items():
                response = requests.get(f"{prometheus_url}/api/v1/query",
                                      params={'query': query}, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    if data['data']['result']:
                        metrics[name] = float(data['data']['result'][0]['value'][1])
                    else:
                        metrics[name] = 0
                else:
                    metrics[name] = 0

            return metrics
        except Exception as e:
            logging.error(f"Failed to get application metrics: {e}")
            return {'rps': 0, 'p95_latency': 0, 'connections': 0}

    # Include existing methods from zscaler
    def get_average_cpu_utilization(self):
        # Copy from existing zscaler implementation
        pass

    def get_average_memory_utilization(self):
        # New method similar to CPU monitoring
        pass

    def get_current_node_count(self):
        # Copy from existing zscaler implementation
        pass

    def trigger_k3s_scale_up(self):
        # Copy from existing zscaler implementation
        pass

def main():
    """Main execution loop"""
    scaler = HybridIntelligentScaler()
    logging.info("Starting Hybrid Intelligent Scaler...")

    while True:
        try:
            # Collect current metrics
            current_metrics = scaler.collect_metrics()

            # Make routing decision
            routing_decision = scaler.make_routing_decision(current_metrics)

            # Log current state
            logging.info(f"Load: {current_metrics.cpu_usage:.1f}% CPU, "
                        f"{current_metrics.rps} RPS, "
                        f"Routing: k3s={routing_decision.k3s_percentage}%/"
                        f"serverless={routing_decision.serverless_percentage}%, "
                        f"Cost: ${routing_decision.estimated_cost:.4f}/hr")

            # Sleep until next check
            time.sleep(60)  # Check every minute

        except KeyboardInterrupt:
            logging.info("Scaler terminated by user")
            break
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            time.sleep(10)  # Brief pause before retrying

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                       format='%(asctime)s %(levelname)s: %(message)s')
    main()
```

### 2.2 Traffic Router Implementation

**File**: `controller/hybrid-router.py`

```python
#!/usr/bin/env python3

import json
import subprocess
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

class TrafficRouter:
    def __init__(self):
        self.current_config = {'k3s_weight': 100, 'serverless_weight': 0}
        self.stats = {'k3s_requests': 0, 'serverless_requests': 0, 'errors': 0}

    def update_haproxy_config(self, k3s_weight: int, serverless_weight: int):
        """Update HAProxy configuration with new weights"""
        haproxy_config = f"""
global
    daemon

defaults
    mode http
    timeout connect 5000ms
    timeout client 50000ms
    timeout server 50000ms

frontend main
    bind *:8080
    default_backend servers

backend servers
    balance roundrobin
    server k3s-cluster 127.0.0.1:30080 weight {k3s_weight} check
    server serverless-sim 127.0.0.1:30081 weight {serverless_weight} check
"""

        with open('/tmp/haproxy.cfg', 'w') as f:
            f.write(haproxy_config)

        # Reload HAProxy
        subprocess.run(['haproxy', '-f', '/tmp/haproxy.cfg', '-D'], check=False)

    def monitor_routing_config(self):
        """Monitor for routing configuration changes"""
        while True:
            try:
                with open('/tmp/routing_config.json', 'r') as f:
                    config = json.load(f)

                if (config['k3s_weight'] != self.current_config['k3s_weight'] or
                    config['serverless_weight'] != self.current_config['serverless_weight']):

                    self.update_haproxy_config(config['k3s_weight'], config['serverless_weight'])
                    self.current_config = config
                    print(f"Updated routing: k3s={config['k3s_weight']}%, "
                          f"serverless={config['serverless_weight']}%")

            except (FileNotFoundError, json.JSONDecodeError):
                pass

            time.sleep(5)

if __name__ == "__main__":
    router = TrafficRouter()

    # Start monitoring in background thread
    monitor_thread = threading.Thread(target=router.monitor_routing_config, daemon=True)
    monitor_thread.start()

    print("Traffic Router started...")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Traffic Router stopped")
```

## 3. Test Scenarios Implementation

### 3.1 Load Generator

**File**: `workload/intelligent-load-generator.py`

```python
#!/usr/bin/env python3

import asyncio
import aiohttp
import time
import json
from datetime import datetime
from typing import List, Dict
import argparse

class LoadPattern:
    def __init__(self, name: str, rps_over_time: List[Tuple[int, int]]):
        self.name = name
        self.rps_over_time = rps_over_time  # [(time_seconds, rps), ...]

class LoadGenerator:
    def __init__(self, target_url: str):
        self.target_url = target_url
        self.results = []

    async def send_request(self, session: aiohttp.ClientSession) -> Dict:
        """Send single HTTP request and measure response"""
        start_time = time.time()
        try:
            async with session.get(self.target_url) as response:
                end_time = time.time()
                return {
                    'timestamp': datetime.now().isoformat(),
                    'status_code': response.status,
                    'response_time': (end_time - start_time) * 1000,  # ms
                    'success': response.status == 200
                }
        except Exception as e:
            end_time = time.time()
            return {
                'timestamp': datetime.now().isoformat(),
                'status_code': 0,
                'response_time': (end_time - start_time) * 1000,
                'success': False,
                'error': str(e)
            }

    async def run_pattern(self, pattern: LoadPattern):
        """Execute a load pattern"""
        print(f"Starting load pattern: {pattern.name}")

        async with aiohttp.ClientSession() as session:
            start_time = time.time()

            for duration, target_rps in pattern.rps_over_time:
                print(f"  Running {target_rps} RPS for {duration} seconds...")

                phase_start = time.time()
                requests_sent = 0

                while time.time() - phase_start < duration:
                    # Calculate how many requests to send in this second
                    requests_this_second = target_rps
                    second_start = time.time()

                    # Send requests for this second
                    tasks = []
                    for _ in range(requests_this_second):
                        task = asyncio.create_task(self.send_request(session))
                        tasks.append(task)

                    # Wait for all requests to complete
                    results = await asyncio.gather(*tasks)
                    self.results.extend(results)
                    requests_sent += len(results)

                    # Wait until the second is complete
                    elapsed = time.time() - second_start
                    if elapsed < 1.0:
                        await asyncio.sleep(1.0 - elapsed)

                print(f"    Sent {requests_sent} requests in {duration} seconds")

        print(f"Pattern '{pattern.name}' completed")
        return self.results

# Predefined test patterns
PATTERNS = {
    'baseline': LoadPattern('Baseline', [(1800, 100)]),  # 30 min at 100 RPS
    'gradual_scale': LoadPattern('Gradual Scale', [
        (300, 100), (300, 200), (300, 300), (300, 400), (300, 500)
    ]),
    'traffic_spike': LoadPattern('Traffic Spike', [
        (300, 100), (300, 1000), (300, 100)  # Spike to 1000 RPS
    ]),
    'sustained_heavy': LoadPattern('Sustained Heavy', [
        (300, 100), (300, 800), (1200, 800), (300, 100)  # 20 min heavy load
    ]),
    'mixed_workload': LoadPattern('Mixed Workload', [
        (120, 100), (60, 500), (120, 200), (60, 1200), (120, 300),
        (60, 800), (120, 150), (60, 600), (120, 100)
    ])
}

async def main():
    parser = argparse.ArgumentParser(description='Intelligent Load Generator')
    parser.add_argument('--pattern', choices=PATTERNS.keys(), required=True,
                       help='Load pattern to execute')
    parser.add_argument('--url', default='http://localhost:8080',
                       help='Target URL')
    parser.add_argument('--output', default='load_test_results.json',
                       help='Output file for results')

    args = parser.parse_args()

    generator = LoadGenerator(args.url)
    pattern = PATTERNS[args.pattern]

    results = await generator.run_pattern(pattern)

    # Save results
    with open(args.output, 'w') as f:
        json.dump(results, f, indent=2)

    # Print summary
    successful_requests = [r for r in results if r['success']]
    if successful_requests:
        response_times = [r['response_time'] for r in successful_requests]
        print(f"\nSummary:")
        print(f"  Total requests: {len(results)}")
        print(f"  Successful: {len(successful_requests)} ({len(successful_requests)/len(results)*100:.1f}%)")
        print(f"  Average response time: {sum(response_times)/len(response_times):.2f}ms")
        print(f"  95th percentile: {sorted(response_times)[int(len(response_times)*0.95)]:.2f}ms")

if __name__ == "__main__":
    asyncio.run(main())
```

## 4. Execution Workflow

### 4.1 Setup Phase

```bash
# 1. Setup infrastructure
./infra/setup-clusters.sh

# 2. Build and deploy applications
cd apps/rust-app/v2-prometheus
cargo build --release
docker build -t rust-app:hybrid .

# 3. Start monitoring
kubectl apply -f monitoring/prometheus.yaml

# 4. Initialize hybrid scaler
cd autoscaler/hybrid-experiment
python3 intelligent-scaler.py &

# 5. Start traffic router
python3 ../controller/hybrid-router.py &
```

### 4.2 Experiment Execution

```bash
# Run each test scenario
cd workload
python3 intelligent-load-generator.py --pattern baseline
python3 intelligent-load-generator.py --pattern gradual_scale
python3 intelligent-load-generator.py --pattern traffic_spike
python3 intelligent-load-generator.py --pattern sustained_heavy
python3 intelligent-load-generator.py --pattern mixed_workload
```

### 4.3 Data Collection

```bash
# Collect metrics from Prometheus
curl -G 'http://localhost:9090/api/v1/query_range' \
  --data-urlencode 'query=rate(http_requests_total[1m])' \
  --data-urlencode 'start=2024-01-01T00:00:00Z' \
  --data-urlencode 'end=2024-01-01T01:00:00Z' \
  --data-urlencode 'step=60s' > metrics_data.json

# Collect cost and routing decisions
cat /var/log/hybrid-scaler.log | grep "Routing:" > routing_decisions.log
```

## 5. Success Metrics & Analysis

### 5.1 Performance Metrics

- **Response Time**: p50, p95, p99 latency during each scenario
- **Throughput**: Requests per second handled successfully
- **Error Rate**: Percentage of failed requests
- **Scaling Latency**: Time to react to load changes

### 5.2 Cost Analysis

- **k3s Utilization**: Percentage of k3s capacity used
- **Serverless Activation**: Frequency and duration of serverless usage
- **Cost Per Request**: Calculated cost for each routing scenario
- **Total Cost**: Overall experiment cost vs alternatives

### 5.3 Routing Intelligence

- **Decision Accuracy**: Correctness of routing decisions
- **Prediction Quality**: Accuracy of load predictions
- **Threshold Optimization**: Effectiveness of switching points

This methodology provides a comprehensive framework for conducting the hybrid k3s-serverless experiment, building on your existing zscaler foundation while adding intelligent routing and cost optimization capabilities.
