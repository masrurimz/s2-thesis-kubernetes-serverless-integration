# Thesis-Aligned Experiment Plan: ElaX-GRU Hybrid K8s-Serverless Integration

## Abstract Alignment

This experiment implements the thesis proposal: "Decision Making and Elastic Scalability Management in Heterogeneous Cloud Environments Based on Workload Prediction" using GRU-based workload prediction and resource reservation for tail latency optimization.

## 1. Methodology Implementation

### 1.1 Literature Foundation
- **Base Algorithm**: ElaX (Yang et al., 2019) with GRU modification
- **GRU Selection**: Based on Mondal et al. (2023) efficiency findings
- **Hybrid Approach**: Senjab et al. (2023) and Mampage et al. (2022) integration patterns

### 1.2 Dataset Integration

**Primary Dataset**: ClarkNet and Calgary HTTP Trace Data
```
Total Requests: 4,055,326 HTTP requests
Format: Combined Common Log Format (CLF)
Structure:
- host: requesting host (name or IP)
- timestamp: [DD/MON/YYYY:HH:MM:SS timezone]
- request: "METHOD URL HTTP/version"
- status: HTTP response code
- bytes: response size in bytes
```

**Data Processing Pipeline**:
```
Raw HTTP Logs → RPS Transformation → GRU Training Data → Prediction Model
```

## 2. System Architecture (ElaX-Based)

### 2.1 Core Components

```
┌─────────────────────────────────────────────────────────────────┐
│                    ElaX-GRU Hybrid System                      │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌──────────────────┐    ┌─────────────┐ │
│  │   GRU Workload  │    │ Resource         │    │ Online      │ │
│  │   Predictor     │───►│ Allocator        │───►│ Controller  │ │
│  │ (30s horizon)   │    │ R = α·x + β      │    │ (Error      │ │
│  │                 │    │ (OLS tuning)     │    │  Correction)│ │
│  └─────────────────┘    └──────────────────┘    └─────────────┘ │
│           │                       │                      │      │
│           ▼                       ▼                      ▼      │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │              Traffic Distribution Engine                    │ │
│  └─────────────────────────────────────────────────────────────┘ │
│           │                                              │      │
│           ▼                                              ▼      │
│  ┌─────────────────┐                           ┌─────────────────┐ │
│  │ Routing         │                           │ Cluster         │ │
│  │ Controller      │                           │ Controller      │ │
│  │ (SLO Monitor)   │                           │ (K8s Scaling)   │ │
│  └─────────────────┘                           └─────────────────┘ │
│           │                                              │      │
│           ▼                                              ▼      │
│  ┌─────────────────┐                           ┌─────────────────┐ │
│  │ Serverless      │                           │ Kubernetes      │ │
│  │ Functions       │                           │ Cluster         │ │
│  │ (Overflow)      │                           │ (Base Load)     │ │
│  └─────────────────┘                           └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Component Specifications

**GRU Workload Predictor**:
- **Model**: Multi-point prediction (30 seconds ahead)
- **Input**: Historical RPS data from HTTP traces
- **Architecture**: GRU layers with dropout for efficiency
- **Training**: ClarkNet/Calgary dataset transformation

**Resource Allocator**:
- **Model**: Linear equation R = α·x + β
- **Tuning**: OLS (Ordinary Least Squares) using scikit-learn
- **Input**: Predicted load (x), historical CPU/memory usage
- **Output**: Required CPU/memory resources (R)

**Online Controller**:
- **Function**: Error correction and coefficient adjustment
- **Feedback**: Real-time SLO violations and resource utilization
- **Update**: Dynamic α, β coefficient refinement

## 3. Controller Implementation

### 3.1 Routing Controller (Algorithm 1 from Thesis)

```python
#!/usr/bin/env python3

import time
import logging
from dataclasses import dataclass
from typing import Dict, List

@dataclass
class SLOMetrics:
    tail_latency_p99: float
    cpu_usage: float
    timestamp: float
    violation_count: int

