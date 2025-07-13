#!/bin/bash

# Traffic Distribution Testing Script
# Tests HAProxy traffic routing and distribution accuracy

set -e

HAPROXY_ENDPOINT="http://localhost:8082"
K3S_ENDPOINT="http://localhost:8080" 
KNATIVE_ENDPOINT="http://localhost:8081"
STATS_ENDPOINT="http://localhost:8404/stats"
TEST_REQUESTS=20

echo "HAProxy Traffic Distribution Test"
echo "================================="

# Check if all endpoints are available
echo "1. Checking endpoint availability..."

if ! curl -s $K3S_ENDPOINT > /dev/null; then
    echo "❌ K3s cluster not available at $K3S_ENDPOINT"
    exit 1
fi

if ! curl -s -H "Host: serverless-sim.default.localhost" $KNATIVE_ENDPOINT > /dev/null; then
    echo "❌ Knative serverless not available at $KNATIVE_ENDPOINT"
    exit 1
fi

if ! curl -s $HAPROXY_ENDPOINT > /dev/null; then
    echo "❌ HAProxy not available at $HAPROXY_ENDPOINT"
    exit 1
fi

echo "✅ All endpoints available"

# Test traffic distribution
echo ""
echo "2. Testing traffic distribution with $TEST_REQUESTS requests..."

K3S_COUNT=0
KNATIVE_COUNT=0

for i in $(seq 1 $TEST_REQUESTS); do
    RESPONSE=$(curl -s $HAPROXY_ENDPOINT)
    
    if echo "$RESPONSE" | grep -q "K3s Cluster"; then
        ((K3S_COUNT++))
    elif echo "$RESPONSE" | grep -q "Knative Serverless"; then
        ((KNATIVE_COUNT++))
    else
        echo "⚠️  Unexpected response from request $i"
    fi
    
    # Brief delay to spread requests
    sleep 0.1
done

# Calculate percentages
K3S_PERCENT=$((K3S_COUNT * 100 / TEST_REQUESTS))
KNATIVE_PERCENT=$((KNATIVE_COUNT * 100 / TEST_REQUESTS))

echo ""
echo "3. Traffic Distribution Results:"
echo "   K3s Cluster: $K3S_COUNT/$TEST_REQUESTS ($K3S_PERCENT%)"
echo "   Knative Serverless: $KNATIVE_COUNT/$TEST_REQUESTS ($KNATIVE_PERCENT%)"

# Check if distribution is roughly correct (80/20 ±15%)
if [ $K3S_PERCENT -ge 65 ] && [ $K3S_PERCENT -le 95 ]; then
    echo "✅ K3s traffic distribution within expected range"
else
    echo "⚠️  K3s traffic distribution outside expected range (65-95%)"
fi

if [ $KNATIVE_PERCENT -ge 5 ] && [ $KNATIVE_PERCENT -le 35 ]; then
    echo "✅ Knative traffic distribution within expected range"
else
    echo "⚠️  Knative traffic distribution outside expected range (5-35%)"
fi

# Test stats endpoint
echo ""
echo "4. HAProxy Stats Check:"
if curl -s $STATS_ENDPOINT | grep -q "HAProxy Statistics"; then
    echo "✅ Stats endpoint accessible at $STATS_ENDPOINT"
else
    echo "❌ Stats endpoint not accessible"
fi

echo ""
echo "5. Current Backend Status:"
curl -s $STATS_ENDPOINT | grep -E "k3s-cluster|serverless-sim" | head -2 || echo "Unable to fetch backend status"

echo ""
echo "Traffic test completed!"
echo "View detailed stats at: $STATS_ENDPOINT"