# Technical Design Document: Intelligent Routing Architecture

**Sprint**: 2 - Intelligent Routing with Load Prediction  
**Version**: 2.0  
**Date**: July 2025  
**Author**: LLM-Assisted Development Team

## Architecture Overview

Sprint 2 enhances Sprint 1's proven hybrid foundation with intelligent routing capabilities using linear regression for load prediction and automated traffic weight adjustment. The design maintains Sprint 1's exceptional performance while adding predictive intelligence.

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                           Sprint 2 Architecture                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐  │
│  │ Prediction      │    │ Intelligent     │    │   K3s Cluster   │  │
│  │ Engine          │───►│ Router          │───►│   (nginx app)   │  │
│  │ (FastAPI +      │    │ (Weight Mgmt)   │    │   Port: 8080    │  │
│  │ scikit-learn)   │    │                 │    └─────────────────┘  │
│  └─────────────────┘    │                 │           │            │
│          ▲               │                 │    ┌─────────────────┐  │
│          │               │                 │───►│ Knative Service │  │
│     Historical Data      │                 │    │ (Serverless)    │  │
│          │               └─────────────────┘    │ Port: 8081      │  │
│  ┌─────────────────┐                           └─────────────────┘  │
│  │ Enhanced        │                                  │            │
│  │ Monitoring      │◄─────────────────────────────────┘            │
│  │ (Prometheus +   │                                                │
│  │ Grafana +       │                                                │
│  │ Custom Metrics) │                                                │
│  └─────────────────┘                                                │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Design Principles

1. **Non-Breaking Enhancement**: Sprint 1 foundation remains unchanged
2. **Graceful Degradation**: Fallback to manual routing when intelligence fails
3. **Performance First**: Maintain Sprint 1's exceptional performance baseline
4. **Resource Efficiency**: Operate within Sprint 1's available resource headroom
5. **Observability**: Comprehensive monitoring of intelligent routing decisions

## Component Architecture

### 1. Prediction Engine

**Technology Stack**: Python 3.9 + FastAPI + scikit-learn + Poetry

#### 1.1 Data Collector
```python
class DataCollector:
    - collect_current_stats() -> Dict
    - store_stats(stats: Dict) -> bool
    - get_historical_data(hours: int) -> pd.DataFrame
    - continuous_collection() -> None
```

**Responsibilities**:
- Parse HAProxy CSV stats every 30 seconds
- Store historical traffic patterns in SQLite database
- Provide historical data for model training
- Generate synthetic data for initial training

**Data Schema**:
```sql
CREATE TABLE traffic_patterns (
    id INTEGER PRIMARY KEY,
    timestamp INTEGER NOT NULL,
    total_requests INTEGER NOT NULL,
    k3s_requests INTEGER NOT NULL,
    knative_requests INTEGER NOT NULL,
    avg_response_time REAL NOT NULL,
    error_rate REAL NOT NULL,
    k3s_weight INTEGER NOT NULL,
    knative_weight INTEGER NOT NULL
);
```

#### 1.2 Linear Regression Model
```python
class TrafficPredictor:
    - prepare_features(df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]
    - train(df: pd.DataFrame) -> Dict[str, float]
    - predict(current_data: Dict) -> Dict[str, float]
    - save_model() -> bool
    - load_model() -> bool
```

**Model Features**:
- Traffic volume statistics (mean, std, trend)
- Backend distribution ratios
- Performance metrics (response time, error rate)
- Temporal features (hour of day, day of week with sinusoidal encoding)
- Trend analysis using polynomial fitting

**Performance Targets**:
- RMSE < 20% for 30-second forecasts
- Training time < 60 seconds for 24 hours of data
- Prediction latency < 100ms p95

#### 1.3 Prediction API Server
```python
FastAPI Application:
- POST /predict -> PredictionResponse
- GET /health -> HealthResponse
- POST /retrain -> RetrainResponse
- GET /metrics -> MetricsResponse
- GET /data/export -> DataExportResponse
```

