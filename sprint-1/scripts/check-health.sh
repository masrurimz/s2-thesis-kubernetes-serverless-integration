#!/bin/bash
# Sprint 1 - System Health Check Script
# LLM Implementation: Day 3 Monitoring

set -e

echo "🔍 Sprint 1 Hybrid System Health Check"
echo "======================================"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Health check functions
check_component() {
    local name="$1"
    local url="$2"
    local expected_code="${3:-200}"
    
    echo -n "Checking $name... "
    
    if curl -s -o /dev/null -w "%{http_code}" "$url" | grep -q "$expected_code"; then
        echo -e "${GREEN}✅ UP${NC}"
        return 0
    else
        echo -e "${RED}❌ DOWN${NC}"
        return 1
    fi
}

check_metrics() {
    local service="$1"
    local query="$2"
    
    echo -n "Checking $service metrics... "
    
    if curl -s "http://localhost:9090/api/v1/query?query=$query" | jq -r '.status' | grep -q "success"; then
        echo -e "${GREEN}✅ OK${NC}"
        return 0
    else
        echo -e "${RED}❌ FAIL${NC}"
        return 1
    fi
}

# Start health checks
echo "📋 Component Status:"
echo "-------------------"

# Core components
check_component "K3s Backend" "http://localhost:8080" || K3S_FAIL=1
check_component "Knative Serverless" "http://localhost:8081" || KNATIVE_FAIL=1
check_component "HAProxy Router" "http://localhost:8082" || HAPROXY_FAIL=1
check_component "HAProxy Stats" "http://localhost:8404/stats" || STATS_FAIL=1
check_component "Prometheus" "http://localhost:9090/-/healthy" || PROMETHEUS_FAIL=1

echo ""
echo "📊 Metrics Validation:"
echo "---------------------"

# Metrics checks
check_metrics "HAProxy" "up{job=\"haproxy\"}" || HAPROXY_METRICS_FAIL=1
check_metrics "Prometheus" "up{job=\"prometheus\"}" || PROMETHEUS_METRICS_FAIL=1
check_metrics "Traffic Distribution" "hybrid:traffic_distribution:k3s_percentage" || TRAFFIC_METRICS_FAIL=1

echo ""
echo "🎯 Traffic Distribution:"
echo "-----------------------"

# Get traffic distribution from Prometheus
K3S_PERCENT=$(curl -s "http://localhost:9090/api/v1/query?query=hybrid:traffic_distribution:k3s_percentage" | jq -r '.data.result[0].value[1]' 2>/dev/null || echo "N/A")
SERVERLESS_PERCENT=$(curl -s "http://localhost:9090/api/v1/query?query=hybrid:traffic_distribution:serverless_percentage" | jq -r '.data.result[0].value[1]' 2>/dev/null || echo "N/A")

echo "K3s Cluster: ${K3S_PERCENT}%"
echo "Serverless: ${SERVERLESS_PERCENT}%"

# Traffic distribution validation
if [[ "$K3S_PERCENT" != "N/A" ]] && [[ "$SERVERLESS_PERCENT" != "N/A" ]]; then
    # Check if within expected ranges (70-90% for K3s, 10-30% for serverless)
    if (( $(echo "$K3S_PERCENT >= 70 && $K3S_PERCENT <= 90" | bc -l) )); then
        echo -e "Traffic Distribution: ${GREEN}✅ HEALTHY (within 80/20 ±10%)${NC}"
    else
        echo -e "Traffic Distribution: ${YELLOW}⚠️ WARNING (outside expected range)${NC}"
        TRAFFIC_DISTRIBUTION_WARN=1
    fi
else
    echo -e "Traffic Distribution: ${RED}❌ NO DATA${NC}"
    TRAFFIC_DISTRIBUTION_FAIL=1
fi

echo ""
echo "🔧 Resource Utilization:"
echo "------------------------"

# Container resource usage
echo "Docker Containers:"
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" \
    sprint1-haproxy sprint1-prometheus 2>/dev/null || echo "Containers not running"

echo ""
echo "📈 Recent Performance:"
echo "---------------------"

# Get recent response times
AVG_RESPONSE=$(curl -s "http://localhost:9090/api/v1/query?query=hybrid:response_time:weighted_average" | jq -r '.data.result[0].value[1]' 2>/dev/null || echo "N/A")
REQUEST_RATE=$(curl -s "http://localhost:9090/api/v1/query?query=rate(hybrid:request_rate:total[5m])" | jq -r '.data.result[0].value[1]' 2>/dev/null || echo "N/A")

echo "Average Response Time: ${AVG_RESPONSE}s"
echo "Request Rate (5m): ${REQUEST_RATE} req/s"

# Performance validation
if [[ "$AVG_RESPONSE" != "N/A" ]]; then
    if (( $(echo "$AVG_RESPONSE < 0.2" | bc -l) )); then
        echo -e "Performance: ${GREEN}✅ GOOD (<200ms average)${NC}"
    else
        echo -e "Performance: ${YELLOW}⚠️ SLOW (>200ms average)${NC}"
        PERFORMANCE_WARN=1
    fi
fi

echo ""
echo "📋 Overall System Status:"
echo "========================"

# Calculate overall health
FAILURES=0
WARNINGS=0

[[ -n "$K3S_FAIL" ]] && ((FAILURES++))
[[ -n "$KNATIVE_FAIL" ]] && ((FAILURES++))
[[ -n "$HAPROXY_FAIL" ]] && ((FAILURES++))
[[ -n "$STATS_FAIL" ]] && ((FAILURES++))
[[ -n "$PROMETHEUS_FAIL" ]] && ((FAILURES++))
[[ -n "$HAPROXY_METRICS_FAIL" ]] && ((FAILURES++))
[[ -n "$PROMETHEUS_METRICS_FAIL" ]] && ((FAILURES++))
[[ -n "$TRAFFIC_METRICS_FAIL" ]] && ((FAILURES++))
[[ -n "$TRAFFIC_DISTRIBUTION_FAIL" ]] && ((FAILURES++))

[[ -n "$TRAFFIC_DISTRIBUTION_WARN" ]] && ((WARNINGS++))
[[ -n "$PERFORMANCE_WARN" ]] && ((WARNINGS++))

if [[ $FAILURES -eq 0 && $WARNINGS -eq 0 ]]; then
    echo -e "Status: ${GREEN}✅ ALL SYSTEMS HEALTHY${NC}"
    exit 0
elif [[ $FAILURES -eq 0 ]]; then
    echo -e "Status: ${YELLOW}⚠️ HEALTHY WITH WARNINGS ($WARNINGS warnings)${NC}"
    exit 1
else
    echo -e "Status: ${RED}❌ SYSTEM ISSUES DETECTED ($FAILURES failures, $WARNINGS warnings)${NC}"
    exit 2
fi