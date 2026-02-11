# S4 Hybrid-Predictive Integration Guide

**Status:** GRU Model Integrated ✅  
**Model:** `controller/data/models/gru_model.pt` (621KB, PyTorch)  
**Performance:** 6.01% RMSE, 0.88 avg confidence

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        S4: Hybrid-Predictive                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────┐      HTTP:8090      ┌──────────────┐             │
│  │   routing    │ ◄────────────────── │ GRU Predict  │             │
│  │   daemon     │   /predict          │   Server     │             │
│  │   (S4)       │                     │  (PyTorch)   │             │
│  └──────┬───────┘                     └──────┬───────┘             │
│         │                                       │                    │
│         │                                       │                    │
│         ▼                                       ▼                    │
│  ┌──────────────┐                     ┌──────────────┐             │
│  │  Algorithm 1 │                     │  gru_model   │             │
│  │  Controller  │                     │   .pt        │             │
│  │              │                     │  (trained)   │             │
│  └──────┬───────┘                     └──────────────┘             │
│         │                                                            │
│         │ weight adjustments                                         │
│         ▼                                                            │
│  ┌──────────────┐                                                  │
│  │   HAProxy    │  ◄── traffic ──▶  K3s (80%) / Knative (20%)     │
│  └──────────────┘                                                  │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Components

### 1. GRU Prediction Server (Port 8090)

**File:** `controller/prediction/prediction_server.py`

```bash
# Start the prediction server
HSA_OVERRIDE_GFX_VERSION=11.0.0 sg render -c \
  "cd controller && uv run python -m prediction.prediction_server"
```

**Endpoints:**
- `GET /health` - Check model status
- `POST /predict` - Get prediction
- `GET /model/status` - Detailed model info

**Example Prediction Request:**
```bash
curl -X POST http://localhost:8090/predict \
  -H "Content-Type: application/json" \
  -d '{"history": [100, 105, 110, ...], "horizon": 1}'
```

### 2. Routing Daemon (S4 Scenario)

**File:** `controller/daemon/routing_daemon.py`

```bash
# Run S4 scenario
HSA_OVERRIDE_GFX_VERSION=11.0.0 sg render -c \
  "cd controller && uv run python -m daemon.routing_daemon --scenario s4-hybrid-predictive"
```

**S4 Configuration:**
```python
Scenario.S4_HYBRID_PREDICTIVE: ScenarioConfig(
    k3s_weight=80,
    knative_weight=20,
    use_algorithm=True,
    use_predictions=True,  # <-- GRU enabled
    description="Algorithm 1 with GRU predictions",
)
```

### 3. GRU Client

**File:** `controller/daemon/gru_client.py`

The client queries the prediction server and provides:
- `predicted_requests`: Forecast RPS
- `confidence`: 0.0-1.0 prediction confidence
- `latency_ms`: Response time

---

## Startup Sequence

### Step 1: Start Prediction Server
```bash
cd /home/zahid/work/master-s2-study/thesis-kubernetes-serverless-integration/controller

# Terminal 1: Start GRU prediction server
HSA_OVERRIDE_GFX_VERSION=11.0.0 sg render -c \
  "uv run python -m prediction.prediction_server"
```

Verify: `curl http://localhost:8090/health`

### Step 2: Start Routing Daemon (S4)
```bash
# Terminal 2: Run S4 scenario
HSA_OVERRIDE_GFX_VERSION=11.0.0 sg render -c \
  "uv run python -m daemon.routing_daemon --scenario s4-hybrid-predictive"
```

### Step 3: Verify Integration
```bash
# Check daemon logs for GRU predictions
# Look for: "GRU prediction received" or "PREDICTIVE decision"
```

---

## Testing the Integration

### Quick Test Script
```python
# test_s4_integration.py
import sys
sys.path.insert(0, 'controller')

from daemon.gru_client import GRUClient

client = GRUClient()

# Test 1: Health check
assert client.is_healthy(), "GRU server not healthy"
print("✅ GRU server healthy")

# Test 2: Prediction
result = client.predict([100] * 30, horizon=1)
assert result.success, f"Prediction failed: {result.error}"
print(f"✅ Prediction: {result.predicted_requests} RPS")
print(f"✅ Confidence: {result.confidence:.2f}")

print("\n🎉 S4 integration working!")
```

### Run Test
```bash
cd /home/zahid/work/master-s2-study/thesis-kubernetes-serverless-integration
uv run python test_s4_integration.py
```

---

## Troubleshooting

### Issue: "Model not loaded"
**Solution:**
```bash
# Verify model file exists
ls -lh controller/data/models/gru_model.pt

# Reload model via API
curl -X POST http://localhost:8090/model/reload
```

### Issue: "GPU not available"
**Solution:**
```bash
# Set environment variable
export HSA_OVERRIDE_GFX_VERSION=11.0.0
# Or add to ~/.bashrc
```

### Issue: "Connection refused" (port 8090)
**Solution:**
```bash
# Check if server is running
lsof -i :8090

# Start server if not running
uv run python -m prediction.prediction_server
```

---

## Metrics to Monitor

| Metric | Source | Target |
|--------|--------|--------|
| GRU Latency | Prediction server logs | <50ms |
| GRU Confidence | Prediction response | >0.7 for routing decisions |
| Prediction RMSE | Model metadata | 6.15% (validated) |
| PREDICTIVE decisions | Daemon logs | Should see PREDICTIVE actions |

---

## Summary

✅ **GRU Model:** Trained and saved (6.01% RMSE)  
✅ **Prediction Server:** FastAPI on port 8090  
✅ **GRU Client:** HTTP client for routing daemon  
✅ **S4 Scenario:** Configured with `use_predictions=True`  
✅ **GPU Acceleration:** ROCm working with gfx1103 override  

**Next:** Run load test against S4 scenario to validate end-to-end performance!
