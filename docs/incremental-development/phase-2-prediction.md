# Sprint 2: Basic Load Prediction

## Goal
Replace manual traffic routing with automated decisions based on simple load prediction.

## Duration
**1 Week** (5 working days)

## Prerequisites
- Completed Sprint 1: Basic hybrid foundation working
- Stable HAProxy routing between k3s and serverless
- Monitoring system collecting basic metrics

## Success Criteria
- ✅ System automatically adjusts traffic weights based on load prediction
- ✅ Prediction accuracy >70% for simple traffic patterns
- ✅ No manual intervention needed for basic load scenarios  
- ✅ Response time improves during traffic spikes vs manual approach
- ✅ Historical data collection and trend analysis functional

## Scope & Approach

### What We're Adding
- **Simple Linear Regression** for load prediction (not GRU yet)
- **Automated Traffic Weight Adjustment** based on predictions
- **Historical Data Storage** for trend analysis
- **Threshold-Based Decision Making** for routing
- **Basic Prediction Accuracy Measurement**

### What We're NOT Doing Yet
- ❌ Complex machine learning models (GRU comes in Sprint 4)
- ❌ Real dataset integration (ClarkNet/Calgary)
- ❌ SLO-based routing (comes in Sprint 3)
- ❌ Formal resource allocation models

## Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Historical    │    │ Load Predictor  │    │ Traffic Router  │
│   Data Store    │───►│ (Linear Reg)    │───►│   Controller    │
│   (InfluxDB)    │    │                 │    │   (Python)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         ▲                       │                       │
         │                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Monitoring    │    │ Decision Logic  │    │   HAProxy       │
│  (Prometheus)   │    │ (Thresholds)    │    │ (Auto Weights)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Components to Build

### 1. Load Predictor (Python)
**Purpose**: Predict next 5 minutes of traffic based on historical patterns
```python
class SimpleLoadPredictor:
    def __init__(self):
        self.model = LinearRegression()
        self.window_size = 60  # 60 data points (minutes)
        
    def predict_load(self, historical_rps: List[float]) -> float:
        # Simple linear regression on recent trend
        # Returns predicted RPS for next 5 minutes
```

### 2. Traffic Controller (Python)
**Purpose**: Automatically adjust HAProxy weights based on predictions
```python  
class TrafficController:
    def __init__(self):
        self.k3s_capacity = 200  # RPS
        self.serverless_threshold = 150  # RPS
        
    def calculate_weights(self, predicted_load: float) -> Tuple[int, int]:
        # Return (k3s_weight, serverless_weight)
```

### 3. Historical Data Store (InfluxDB)
**Purpose**: Store time-series data for prediction model training
- Request rate (RPS) over time
- Response times per backend
- CPU/memory usage patterns
- Prediction accuracy metrics

### 4. Automated Decision Loop
**Purpose**: Continuous monitoring and adjustment cycle
```
Every 30 seconds:
1. Collect current metrics
2. Update historical data store  
3. Generate load prediction
4. Calculate optimal traffic weights
5. Update HAProxy configuration
6. Log decision and accuracy
```

## Implementation Plan

### Day 1: Data Collection Infrastructure
**Morning**:
- [ ] Setup InfluxDB for time-series data storage
- [ ] Implement metrics collection pipeline
- [ ] Create historical data ingestion from Prometheus

**Afternoon**:
- [ ] Build data retention and cleanup policies
- [ ] Test data collection under various load patterns
- [ ] Verify data quality and completeness

### Day 2: Simple Prediction Model
**Morning**:
- [ ] Implement linear regression predictor
- [ ] Create training data pipeline from historical metrics
- [ ] Test prediction accuracy with synthetic data

**Afternoon**:
- [ ] Add prediction horizon configuration (5-minute default)
- [ ] Implement prediction confidence scoring
- [ ] Create prediction accuracy measurement framework

### Day 3: Automated Traffic Controller
**Morning**:
- [ ] Build traffic weight calculation logic
- [ ] Implement HAProxy configuration API integration
- [ ] Add safety limits and bounds checking