**API Specifications**:
```python
class PredictionResponse:
    predicted_requests: float
    confidence: float
    timestamp: int
    model_performance: Dict[str, float]
    recommendation: Dict[str, int]
```

### 2. Intelligent Routing Controller

**Technology Stack**: Python 3.9 + asyncio + Poetry

#### 2.1 Routing Controller
```python
class IntelligentRoutingController:
    - start() -> None
    - _make_routing_decision() -> None
    - _get_prediction() -> Optional[Dict]
    - _calculate_intelligent_weights() -> Dict[str, int]
    - _apply_weight_changes() -> bool
```

**Decision Logic**:
1. Collect current traffic statistics
2. Request prediction from Prediction Engine
3. Calculate optimal weights based on prediction and confidence
4. Apply weight changes via HAProxy admin socket
5. Log decision with complete audit trail

#### 2.2 Weight Adjuster
```python
class HAProxyWeightAdjuster:
    - set_weights(k3s_weight: int, knative_weight: int) -> bool
    - get_current_weights() -> Dict[str, int]
    - test_connection() -> bool
```

**HAProxy Integration**:
- Unix socket communication with HAProxy admin interface
- Weight adjustment commands: `set weight backend/server weight`
- Health check validation before applying changes
- Rollback capability for failed adjustments

#### 2.3 Decision Logger
```python
class DecisionLogger:
    - log_decision(decision: Dict) -> None
    - get_decision_history() -> List[Dict]
    - export_decisions() -> bool
```

**Decision Schema**:
```python
{
    'timestamp': int,
    'decision_type': str,  # 'intelligent' | 'fallback'
    'current_stats': Dict,
    'prediction': Optional[Dict],
    'previous_weights': Dict[str, int],
    'target_weights': Dict[str, int],
    'weights_changed': bool,
    'decision_latency': float
}
```

#### 2.4 Fallback Handler
```python
class FallbackHandler:
    - get_fallback_weights(current_stats: Dict) -> Dict[str, int]
    - is_fallback_needed(consecutive_failures: int) -> bool
    - calculate_safe_weights() -> Dict[str, int]
```

**Fallback Strategies**:
- Return to Sprint 1 optimal weights (80/20) on prediction failure
- Conservative adjustment based on current load only
- Emergency fallback to k3s-only if critical failures detected

### 3. Enhanced Monitoring

**Technology Stack**: Prometheus + Grafana + Python custom metrics

#### 3.1 Custom Metrics Collection
```python
# Prediction accuracy metrics
prediction_rmse = Gauge('prediction_rmse_percent')
prediction_confidence = Histogram('prediction_confidence')
prediction_latency = Histogram('prediction_latency_seconds')

# Routing decision metrics
routing_decision_total = Counter('routing_decisions_total')
weight_change_total = Counter('weight_changes_total')
fallback_mode_total = Counter('fallback_mode_total')

# Cost optimization metrics
cost_efficiency_ratio = Gauge('cost_efficiency_ratio')
resource_utilization = Gauge('resource_utilization_percent')
```

#### 3.2 Dashboard Configuration
```json
{
  "dashboards": [
    {
      "title": "Intelligent Routing Overview",
      "panels": [
        "Prediction Accuracy (RMSE)",
        "Routing Decisions Timeline",
        "Weight Changes Frequency",
        "Cost Optimization Metrics"
      ]
    },
    {
      "title": "System Performance",
      "panels": [
        "End-to-End Latency",
        "Traffic Distribution",
        "Error Rate Tracking",
        "Resource Usage"
      ]
    }
  ]
}
```

## Data Flow Architecture

### 1. Prediction Flow
```
HAProxy Stats → Data Collector → SQLite Database → Linear Model → Prediction API
```

### 2. Routing Decision Flow
```
Current Stats → Prediction Request → Weight Calculation → HAProxy Update → Decision Log
```

