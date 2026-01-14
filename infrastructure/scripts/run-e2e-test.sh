#!/bin/bash
# End-to-End Integration Test Runner
# Runs full system: HAProxy + Prediction Server + Routing Controller + Load Test

set -e

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
SCENARIO=${1:-s4-hybrid-predictive}
WORKLOAD=${2:-steady}

echo "=============================================="
echo "End-to-End Integration Test"
echo "Scenario: $SCENARIO"
echo "Workload: $WORKLOAD"
echo "=============================================="
echo ""

# Step 1: Check prerequisites
echo "[1/5] Checking prerequisites..."

if ! command -v docker &> /dev/null; then
    echo "ERROR: docker not found"
    exit 1
fi

if ! command -v k6 &> /dev/null; then
    echo "WARNING: k6 not found - install with: brew install k6"
fi

echo "  ✓ Prerequisites OK"
echo ""

# Step 2: Start HAProxy
echo "[2/5] Starting HAProxy..."
cd "$PROJECT_ROOT/infrastructure/haproxy"
docker-compose up -d
sleep 2
echo "  ✓ HAProxy started on :8082"
echo ""

# Step 3: Start Prediction Server (if needed)
echo "[3/5] Starting Prediction Server..."
cd "$PROJECT_ROOT/controller"

# Kill any existing process
pkill -f "prediction_engine.prediction_server" 2>/dev/null || true
sleep 1

# Start in background
nohup uv run python -m prediction_engine.prediction_server > /tmp/prediction_server.log 2>&1 &
PRED_PID=$!
sleep 3

# Check if running
if curl -s http://localhost:8003/health > /dev/null; then
    echo "  ✓ Prediction Server started on :8003 (PID: $PRED_PID)"
else
    echo "  ✗ Prediction Server failed to start"
    cat /tmp/prediction_server.log
    exit 1
fi
echo ""

# Step 4: Verify HAProxy connectivity
echo "[4/5] Verifying HAProxy connectivity..."
if curl -s http://localhost:8082/ > /dev/null 2>&1; then
    echo "  ✓ HAProxy responding on :8082"
else
    echo "  ✗ HAProxy not responding"
    echo "  Note: Backend services may not be running"
fi

# Check stats
if curl -s http://localhost:8404/stats > /dev/null; then
    echo "  ✓ HAProxy stats available on :8404"
else
    echo "  ✗ HAProxy stats not available"
fi
echo ""

# Step 5: Run load test (if k6 available)
echo "[5/5] Running load test ($WORKLOAD)..."
if command -v k6 &> /dev/null; then
    cd "$PROJECT_ROOT"
    mkdir -p results/load-tests
    
    echo "  Starting k6 with $WORKLOAD workload..."
    k6 run --duration 30s \
        -e BASE_URL=http://localhost:8082 \
        "infrastructure/load-tests/${WORKLOAD}.js" 2>&1 | tail -20
    
    echo "  ✓ Load test complete"
else
    echo "  ⚠ k6 not installed - skipping load test"
    echo "    Install with: brew install k6"
fi
echo ""

# Summary
echo "=============================================="
echo "E2E Test Complete"
echo "=============================================="
echo "HAProxy:          http://localhost:8082"
echo "HAProxy Stats:    http://localhost:8404/stats"
echo "Prediction API:   http://localhost:8003"
echo ""
echo "To stop services:"
echo "  docker-compose -f infrastructure/haproxy/docker-compose.yml down"
echo "  kill $PRED_PID"