**Afternoon**:
- [ ] Create decision logging and audit trail
- [ ] Implement rollback mechanisms for bad decisions
- [ ] Test controller with various prediction scenarios

### Day 4: Integration & Testing
**Morning**:
- [ ] Integrate predictor with traffic controller
- [ ] Implement automated decision loop
- [ ] Test end-to-end automation under steady load

**Afternoon**:
- [ ] Test system response to traffic spikes
- [ ] Validate prediction accuracy against actual load
- [ ] Tune thresholds and parameters

### Day 5: Validation & Documentation
**Morning**:
- [ ] Run comprehensive automated testing scenarios
- [ ] Compare automated vs manual routing performance
- [ ] Measure prediction accuracy over extended periods

**Afternoon**:
- [ ] Document automated system behavior
- [ ] Create troubleshooting guides
- [ ] Plan Sprint 3 based on learnings

## Technical Specifications

### Prediction Model
```python
from sklearn.linear_model import LinearRegression
import numpy as np

class LoadPredictor:
    def __init__(self, window_minutes=60):
        self.model = LinearRegression()
        self.window_size = window_minutes
        self.last_training = None
        
    def train_model(self, timestamps, rps_values):
        # Prepare features: time-based and trend features
        X = self._prepare_features(timestamps, rps_values)
        y = rps_values[self.window_size:]
        
        self.model.fit(X, y)
        self.last_training = time.time()
        
    def predict_next_period(self, recent_data):
        # Predict next 5-minute average RPS
        features = self._prepare_features_single(recent_data)
        prediction = self.model.predict([features])[0]
        return max(0, prediction)  # No negative predictions
```

### Traffic Weight Calculation
```python
def calculate_optimal_weights(predicted_rps: float, k3s_capacity: float) -> Tuple[int, int]:
    """
    Calculate traffic weights based on predicted load and k3s capacity
    
    Logic:
    - If predicted_rps <= k3s_capacity: 90% k3s, 10% serverless
    - If predicted_rps > k3s_capacity: Scale serverless proportionally
    """
    if predicted_rps <= k3s_capacity:
        return 90, 10
    
    overflow = predicted_rps - k3s_capacity
    total_overflow_capacity = predicted_rps
    
    k3s_percentage = int((k3s_capacity / total_overflow_capacity) * 100)
    serverless_percentage = 100 - k3s_percentage
    
    # Ensure minimum 10% to each backend for health checks
    k3s_percentage = max(10, min(90, k3s_percentage))
    serverless_percentage = 100 - k3s_percentage
    
    return k3s_percentage, serverless_percentage
```

### Automated Decision Loop
```python
async def automated_routing_loop():
    """Main automation loop - runs every 30 seconds"""
    
    while True:
        try:
            # 1. Collect current metrics
            current_rps = await get_current_rps()
            current_metrics = await collect_system_metrics()
            
            # 2. Update historical data
            await store_metrics(current_metrics)
            
            # 3. Generate prediction (if enough data)
            historical_data = await get_historical_data(window_minutes=60)
            if len(historical_data) >= 60:
                predicted_rps = predictor.predict_next_period(historical_data)
                
                # 4. Calculate optimal weights
                k3s_weight, serverless_weight = calculate_optimal_weights(
                    predicted_rps, K3S_CAPACITY
                )
                
                # 5. Update HAProxy configuration
                await update_haproxy_weights(k3s_weight, serverless_weight)
                
                # 6. Log decision
                log_routing_decision(predicted_rps, k3s_weight, serverless_weight)
            
            await asyncio.sleep(30)  # Wait 30 seconds
            
        except Exception as e:
            logging.error(f"Error in routing loop: {e}")
            await asyncio.sleep(10)  # Brief pause before retry
```

## Metrics to Track

### Prediction Accuracy
- **Mean Absolute Error (MAE)**: Average prediction error
- **Mean Absolute Percentage Error (MAPE)**: Relative accuracy
- **R² Score**: How well model explains variance
- **Prediction Confidence**: Model certainty scores

### Automation Performance
- **Decision Frequency**: How often weights change
- **Response Time Improvement**: Automated vs manual routing
- **Stability**: System oscillation and convergence
- **Override Frequency**: Manual interventions needed