### 3. Monitoring Flow
```
All Components → Prometheus Metrics → Grafana Dashboards → Alerts
```

## Integration Specifications

### 1. HAProxy Admin Socket Integration

**Socket Configuration** (Sprint 1 enhancement):
```
global
    stats socket /tmp/haproxy-admin.sock mode 660 level admin
```

**Command Interface**:
```bash
# Set backend server weights
echo "set weight hybrid-backend/k3s-backend 80" | socat - /tmp/haproxy-admin.sock
echo "set weight hybrid-backend/knative-backend 20" | socat - /tmp/haproxy-admin.sock

# Verify weight changes
echo "show stat" | socat - /tmp/haproxy-admin.sock
```

### 2. Prediction API Integration

**Request Format**:
```json
POST /predict
{
    "timestamp": 1690156800,
    "current_requests": 1500,
    "include_confidence": true
}
```

**Response Format**:
```json
{
    "predicted_requests": 1750.5,
    "confidence": 0.85,
    "timestamp": 1690156830,
    "model_performance": {
        "rmse": 12.5,
        "r2_score": 0.92
    },
    "recommendation": {
        "k3s_weight": 75,
        "knative_weight": 25
    }
}
```

### 3. Database Schema Design

**Historical Data Storage**:
```sql
-- Main traffic patterns table
CREATE TABLE traffic_patterns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp INTEGER NOT NULL,
    total_requests INTEGER NOT NULL,
    k3s_requests INTEGER NOT NULL,
    knative_requests INTEGER NOT NULL,
    avg_response_time REAL NOT NULL,
    error_rate REAL NOT NULL,
    k3s_weight INTEGER NOT NULL,
    knative_weight INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Routing decisions audit table
CREATE TABLE routing_decisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp INTEGER NOT NULL,
    decision_type TEXT NOT NULL,
    prediction_data TEXT,
    previous_weights TEXT NOT NULL,
    target_weights TEXT NOT NULL,
    weights_changed BOOLEAN NOT NULL,
    decision_latency REAL NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Model performance tracking
CREATE TABLE model_performance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp INTEGER NOT NULL,
    rmse REAL NOT NULL,
    r2_score REAL NOT NULL,
    training_samples INTEGER NOT NULL,
    model_version TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Performance Specifications

### 1. Latency Requirements

| Component | Target Latency | Measurement |
|-----------|---------------|-------------|
| Prediction API | < 100ms p95 | API response time |
| Weight Adjustment | < 5 seconds | HAProxy update to effect |
| Routing Decision | < 30 seconds | Complete cycle time |
| Model Training | < 60 seconds | 24 hours of data |

### 2. Accuracy Requirements

| Metric | Target | Measurement Method |
|--------|--------|--------------------|
| Prediction RMSE | < 20% | Rolling 1-hour validation |
| Prediction Confidence | > 70% | Routine traffic patterns |
| Weight Accuracy | ±5% | Actual vs target weights |
| System Availability | > 98% | Intelligent routing uptime |

### 3. Resource Specifications

| Component | RAM Allocation | CPU Allocation | Storage |
|-----------|---------------|----------------|---------|
| Prediction Engine | 1.2GB | 1.0 core | 1GB |
| Intelligent Router | 400MB | 0.5 core | 200MB |
| Enhanced Monitoring | 800MB | 0.5 core | 1GB |
| **Total Addition** | **2.4GB** | **2.0 cores** | **2.2GB** |
| **Sprint 1 Available** | **3.4GB** | **2.4 cores** | **17.8GB** |
| **Remaining Buffer** | **1.0GB** | **0.4 cores** | **15.6GB** |

## Security Considerations

### 1. API Security
- FastAPI with request validation and rate limiting
- No authentication required for internal services
- Input sanitization for all prediction requests
- Error handling without information disclosure

### 2. Socket Security
- HAProxy admin socket with restricted permissions (660)
- Local Unix socket only (no network exposure)
- Command validation before HAProxy execution
- Audit logging of all weight changes

### 3. Data Security
- SQLite database with appropriate file permissions
- No sensitive data in historical patterns
- Decision logs with configurable retention
- Model artifacts stored securely

## Error Handling and Resilience

### 1. Prediction Service Failures
```python
# Fallback strategy
if prediction_service_down:
    return fallback_weights(current_stats)
    