class RoutingController:
    def __init__(self, slo_threshold_ms: float = 200.0):
        self.slo_threshold = slo_threshold_ms
        self.reroute_traffic = False
        self.violation_timer = 0
        self.compliance_timer = 0
        self.metrics_history: List[SLOMetrics] = []
        
    def get_tail_latency(self) -> float:
        """Get 99th percentile latency from Prometheus"""
        # Query: histogram_quantile(0.99, http_request_duration_seconds_bucket)
        pass
        
    def get_cpu_usage(self) -> float:
        """Get current CPU usage from cluster"""
        pass
        
    def reroute_to_serverless(self):
        """Redirect traffic to serverless functions"""
        logging.info("SLO violation detected. Rerouting to serverless.")
        self.update_traffic_weights(k8s_weight=20, serverless_weight=80)
        
    def reroute_to_kubernetes(self):
        """Return traffic to Kubernetes cluster"""
        logging.info("SLO compliance restored. Returning to Kubernetes.")
        self.update_traffic_weights(k8s_weight=80, serverless_weight=20)
        
    def update_traffic_weights(self, k8s_weight: int, serverless_weight: int):
        """Update HAProxy weights for traffic distribution"""
        pass
        
    def run_routing_loop(self):
        """Main routing control loop (Algorithm 1 from thesis)"""
        while True:
            # Step 6: Get current metrics
            tail_latency = self.get_tail_latency()
            cpu_usage = self.get_cpu_usage()
            
            # Step 7-14: Check SLO violation
            if tail_latency > self.slo_threshold:
                self.violation_timer += 1
                self.compliance_timer = 0
            else:
                self.compliance_timer += 1
                self.violation_timer = 0
                
            # Step 15-21: Make routing decisions
            if self.violation_timer >= 5 and not self.reroute_traffic:
                self.reroute_to_serverless()
                self.reroute_traffic = True
            elif self.compliance_timer >= 5 and self.reroute_traffic:
                self.reroute_to_kubernetes()
                self.reroute_traffic = False
                
            # Log metrics
            metrics = SLOMetrics(
                tail_latency_p99=tail_latency,
                cpu_usage=cpu_usage,
                timestamp=time.time(),
                violation_count=self.violation_timer
            )
            self.metrics_history.append(metrics)
            
            # Step 22: Wait 1 second
            time.sleep(1)
```

### 3.2 Cluster Controller

```python
import numpy as np
from sklearn.linear_model import LinearRegression
from typing import Tuple

class ClusterController:
    def __init__(self):
        self.alpha = 0.1  # Initial coefficient
        self.beta = 0.05  # Initial coefficient  
        self.ols_model = LinearRegression()
        self.resource_history = []
        
    def tune_coefficients(self, rps_history: List[float], 
                         cpu_history: List[float]) -> Tuple[float, float]:
        """Tune α and β coefficients using OLS"""
        if len(rps_history) < 10:
            return self.alpha, self.beta
            
        X = np.array(rps_history).reshape(-1, 1)
        y = np.array(cpu_history)
        
        self.ols_model.fit(X, y)
        
        self.alpha = self.ols_model.coef_[0]
        self.beta = self.ols_model.intercept_
        
        logging.info(f"Updated coefficients: α={self.alpha:.4f}, β={self.beta:.4f}")
        return self.alpha, self.beta
        
    def calculate_resource_requirement(self, predicted_rps: float) -> float:
        """Calculate required resources using R = α·x + β"""
        required_cpu = self.alpha * predicted_rps + self.beta
        return max(0.1, required_cpu)  # Minimum 0.1 CPU cores
        
    def scale_cluster(self, required_cpu: float):
        """Scale Kubernetes cluster to meet resource requirements"""
        current_nodes = self.get_current_node_count()
        required_nodes = int(np.ceil(required_cpu / 2.0))  # 2 CPU per node
        
        if required_nodes > current_nodes:
            self.scale_up_cluster(required_nodes - current_nodes)
        elif required_nodes < current_nodes and current_nodes > 1:
            self.scale_down_cluster(current_nodes - required_nodes)
```

### 3.3 GRU Workload Predictor

```python
import torch
import torch.nn as nn
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class GRUWorkloadPredictor(nn.Module):
    def __init__(self, input_size=1, hidden_size=64, num_layers=2, 
                 output_size=30, dropout=0.2):
        super(GRUWorkloadPredictor, self).__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.output_size = output_size
        
        self.gru = nn.GRU(input_size, hidden_size, num_layers, 
                         batch_first=True, dropout=dropout)
        self.fc = nn.Linear(hidden_size, output_size)
        self.dropout = nn.Dropout(dropout)
        
    def forward(self, x):
        # Initialize hidden state
        h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size)
        
        # Forward propagate GRU
        out, _ = self.gru(x, h0)
        
        # Apply dropout and final layer
        out = self.dropout(out[:, -1, :])  # Use last time step
        out = self.fc(out)
        
        return out
        
class DatasetProcessor:
    def __init__(self):
        self.rps_data = []
        
    def process_clarknet_data(self, file_path: str) -> pd.DataFrame:
        """Process ClarkNet HTTP trace data to RPS format"""
        requests = []
        
        with open(file_path, 'r') as f:
            for line in f:
                try:
                    # Parse CLF format
                    parts = line.strip().split(' ')
                    timestamp_str = ' '.join(parts[3:5]).strip('[]')
                    timestamp = datetime.strptime(timestamp_str, 
                                                '%d/%b/%Y:%H:%M:%S %z')
                    requests.append(timestamp)
                except:
                    continue
                    
        # Convert to RPS data
        df = pd.DataFrame({'timestamp': requests})
        df['second'] = df['timestamp'].dt.floor('S')
        rps_data = df.groupby('second').size().reset_index(name='rps')
        
        return rps_data
        
    def create_sequences(self, data: np.ndarray, seq_length: int = 60) -> Tuple:
        """Create sequences for GRU training"""
        X, y = [], []
        for i in range(len(data) - seq_length - 30):
            X.append(data[i:(i + seq_length)])
            y.append(data[(i + seq_length):(i + seq_length + 30)])
        return np.array(X), np.array(y)