### System Behavior
- **Weight Distribution**: Time spent in different routing modes
- **Transition Smoothness**: Weight change gradients
- **Error Recovery**: Response to prediction failures
- **Capacity Utilization**: How well we use available resources

## Expected Results

### Prediction Performance
- **Simple Patterns**: >80% accuracy for steady/gradual changes
- **Spike Detection**: 60-70% accuracy for traffic spikes
- **Trend Following**: Good performance on sustained increases/decreases
- **Noise Handling**: Reasonable performance despite metric noise

### Routing Performance
- **Automated Response**: <1 minute to adjust to load changes
- **Stability**: No oscillation or hunting behavior
- **Performance**: 10-20% better response times vs manual routing
- **Availability**: >99% uptime with automated decisions

## Testing Scenarios

### Scenario 1: Gradual Load Increase
```
Load Pattern: 50 → 100 → 150 → 200 RPS over 30 minutes
Expected: Smooth weight transitions, good prediction accuracy
Measure: Response time, prediction error, weight stability
```

### Scenario 2: Traffic Spike
```
Load Pattern: 80 RPS → 300 RPS spike for 5 minutes → 80 RPS  
Expected: Quick detection and response, graceful return
Measure: Spike detection time, serverless activation speed
```

### Scenario 3: Noisy Traffic
```
Load Pattern: Random variations between 50-150 RPS
Expected: Stable routing despite noise, no over-reaction
Measure: Weight change frequency, prediction stability
```

## Risk Mitigation

### Prediction Failures
- **Fallback**: Default to conservative 70/30 k3s/serverless split
- **Monitoring**: Alert on consistent prediction errors
- **Manual Override**: Easy way to disable automation

### Automation Issues
- **Circuit Breaker**: Stop automation if error rate too high
- **Rate Limiting**: Limit frequency of weight changes
- **Bounds Checking**: Ensure weights stay within safe ranges

### Data Quality Issues
- **Validation**: Check metrics for completeness and sanity
- **Interpolation**: Handle missing data points gracefully
- **Cleanup**: Remove outliers that could skew predictions

## Success Validation

### Functional Tests
```bash
# Test prediction accuracy
python test_predictor.py --scenario gradual_increase

# Test automated routing
python test_automation.py --duration 60 --load_pattern spike

# Test system stability
python test_stability.py --duration 180 --noise_level medium
```

### Performance Comparison
```bash
# Compare automated vs manual routing
./run_comparison_test.sh --duration 30 --patterns "steady,spike,gradual"

# Measure prediction accuracy over time
python measure_accuracy.py --window_hours 24
```

## Deliverables

### Code Components
- [ ] Simple load predictor with linear regression
- [ ] Automated traffic controller with HAProxy integration
- [ ] Historical data storage and retrieval system
- [ ] Prediction accuracy measurement framework
- [ ] Automated decision loop with error handling

### Documentation
- [ ] Automation system architecture and design
- [ ] Prediction model methodology and limitations
- [ ] Configuration and tuning guide
- [ ] Troubleshooting and monitoring procedures
- [ ] Performance comparison with manual routing

### Demonstration
- [ ] Automated routing under various load patterns
- [ ] Prediction accuracy visualization and metrics
- [ ] System response to traffic spikes and gradual changes
- [ ] Error handling and recovery scenarios

## Sprint Review Questions

1. **Does the system reliably predict simple traffic patterns?**
2. **Do automated routing decisions improve response times?**
3. **Is the system stable without manual intervention?**
4. **What patterns does the predictor handle well/poorly?**
5. **How often does automation need manual override?**
6. **What should be improved for Sprint 3?**

## Next Sprint Preview

Sprint 3 will focus on adding sophistication that moves us toward thesis requirements:
- **SLO-Based Routing**: Replace RPS thresholds with tail latency monitoring
- **99th Percentile Tracking**: Implement formal SLO violation detection
- **Algorithm 1 Implementation**: Add thesis routing controller logic
- **Cost Optimization**: Formal cost modeling and optimization

The automation foundation built in Sprint 2 provides the platform for adding SLO-aware intelligence in Sprint 3.