if prediction_confidence < threshold:
    return conservative_adjustment(current_stats)
    
if consecutive_failures > max_failures:
    enter_fallback_mode()
```

### 2. HAProxy Integration Failures
```python
# Weight adjustment resilience
try:
    apply_weights(target_weights)
except HAProxyError:
    log_failure()
    maintain_current_weights()
    schedule_retry()
```

### 3. Model Training Failures
```python
# Model management
if model_training_fails:
    use_previous_model()
    alert_operators()
    retry_with_reduced_data()
```

## Deployment Architecture

### 1. Poetry Package Management

**Project Structure**:
```
sprint-2/
├── pyproject.toml                 # Poetry configuration
├── poetry.lock                    # Locked dependencies
├── prediction-engine/
│   ├── pyproject.toml            # Package-specific config
│   └── src/                      # Source code
├── intelligent-router/
│   ├── pyproject.toml            # Package-specific config
│   └── src/                      # Source code
└── tests/                        # Integration tests
```

**Poetry Configuration**:
```toml
[tool.poetry]
name = "sprint2-intelligent-routing"
version = "2.0.0"
description = "Intelligent routing with load prediction"

[tool.poetry.dependencies]
python = "^3.9"
fastapi = "^0.100.0"
scikit-learn = "^1.3.0"
pandas = "^2.0.0"
uvicorn = "^0.23.0"

[tool.poetry.group.dev.dependencies]
pytest = "^7.4.0"
black = "^23.0.0"
flake8 = "^6.0.0"
```

### 2. Service Deployment

**Production Deployment**:
```bash
# Install dependencies
poetry install --only=main

# Start prediction service
poetry run python prediction-engine/src/prediction_server.py &

# Start intelligent router
poetry run python intelligent-router/src/routing_controller.py &

# Start enhanced monitoring
poetry run python monitoring-v2/src/metrics_collector.py &
```

### 3. Development Environment

**Development Setup**:
```bash
# Install all dependencies including dev
poetry install

# Run tests
poetry run pytest

# Code formatting
poetry run black .

# Linting
poetry run flake8
```

## Testing Strategy

### 1. Unit Testing
- Individual component testing with pytest
- Model accuracy validation with synthetic data
- API endpoint testing with FastAPI test client
- Database operations testing with SQLite

### 2. Integration Testing
- End-to-end intelligent routing workflow
- HAProxy integration with test socket
- Prediction API integration testing
- Monitoring metrics collection validation

### 3. Performance Testing
- Prediction latency under load
- Weight adjustment responsiveness
- Resource usage monitoring
- Extended operation testing (24+ hours)

### 4. Failure Testing
- Prediction service outage simulation
- HAProxy admin socket failure handling
- Model training failure scenarios
- Network partition resilience

## Migration Strategy from Sprint 1

### 1. Zero-Downtime Enhancement
1. Deploy Sprint 2 components alongside Sprint 1
2. Validate intelligent routing in read-only mode
3. Enable intelligent routing with manual override ready
4. Monitor performance and rollback if needed

### 2. Fallback Strategy
- Sprint 1 manual routing remains functional
- Instant fallback to 80/20 weights on failures
- Manual override capability always available
- Independent monitoring of Sprint 1 vs Sprint 2 performance

### 3. Configuration Management
- Sprint 1 HAProxy config enhanced (not replaced)
- Additional admin socket configuration
- Monitoring stack extension (not replacement)
- Backward compatibility maintained

---

This technical design provides comprehensive architecture for Sprint 2 intelligent routing while ensuring compatibility with Sprint 1's proven foundation and preparing for Sprint 3's advanced ML capabilities.