```

## 4. Evaluation Methodology (Thesis-Aligned)

### 4.1 Traffic Predictor Evaluation

**Metric**: Root Mean Square Error (RMSE)
```python
def evaluate_prediction_accuracy(actual: np.ndarray, predicted: np.ndarray) -> float:
    """Calculate RMSE for prediction accuracy"""
    rmse = np.sqrt(np.mean((actual - predicted) ** 2))
    return rmse
```

**Dataset Split**:
- Training: 70% of ClarkNet/Calgary data
- Validation: 15% for hyperparameter tuning
- Test: 15% for final evaluation

### 4.2 Router and Scaling Evaluation

**Primary Metrics** (as specified in thesis):

1. **Request Running Time**: End-to-end request processing time
2. **Tail Latency**: 99th percentile response time
3. **CPU/RAM Allocation**: Resource allocation per cluster
4. **CPU Utilization**: Actual CPU usage percentage
5. **Request Distribution**: Traffic split between K8s/serverless
6. **Request Count**: Total processed requests
7. **Cost Estimation**: Based on Google Cloud pricing

**Control Variables**:
- **Deployment Method**: Full serverless vs Full Kubernetes vs Hybrid
- **Scaling Method**: Cluster autoscaler vs ElaX vs Proposed method

> **⚠️ SUPERSEDED:** This CostCalculator prototype was replaced by `scripts/cost_analyzer.py` which uses three billing models (Lambda Provisioned Concurrency, Cloud Run Always-Allocated, EC2 Node-Hours) with actual measured experiment data. See `results/cost/2026-02-17_three-model-cost-comparison/report.md` for the final cost analysis.

### 4.3 Cost Calculation

```python
class CostCalculator:
    def __init__(self):
        # Google Cloud pricing (as specified in thesis)
        self.k8s_node_cost_per_hour = 0.095  # e2-standard-2
        self.serverless_cost_per_100ms = 0.0000004  # Cloud Functions
        self.memory_cost_per_gb_hour = 0.0125
        
    def calculate_hybrid_cost(self, k8s_hours: float, serverless_invocations: int,
                            avg_duration_ms: float, memory_gb: float) -> float:
        """Calculate total cost for hybrid deployment"""
        k8s_cost = k8s_hours * self.k8s_node_cost_per_hour
        serverless_cost = (serverless_invocations * avg_duration_ms / 100) * self.serverless_cost_per_100ms
        memory_cost = memory_gb * k8s_hours * self.memory_cost_per_gb_hour
        
        return k8s_cost + serverless_cost + memory_cost
```

## 5. Updated Experiment Scenarios

### 5.1 Real-World Trace Replay
- **Dataset**: ClarkNet trace patterns
- **Duration**: 24-hour replay with time compression
- **Pattern**: Realistic diurnal traffic variations

### 5.2 SLO Violation Scenarios  
- **Normal Load**: Maintain 99th percentile <200ms
- **Spike Response**: Handle 10x traffic increase
- **Sustained High**: Extended high-load periods

### 5.3 Comparative Analysis
- **Baseline 1**: Pure Kubernetes with cluster autoscaler
- **Baseline 2**: Pure serverless deployment
- **Baseline 3**: ElaX algorithm (original)
- **Proposed**: ElaX-GRU hybrid system

## 6. Implementation Phases (Updated)

### Phase 1: Foundation & Dataset (Week 1)
- [ ] Download and process ClarkNet/Calgary datasets
- [ ] Implement dataset preprocessing pipeline
- [ ] Setup GRU training environment
- [ ] Basic ElaX architecture implementation

### Phase 2: Core Algorithm Implementation (Week 2)
- [ ] GRU workload predictor training
- [ ] Resource allocation model (R = α·x + β)
- [ ] OLS coefficient tuning system
- [ ] Separated controller architecture

### Phase 3: SLO-Focused Integration (Week 3)
- [ ] Tail latency monitoring system
- [ ] Routing controller with 5-second SLO detection
- [ ] Cluster controller with real-time scaling
- [ ] Cost calculation integration

### Phase 4: Formal Evaluation (Week 4)
- [ ] RMSE evaluation for GRU predictor
- [ ] Comparative analysis with control variables
- [ ] Statistical significance testing
- [ ] Thesis-aligned result documentation

## 7. Expected Thesis Contributions

1. **Novel GRU Integration**: First implementation of GRU-based ElaX modification
2. **SLO-Aware Routing**: Tail latency-focused hybrid traffic management
3. **Real Dataset Validation**: ClarkNet/Calgary trace-based evaluation
4. **Formal Resource Modeling**: OLS-tuned linear resource allocation
5. **Comprehensive Comparison**: Multi-method comparative analysis

This updated plan aligns directly with your thesis methodology and evaluation requirements, ensuring your implementation matches your formal research proposal.